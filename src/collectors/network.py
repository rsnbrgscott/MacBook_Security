"""Network signal collectors: Application Firewall, Stealth Mode, Listening Services,
Wi-Fi Security, DNS Configuration.

All use socketfilterfw, lsof, system_profiler, or scutil — no elevated privileges required.
"""

import ipaddress
import re

try:
    from .utils import run_cmd, make_result
except ImportError:
    from utils import run_cmd, make_result  # noqa: F401 — direct script execution

# Absolute path to the macOS Application Firewall control binary.
_SOCKETFILTERFW = "/usr/libexec/ApplicationFirewall/socketfilterfw"

# Public resolvers with documented DoH/DoT support. IPs in this set are treated
# as "known secure" even though they are not RFC 1918 private addresses.
_KNOWN_SECURE_DNS = {
    "1.1.1.1", "1.0.0.1",               # Cloudflare
    "8.8.8.8", "8.8.4.4",               # Google
    "9.9.9.9", "149.112.112.112",        # Quad9
    "208.67.222.222", "208.67.220.220",  # OpenDNS
    "94.140.14.14", "94.140.15.15",      # AdGuard
}


def check_firewall() -> dict:
    """Check whether the macOS Application Firewall is enabled via socketfilterfw."""
    name = "Application Firewall"
    desc = "Blocks unsolicited inbound connections to applications on this machine."
    raw, error = run_cmd([_SOCKETFILTERFW, "--getglobalstate"])
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)
    if "enabled" in raw:
        status = "PASS"
    elif "disabled" in raw:
        status = "FAIL"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return make_result(name, desc, status, raw, error)


def check_stealth_mode() -> dict:
    """Check Stealth Mode state — both 'is on' and 'enabled' are valid active-state strings."""
    name = "Stealth Mode"
    desc = "Prevents the machine from responding to unsolicited network probes such as ICMP ping."
    raw, error = run_cmd([_SOCKETFILTERFW, "--getstealthmode"])
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)
    # macOS output varies by version: some say "enabled", others say "Firewall stealth mode is on".
    if "enabled" in raw or "is on" in raw:
        status = "PASS"
    elif "off" in raw or "disabled" in raw:
        status = "WARN"
    else:
        status, error = "UNKNOWN", f"Unrecognized output: {raw!r}"
    return make_result(name, desc, status, raw, error)


def check_listening_ports() -> dict:
    """List TCP and UDP services with external bindings; WARN if any bound to all interfaces."""
    name = "Listening Services"
    desc = (
        "TCP and UDP services accepting inbound connections. "
        "External listeners are reachable from the local network."
    )

    tcp_raw, tcp_error = run_cmd(["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"], timeout=15)
    if tcp_error:
        return make_result(name, desc, "UNKNOWN", tcp_raw, tcp_error)

    udp_raw, udp_error = run_cmd(["lsof", "-iUDP", "-P", "-n"], timeout=15)
    if udp_error:
        return make_result(name, desc, "UNKNOWN", udp_raw, udp_error)

    # TCP LISTEN: NAME format is "*:port (LISTEN)" — address is second-to-last token.
    # Note: lsof runs without root, so root-owned processes are not visible.
    tcp_lines = [ln for ln in tcp_raw.splitlines()[1:] if ln.strip()]
    tcp_external = [
        ln for ln in tcp_lines
        if len(ln.split()) >= 2 and ln.split()[-2].startswith("*:")
    ]

    # UDP: NAME format is "*:port" (last token). Exclude "*:*" — sockets with no port
    # assigned yet cannot receive unsolicited inbound datagrams on a specific port.
    udp_lines = [ln for ln in udp_raw.splitlines()[1:] if ln.strip()]
    udp_external = [
        ln for ln in udp_lines
        if ln.split()[-1].startswith("*:") and ln.split()[-1] != "*:*"
    ]

    tcp_section = "\n".join(tcp_external) if tcp_external else "none"
    udp_section = "\n".join(udp_external) if udp_external else "none"
    merged = f"TCP (LISTEN):\n{tcp_section}\n\nUDP (external):\n{udp_section}"

    status = "WARN" if (tcp_external or udp_external) else "PASS"
    return make_result(name, desc, status, merged)


