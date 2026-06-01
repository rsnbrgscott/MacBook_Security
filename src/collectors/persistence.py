import subprocess
from pathlib import Path


def _run(cmd: list[str], timeout: int = 10) -> tuple[str, str | None]:
    """Run cmd, return (output, error). Never raises."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip() or result.stderr.strip()
        if not output and result.returncode != 0:
            return "", f"Command exited {result.returncode}: {' '.join(cmd)}"
        return output, None
    except subprocess.TimeoutExpired:
        return "", f"Timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return "", str(e)


def _read_plists(path: Path, filter_apple: bool = False) -> tuple[list[str], str | None]:
    """Return (plist_names, error). Never raises."""
    try:
        if not path.exists():
            return [], None
        entries = [p.name for p in path.iterdir() if p.suffix == ".plist"]
        if filter_apple:
            entries = [e for e in entries if not e.startswith("com.apple.")]
        return sorted(entries), None
    except OSError as e:
        return [], str(e)


def check_user_launch_agents() -> dict:
    name = "User Launch Agents"
    desc = "Per-user background tasks in ~/Library/LaunchAgents/. WARN means items are present — review them."
    entries, error = _read_plists(Path.home() / "Library" / "LaunchAgents")
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": "", "error": error}
    if entries:
        return {"name": name, "description": desc, "status": "WARN", "raw": "\n".join(entries), "error": None}
    return {"name": name, "description": desc, "status": "PASS", "raw": "No entries found.", "error": None}


def check_global_launch_agents() -> dict:
    name = "Global Launch Agents"
    desc = "System-wide background tasks in /Library/LaunchAgents/. Non-Apple entries are shown as WARN for review."
    entries, error = _read_plists(Path("/Library/LaunchAgents"), filter_apple=True)
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": "", "error": error}
    if entries:
        return {"name": name, "description": desc, "status": "WARN", "raw": "\n".join(entries), "error": None}
    return {"name": name, "description": desc, "status": "PASS", "raw": "Apple system entries only.", "error": None}


def check_launch_daemons() -> dict:
    name = "Launch Daemons"
    desc = "Privileged background services in /Library/LaunchDaemons/. Non-Apple entries are shown as WARN for review."
    entries, error = _read_plists(Path("/Library/LaunchDaemons"), filter_apple=True)
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": "", "error": error}
    if entries:
        return {"name": name, "description": desc, "status": "WARN", "raw": "\n".join(entries), "error": None}
    return {"name": name, "description": desc, "status": "PASS", "raw": "Apple system entries only.", "error": None}


def check_login_items() -> dict:
    name = "Login Items"
    desc = "Applications and helpers that launch at login. WARN means items are registered — review them."
    raw, error = _run(
        ["osascript", "-e", "tell application \"System Events\" to get the name of every login item"]
    )
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    items = [item.strip() for item in raw.split(",") if item.strip()] if raw else []
    if items:
        return {"name": name, "description": desc, "status": "WARN", "raw": "\n".join(items), "error": None}
    return {"name": name, "description": desc, "status": "PASS", "raw": "No login items registered.", "error": None}


if __name__ == "__main__":
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
