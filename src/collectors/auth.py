import subprocess
from pathlib import Path

_FAILED_LOGIN_PREDICATE = (
    '(process == "loginwindow" AND eventMessage CONTAINS "FAILED")'
    ' OR '
    '(process == "sshd" AND (eventMessage CONTAINS "Failed" OR eventMessage CONTAINS "Invalid"))'
)


def _run(cmd: list[str], timeout: int = 30) -> tuple[str, str | None]:
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


def check_failed_logins() -> dict:
    name = "Failed Logins"
    desc = (
        "Failed login attempts via the macOS login screen or SSH in the past 24h. "
        "WARN means failures were detected — review if unexpected."
    )
    raw, error = _run(
        ["log", "show", "--predicate", _FAILED_LOGIN_PREDICATE, "--last", "24h", "--style", "compact"],
        timeout=30,
    )
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    if not raw:
        return {
            "name": name, "description": desc, "status": "UNKNOWN", "raw": "",
            "error": "log show returned no output — Full Disk Access may be required",
        }
    lines = [ln for ln in raw.splitlines() if ln.strip() and not ln.startswith("Timestamp")]
    if not lines:
        return {"name": name, "description": desc, "status": "PASS", "raw": "No failed login events in past 24h.", "error": None}
    trimmed = "\n".join(lines[:20])
    suffix = f"\n... ({len(lines) - 20} more lines)" if len(lines) > 20 else ""
    return {"name": name, "description": desc, "status": "WARN", "raw": trimmed + suffix, "error": None}


def check_ssh_keys() -> dict:
    name = "SSH Authorized Keys"
    desc = (
        "Keys in ~/.ssh/authorized_keys that allow remote login to this machine. "
        "WARN means remote key-based access is enabled — review if unexpected."
    )
    path = Path.home() / ".ssh" / "authorized_keys"
    try:
        if not path.exists():
            return {"name": name, "description": desc, "status": "PASS", "raw": "No authorized keys found.", "error": None}
        lines = [ln for ln in path.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
        if not lines:
            return {"name": name, "description": desc, "status": "PASS", "raw": "No authorized keys found.", "error": None}
        return {"name": name, "description": desc, "status": "WARN", "raw": "\n".join(lines), "error": None}
    except OSError as e:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": "", "error": str(e)}


if __name__ == "__main__":
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
