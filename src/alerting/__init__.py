import threading
import time

from collectors import run_all_collectors
from .notifier import send_notification

_state: dict[str, str] = {}
_lock = threading.Lock()


def start_alerter(interval: int, external: bool = False) -> None:
    t = threading.Thread(
        target=_poll_loop, args=(interval, external), daemon=True
    )
    t.start()


def _poll_loop(interval: int, external: bool) -> None:
    while True:
        try:
            results = run_all_collectors(external=external)
            _process(results)
            from history import store_snapshot
            store_snapshot(results)
        except Exception:
            pass
        time.sleep(interval)


def _process(results: list[dict]) -> None:
    with _lock:
        for signal in results:
            name = signal["name"]
            new_status = signal["status"]
            old_status = _state.get(name)
            if old_status is not None and old_status != new_status:
                send_notification(
                    title=f"Security Alert: {name}",
                    message=f"{old_status} → {new_status}",
                )
            _state[name] = new_status
