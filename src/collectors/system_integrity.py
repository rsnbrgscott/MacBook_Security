import subprocess


def _run(cmd: list[str], timeout: int = 10) -> tuple[str, str | None]:
    """Run cmd, return (output, error). Never raises."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        # spctl writes to stderr on some macOS versions; prefer stdout, fall back to stderr
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


def check_sip() -> dict:
    raw, error = _run(["csrutil", "status"])
    if error:
        return {"name": "System Integrity Protection", "description": "Prevents modification of protected system files and directories, even by root.", "status": "UNKNOWN", "raw": raw, "error": error}
    if "enabled" in raw:
        status = "PASS"
    elif "disabled" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return {"name": "System Integrity Protection", "description": "Prevents modification of protected system files and directories, even by root.", "status": status, "raw": raw, "error": error}


def check_gatekeeper() -> dict:
    raw, error = _run(["spctl", "--status"])
    if error:
        return {"name": "Gatekeeper", "description": "Enforces that apps are signed by an Apple-notarized developer before they can run.", "status": "UNKNOWN", "raw": raw, "error": error}
    if "assessments enabled" in raw:
        status = "PASS"
    elif "assessments disabled" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return {"name": "Gatekeeper", "description": "Enforces that apps are signed by an Apple-notarized developer before they can run.", "status": status, "raw": raw, "error": error}


def check_filevault() -> dict:
    raw, error = _run(["fdesetup", "status"])
    if error:
        return {"name": "FileVault", "description": "Full-disk encryption — protects all data at rest if the machine is lost or stolen.", "status": "UNKNOWN", "raw": raw, "error": error}
    if "FileVault is On" in raw:
        status = "PASS"
    elif "FileVault is Off" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return {"name": "FileVault", "description": "Full-disk encryption — protects all data at rest if the machine is lost or stolen.", "status": status, "raw": raw, "error": error}


def check_secure_boot() -> dict:
    raw, error = _run(["system_profiler", "SPiBridgeDataType"])
    if error:
        return {"name": "Secure Boot", "description": "Ensures only a trusted, Apple-signed operating system loads at startup.", "status": "UNKNOWN", "raw": raw, "error": error}

    secure_boot_line = next(
        (line.strip() for line in raw.splitlines() if "Secure Boot:" in line),
        None,
    )
    if secure_boot_line is None:
        return {"name": "Secure Boot", "description": "Ensures only a trusted, Apple-signed operating system loads at startup.", "status": "UNKNOWN", "raw": raw, "error": "'Secure Boot:' field not found in output"}

    if "Full Security" in secure_boot_line:
        status = "PASS"
    elif "No Security" in secure_boot_line or "Permissive Security" in secure_boot_line:
        status = "FAIL"
    elif "Medium Security" in secure_boot_line or "Reduced Security" in secure_boot_line:
        # Intentional but reduced posture — not a hard failure, flagged for awareness
        status = "WARN"
    else:
        status, error = "UNKNOWN", f"Unrecognized Secure Boot value: {secure_boot_line!r}"

    return {"name": "Secure Boot", "description": "Ensures only a trusted, Apple-signed operating system loads at startup.", "status": status, "raw": raw, "error": error}


if __name__ == "__main__":
    checks = [
        ("SIP", check_sip),
        ("Gatekeeper", check_gatekeeper),
        ("FileVault", check_filevault),
        ("Secure Boot", check_secure_boot),
    ]
    for name, fn in checks:
        result = fn()
        preview = result["raw"][:120].replace("\n", " ").strip()
        ellipsis = "..." if len(result["raw"]) > 120 else ""
        print(f"[{result['status']:^7}] {name}")
        print(f"         raw: {preview!r}{ellipsis}")
        if result["error"]:
            print(f"         error: {result['error']}")
        print()
