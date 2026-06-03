# Authentication signal collectors for the macOS security dashboard.
# Checks: Failed Logins (unified log via `log show`), SSH Authorized Keys (file read).
# Both signals return WARN when activity is detected, PASS when clean.
# `log show` requires Full Disk Access; empty output without an error is treated as UNKNOWN.

from pathlib import Path

try:
    from .utils import run_cmd, make_result
except ImportError:
    from utils import run_cmd, make_result  # noqa: F401 — direct script execution

# Case-sensitive predicates — CONTAINS[c] is intentional.
# loginwindow uses all-caps "FAILED"; sshd uses title-case "Failed"/"Invalid".
# A case-insensitive match would catch unrelated clipboard log entries (false positives).
_FAILED_LOGIN_PREDICATE = (
    '(process == "loginwindow" AND eventMessage CONTAINS "FAILED")'
    ' OR '
    '(process == "sshd" AND (eventMessage CONTAINS "Failed" OR eventMessage CONTAINS "Invalid"))'
)


def check_failed_logins() -> dict:
    """Query the unified log for failed GUI and SSH login attempts in the past 24 hours."""
    name = "Failed Logins"
    desc = (
        "Failed login attempts via the macOS login screen or SSH in the past 24h. "
        "WARN means failures were detected — review if unexpected."
    )
    raw, error = run_cmd(
        ["log", "show", "--predicate", _FAILED_LOGIN_PREDICATE, "--last", "24h", "--style", "compact"],
        timeout=30,
    )
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)
    # Empty output with no error means Full Disk Access was denied — not a clean result.
    if not raw:
        return make_result(
            name, desc, "UNKNOWN", "",
            "log show returned no output — Full Disk Access may be required",
        )
    lines = [ln for ln in raw.splitlines() if ln.strip() and not ln.startswith("Timestamp")]
    if not lines:
        return make_result(name, desc, "PASS", "No failed login events in past 24h.")
    # Cap displayed output at 20 lines to keep the dashboard readable.
    trimmed = "\n".join(lines[:20])
    suffix = f"\n... ({len(lines) - 20} more lines)" if len(lines) > 20 else ""
    return make_result(name, desc, "WARN", trimmed + suffix)


def check_ssh_keys() -> dict:
    """Check ~/.ssh/authorized_keys for any keys that permit remote login to this machine."""
    name = "SSH Authorized Keys"
    desc = (
        "Keys in ~/.ssh/authorized_keys that allow remote login to this machine. "
        "WARN means remote key-based access is enabled — review if unexpected."
    )
    path = Path.home() / ".ssh" / "authorized_keys"
    try:
        if not path.exists():
            return make_result(name, desc, "PASS", "No authorized keys found.")
        # Skip blank lines and comments — only count active key entries.
        lines = [ln for ln in path.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
        if not lines:
            return make_result(name, desc, "PASS", "No authorized keys found.")
        return make_result(name, desc, "WARN", "\n".join(lines))
    except OSError as e:
        return make_result(name, desc, "UNKNOWN", "", str(e))


if __name__ == "__main__":
    # Quick smoke-test: run this file directly to see current signal output.
    checks = [
        ("Failed Logins", check_failed_logins),
        ("SSH Authorized Keys", check_ssh_keys),
    ]
    for label, fn in checks:
        result = fn()
        preview = result["raw"][:120].replace("\n", " ").strip()
        ellipsis = "..." if len(result["raw"]) > 120 else ""
        print(f"[{result['status']:^7}] {label}")
        print(f"         raw: {preview!r}{ellipsis}")
        if result["error"]:
            print(f"         error: {result['error']}")
        print()
