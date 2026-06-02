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
from .external import check_macos_version

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
