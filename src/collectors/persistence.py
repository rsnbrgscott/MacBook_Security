"""Persistence signal collectors: User/Global LaunchAgents, LaunchDaemons, Login Items.

All checks are read-only filesystem or AppleScript queries — no elevated privileges needed.
WARN is the expected result on most machines; raw output lets the user decide what's unusual.
"""

from pathlib import Path

try:
    from .utils import run_cmd, make_result
except ImportError:
    from utils import run_cmd, make_result  # noqa: F401 — direct script execution


def _read_plists(path: Path, filter_apple: bool = False) -> tuple[list[str], str | None]:
    """List .plist filenames in path; strip com.apple.* entries when filter_apple=True."""
    try:
        if not path.exists():
            return [], None
        entries = [p.name for p in path.iterdir() if p.suffix == ".plist"]
        if filter_apple:
            # Global locations contain hundreds of Apple-owned plists by design;
            # only third-party entries are security-relevant.
            entries = [e for e in entries if not e.startswith("com.apple.")]
        return sorted(entries), None
    except OSError as e:
        return [], str(e)


def check_user_launch_agents() -> dict:
    """List per-user LaunchAgents in ~/Library/LaunchAgents/; WARN if any are present."""
    name = "User Launch Agents"
    desc = (
        "Per-user background tasks in ~/Library/LaunchAgents/. "
        "WARN means items are present — review them."
    )
    entries, error = _read_plists(Path.home() / "Library" / "LaunchAgents")
    if error:
        return make_result(name, desc, "UNKNOWN", "", error)
    if entries:
        return make_result(name, desc, "WARN", "\n".join(entries))
    return make_result(name, desc, "PASS", "No entries found.")


def check_global_launch_agents() -> dict:
    """List non-Apple LaunchAgents in /Library/LaunchAgents/; WARN if third-party entries exist."""
    name = "Global Launch Agents"
    desc = (
        "System-wide background tasks in /Library/LaunchAgents/. "
        "Non-Apple entries are shown as WARN for review."
    )
    entries, error = _read_plists(Path("/Library/LaunchAgents"), filter_apple=True)
    if error:
        return make_result(name, desc, "UNKNOWN", "", error)
    if entries:
        return make_result(name, desc, "WARN", "\n".join(entries))
    return make_result(name, desc, "PASS", "Apple system entries only.")


def check_launch_daemons() -> dict:
    """List non-Apple LaunchDaemons in /Library/LaunchDaemons/; WARN if third-party entries exist."""
    name = "Launch Daemons"
    desc = (
        "Privileged background services in /Library/LaunchDaemons/. "
        "Non-Apple entries are shown as WARN for review."
    )
    entries, error = _read_plists(Path("/Library/LaunchDaemons"), filter_apple=True)
    if error:
        return make_result(name, desc, "UNKNOWN", "", error)
    if entries:
        return make_result(name, desc, "WARN", "\n".join(entries))
    return make_result(name, desc, "PASS", "Apple system entries only.")


def check_login_items() -> dict:
    """Query System Events for registered login items via AppleScript; WARN if any are found."""
    name = "Login Items"
    desc = (
        "Applications and helpers that launch at login. "
        "WARN means items are registered — review them."
    )
    raw, error = run_cmd(
        ["osascript", "-e", "tell application \"System Events\" to get the name of every login item"]
    )
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)
    # AppleScript returns a comma-separated string; split and strip whitespace.
    items = [item.strip() for item in raw.split(",") if item.strip()] if raw else []
    if items:
        return make_result(name, desc, "WARN", "\n".join(items))
    return make_result(name, desc, "PASS", "No login items registered.")


if __name__ == "__main__":
    # Quick smoke-test: run this file directly to see current signal output.
    checks = [
        ("User Launch Agents", check_user_launch_agents),
        ("Global Launch Agents", check_global_launch_agents),
        ("Launch Daemons", check_launch_daemons),
        ("Login Items", check_login_items),
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
