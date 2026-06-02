"""System integrity signal collectors: SIP, Gatekeeper, FileVault, Secure Boot."""

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
        # spctl writes to stderr on some macOS versions; prefer stdout, fall back to stderr.
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
    """Check System Integrity Protection state via csrutil."""
    name = "System Integrity Protection"
    desc = "Prevents modification of protected system files and directories, even by root."
    raw, error = _run(["csrutil", "status"])
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    if "enabled" in raw:
        status = "PASS"
    elif "disabled" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return {"name": name, "description": desc, "status": status, "raw": raw, "error": error}


def check_gatekeeper() -> dict:
    """Check Gatekeeper state via spctl; output goes to stderr on some macOS versions."""
    name = "Gatekeeper"
    desc = "Enforces that apps are signed by an Apple-notarized developer before they can run."
    raw, error = _run(["spctl", "--status"])
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    if "assessments enabled" in raw:
        status = "PASS"
    elif "assessments disabled" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return {"name": name, "description": desc, "status": status, "raw": raw, "error": error}


def check_filevault() -> dict:
    """Check FileVault full-disk encryption state via fdesetup."""
    name = "FileVault"
    desc = "Full-disk encryption — protects all data at rest if the machine is lost or stolen."
    raw, error = _run(["fdesetup", "status"])
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}
    if "FileVault is On" in raw:
        status = "PASS"
    elif "FileVault is Off" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return {"name": name, "description": desc, "status": status, "raw": raw, "error": error}


def check_secure_boot() -> dict:
    """Check Secure Boot level via system_profiler SPiBridgeDataType (T2/Apple Silicon)."""
    name = "Secure Boot"
    desc = "Ensures only a trusted, Apple-signed operating system loads at startup."
    raw, error = _run(["system_profiler", "SPiBridgeDataType"])
    if error:
        return {"name": name, "description": desc, "status": "UNKNOWN", "raw": raw, "error": error}

    secure_boot_line = next(
        (line.strip() for line in raw.splitlines() if "Secure Boot:" in line),
        None,
    )
    if secure_boot_line is None:
        return {
            "name": name, "description": desc, "status": "UNKNOWN", "raw": raw,
            "error": "'Secure Boot:' field not found in output",
        }

    if "Full Security" in secure_boot_line:
        status = "PASS"
    elif "No Security" in secure_boot_line or "Permissive Security" in secure_boot_line:
        status = "FAIL"
    elif "Medium Security" in secure_boot_line or "Reduced Security" in secure_boot_line:
        # Intentional but reduced posture — not a hard failure, flagged for awareness.
        status = "WARN"
    else:
        status, error = "UNKNOWN", f"Unrecognized Secure Boot value: {secure_boot_line!r}"

    return {"name": name, "description": desc, "status": status, "raw": raw, "error": error}


if __name__ == "__main__":
    # Quick smoke-test: run this file directly to see current signal output.
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
