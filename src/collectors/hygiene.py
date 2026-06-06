"""Software hygiene signal collectors: Automatic Updates, Root Certificate Trust, Screen Lock, Screensaver Idle Timeout.

Detection uses defaults(1), security(1), and osascript for System Events.
No sudo required.

Absent-key semantics (verified on macOS 26):
  - AutomaticCheckEnabled absent → macOS default (enabled) → PASS
  - askForPasswordDelay absent → 0s delay → PASS
  - security dump-trust-settings -d exits 1 with "No Trust Settings were found."
    when the system trust store is empty — treated as PASS.
"""

try:
    from .utils import run_cmd_rc, make_result
except ImportError:
    from utils import run_cmd_rc, make_result  # noqa: F401 — direct script execution


def check_auto_updates() -> dict:
    """Check whether macOS automatic updates are enabled.

    Reads AutomaticCheckEnabled and CriticalUpdateInstall from the system
    SoftwareUpdate preferences. Key absent = macOS default (enabled) = PASS.

    FAIL  — AutomaticCheckEnabled explicitly set to 0
    WARN  — Auto-check on but CriticalUpdateInstall explicitly set to 0
    PASS  — Auto-check on (or default) and CriticalUpdateInstall on (or default)
    """
    name = "Automatic Updates"
    desc = (
        "Automatic Updates ensure macOS downloads and installs security patches "
        "without requiring manual action. Disabling them leaves known vulnerabilities "
        "unpatched."
    )
    _pref = "/Library/Preferences/com.apple.SoftwareUpdate"

    auto_raw, auto_rc, auto_err = run_cmd_rc(
        ["defaults", "read", _pref, "AutomaticCheckEnabled"]
    )
    if auto_err:
        return make_result(name, desc, "UNKNOWN", "", auto_err)

    if auto_rc == 1:
        # Key absent — macOS default is enabled; all update sub-settings also default on.
        return make_result(name, desc, "PASS", "AutomaticCheckEnabled: absent (macOS default: on)")

    if auto_raw == "0":
        return make_result(name, desc, "FAIL", "AutomaticCheckEnabled: 0 (disabled)")

    if auto_raw != "1":
        return make_result(
            name, desc, "UNKNOWN", auto_raw,
            f"Unexpected AutomaticCheckEnabled value: {auto_raw!r}",
        )

    # AutomaticCheckEnabled = 1; check whether critical/security updates auto-install.
    crit_raw, crit_rc, crit_err = run_cmd_rc(
        ["defaults", "read", _pref, "CriticalUpdateInstall"]
    )
    if crit_err:
        return make_result(name, desc, "UNKNOWN", auto_raw, crit_err)

    if crit_rc == 1:
        # Key absent — macOS default is enabled.
        return make_result(
            name, desc, "PASS",
            "AutomaticCheckEnabled: 1, CriticalUpdateInstall: absent (macOS default: on)",
        )

    if crit_raw == "1":
        return make_result(name, desc, "PASS", "AutomaticCheckEnabled: 1, CriticalUpdateInstall: 1")

    if crit_raw == "0":
        return make_result(
            name, desc, "WARN",
            "AutomaticCheckEnabled: 1, CriticalUpdateInstall: 0 (security updates not auto-installed)",
        )

    return make_result(
        name, desc, "UNKNOWN", crit_raw,
        f"Unexpected CriticalUpdateInstall value: {crit_raw!r}",
    )


def check_root_certificates() -> dict:
    """Check for custom CA trust anchors in the system trust-settings domain.

    Uses `security dump-trust-settings -d` which reads the system-domain
    trust overrides — the same store that can be used to install rogue CA
    certificates for HTTPS interception. Apple-managed certs are never
    represented here; only explicitly added trust overrides appear.

    PASS  — "No Trust Settings were found." (no custom CAs)
    WARN  — One or more custom trust anchors are present; user should review
    """
    name = "Root Certificate Trust"
    desc = (
        "Custom root CA certificates added to the system trust store can silently "
        "intercept HTTPS connections. This checks for non-Apple trust overrides in "
        "the system domain."
    )
    raw, rc, err = run_cmd_rc(["security", "dump-trust-settings", "-d"])
    if err:
        return make_result(name, desc, "UNKNOWN", raw, err)

    # Exits 1 with this message when the store is empty — PASS, not an error.
    if "No Trust Settings were found." in raw:
        return make_result(name, desc, "PASS", "No Trust Settings were found.")

    if rc != 0:
        return make_result(name, desc, "UNKNOWN", raw, f"security dump-trust-settings exited {rc}")

    return make_result(name, desc, "WARN", raw)


