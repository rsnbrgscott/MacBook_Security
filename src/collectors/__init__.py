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

# To add a new signal category: import its check functions and append them here.
# app.py never needs to change — it only calls run_all_collectors().
_COLLECTORS = [
    check_sip,
    check_gatekeeper,
    check_filevault,
    check_secure_boot,
    check_firewall,
    check_stealth_mode,
    check_listening_ports,
]


def run_all_collectors() -> list[dict]:
    return [fn() for fn in _COLLECTORS]
