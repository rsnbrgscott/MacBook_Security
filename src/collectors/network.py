"""Network signal collectors: Application Firewall, Stealth Mode, Listening Services.

All three use socketfilterfw or lsof — no elevated privileges required.
"""

import subprocess

# Absolute path to the macOS Application Firewall control binary.
_SOCKETFILTERFW = "/usr/libexec/ApplicationFirewall/socketfilterfw"


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


def check_firewall() -> dict:
    """Check whether the macOS Application Firewall is enabled via socketfilterfw."""
    name = "Application Firewall"
    desc = "Blocks unsolicited inbound connections to applications on this machine."
    raw, error = _run([_SOCKETFILTERFW, "--getglobalstate"])
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    if "enabled" in raw:
        status = "PASS"
    elif "disabled" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return {"name": name, "description": desc, "status": status, "raw": raw, "error": error}


def check_stealth_mode() -> dict:
    """Check Stealth Mode state — both 'is on' and 'enabled' are valid active-state strings."""
    name = "Stealth Mode"
    desc = "Prevents the machine from responding to unsolicited network probes such as ICMP ping."
    raw, error = _run([_SOCKETFILTERFW, "--getstealthmode"])
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    # macOS output varies by version: some say "enabled", others say "Firewall stealth mode is on".
    if "enabled" in raw or "is on" in raw:
        status = "PASS"
    elif "off" in raw or "disabled" in raw:
        status = "WARN"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return {"name": name, "description": desc, "status": status, "raw": raw, "error": error}


def check_listening_ports() -> dict:
    """List TCP services in LISTEN state; WARN if any are bound to all interfaces (*:port)."""
    name = "Listening Services"
    desc = (
        "TCP services accepting inbound connections. "
        "External listeners are reachable from the local network."
    )
    raw, error = _run(["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"], timeout=15)
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}

    lines = raw.splitlines()
    data_lines = [ln for ln in lines[1:] if ln.strip()]  # skip header row

    # A process bound to '*:port' is reachable from the local network.
    # Processes bound to '127.0.0.1:port' are local-only and not flagged.
    # Note: lsof runs without root, so system-owned (root) processes are not visible.
    external = [
        ln for ln in data_lines
        if len(ln.split()) >= 2 and ln.split()[-2].startswith("*:")
    ]

    status = "WARN" if external else "PASS"
    return {"name": name, "description": desc, "status": status, "raw": raw, "error": None}


if __name__ == "__main__":
    # Quick smoke-test: run this file directly to see current signal output.
    checks = [
        ("Application Firewall", check_firewall),
        ("Stealth Mode", check_stealth_mode),
        ("Listening Services", check_listening_ports),
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
