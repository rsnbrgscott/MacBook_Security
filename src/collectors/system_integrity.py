"""System integrity signal collectors: SIP, Gatekeeper, FileVault, Secure Boot."""

try:
    from .utils import run_cmd, make_result
except ImportError:
    from utils import run_cmd, make_result  # noqa: F401 — direct script execution


def check_sip() -> dict:
    """Check System Integrity Protection state via csrutil."""
    name = "System Integrity Protection"
    desc = "Prevents modification of protected system files and directories, even by root."
    raw, error = run_cmd(["csrutil", "status"])
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)
    if "enabled" in raw:
        status = "PASS"
    elif "disabled" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return make_result(name, desc, status, raw, error)


def check_gatekeeper() -> dict:
    """Check Gatekeeper state via spctl; output goes to stderr on some macOS versions."""
    name = "Gatekeeper"
    desc = "Enforces that apps are signed by an Apple-notarized developer before they can run."
    raw, error = run_cmd(["spctl", "--status"])
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)
    if "assessments enabled" in raw:
        status = "PASS"
    elif "assessments disabled" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return make_result(name, desc, status, raw, error)


def check_filevault() -> dict:
    """Check FileVault full-disk encryption state via fdesetup."""
    name = "FileVault"
    desc = "Full-disk encryption — protects all data at rest if the machine is lost or stolen."
    raw, error = run_cmd(["fdesetup", "status"])
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)
    if "FileVault is On" in raw:
        status = "PASS"
    elif "FileVault is Off" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return make_result(name, desc, status, raw, error)


def check_secure_boot() -> dict:
    """Check Secure Boot level via system_profiler SPiBridgeDataType (T2/Apple Silicon)."""
    name = "Secure Boot"
    desc = "Ensures only a trusted, Apple-signed operating system loads at startup."
    raw, error = run_cmd(["system_profiler", "SPiBridgeDataType"])
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)

    secure_boot_line = next(
        (line.strip() for line in raw.splitlines() if "Secure Boot:" in line),
        None,
    )
    if secure_boot_line is None:
        return make_result(name, desc, "UNKNOWN", raw, "'Secure Boot:' field not found in output")

    if "Full Security" in secure_boot_line:
        status = "PASS"
    elif "No Security" in secure_boot_line or "Permissive Security" in secure_boot_line:
        status = "FAIL"
    elif "Medium Security" in secure_boot_line or "Reduced Security" in secure_boot_line:
        # Intentional but reduced posture — not a hard failure, flagged for awareness.
        status = "WARN"
    else:
        status, error = "UNKNOWN", f"Unrecognized Secure Boot value: {secure_boot_line!r}"

    return make_result(name, desc, status, raw, error)


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
