from unittest.mock import patch
from collectors.hygiene import check_auto_updates, check_root_certificates, check_screen_lock


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


# --- check_auto_updates ---
# First run_cmd_rc: AutomaticCheckEnabled; second: CriticalUpdateInstall.

def test_auto_updates_pass_key_absent():
    # rc=1 on first call means key absent → macOS default on → PASS
    with patch("collectors.hygiene.run_cmd_rc", return_value=("", 1, None)):
        _ok(check_auto_updates(), "PASS")


def test_auto_updates_fail_check_disabled():
    with patch("collectors.hygiene.run_cmd_rc", return_value=("0", 0, None)):
        _ok(check_auto_updates(), "FAIL")


def test_auto_updates_pass_both_enabled():
    with patch("collectors.hygiene.run_cmd_rc",
               side_effect=[("1", 0, None), ("1", 0, None)]):
        _ok(check_auto_updates(), "PASS")


def test_auto_updates_pass_check_on_crit_absent():
    with patch("collectors.hygiene.run_cmd_rc",
               side_effect=[("1", 0, None), ("", 1, None)]):
        _ok(check_auto_updates(), "PASS")


def test_auto_updates_warn_crit_disabled():
    with patch("collectors.hygiene.run_cmd_rc",
               side_effect=[("1", 0, None), ("0", 0, None)]):
        _ok(check_auto_updates(), "WARN")


def test_auto_updates_unknown_command_error():
    with patch("collectors.hygiene.run_cmd_rc", return_value=("", -1, "error")):
        _ok(check_auto_updates(), "UNKNOWN")


# --- check_root_certificates ---

def test_root_certificates_pass():
    with patch("collectors.hygiene.run_cmd_rc",
               return_value=("No Trust Settings were found.", 1, None)):
        _ok(check_root_certificates(), "PASS")


def test_root_certificates_warn():
    with patch("collectors.hygiene.run_cmd_rc",
               return_value=("Certificate data...", 0, None)):
        _ok(check_root_certificates(), "WARN")


# --- check_screen_lock ---
# First run_cmd_rc: osascript require-password-to-wake; second: askForPasswordDelay.

def test_screen_lock_fail_no_password():
    with patch("collectors.hygiene.run_cmd_rc", return_value=("false", 0, None)):
        _ok(check_screen_lock(), "FAIL")


def test_screen_lock_pass_immediate_lock():
    # pw=true, delay key absent (rc=1) → immediate lock → PASS
    with patch("collectors.hygiene.run_cmd_rc",
               side_effect=[("true", 0, None), ("", 1, None)]):
        _ok(check_screen_lock(), "PASS")


def test_screen_lock_pass_zero_delay():
    with patch("collectors.hygiene.run_cmd_rc",
               side_effect=[("true", 0, None), ("0", 0, None)]):
        _ok(check_screen_lock(), "PASS")


def test_screen_lock_warn_nonzero_delay():
    with patch("collectors.hygiene.run_cmd_rc",
               side_effect=[("true", 0, None), ("300", 0, None)]):
        _ok(check_screen_lock(), "WARN")


def test_screen_lock_unknown_command_error():
    with patch("collectors.hygiene.run_cmd_rc",
               return_value=("", -1, "error")):
        _ok(check_screen_lock(), "UNKNOWN")
