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

### System integrity

| Signal | What it checks | Why it matters |
|--------|---------------|----------------|
| **System Integrity Protection (SIP)** | `csrutil status` | Prevents modification of protected system files and directories, even by root. If disabled, malware can alter core OS binaries. |
| **Gatekeeper** | `spctl --status` | Enforces that apps are signed by an Apple-notarized developer before running. If disabled, unsigned or tampered apps run without warning. |
| **FileVault** | `fdesetup status` | Full-disk encryption — protects all data at rest. If off, anyone with physical access to the machine can read all data. |
| **Secure Boot** | `system_profiler SPiBridgeDataType` | Ensures only a trusted, Apple-signed OS loads at startup. If weakened, a compromised bootloader can persist silently across reinstalls. |

### Network

| Signal | What it checks | Why it matters |
|--------|---------------|----------------|
| **Application Firewall** | `socketfilterfw --getglobalstate` | Blocks unsolicited inbound connections to applications. If disabled, any app can accept connections from the network without restriction. |
| **Stealth Mode** | `socketfilterfw --getstealthmode` | Prevents the machine from responding to network probe requests such as ICMP ping. If off, the machine is more easily discovered during a network scan. |
| **Listening Services** | `lsof -iTCP -sTCP:LISTEN -P -n` | Shows TCP services accepting inbound connections. Services bound to all interfaces (`*`) are reachable from the local network, not just from this machine. |

### Persistence

WARN on persistence signals means items are present — that is expected for most systems. Review the listed entries to confirm they belong to software you installed.

| Signal | What it checks | Why it matters |
|--------|---------------|----------------|
| **User Launch Agents** | `~/Library/LaunchAgents/` | Per-user background tasks that run at login. Any `.plist` here launches a process automatically. Unexpected entries may indicate unwanted software. |
| **Global Launch Agents** | `/Library/LaunchAgents/` | System-wide background tasks installed by third-party software. Apple's own entries (`com.apple.*`) are filtered out — only third-party entries are shown. |
| **Launch Daemons** | `/Library/LaunchDaemons/` | Privileged background services that run as root. Apple's own entries are filtered out. Unexpected third-party daemons warrant review. |
| **Login Items** | `osascript` / System Events | Applications and helpers registered to launch at login. Shown as a list — review for anything you don't recognise. |

### Authentication

WARN on authentication signals means activity was detected — review if unexpected.

| Signal | What it checks | Why it matters |
|--------|---------------|----------------|
| **Failed Logins** | `log show` (loginwindow + sshd, past 24h) | Failed authentication attempts at the macOS login screen or via SSH. A WARN may be a mistyped password or an external probe — review the listed events. |
| **SSH Authorized Keys** | `~/.ssh/authorized_keys` | Keys that allow passwordless remote login to this machine. If present, anyone holding a matching private key can SSH in. |

Status values: **PASS** (green) · **FAIL** (red) · **WARN** (amber) · **UNKNOWN** (yellow, check failed or output unrecognized)

## Known limitations

- **Apple Silicon only.** The Secure Boot check uses `system_profiler SPiBridgeDataType`, which is not available on Intel Macs.
- **Read-only.** The dashboard displays status only — it cannot enable FileVault, toggle Gatekeeper, or apply any fixes.
- **No persistence.** Data is collected fresh on every page load and is never written to disk.
- **Local access only.** The server binds to `127.0.0.1` and is not reachable from other devices on the network.
- **Listening Services shows current-user processes only.** `lsof` runs without elevated privileges, so system-owned processes (running as root) do not appear in the Listening Services output.
- **Sudo activity is not monitored.** `sudo`'s audit record (the command that was run) is written to the BSM audit trail (`/var/audit/`), which requires root to read. The unified log only surfaces background system-level sudo calls (~500+ per day from daemons), which cannot be distinguished from user invocations. Deferred until a root-free data source is identified.
- **Other signal categories are planned.** See `docs/SPEC.md` for the full roadmap.

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
│   │   ├── system_integrity.py  # SIP, Gatekeeper, FileVault, Secure Boot checks
│   │   ├── network.py           # Application Firewall, Stealth Mode, Listening Services
│   │   ├── persistence.py       # User/Global Launch Agents, Launch Daemons, Login Items
│   │   └── auth.py              # Failed Logins, SSH Authorized Keys
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
