"""Bluetooth signal collector: radio power state and discoverability.

No sudo required. Uses system_profiler(8) SPBluetoothDataType.
The full output contains device MAC addresses and serial numbers;
only the parsed State and Discoverable controller fields appear in raw.

Field names verified on macOS 15.5, Apple Silicon (Step 27.1):
  State:        On | Off   (power; under "Bluetooth Controller:")
  Discoverable: Yes | Off  (discoverability; under "Bluetooth Controller:")
"""

import re

try:
    from .utils import run_cmd_rc, make_result
except ImportError:
    from utils import run_cmd_rc, make_result  # noqa: F401 — direct script execution


def check_bluetooth() -> dict:
    """Check Bluetooth radio power state and discoverability.

    PASS    — Bluetooth is off (State: Off)
    WARN    — Bluetooth is on, not discoverable (State: On, Discoverable: Off)
    FAIL    — Bluetooth is on and discoverable (State: On, Discoverable: Yes)
    UNKNOWN — system_profiler failed, or output fields could not be parsed
    """
    name = "Bluetooth"
    desc = (
        "A discoverable Bluetooth radio broadcasts this machine's presence to any "
        "nearby scanner and accepts connection requests from unpaired devices. "
        "Bluetooth on but not discoverable (typical daily-use state for paired "
        "peripherals) is flagged WARN; discoverable is FAIL. Off is PASS."
    )

    out, rc, err = run_cmd_rc(
        ["system_profiler", "SPBluetoothDataType"], timeout=10
    )

    if err:
        return make_result(name, desc, "UNKNOWN", "", err)

    if rc != 0:
        return make_result(name, desc, "UNKNOWN", "",
                           out or f"system_profiler exited {rc}")

    state_match = re.search(r"\bState:\s+(On|Off)\b", out)
    if not state_match:
        return make_result(name, desc, "UNKNOWN", "",
                           "Could not parse Bluetooth power state")

    if state_match.group(1) == "Off":
        return make_result(name, desc, "PASS", "State: Off")

    disc_match = re.search(r"\bDiscoverable:\s+(Yes|Off)\b", out)
    if not disc_match:
        return make_result(name, desc, "UNKNOWN", "",
                           "Could not parse Bluetooth discoverability state")

    if disc_match.group(1) == "Yes":
        return make_result(name, desc, "FAIL", "State: On, Discoverable: Yes")

    return make_result(name, desc, "WARN", "State: On, Discoverable: Off")


if __name__ == "__main__":
    checks = [
        ("Bluetooth", check_bluetooth),
    ]
    for label, fn in checks:
        sig = fn()
        print(f"[{sig['status']:^7}] {label}")
        print(f"         raw: {sig['raw']!r}")
        if sig["error"]:
            print(f"         error: {sig['error']}")
        print()
