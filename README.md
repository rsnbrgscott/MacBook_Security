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

### External (opt-in)

These signals make outbound network requests and are disabled by default. Enable with `EXTERNAL_CALLS=1`.

| Signal | What it checks | Why it matters |
|--------|---------------|----------------|
| **macOS Version** | Compares `sw_vers` output against Apple's GDMF feed | Running an out-of-date macOS version means missing security patches. WARN = minor update available; FAIL = running a prior major release no longer receiving security backports. |

Status values: **PASS** (green) · **FAIL** (red) · **WARN** (amber) · **UNKNOWN** (yellow, check failed or output unrecognized)

## Remediations

Two signals have a **Fix** button that enables the control with a single click. macOS will prompt for your administrator password before any change is made.

| Signal | Fix action | Appears when |
|--------|-----------|--------------|
| **Application Firewall** | Enables the application firewall (`socketfilterfw --setglobalstate on`) | Status is FAIL |
| **Stealth Mode** | Enables stealth mode (`socketfilterfw --setstealthmode on`) | Status is WARN |

The fix runs under your own account via `osascript` with administrator privileges — no `sudoers` changes are required. Clicking Cancel in the password dialog leaves the setting unchanged.

## Known limitations

- **Apple Silicon only.** The Secure Boot check uses `system_profiler SPiBridgeDataType`, which is not available on Intel Macs.
- **History is local only.** Signal history is stored in `data/history.db` (SQLite, auto-created). Only status transitions are recorded; identical consecutive statuses are not duplicated. Data older than 30 days is pruned automatically.
- **Most signals have no Fix button.** SIP and Secure Boot can only be toggled in Recovery Mode and cannot be changed from a running OS. FileVault enrollment generates a recovery key and requires interactive input — use System Settings instead. Gatekeeper, Listening Services, persistence signals, and authentication signals do not have automated remediations.
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
├── data/
│   └── history.db               # SQLite history (auto-created; gitignored)
├── src/
│   ├── collectors/
│   │   ├── __init__.py          # Collector registry (run_all_collectors)
│   │   ├── system_integrity.py  # SIP, Gatekeeper, FileVault, Secure Boot checks
│   │   ├── network.py           # Application Firewall, Stealth Mode, Listening Services
│   │   ├── persistence.py       # User/Global Launch Agents, Launch Daemons, Login Items
│   │   ├── auth.py              # Failed Logins, SSH Authorized Keys
│   │   └── external.py          # macOS Version (opt-in, requires EXTERNAL_CALLS=1)
│   ├── alerting/
│   │   ├── __init__.py          # start_alerter() — background polling thread
│   │   └── notifier.py          # send_notification() via osascript
│   ├── history/
│   │   └── __init__.py          # init_db(), store_snapshot(), get_summary()
│   ├── remediations/
│   │   ├── __init__.py          # REMEDIATIONS registry (signal → label, cmd, applies_to)
│   │   └── executor.py          # run_fix() — executes fix via osascript with admin privileges
│   └── app.py                   # Flask entry point
├── templates/
│   ├── dashboard.html           # Jinja2 dashboard template
│   └── history.html             # Signal history / state-change log
├── static/
│   └── style.css                # Dashboard stylesheet
└── requirements.txt
```

## History

Open `http://127.0.0.1:8000/history` to see a state-change log for all signals. The table shows each signal's current status, when it last changed, and up to five recent transitions (e.g., PASS → FAIL).

History is stored in `data/history.db` (created automatically on first launch). Only status transitions are written — if a signal's status is unchanged between checks, nothing is stored. Records older than 30 days are pruned automatically. The file is gitignored and never leaves the machine.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Port the server listens on |
| `REFRESH_INTERVAL` | `0` | Auto-refresh interval in seconds. `0` disables auto-refresh (on-demand only). Any positive integer enables the countdown and automatic page reload. |
| `EXTERNAL_CALLS` | `""` | Set to `1` to enable opt-in signals that make outbound network requests (currently: macOS Version check). |
| `ALERT_INTERVAL` | `0` | Polling interval for background alerting, in seconds. `0` disables alerting. Any positive integer starts a background thread that checks all signals at that interval and fires a macOS notification on any status change. |
| `FLASK_DEBUG` | — | Must not be set — the app will refuse to start if it is |

To enable auto-refresh every 30 seconds:

```zsh
REFRESH_INTERVAL=30 .venv/bin/python src/app.py
```

To enable the macOS version check:

```zsh
EXTERNAL_CALLS=1 .venv/bin/python src/app.py
```

To enable background alerting (check every 5 minutes):

```zsh
ALERT_INTERVAL=300 .venv/bin/python src/app.py
```

## Alerting

When `ALERT_INTERVAL` is set to a positive integer, the app runs a background thread that calls all collectors on that interval and fires a macOS notification banner whenever any signal changes status — in either direction (e.g., PASS→FAIL, FAIL→PASS, PASS→WARN).

The first poll after startup silently initialises state; no notifications fire until the second poll. If the app is restarted, state resets and the first poll is again silent. Notification delivery uses `osascript display notification` — no third-party dependencies and no TCC permission required.

## Privacy

When `EXTERNAL_CALLS=1` is set, the dashboard makes one `GET` request per page load to `https://gdmf.apple.com/v2/pmv` (Apple's official MDM version feed). No machine-identifying data is transmitted — only a standard `User-Agent` header is sent. The response is used solely to compare version strings; nothing is stored or forwarded.
