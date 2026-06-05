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
)
from .ai import (
    check_ai_keys_shell_config,
    check_ai_keys_shell_history,
    check_local_ai_server,
)
from .external import check_macos_version

CATEGORIES: list[tuple[str, list[str]]] = [
    ("System Integrity", ["System Integrity Protection", "Gatekeeper", "FileVault", "Secure Boot"]),
    ("Network", ["Application Firewall", "Stealth Mode", "Listening Services"]),
    ("Persistence", ["User Launch Agents", "Global Launch Agents", "Launch Daemons", "Login Items"]),
    ("Authentication", ["Failed Logins", "SSH Authorized Keys"]),
    ("Sharing & Remote Access", ["Remote Login (SSH)", "Screen Sharing / Remote Management", "AirDrop Receiver Mode"]),
    ("Software Hygiene", ["Automatic Updates", "Root Certificate Trust", "Screen Lock"]),
    ("AI Security", ["AI API Keys in Shell Config", "Shell History Key Exposure", "Local AI Server Exposure"]),
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
    check_user_launch_agents,
    check_global_launch_agents,
    check_launch_daemons,
    check_login_items,
    check_failed_logins,
    check_ssh_keys,
    check_remote_login,
    check_screen_sharing,
    check_airdrop,
    check_auto_updates,
    check_root_certificates,
    check_screen_lock,
    check_ai_keys_shell_config,
    check_ai_keys_shell_history,
    check_local_ai_server,
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
