# Flask entry point for the macOS security dashboard.
# Serves the single-page dashboard at http://127.0.0.1:PORT (local only).
# All signal collection, history storage, and remediation execution are
# delegated to the collectors, history, and remediations packages.
# Never import this file as a module — run it directly with: .venv/bin/python src/app.py

import os
import sys
from collections import Counter
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from collectors import run_all_collectors, CATEGORIES
from history import init_db, store_snapshot, get_summary, get_fix_log, log_fix_attempt
from remediations import REMEDIATIONS
from remediations.executor import run_fix

ROOT = Path(__file__).parent.parent

app = Flask(
    __name__,
    template_folder=str(ROOT / "templates"),
    static_folder=str(ROOT / "static"),
)


def _get_int_env(name: str) -> int:
    """Read an env var as a non-negative integer; exit with an error message if invalid."""
    raw = os.environ.get(name, "0").strip()
    try:
        value = int(raw)
    except ValueError:
        print(f"ERROR: {name} must be a non-negative integer, got {raw!r}.", file=sys.stderr)
        sys.exit(1)
    if value < 0:
        print(f"ERROR: {name} must be >= 0, got {value}.", file=sys.stderr)
        sys.exit(1)
    return value


@app.template_filter('status_sort')
def _status_sort(signals_list):
    order = {'FAIL': 0, 'WARN': 1, 'UNKNOWN': 2, 'PASS': 3}
    return sorted(signals_list, key=lambda s: order.get(s.get('status', ''), 4))


@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; script-src 'self' 'unsafe-inline'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.route("/")
def dashboard():
    """Run all collectors, persist the snapshot, and render the main dashboard page."""
    signals = run_all_collectors(external=app.config["EXTERNAL_CALLS"])
    store_snapshot(signals)
    cat_names = frozenset(n for _, names in CATEGORIES for n in names)
    status_counts = Counter(s['status'] for s in signals)
    return render_template(
        "dashboard.html",
        signals=signals,
        refresh_interval=app.config["REFRESH_INTERVAL"],
        remediations=REMEDIATIONS,
        categories=CATEGORIES,
        categorized_names=cat_names,
        status_counts=status_counts,
    )


@app.route("/history")
def history_view():
    """Render the history page showing per-signal status transitions from SQLite."""
    return render_template("history.html", summary=get_summary(), fix_log=get_fix_log())


@app.route("/fix/<path:signal_name>", methods=["POST"])
def fix(signal_name):
    """Execute a remediation for the named signal via a privileged osascript call."""
    origin = request.headers.get("Origin")
    if origin is not None:
        expected = f"http://127.0.0.1:{app.config['PORT']}"
        if origin != expected:
            return jsonify({"success": False, "error": "Invalid request origin"}), 403
    if signal_name not in REMEDIATIONS:
        return jsonify({"success": False, "error": f"No remediation available for '{signal_name}'"}), 404
    result = run_fix(signal_name)
    log_fix_attempt(signal_name, result["success"], result.get("error"))
    return jsonify(result)


if __name__ == "__main__":
    # Refuse to start in Flask debug mode — it re-executes the file and would
    # spawn duplicate background threads (alerter, poll loop).
    if os.environ.get("FLASK_DEBUG", "0").strip() not in ("0", "false", ""):
        print("ERROR: FLASK_DEBUG is set. This dashboard does not run in debug mode.", file=sys.stderr)
        sys.exit(1)

    app.config["REFRESH_INTERVAL"] = _get_int_env("REFRESH_INTERVAL")
    app.config["ALERT_INTERVAL"] = _get_int_env("ALERT_INTERVAL")
    app.config["EXTERNAL_CALLS"] = os.environ.get("EXTERNAL_CALLS", "").strip() == "1"
    port = int(os.environ.get("PORT", 8000))
    app.config["PORT"] = port

    init_db()

    # Start the background alerter thread only when ALERT_INTERVAL > 0.
    # Imported here to avoid a circular import at module load time.
    if app.config["ALERT_INTERVAL"] > 0:
        from alerting import start_alerter
        start_alerter(app.config["ALERT_INTERVAL"], external=app.config["EXTERNAL_CALLS"])

    interval = app.config["REFRESH_INTERVAL"]
    alert = app.config["ALERT_INTERVAL"]
    refresh_note = f", auto-refresh every {interval}s" if interval else ", on-demand refresh"
    external_note = ", external calls: on" if app.config["EXTERNAL_CALLS"] else ", external calls: off"
    alert_note = f", alerting: every {alert}s" if alert else ", alerting: off"
    print(f"Dashboard running at http://127.0.0.1:{port} — local access only{refresh_note}{external_note}{alert_note}")
    app.run(host="127.0.0.1", port=port, debug=False)