def check_screen_lock() -> dict:
    """Check whether a password is required when waking from sleep or screensaver.

    Uses the System Events API (no TCC permission required on macOS 26) to read
    the effective password-on-wake state. If enabled, checks askForPasswordDelay
    (absent = 0s = immediate lock).

    FAIL  — Password not required on wake
    WARN  — Password required but with a non-zero delay (grace period)
    PASS  — Password required immediately on wake (delay = 0 or absent)
    """
    name = "Screen Lock"
    desc = (
        "Requiring a password when waking from sleep or screensaver prevents "
        "unauthorised access when the machine is left unattended."
    )

    pw_raw, pw_rc, pw_err = run_cmd_rc(
        [
            "osascript", "-e",
            "tell application \"System Events\" to tell security preferences"
            " to return require password to wake",
        ],
        timeout=15,
    )
    if pw_err:
        return make_result(name, desc, "UNKNOWN", pw_raw, pw_err)
    if pw_rc != 0:
        return make_result(name, desc, "UNKNOWN", pw_raw, f"osascript exited {pw_rc}: {pw_raw!r}")

    if pw_raw.strip().lower() == "false":
        return make_result(name, desc, "FAIL", "require password to wake: false")

    if pw_raw.strip().lower() != "true":
        return make_result(name, desc, "UNKNOWN", pw_raw, f"Unexpected osascript output: {pw_raw!r}")

    # Password is required; check grace-period delay.
    delay_raw, delay_rc, delay_err = run_cmd_rc(
        ["defaults", "-currentHost", "read", "com.apple.screensaver", "askForPasswordDelay"]
    )
    if delay_err:
        return make_result(name, desc, "UNKNOWN", pw_raw, delay_err)

    if delay_rc == 1:
        # Key absent = 0s delay = immediate lock.
        return make_result(
            name, desc, "PASS",
            "require password to wake: true, delay: absent (0s — immediate)",
        )

    try:
        delay_seconds = int(float(delay_raw.strip()))
    except ValueError:
        return make_result(
            name, desc, "UNKNOWN", delay_raw,
            f"Unexpected askForPasswordDelay value: {delay_raw!r}",
        )

    if delay_seconds == 0:
        return make_result(name, desc, "PASS", "require password to wake: true, delay: 0s (immediate)")

    return make_result(
        name, desc, "WARN",
        f"require password to wake: true, delay: {delay_seconds}s",
    )


def check_screensaver_idle_timeout() -> dict:
    """FAIL if screensaver idle timeout is 0 or absent; WARN if > 10 min; PASS if 0 < value ≤ 600 s."""
    name = "Screensaver Idle Timeout"
    desc = (
        "How long the machine must be idle before the screensaver engages and locks "
        "the screen. A long timeout leaves the screen accessible while unattended even "
        "if lock-on-wake is configured correctly."
    )
    out, rc, err = run_cmd_rc(
        ["defaults", "-currentHost", "read", "com.apple.screensaver", "idleTime"],
        timeout=5,
    )
    if err:
        return make_result(name, desc, "UNKNOWN", "", err)
    if rc != 0 and "does not exist" in out:
        return make_result(
            name, desc, "FAIL",
            "idleTime: absent (screensaver not configured; screen will not auto-lock on idle)",
        )
    if rc != 0:
        return make_result(name, desc, "UNKNOWN", out, f"defaults exited {rc}")
    try:
        seconds = int(out)
    except ValueError:
        return make_result(name, desc, "UNKNOWN", out, f"Non-integer value: {out!r}")
    if seconds == 0:
        return make_result(
            name, desc, "FAIL",
            "idleTime: 0 (Never — screen will not auto-lock on idle)",
        )
    if seconds > 600:
        return make_result(
            name, desc, "WARN",
            f"idleTime: {seconds} s (> 10 min recommended maximum)",
        )
    return make_result(name, desc, "PASS", f"idleTime: {seconds} s")


if __name__ == "__main__":
    checks = [
        ("Automatic Updates", check_auto_updates),
        ("Root Certificate Trust", check_root_certificates),
        ("Screen Lock", check_screen_lock),
        ("Screensaver Idle Timeout", check_screensaver_idle_timeout),
    ]
    for label, fn in checks:
        sig = fn()
        print(f"[{sig['status']:^7}] {label}")
        print(f"         raw: {sig['raw']!r}")
        if sig["error"]:
            print(f"         error: {sig['error']}")
        print()