def _classify_ip(addr: str) -> str:
    """Returns 'local', 'known_doh', or 'unknown_public' for a nameserver IP string."""
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return "unknown_public"
    if ip.is_loopback or ip.is_private or ip.is_link_local:
        return "local"
    if addr in _KNOWN_SECURE_DNS:
        return "known_doh"
    return "unknown_public"


def check_wifi_security() -> dict:
    name = "Wi-Fi Security"
    desc = (
        "Wireless encryption protocol on the currently associated network. "
        "WPA3 offers per-session forward secrecy and SAE authentication. "
        "WPA2 is acceptable but lacks forward secrecy. "
        "WEP, WPA1, and open networks provide inadequate or no protection."
    )
    raw, error = run_cmd(["system_profiler", "SPAirPortDataType"], timeout=10)
    if error:
        return make_result(name, desc, "UNKNOWN", "", error)

    if "Status: Connected" not in raw:
        return make_result(name, desc, "PASS", "Not connected")

    # Extract only the connected-network block, stopping before Other Local Wi-Fi Networks:
    # to avoid matching Security: values from neighboring networks in that section.
    section_match = re.search(
        r"Current Network Information:(.*?)(?:Other Local Wi-Fi Networks:|$)",
        raw,
        re.DOTALL,
    )
    if not section_match:
        return make_result(name, desc, "UNKNOWN", "", "Could not parse Wi-Fi section")

    section = section_match.group(1)
    sec_match = re.search(r"Security:\s+(.+)", section)
    if not sec_match:
        # Connected but no Security field — treat as open.
        return make_result(name, desc, "FAIL", "Security: Open")

    value = sec_match.group(1).strip()
    raw_out = f"Security: {value}"

    # Check WPA3 before WPA2 to prevent "WPA2" substring matching "WPA3" branch.
    if "WPA3" in value:
        return make_result(name, desc, "PASS", raw_out)
    if "WPA2" in value:
        return make_result(name, desc, "WARN", raw_out)
    if "WEP" in value:
        return make_result(name, desc, "FAIL", raw_out)
    if value.lower() in ("open", "none", ""):
        return make_result(name, desc, "FAIL", raw_out)
    if "WPA" in value:
        # Catches WPA1 / WPA/WPA2 mixed-mode.
        return make_result(name, desc, "FAIL", raw_out)
    # Unrecognized protocol — surface for user review.
    return make_result(name, desc, "WARN", raw_out)


def check_dns_config() -> dict:
    name = "DNS Configuration"
    desc = (
        "Active DNS nameservers. Unrecognized public resolvers cannot be assumed to use "
        "encrypted transport (DoH/DoT) and may log or modify DNS queries."
    )
    raw, error = run_cmd(["scutil", "--dns"], timeout=5)
    if error:
        return make_result(name, desc, "UNKNOWN", "", error)

    # Extract all nameserver IPs. They appear twice (main section + "for scoped queries"),
    # so deduplicate while preserving first-seen order.
    ips = list(dict.fromkeys(re.findall(r"nameserver\[\d+\]\s*:\s*(\S+)", raw)))

    if not ips:
        return make_result(name, desc, "PASS", "No nameservers configured")

    unknown = [ip for ip in ips if _classify_ip(ip) == "unknown_public"]
    all_str = ", ".join(ips)

    if unknown:
        return make_result(
            name, desc, "WARN",
            f"nameservers: {all_str}; unrecognized: {', '.join(unknown)}",
        )
    return make_result(name, desc, "PASS", f"nameservers: {all_str}")


if __name__ == "__main__":
    # Quick smoke-test: run this file directly to see current signal output.
    checks = [
        ("Application Firewall", check_firewall),
        ("Stealth Mode", check_stealth_mode),
        ("Listening Services", check_listening_ports),
        ("Wi-Fi Security", check_wifi_security),
        ("DNS Configuration", check_dns_config),
    ]
    for label, fn in checks:
        result = fn()
        preview = result["raw"][:120].replace("\n", " ").strip()
        ellipsis = "..." if len(result["raw"]) > 120 else ""
        print(f"[{result['status']:^7}] {label}")
        print(f"         raw: {preview!r}{ellipsis}")
        if result["error"]:
            print(f"         error: {result['error']}")
        print()
