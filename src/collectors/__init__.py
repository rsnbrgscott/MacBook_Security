# Collector registry for the macOS security dashboard.
# This is the single file to edit when adding or removing signals.
# app.py only calls run_all_collectors() and is never modified for signal changes.
# Each collector function returns a dict with keys:
#   name, description, status (PASS/FAIL/WARN/UNKNOWN), raw, error

from .system_integrity import (
    check_sip,
    check_gatekeeper,
    check_filevault,
    check_secure_boot,
)
from .network import (
    check_firewall,
    check_stealth_mode,
    check_listening_ports,
    check_wifi_security,
    check_dns_config,
)
from .persistence import (
    check_user_launch_agents,
    check_global_launch_agents,
    check_launch_daemons,
    check_login_items,
)
from .auth import (
    check_failed_logins,
    check_ssh_keys,
    check_ssh_key_passphrases,
    check_ssh_agent_forwarding,
    check_ssh_key_strength,
)
from .sharing import (
    check_remote_login,
    check_screen_sharing,
    check_airdrop,
)
from .hygiene import (
    check_auto_updates,
    check_root_certificates,
    check_screen_lock,
    check_screensaver_idle_timeout,
)
from .accounts import (
    check_guest_account,
    check_login_window_display,
    check_admin_group_members,
)
from .ai import (
    check_ai_keys_shell_config,
    check_ai_keys_shell_history,
    check_local_ai_server,
)
from .bluetooth import check_bluetooth
from .external import check_macos_version

CATEGORIES: list[tuple[str, list[str]]] = [
    ("System Integrity", ["System Integrity Protection", "Gatekeeper", "FileVault", "Secure Boot"]),
    ("Network", ["Application Firewall", "Stealth Mode", "Listening Services", "Wi-Fi Security", "DNS Configuration"]),
    ("Persistence", ["User Launch Agents", "Global Launch Agents", "Launch Daemons", "Login Items"]),
    ("Authentication", ["Failed Logins", "SSH Authorized Keys", "SSH Key Passphrases", "SSH Agent Forwarding", "SSH Key Strength"]),
    ("User Accounts", ["Guest Account", "Login Window Display", "Admin Group Members"]),
    ("Sharing & Remote Access", ["Remote Login (SSH)", "Screen Sharing / Remote Management", "AirDrop Receiver Mode"]),
    ("Software Hygiene", ["Automatic Updates", "Root Certificate Trust", "Screen Lock", "Screensaver Idle Timeout"]),
    ("AI Security", ["AI API Keys in Shell Config", "Shell History Key Exposure", "Local AI Server Exposure"]),
    ("Bluetooth", ["Bluetooth"]),
]

# Always-on signals — run on every page load regardless of env var settings.
# To add a new signal: import its check function and append it here.
_COLLECTORS = [
    check_sip,
    check_gatekeeper,
    check_filevault,
    check_secure_boot,
    check_firewall,
    check_stealth_mode,
    check_listening_ports,
    check_wifi_security,
    check_dns_config,
    check_user_launch_agents,
    check_global_launch_agents,
    check_launch_daemons,
    check_login_items,
    check_failed_logins,
    check_ssh_keys,
    check_ssh_key_passphrases,
    check_ssh_agent_forwarding,
    check_ssh_key_strength,
    check_guest_account,
    check_login_window_display,
    check_admin_group_members,
    check_remote_login,
    check_screen_sharing,
    check_airdrop,
    check_auto_updates,
    check_root_certificates,
    check_screen_lock,
    check_screensaver_idle_timeout,
    check_ai_keys_shell_config,
    check_ai_keys_shell_history,
    check_local_ai_server,
    check_bluetooth,
]

# Opt-in signals — only run when EXTERNAL_CALLS=1 is set in the environment.
# These collectors make outbound HTTP requests to external hosts.
_EXTERNAL_COLLECTORS = [
    check_macos_version,
]


def run_all_collectors(external: bool = False) -> list[dict]:
    """Run all enabled collectors and return a list of signal result dicts."""
    collectors = _COLLECTORS + (_EXTERNAL_COLLECTORS if external else [])
    return [fn() for fn in collectors]
