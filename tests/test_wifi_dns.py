from unittest.mock import patch
from collectors.network import check_wifi_security, check_dns_config


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


# ---------------------------------------------------------------------------
# Canned system_profiler SPAirPortDataType output
# ---------------------------------------------------------------------------

_WIFI_WPA3 = """\
Wi-Fi:

      Interfaces:
        en0:
          Status: Connected
          Current Network Information:
            HomeNet:
              Security: WPA3 Personal
          Other Local Wi-Fi Networks:
            Neighbor:
              Security: WPA2 Personal
"""

_WIFI_WPA2 = """\
Wi-Fi:

      Interfaces:
        en0:
          Status: Connected
          Current Network Information:
            HomeNet:
              Security: WPA2 Personal
          Other Local Wi-Fi Networks:
            Neighbor:
              Security: WPA2 Personal
"""

_WIFI_OPEN = """\
Wi-Fi:

      Interfaces:
        en0:
          Status: Connected
          Current Network Information:
            CoffeeShop:
              Security: Open
          Other Local Wi-Fi Networks:
"""

_WIFI_WEP = """\
Wi-Fi:

      Interfaces:
        en0:
          Status: Connected
          Current Network Information:
            OldRouter:
              Security: WEP
          Other Local Wi-Fi Networks:
"""

_WIFI_DISCONNECTED = """\
Wi-Fi:

      Interfaces:
        en0:
          Status: Not Associated
        awdl0:
          Current Network Information:
              Network Type: Infrastructure
"""

# ---------------------------------------------------------------------------
# Canned scutil --dns output
# ---------------------------------------------------------------------------

def _dns_output(*nameservers):
    """Build a minimal scutil --dns output containing the given nameserver IPs."""
    ns_lines = "\n".join(
        f"  nameserver[{i}] : {ip}" for i, ip in enumerate(nameservers)
    )
    # Duplicate the nameservers in the scoped section to match real output.
    return (
        f"DNS configuration\n\nresolver #1\n{ns_lines}\n"
        f"  flags    : Request A records\n\n"
        f"DNS configuration (for scoped queries)\n\nresolver #1\n{ns_lines}\n"
        f"  flags    : Scoped\n"
    )


_DNS_NO_NAMESERVERS = """\
DNS configuration

resolver #1
  domain   : local
  options  : mdns
  timeout  : 5
  flags    : Request A records
  reach    : 0x00000000 (Not Reachable)
  order    : 300000
"""

# ---------------------------------------------------------------------------
# check_wifi_security tests
# ---------------------------------------------------------------------------

def test_wifi_wpa3_pass():
    with patch("collectors.network.run_cmd", return_value=(_WIFI_WPA3, None)):
        result = check_wifi_security()
        _ok(result, "PASS")
        assert "WPA3" in result["raw"]


def test_wifi_wpa2_warn():
    with patch("collectors.network.run_cmd", return_value=(_WIFI_WPA2, None)):
        result = check_wifi_security()
        _ok(result, "WARN")
        assert "WPA2" in result["raw"]


def test_wifi_open_fail():
    with patch("collectors.network.run_cmd", return_value=(_WIFI_OPEN, None)):
        result = check_wifi_security()
        _ok(result, "FAIL")


def test_wifi_wep_fail():
    with patch("collectors.network.run_cmd", return_value=(_WIFI_WEP, None)):
        result = check_wifi_security()
        _ok(result, "FAIL")
        assert "WEP" in result["raw"]


def test_wifi_not_connected_pass():
    with patch("collectors.network.run_cmd", return_value=(_WIFI_DISCONNECTED, None)):
        result = check_wifi_security()
        _ok(result, "PASS")
        assert result["raw"] == "Not connected"


def test_wifi_command_fails_unknown():
    with patch("collectors.network.run_cmd", return_value=("", "system_profiler not found")):
        _ok(check_wifi_security(), "UNKNOWN")


# ---------------------------------------------------------------------------
# check_dns_config tests
# ---------------------------------------------------------------------------

def test_dns_local_resolver_pass():
    with patch("collectors.network.run_cmd", return_value=(_dns_output("192.168.1.1"), None)):
        result = check_dns_config()
        _ok(result, "PASS")
        assert "192.168.1.1" in result["raw"]


def test_dns_known_doh_pass():
    with patch("collectors.network.run_cmd", return_value=(_dns_output("1.1.1.1", "8.8.8.8"), None)):
        result = check_dns_config()
        _ok(result, "PASS")


def test_dns_mixed_known_pass():
    with patch("collectors.network.run_cmd", return_value=(_dns_output("192.168.1.1", "9.9.9.9"), None)):
        _ok(check_dns_config(), "PASS")


def test_dns_unrecognized_public_warn():
    with patch("collectors.network.run_cmd", return_value=(_dns_output("68.105.28.11"), None)):
        result = check_dns_config()
        _ok(result, "WARN")
        assert "68.105.28.11" in result["raw"]


def test_dns_no_nameservers_pass():
    with patch("collectors.network.run_cmd", return_value=(_DNS_NO_NAMESERVERS, None)):
        result = check_dns_config()
        _ok(result, "PASS")
        assert result["raw"] == "No nameservers configured"


def test_dns_command_fails_unknown():
    with patch("collectors.network.run_cmd", return_value=("", "scutil not found")):
        _ok(check_dns_config(), "UNKNOWN")


def test_dns_ipv6_linklocal_pass():
    with patch("collectors.network.run_cmd", return_value=(_dns_output("fe80::1"), None)):
        _ok(check_dns_config(), "PASS")
