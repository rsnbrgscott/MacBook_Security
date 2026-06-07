from unittest.mock import patch
from collectors.bluetooth import check_bluetooth


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


_BT_OFF = "Bluetooth:\n\n      Bluetooth Controller:\n          State: Off\n          Discoverable: Off\n"
_BT_ON_HIDDEN = "Bluetooth:\n\n      Bluetooth Controller:\n          State: On\n          Discoverable: Off\n"
_BT_ON_VISIBLE = "Bluetooth:\n\n      Bluetooth Controller:\n          State: On\n          Discoverable: Yes\n"


def test_bluetooth_off_pass():
    with patch("collectors.bluetooth.run_cmd_rc", return_value=(_BT_OFF, 0, None)):
        result = check_bluetooth()
        _ok(result, "PASS")
        assert "State: Off" in result["raw"]


def test_bluetooth_on_not_discoverable_warn():
    with patch("collectors.bluetooth.run_cmd_rc", return_value=(_BT_ON_HIDDEN, 0, None)):
        result = check_bluetooth()
        _ok(result, "WARN")
        assert "Discoverable: Off" in result["raw"]


def test_bluetooth_on_discoverable_fail():
    with patch("collectors.bluetooth.run_cmd_rc", return_value=(_BT_ON_VISIBLE, 0, None)):
        result = check_bluetooth()
        _ok(result, "FAIL")
        assert "Discoverable: Yes" in result["raw"]


def test_bluetooth_command_fails_unknown():
    with patch("collectors.bluetooth.run_cmd_rc", return_value=("error output", 1, None)):
        _ok(check_bluetooth(), "UNKNOWN")


def test_bluetooth_no_power_field_unknown():
    with patch("collectors.bluetooth.run_cmd_rc",
               return_value=("Bluetooth:\n\n      Bluetooth Controller:\n          Chipset: BCM\n", 0, None)):
        result = check_bluetooth()
        _ok(result, "UNKNOWN")
        assert "power state" in result["error"]


def test_bluetooth_power_on_no_disc_field_unknown():
    with patch("collectors.bluetooth.run_cmd_rc",
               return_value=("Bluetooth:\n\n      Bluetooth Controller:\n          State: On\n", 0, None)):
        result = check_bluetooth()
        _ok(result, "UNKNOWN")
        assert "discoverability" in result["error"]
