from unittest.mock import patch
from collectors.sharing import check_remote_login, check_screen_sharing, check_airdrop


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


# --- check_remote_login ---

def test_remote_login_pass():
    # launchctl exit 113 = "Could not find service" → not loaded → PASS
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("Could not find service", 113, None)):
        _ok(check_remote_login(), "PASS")


def test_remote_login_fail():
    # launchctl exit 0 → service loaded → FAIL
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("service info...", 0, None)):
        _ok(check_remote_login(), "FAIL")


def test_remote_login_unknown_error():
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("", -1, "Command not found: launchctl")):
        _ok(check_remote_login(), "UNKNOWN")


def test_remote_login_unknown_unexpected_rc():
    # Non-zero, non-113 exit with no "Could not find service" text
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("some error", 1, None)):
        _ok(check_remote_login(), "UNKNOWN")


# --- check_screen_sharing ---

def test_screen_sharing_pass():
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("Could not find service", 113, None)):
        _ok(check_screen_sharing(), "PASS")


def test_screen_sharing_fail():
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("service info...", 0, None)):
        _ok(check_screen_sharing(), "FAIL")


def test_screen_sharing_unknown():
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("", -1, "error")):
        _ok(check_screen_sharing(), "UNKNOWN")


# --- check_airdrop ---

def test_airdrop_pass_off():
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("Off", 0, None)):
        _ok(check_airdrop(), "PASS")


def test_airdrop_pass_contacts_only():
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("Contacts Only", 0, None)):
        _ok(check_airdrop(), "PASS")


def test_airdrop_warn_everyone():
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("Everyone", 0, None)):
        _ok(check_airdrop(), "WARN")


def test_airdrop_unknown_error():
    with patch("collectors.sharing.run_cmd_rc",
               return_value=("", -1, "error")):
        _ok(check_airdrop(), "UNKNOWN")
