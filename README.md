# MacBook Security Dashboard

A personal, read-only security monitoring dashboard for macOS (Apple Silicon). Displays the status of key security controls using native macOS tools, served as a local web page. No data leaves the machine.

## Prerequisites

- macOS (Apple Silicon)
- Python 3.10 or later

## Setup

```zsh
/opt/homebrew/bin/python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

> The system `python3` on macOS is 3.9 and does not meet the 3.10 minimum. Use the Homebrew Python at `/opt/homebrew/bin/python3`, or whichever `python3` reports 3.10+.

## Run

```zsh
.venv/bin/python src/app.py
```

Then open `http://127.0.0.1:8000` in a browser.

To use a different port:

```zsh
PORT=9000 .venv/bin/python src/app.py
```

## Signals monitored

| Signal | What it checks | Why it matters |
|--------|---------------|----------------|
| **System Integrity Protection (SIP)** | `csrutil status` | Prevents modification of protected system files and directories, even by root. If disabled, malware can alter core OS binaries. |
| **Gatekeeper** | `spctl --status` | Enforces that apps are signed by an Apple-notarized developer before running. If disabled, unsigned or tampered apps run without warning. |
| **FileVault** | `fdesetup status` | Full-disk encryption — protects all data at rest. If off, anyone with physical access to the machine can read all data. |
| **Secure Boot** | `system_profiler SPiBridgeDataType` | Ensures only a trusted, Apple-signed OS loads at startup. If weakened, a compromised bootloader can persist silently across reinstalls. |

Status values: **PASS** (green) · **FAIL** (red) · **WARN** (amber) · **UNKNOWN** (yellow, check failed or output unrecognized)

## Known limitations

- **Apple Silicon only.** The Secure Boot check uses `system_profiler SPiBridgeDataType`, which is not available on Intel Macs.
- **Read-only.** The dashboard displays status only — it cannot enable FileVault, toggle Gatekeeper, or apply any fixes.
- **No persistence.** Data is collected fresh on every page load and is never written to disk.
- **On-demand refresh only.** There is no background polling or automatic refresh — click Refresh to re-run all checks.
- **Local access only.** The server binds to `127.0.0.1` and is not reachable from other devices on the network.
- **System integrity signals only (MVP).** Network, persistence, authentication, and other signal categories are planned for future phases. See `docs/SPEC.md`.

## Project structure

```
MacBook_Security/
├── docs/
│   ├── SPEC.md                  # Full project specification
│   ├── IMPLEMENTATION_PLAN.md   # Phased build plan with validation checklists
│   └── Security_Monitoring_Notes.md
├── src/
│   ├── collectors/
│   │   ├── __init__.py          # Collector registry (run_all_collectors)
│   │   └── system_integrity.py  # SIP, Gatekeeper, FileVault, Secure Boot checks
│   └── app.py                   # Flask entry point
├── templates/
│   └── dashboard.html           # Jinja2 dashboard template
├── static/
│   └── style.css                # Dashboard stylesheet
└── requirements.txt
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Port the server listens on |
| `REFRESH_INTERVAL` | `0` | Auto-refresh interval in seconds. `0` disables auto-refresh (on-demand only). Any positive integer enables the countdown and automatic page reload. |
| `FLASK_DEBUG` | — | Must not be set — the app will refuse to start if it is |

To enable auto-refresh every 30 seconds:

```zsh
REFRESH_INTERVAL=30 .venv/bin/python src/app.py
```
