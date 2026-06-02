"""SQLite-backed history store for signal status snapshots.

Snapshots are written on every dashboard load and every alerter poll cycle.
Only status changes are recorded (deduplication by comparing to the most
recent row for each signal). Data older than _RETENTION_DAYS is pruned on
each write. The connection is shared across the main thread and the alerter
thread; all writes are serialised with _lock.
"""

import sqlite3
import threading
import time
from collections import defaultdict
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent.parent / "data" / "history.db"
_RETENTION_DAYS = 30
_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def init_db() -> None:
    """Open (or create) the SQLite database and ensure the snapshots table exists."""
    global _conn
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          INTEGER NOT NULL,
            signal_name TEXT NOT NULL,
            status      TEXT NOT NULL
        )
    """)
    _conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_snapshots ON snapshots (signal_name, ts DESC)"
    )
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS fix_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ts            INTEGER NOT NULL,
            signal_name   TEXT NOT NULL,
            success       INTEGER NOT NULL,
            error_message TEXT
        )
    """)
    _conn.commit()


def log_fix_attempt(signal_name: str, success: bool, error_message: str | None) -> None:
    """Record one fix attempt in fix_log; never raises."""
    try:
        if _conn is None:
            return
        ts = int(time.time())
        with _lock:
            _conn.execute(
                "INSERT INTO fix_log (ts, signal_name, success, error_message) VALUES (?, ?, ?, ?)",
                (ts, signal_name, int(success), error_message),
            )
            _conn.commit()
    except Exception:
        pass


def store_snapshot(results: list[dict]) -> None:
    """Persist status for each signal, skipping rows where status hasn't changed."""
    if _conn is None:
        return
    ts = int(time.time())
    cutoff = ts - _RETENTION_DAYS * 86400
    with _lock:
        for signal in results:
            name = signal["name"]
            status = signal["status"]
            # Only insert a new row when the status differs from the most recent entry.
            row = _conn.execute(
                "SELECT status FROM snapshots WHERE signal_name = ? ORDER BY ts DESC LIMIT 1",
                (name,),
            ).fetchone()
            if row is None or row[0] != status:
                _conn.execute(
                    "INSERT INTO snapshots (ts, signal_name, status) VALUES (?, ?, ?)",
                    (ts, name, status),
                )
        _conn.execute("DELETE FROM snapshots WHERE ts < ?", (cutoff,))
        _conn.commit()


def _relative_time(ts: int) -> str:
    """Convert a Unix timestamp to a human-readable relative string (e.g. '3 hours ago')."""
    delta = int(time.time()) - ts
    if delta < 60:
        return "just now"
    if delta < 3600:
        m = delta // 60
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if delta < 86400:
        h = delta // 3600
        return f"{h} hour{'s' if h != 1 else ''} ago"
    d = delta // 86400
    return f"{d} day{'s' if d != 1 else ''} ago"


def get_fix_log(limit: int = 20) -> list[dict]:
    """Return the most recent fix attempts from fix_log, newest first."""
    if _conn is None:
        return []
    with _lock:
        rows = _conn.execute(
            "SELECT ts, signal_name, success, error_message FROM fix_log ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "ts_display": _relative_time(ts),
            "signal_name": signal_name,
            "success": bool(success),
            "error_message": error_message,
        }
        for ts, signal_name, success, error_message in rows
    ]


def get_summary() -> list[dict]:
    """Return per-signal status history sorted by name, for rendering the history page."""
    if _conn is None:
        return []
    with _lock:
        rows = _conn.execute(
            "SELECT signal_name, status, ts FROM snapshots ORDER BY signal_name, ts ASC"
        ).fetchall()

    by_signal: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for name, status, ts in rows:
        by_signal[name].append((ts, status))

    result = []
    for name in sorted(by_signal):
        entries = by_signal[name]
        last_ts, last_status = entries[-1]

        # Build a list of status transitions for display; cap at the 5 most recent.
        transitions = [
            {
                "from_status": entries[i - 1][1],
                "to_status": entries[i][1],
                "when": _relative_time(entries[i][0]),
            }
            for i in range(1, len(entries))
        ]

        result.append({
            "name": name,
            "last_status": last_status,
            "last_changed": _relative_time(last_ts) if len(entries) > 1 else None,
            "transitions": transitions[-5:],
        })
    return result
