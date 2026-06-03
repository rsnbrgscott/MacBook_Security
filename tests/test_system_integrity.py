from unittest.mock import patch
from collectors.system_integrity import (
    check_sip,
    check_gatekeeper,
    check_filevault,
    check_secure_boot,
)


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


# --- check_sip ---

def test_sip_pass():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("System Integrity Protection status enabled.", None)):
        _ok(check_sip(), "PASS")


def test_sip_fail():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("System Integrity Protection status disabled.", None)):
        _ok(check_sip(), "FAIL")


def test_sip_unknown_command_error():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("", "Command not found: csrutil")):
        _ok(check_sip(), "UNKNOWN")


def test_sip_unknown_unrecognized_output():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("unexpected output", None)):
        _ok(check_sip(), "UNKNOWN")


# --- check_gatekeeper ---

def test_gatekeeper_pass():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("assessments enabled", None)):
        _ok(check_gatekeeper(), "PASS")


def test_gatekeeper_fail():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("assessments disabled", None)):
        _ok(check_gatekeeper(), "FAIL")


def test_gatekeeper_unknown():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("", "error")):
        _ok(check_gatekeeper(), "UNKNOWN")


# --- check_filevault ---

def test_filevault_pass():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("FileVault is On.", None)):
        _ok(check_filevault(), "PASS")


def test_filevault_fail():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("FileVault is Off.", None)):
        _ok(check_filevault(), "FAIL")


def test_filevault_unknown():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("", "error")):
        _ok(check_filevault(), "UNKNOWN")


# --- check_secure_boot ---

def test_secure_boot_pass():
    raw = "  Secure Boot: Full Security"
    with patch("collectors.system_integrity.run_cmd", return_value=(raw, None)):
        _ok(check_secure_boot(), "PASS")


def test_secure_boot_unknown_command_error():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("", "error")):
        _ok(check_secure_boot(), "UNKNOWN")


def test_secure_boot_unknown_no_field():
    with patch("collectors.system_integrity.run_cmd",
               return_value=("No secure boot line here", None)):
        _ok(check_secure_boot(), "UNKNOWN")
