import os
from pathlib import Path

from flask import Flask, render_template
from collectors import run_all_collectors

ROOT = Path(__file__).parent.parent

app = Flask(
    __name__,
    template_folder=str(ROOT / "templates"),
    static_folder=str(ROOT / "static"),
)


@app.route("/")
def dashboard():
    signals = run_all_collectors()
    return render_template("dashboard.html", signals=signals)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Dashboard running at http://127.0.0.1:{port} — local access only")
    app.run(host="127.0.0.1", port=port, debug=False)
