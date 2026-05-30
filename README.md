# MacBook Security Dashboard

A personal, read-only security monitoring dashboard for macOS (Apple Silicon). Collects security signals from the local machine using native macOS tools and displays them in a lightweight web UI served on localhost.

## Prerequisites

- macOS (Apple Silicon)
- Python 3.10 or later

## Setup

```zsh
# Create and activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Run

```zsh
python src/app.py
```

Then open `http://127.0.0.1:5000` in a browser.

To use a different port:

```zsh
PORT=8080 python src/app.py
```

## Project structure

```
MacBook_Security/
├── docs/                  # Specification and planning documents
│   ├── SPEC.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── Security_Monitoring_Notes.md
├── src/
│   ├── collectors/        # One module per signal category
│   └── app.py             # Flask entry point
├── templates/             # Jinja2 HTML templates
├── static/
│   └── style.css          # Dashboard stylesheet
└── requirements.txt
```

## Notes

- The dashboard binds to `127.0.0.1` only — it is not accessible from other devices on the network.
- All data is collected locally. Nothing leaves the machine.
- This is a learning project. See `docs/SPEC.md` for full scope and design decisions.
