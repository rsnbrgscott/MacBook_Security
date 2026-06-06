from unittest.mock import patch
from collectors.accounts import (
    check_guest_account,
    check_login_window_display,
    check_admin_group_members,
)


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


# ---------------------------------------------------------------------------
# check_guest_account
# ---------------------------------------------------------------------------

def test_guest_account_key_absent_pass():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("The domain/default pair of (...) does not exist", 1, None)):
        result = check_guest_account()
        _ok(result, "PASS")
        assert "absent" in result["raw"]


def test_guest_account_disabled_pass():
    with patch("collectors.accounts.run_cmd_rc", return_value=("0", 0, None)):
        result = check_guest_account()
        _ok(result, "PASS")
        assert "GuestEnabled: 0" in result["raw"]


def test_guest_account_enabled_fail():
    with patch("collectors.accounts.run_cmd_rc", return_value=("1", 0, None)):
        result = check_guest_account()
        _ok(result, "FAIL")
        assert "GuestEnabled: 1" in result["raw"]


def test_guest_account_unexpected_value_unknown():
    with patch("collectors.accounts.run_cmd_rc", return_value=("yes", 0, None)):
        _ok(check_guest_account(), "UNKNOWN")


def test_guest_account_command_error_unknown():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("", -1, "Command not found: defaults")):
        _ok(check_guest_account(), "UNKNOWN")


# ---------------------------------------------------------------------------
# check_login_window_display
# ---------------------------------------------------------------------------

def test_login_window_key_absent_warn():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("The domain/default pair of (...) does not exist", 1, None)):
        result = check_login_window_display()
        _ok(result, "WARN")
        assert "absent" in result["raw"]


def test_login_window_name_password_pass():
    with patch("collectors.accounts.run_cmd_rc", return_value=("1", 0, None)):
        result = check_login_window_display()
        _ok(result, "PASS")
        assert "name and password" in result["raw"]


def test_login_window_user_list_warn():
    with patch("collectors.accounts.run_cmd_rc", return_value=("0", 0, None)):
        result = check_login_window_display()
        _ok(result, "WARN")
        assert "user list" in result["raw"]


def test_login_window_command_error_unknown():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("", -1, "Command not found: defaults")):
        _ok(check_login_window_display(), "UNKNOWN")


# ---------------------------------------------------------------------------
# check_admin_group_members
# ---------------------------------------------------------------------------

def test_admin_group_single_user_pass():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("GroupMembership: scottrosenberg", 0, None)), \
         patch.dict("os.environ", {"USER": "scottrosenberg"}):
        result = check_admin_group_members()
        _ok(result, "PASS")
        assert "scottrosenberg" in result["raw"]


def test_admin_group_multiple_users_warn():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("GroupMembership: scottrosenberg backdoor", 0, None)), \
         patch.dict("os.environ", {"USER": "scottrosenberg"}):
        result = check_admin_group_members()
        _ok(result, "WARN")
        assert "scottrosenberg" in result["raw"]
        assert "backdoor" in result["raw"]


def test_admin_group_system_accounts_filtered():
    # root and _mbsetupuser should be stripped; only scottrosenberg remains → PASS
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("GroupMembership: root scottrosenberg _mbsetupuser", 0, None)), \
         patch.dict("os.environ", {"USER": "scottrosenberg"}):
        result = check_admin_group_members()
        _ok(result, "PASS")
        assert "scottrosenberg" in result["raw"]


def test_admin_group_command_error_unknown():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("", -1, "dscl: command not found")):
        _ok(check_admin_group_members(), "UNKNOWN")


def test_admin_group_nonzero_rc_unknown():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("<dscl_cmd> DS Error: -14136 (eDSRecordNotFound)", 56, None)):
        _ok(check_admin_group_members(), "UNKNOWN")


def test_admin_group_empty_members_unknown():
    # Label present but no names after it
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("GroupMembership:", 0, None)), \
         patch.dict("os.environ", {"USER": "scottrosenberg"}):
        _ok(check_admin_group_members(), "UNKNOWN")


def test_admin_group_unrecognized_output_unknown():
    with patch("collectors.accounts.run_cmd_rc",
               return_value=("Something unexpected", 0, None)):
        _ok(check_admin_group_members(), "UNKNOWN")
