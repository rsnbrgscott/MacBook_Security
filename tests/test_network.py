from unittest.mock import patch
from collectors.network import check_firewall, check_stealth_mode, check_listening_ports


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


_LSOF_HEADER   = "COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME"
_LSOF_LOOPBACK = "python3   123   user   5u   IPv4  0x0         0t0  TCP 127.0.0.1:8000 (LISTEN)"
_LSOF_EXTERNAL = "python3   123   user   5u   IPv4  0x0         0t0  TCP *:9000 (LISTEN)"

_UDP_HEADER    = "COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME"
_UDP_EXTERNAL  = "rapportd  625   user   21u  IPv6  0x0         0t0  UDP *:3722"
_UDP_LOCALHOST = "python3   123   user   5u   IPv4  0x0         0t0  UDP 127.0.0.1:53"
_UDP_UNBOUND   = "identitys 635   user   9u   IPv4  0x0         0t0  UDP *:*"


def _tcp(*lines):
    return "\n".join([_LSOF_HEADER, *lines])


def _udp(*lines):
    return "\n".join([_UDP_HEADER, *lines])


# --- check_firewall ---

def test_firewall_pass():
    with patch("collectors.network.run_cmd",
               return_value=("Firewall is enabled.", None)):
        _ok(check_firewall(), "PASS")


def test_firewall_fail():
    with patch("collectors.network.run_cmd",
               return_value=("Firewall is disabled.", None)):
        _ok(check_firewall(), "FAIL")


def test_firewall_unknown():
    with patch("collectors.network.run_cmd",
               return_value=("", "error")):
        _ok(check_firewall(), "UNKNOWN")


# --- check_stealth_mode ---

def test_stealth_mode_pass_is_on():
    with patch("collectors.network.run_cmd",
               return_value=("Firewall stealth mode is on", None)):
        _ok(check_stealth_mode(), "PASS")


def test_stealth_mode_pass_enabled():
    with patch("collectors.network.run_cmd",
               return_value=("stealth mode enabled", None)):
        _ok(check_stealth_mode(), "PASS")


def test_stealth_mode_warn():
    with patch("collectors.network.run_cmd",
               return_value=("Firewall stealth mode is off", None)):
        _ok(check_stealth_mode(), "WARN")


def test_stealth_mode_unknown():
    with patch("collectors.network.run_cmd",
               return_value=("", "error")):
        _ok(check_stealth_mode(), "UNKNOWN")


# --- check_listening_ports ---

def test_listening_ports_pass_loopback():
    raw = "\n".join([_LSOF_HEADER, _LSOF_LOOPBACK])
    with patch("collectors.network.run_cmd", return_value=(raw, None)):
        _ok(check_listening_ports(), "PASS")


def test_listening_ports_pass_empty():
    with patch("collectors.network.run_cmd",
               return_value=(_LSOF_HEADER, None)):
        _ok(check_listening_ports(), "PASS")


def test_listening_ports_warn_external():
    raw = "\n".join([_LSOF_HEADER, _LSOF_EXTERNAL])
    with patch("collectors.network.run_cmd", return_value=(raw, None)):
        _ok(check_listening_ports(), "WARN")


def test_listening_ports_unknown():
    with patch("collectors.network.run_cmd",
               return_value=("", "error")):
        _ok(check_listening_ports(), "UNKNOWN")


def test_listening_ports_udp_external_warn():
    with patch("collectors.network.run_cmd", side_effect=[
        (_tcp(), None),
        (_udp(_UDP_EXTERNAL), None),
    ]):
        _ok(check_listening_ports(), "WARN")


def test_listening_ports_udp_localhost_only_pass():
    with patch("collectors.network.run_cmd", side_effect=[
        (_tcp(), None),
        (_udp(_UDP_LOCALHOST), None),
    ]):
        _ok(check_listening_ports(), "PASS")


def test_listening_ports_udp_unbound_excluded_pass():
    """UDP *:* (no port assigned) must not count as an external binding."""
    with patch("collectors.network.run_cmd", side_effect=[
        (_tcp(), None),
        (_udp(_UDP_UNBOUND), None),
    ]):
        _ok(check_listening_ports(), "PASS")


def test_listening_ports_tcp_and_udp_both_external_warn():
    with patch("collectors.network.run_cmd", side_effect=[
        (_tcp(_LSOF_EXTERNAL), None),
        (_udp(_UDP_EXTERNAL), None),
    ]):
        result = check_listening_ports()
        _ok(result, "WARN")
        assert "TCP (LISTEN):" in result["raw"]
        assert "UDP (external):" in result["raw"]


def test_listening_ports_tcp_pass_udp_external_warn():
    with patch("collectors.network.run_cmd", side_effect=[
        (_tcp(_LSOF_LOOPBACK), None),
        (_udp(_UDP_EXTERNAL), None),
    ]):
        _ok(check_listening_ports(), "WARN")


def test_listening_ports_udp_error_unknown():
    with patch("collectors.network.run_cmd", side_effect=[
        (_tcp(), None),
        ("", "lsof udp failed"),
    ]):
        _ok(check_listening_ports(), "UNKNOWN")


def test_listening_ports_raw_sections():
    with patch("collectors.network.run_cmd", side_effect=[
        (_tcp(), None),
        (_udp(), None),
    ]):
        result = check_listening_ports()
        assert "TCP (LISTEN):" in result["raw"]
        assert "UDP (external):" in result["raw"]
