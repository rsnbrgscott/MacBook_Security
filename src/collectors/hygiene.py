"""Software hygiene signal collectors: Automatic Updates, Root Certificate Trust, Screen Lock.

Detection uses defaults(1), security(1), and osascript for System Events.
No sudo required.

Absent-key semantics (verified on macOS 26):
  - AutomaticCheckEnabled absent → macOS default (enabled) → PASS
  - askForPasswordDelay absent → 0s delay → PASS
  - security dump-trust-settings -d exits 1 with "No Trust Settings were found."
    when the system trust store is empty — treated as PASS.
"""

import subprocess


def _run(cmd: list[str], timeout: int = 10) -> tuple[str, int, str | None]:
    """Run cmd, return (stdout_or_stderr, returncode, error). Never raises."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = proc.stdout.strip() or proc.stderr.strip()
        return output, proc.returncode, None
    except subprocess.TimeoutExpired:
        return "", -1, f"Timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return "", -1, f"Command not found: {cmd[0]}"
    except OSError as e:
        return "", -1, str(e)


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

    auto_raw, auto_rc, auto_err = _run(
        ["defaults", "read", _pref, "AutomaticCheckEnabled"]
    )
    if auto_err:
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": "", "error": auto_err,
        }

    if auto_rc == 1:
        # Key absent — macOS default is enabled; all update sub-settings also default on.
        return {
            "name": name, "description": desc, "status": "PASS",
            "raw": "AutomaticCheckEnabled: absent (macOS default: on)",
            "error": None,
        }

    if auto_raw == "0":
        return {
            "name": name, "description": desc, "status": "FAIL",
            "raw": "AutomaticCheckEnabled: 0 (disabled)",
            "error": None,
        }

    if auto_raw != "1":
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": auto_raw,
            "error": f"Unexpected AutomaticCheckEnabled value: {auto_raw!r}",
        }

    # AutomaticCheckEnabled = 1; check whether critical/security updates auto-install.
    crit_raw, crit_rc, crit_err = _run(
        ["defaults", "read", _pref, "CriticalUpdateInstall"]
    )
    if crit_err:
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": auto_raw, "error": crit_err,
        }

    if crit_rc == 1:
        # Key absent — macOS default is enabled.
        return {
            "name": name, "description": desc, "status": "PASS",
            "raw": (
                "AutomaticCheckEnabled: 1, "
                "CriticalUpdateInstall: absent (macOS default: on)"
            ),
            "error": None,
        }

    if crit_raw == "1":
        return {
            "name": name, "description": desc, "status": "PASS",
            "raw": "AutomaticCheckEnabled: 1, CriticalUpdateInstall: 1",
            "error": None,
        }

    if crit_raw == "0":
        return {
            "name": name, "description": desc, "status": "WARN",
            "raw": (
                "AutomaticCheckEnabled: 1, "
                "CriticalUpdateInstall: 0 (security updates not auto-installed)"
            ),
            "error": None,
        }

    return {
        "name": name, "description": desc, "status": "UNKNOWN",
        "raw": crit_raw,
        "error": f"Unexpected CriticalUpdateInstall value: {crit_raw!r}",
    }


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
    raw, rc, err = _run(["security", "dump-trust-settings", "-d"])
    if err:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": err}

    # Exits 1 with this message when the store is empty — PASS, not an error.
    if "No Trust Settings were found." in raw:
        return {
            "name": name, "description": desc, "status": "PASS",
            "raw": "No Trust Settings were found.", "error": None,
        }

    if rc != 0:
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": raw, "error": f"security dump-trust-settings exited {rc}",
        }

    return {"name": name, "description": desc, "status": "WARN", "raw": raw, "error": None}


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

    pw_raw, pw_rc, pw_err = _run(
        [
            "osascript", "-e",
            "tell application \"System Events\" to tell security preferences"
            " to return require password to wake",
        ],
        timeout=15,
    )
    if pw_err:
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": pw_raw, "error": pw_err,
        }
    if pw_rc != 0:
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": pw_raw, "error": f"osascript exited {pw_rc}: {pw_raw!r}",
        }

    if pw_raw.strip().lower() == "false":
        return {
            "name": name, "description": desc, "status": "FAIL",
            "raw": "require password to wake: false",
            "error": None,
        }

    if pw_raw.strip().lower() != "true":
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": pw_raw, "error": f"Unexpected osascript output: {pw_raw!r}",
        }

    # Password is required; check grace-period delay.
    delay_raw, delay_rc, delay_err = _run(
        ["defaults", "-currentHost", "read", "com.apple.screensaver", "askForPasswordDelay"]
    )
    if delay_err:
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": pw_raw, "error": delay_err,
        }

    if delay_rc == 1:
        # Key absent = 0s delay = immediate lock.
        return {
            "name": name, "description": desc, "status": "PASS",
            "raw": "require password to wake: true, delay: absent (0s — immediate)",
            "error": None,
        }

    try:
        delay_seconds = int(float(delay_raw.strip()))
    except ValueError:
        return {
            "name": name, "description": desc, "status": "UNKNOWN",
            "raw": delay_raw,
            "error": f"Unexpected askForPasswordDelay value: {delay_raw!r}",
        }

    if delay_seconds == 0:
        return {
            "name": name, "description": desc, "status": "PASS",
            "raw": "require password to wake: true, delay: 0s (immediate)",
            "error": None,
        }

    return {
        "name": name, "description": desc, "status": "WARN",
        "raw": f"require password to wake: true, delay: {delay_seconds}s",
        "error": None,
    }


if __name__ == "__main__":
    checks = [
        ("Automatic Updates", check_auto_updates),
        ("Root Certificate Trust", check_root_certificates),
        ("Screen Lock", check_screen_lock),
    ]
    for label, fn in checks:
        sig = fn()
        print(f"[{sig['status']:^7}] {label}")
        print(f"         raw: {sig['raw']!r}")
        if sig["error"]:
            print(f"         error: {sig['error']}")
        print()
