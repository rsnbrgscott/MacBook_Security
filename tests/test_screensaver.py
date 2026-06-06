from unittest.mock import patch
from collectors.hygiene import check_screensaver_idle_timeout


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


def test_screensaver_key_absent_fail():
    with patch("collectors.hygiene.run_cmd_rc",
               return_value=("The domain/default pair of (...) does not exist", 1, None)):
        result = check_screensaver_idle_timeout()
        _ok(result, "FAIL")
        assert "absent" in result["raw"]


def test_screensaver_zero_fail():
    with patch("collectors.hygiene.run_cmd_rc", return_value=("0", 0, None)):
        result = check_screensaver_idle_timeout()
        _ok(result, "FAIL")
        assert "Never" in result["raw"]


def test_screensaver_300s_pass():
    with patch("collectors.hygiene.run_cmd_rc", return_value=("300", 0, None)):
        result = check_screensaver_idle_timeout()
        _ok(result, "PASS")
        assert "300" in result["raw"]


def test_screensaver_600s_pass():
    # Boundary: exactly 600 s is still PASS
    with patch("collectors.hygiene.run_cmd_rc", return_value=("600", 0, None)):
        _ok(check_screensaver_idle_timeout(), "PASS")


def test_screensaver_601s_warn():
    # Boundary: 601 s crosses into WARN
    with patch("collectors.hygiene.run_cmd_rc", return_value=("601", 0, None)):
        _ok(check_screensaver_idle_timeout(), "WARN")


def test_screensaver_1800s_warn():
    with patch("collectors.hygiene.run_cmd_rc", return_value=("1800", 0, None)):
        result = check_screensaver_idle_timeout()
        _ok(result, "WARN")
        assert "1800" in result["raw"]


def test_screensaver_non_integer_unknown():
    with patch("collectors.hygiene.run_cmd_rc", return_value=("abc", 0, None)):
        _ok(check_screensaver_idle_timeout(), "UNKNOWN")


def test_screensaver_command_error_unknown():
    # rc=1 without "does not exist" → unexpected failure → UNKNOWN
    with patch("collectors.hygiene.run_cmd_rc",
               return_value=("permission denied", 1, None)):
        _ok(check_screensaver_idle_timeout(), "UNKNOWN")
