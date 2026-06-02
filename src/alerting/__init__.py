"""Background alerting for the macOS security dashboard.

Runs a daemon thread that polls all collectors on a fixed interval and sends
a macOS notification whenever a signal's status changes (e.g. PASS → FAIL).
State is held in memory; the first poll establishes the baseline and does not
trigger notifications so that startup doesn't flood the notification center.
"""

import threading
import time

from collectors import run_all_collectors
from .notifier import send_notification

# In-memory map of signal name → last known status, used to detect transitions.
_state: dict[str, str] = {}
_lock = threading.Lock()


def start_alerter(interval: int, external: bool = False) -> None:
    """Spawn a daemon thread that polls collectors every interval seconds."""
    t = threading.Thread(
        target=_poll_loop, args=(interval, external), daemon=True
    )
    t.start()


def _poll_loop(interval: int, external: bool) -> None:
    """Continuously collect signals, check for state changes, and persist snapshots."""
    while True:
        try:
            results = run_all_collectors(external=external)
            _process(results)
            # Import here to avoid a circular import at module load time.
            from history import store_snapshot
            store_snapshot(results)
        except Exception:
            pass
        time.sleep(interval)


def _process(results: list[dict]) -> None:
    """Compare each signal's current status against the last known state and notify on change."""
    with _lock:
        for signal in results:
            name = signal["name"]
            new_status = signal["status"]
            old_status = _state.get(name)
            # old_status is None on the first poll — skip notification to avoid startup noise.
            if old_status is not None and old_status != new_status:
                send_notification(
                    title=f"Security Alert: {name}",
                    message=f"{old_status} → {new_status}",
                )
            _state[name] = new_status
