"""Sharing & Remote Access signal collectors: Remote Login, Screen Sharing, AirDrop.

Detection uses launchctl to check whether sharing services are loaded into the
system domain, and defaults read for AirDrop discoverability. No sudo required.

macOS 26 label note: the SSH service label changed from com.apple.sshd to
com.openssh.sshd. This module targets the label present on this machine.
"""

import subprocess


def _run(cmd: list[str], timeout: int = 10) -> tuple[str, int, str | None]:
    """Run cmd, return (output, returncode, error). Never raises."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output, result.returncode, None
    except subprocess.TimeoutExpired:
        return "", -1, f"Timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return "", -1, f"Command not found: {cmd[0]}"
    except Exception as e:
        return "", -1, str(e)


def _check_launchd_service(label: str) -> tuple[bool | None, str, str | None]:
    """Return (enabled, raw_output, error) for a system launchd service.

    enabled=True  → exit 0, service is loaded (running or waiting)
    enabled=False → exit 113, "Could not find service"
    enabled=None  → unexpected result, caller should return UNKNOWN
    """
    raw, returncode, error = _run(["launchctl", "print", f"system/{label}"])
    if error:
        return None, raw, error
    if returncode == 0:
        return True, raw, None
    if returncode == 113 and "Could not find service" in raw:
        return False, raw, None
    return None, raw, f"Unexpected launchctl exit {returncode}: {raw!r}"


def check_remote_login() -> dict:
    """Detect whether Remote Login (SSH server) is enabled.

    An active sshd creates an authenticated inbound network listener.
    FAIL when the service is loaded; PASS when not found in system domain.
    """
    name = "Remote Login (SSH)"
    desc = (
        "Remote Login runs an SSH server that accepts inbound connections. "
        "Disable in System Settings → General → Sharing unless intentionally used."
    )
    enabled, raw, error = _check_launchd_service("com.openssh.sshd")
    if enabled is None:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    status = "FAIL" if enabled else "PASS"
    raw_display = "SSH server loaded (Remote Login enabled)." if enabled else "SSH server not loaded (Remote Login disabled)."
    return {"name": name, "description": desc, "status": status, "raw": raw_display, "error": None}


def check_screen_sharing() -> dict:
    """Detect whether Screen Sharing / Remote Management is enabled.

    Screen Sharing and Remote Management (ARD) both use com.apple.screensharing.
    An active service allows remote graphical access to this machine.
    FAIL when loaded; PASS when not found in system domain.
    """
    name = "Screen Sharing / Remote Management"
    desc = (
        "Screen Sharing allows remote graphical access to this machine. "
        "Disable in System Settings → General → Sharing unless intentionally used."
    )
    enabled, raw, error = _check_launchd_service("com.apple.screensharing")
    if enabled is None:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    status = "FAIL" if enabled else "PASS"
    raw_display = "Screen sharing service loaded (Screen Sharing enabled)." if enabled else "Screen sharing service not loaded (Screen Sharing disabled)."
    return {"name": name, "description": desc, "status": status, "raw": raw_display, "error": None}


def check_airdrop() -> dict:
    """Check AirDrop discoverability via the sharingd preference key.

    'Everyone' makes this machine discoverable to all nearby devices.
    'Contacts Only' or 'Off' are both considered acceptable (PASS).
    """
    name = "AirDrop Receiver Mode"
    desc = (
        "AirDrop discoverability controls who can send files to this machine wirelessly. "
        "'Everyone' exposes it to any nearby device."
    )
    raw, returncode, error = _run(["defaults", "read", "com.apple.sharingd", "DiscoverableMode"])
    if error or returncode != 0:
        err = error or f"defaults exited {returncode}: {raw!r}"
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": err}

    if raw == "Everyone":
        status = "WARN"
    elif raw in ("Off", "Contacts Only"):
        status = "PASS"
    else:
        return {
            "name": name, "description": desc, "status": "UNKNOWN", "raw": raw,
            "error": f"Unrecognized DiscoverableMode value: {raw!r}",
        }
    return {"name": name, "description": desc, "status": status, "raw": raw, "error": None}


if __name__ == "__main__":
    checks = [
        ("Remote Login (SSH)", check_remote_login),
        ("Screen Sharing / Remote Management", check_screen_sharing),
        ("AirDrop Receiver Mode", check_airdrop),
    ]
    for label, fn in checks:
        result = fn()
        print(f"[{result['status']:^7}] {label}")
        print(f"         raw: {result['raw']!r}")
        if result["error"]:
            print(f"         error: {result['error']}")
        print()
