# MacBook Security Dashboard — Specification

## Project Overview

A personal macOS security monitoring dashboard for a MacBook (Apple Silicon, macOS). It collects security-relevant signals from the local machine using native macOS command-line tools, displays them in a lightweight web UI served on localhost, and provides one-click remediations for selected controls. The primary audience is the owner of the machine. The project ships as a local-only Flask app backed by a Waitress WSGI server, with a SQLite database for historical trend data.

**Platform:** macOS Apple Silicon only. Python 3.10+ (Homebrew: `/opt/homebrew/bin/python3`).

**Run command:** `.venv/bin/python src/app.py`

**Default URL:** `http://127.0.0.1:8000`

---

## Goals

- Display the status of 16 always-on security signals across 6 categories (see below)
- Provide an opt-in 17th signal that checks macOS version currency against Apple's API
- Collect data using only native macOS CLI tools; no third-party agents
- Serve a single-page dashboard at `http://127.0.0.1:PORT` using Python + Flask + Waitress
- Support on-demand refresh and configurable auto-refresh
- Provide one-click Fix buttons for 5 remediable controls (privilege-escalated via `osascript`)
- Persist status transition history to a local SQLite database; surface it on `/history`
- Optionally alert via macOS notifications when any signal changes state
- Keep all data strictly local — no data leaves the machine unless `EXTERNAL_CALLS=1` is set

## Non-Goals

- Remediating SIP, FileVault enrollment, or Secure Boot (require Recovery Mode or interactive setup)
- Authentication to access the dashboard (it binds to `127.0.0.1` — local-only access is the security boundary)
- CVE or threat-intel lookups
- Multi-user or networked deployments
- Mobile or non-macOS platforms

---

## Security Signals

### Category: System Integrity

| Signal | Data Source | PASS | FAIL | WARN |
|--------|-------------|------|------|------|
| **System Integrity Protection** | `csrutil status` | enabled | disabled | — |
| **Gatekeeper** | `spctl --status` | enabled | disabled | — |
| **FileVault** | `fdesetup status` | on | off | — |
| **Secure Boot** | `system_profiler SPiBridgeDataType` | Full Security | — | Reduced / No Security |

### Category: Network

| Signal | Data Source | PASS | FAIL | WARN |
|--------|-------------|------|------|------|
| **Application Firewall** | `socketfilterfw --getglobalstate` | on | off | — |
| **Stealth Mode** | `socketfilterfw --getstealthmode` | on | — | off |
| **Listening Services** | `lsof -nP -iTCP -iUDP` | no non-loopback listeners | — | non-loopback listener(s) present |

### Category: Persistence

| Signal | Data Source | PASS | FAIL | WARN |
|--------|-------------|------|------|------|
| **User Launch Agents** | `~/Library/LaunchAgents/` | no entries | — | entries present |
| **Global Launch Agents** | `/Library/LaunchAgents/` (non-Apple) | no entries | — | entries present |
| **Launch Daemons** | `/Library/LaunchDaemons/` (non-Apple) | no entries | — | entries present |
| **Login Items** | `sfltool dumpbtm` | no entries | — | entries present |

### Category: Authentication

| Signal | Data Source | PASS | FAIL | WARN |
|--------|-------------|------|------|------|
| **Failed Logins** | `log show` (loginwindow) | no failures in 24h | — | failures detected |
| **SSH Authorized Keys** | `~/.ssh/authorized_keys` | absent or empty | — | entries present |

### Category: Sharing & Remote Access

| Signal | Data Source | PASS | FAIL | WARN |
|--------|-------------|------|------|------|
| **Remote Login** | `launchctl list com.openssh.sshd` | disabled | enabled | — |
| **Screen Sharing / Remote Management** | `launchctl list com.apple.screensharing` | disabled | enabled | — |
| **AirDrop Receiver Mode** | `defaults read com.apple.NetworkBrowser` | off or Contacts Only | — | Everyone |

### Category: Software Hygiene

| Signal | Data Source | PASS | FAIL | WARN |
|--------|-------------|------|------|------|
| **Automatic Updates** | `defaults read /Library/Preferences/com.apple.SoftwareUpdate` | check + install enabled | check disabled | check on, install off |
| **Root Certificate Trust** | `security find-certificate -a -p /Library/Keychains/System.keychain` | no entries | — | entries present |
| **Screen Lock** | `defaults read com.apple.screensaver` | password on, delay = 0 | password off | password on, delay > 0 |

### Opt-in Signal (requires `EXTERNAL_CALLS=1`)

| Signal | Data Source | PASS | FAIL | WARN |
|--------|-------------|------|------|------|
| **macOS Version** | Apple GDMF API (`gdmf.apple.com`) | current in latest train | behind by a major release | minor update available |

---

## Remediations

Five signals have Fix buttons that escalate privileges via `osascript` (standard macOS password dialog; Touch ID works; Cancel returns a clean error).

| Signal | Button Label | Applies When | Command |
|--------|-------------|--------------|---------|
| **Application Firewall** | Enable Firewall | FAIL | `socketfilterfw --setglobalstate on` |
| **Stealth Mode** | Enable Stealth Mode | WARN | `socketfilterfw --setstealthmode on` |
| **Remote Login** | Disable Remote Login | FAIL | `launchctl disable system/com.openssh.sshd && launchctl bootout system/com.openssh.sshd` |
| **Screen Sharing / Remote Management** | Disable Screen Sharing | FAIL | `launchctl disable system/com.apple.screensharing && launchctl bootout system/com.apple.screensharing` |
| **Automatic Updates** | Enable Auto-Updates | FAIL | `defaults write … AutomaticCheckEnabled true && defaults write … CriticalUpdateInstall true` |

All `cmd` values are fixed constants in the remediations registry — never derived from user input.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Presentation Layer              │
│   Waitress WSGI + Flask (127.0.0.1:PORT)         │
│   Jinja2 templates  ·  static/style.css          │
│   /  (dashboard)    ·  /history                  │
└──────────────┬──────────────────┬────────────────┘
               │ GET /            │ POST /fix/<name>
┌──────────────▼──────┐  ┌────────▼───────────────┐
│   Collector Layer   │  │   Remediation Layer     │
│   src/collectors/   │  │   src/remediations/     │
│   one fn per signal │  │   executor.py (osascript│
│   subprocess, no    │  │   privilege escalation) │
│   sudo, timeout     │  └─────────────────────────┘
└──────────────┬──────┘
               │
┌──────────────▼──────────────────────────────────┐
│                  Storage Layer                   │
│   SQLite  ·  data/history.db                     │
│   signal_history: transition-only writes         │
│   fix_log: every fix attempt                     │
│   Pruned to 30 days on each write                │
└──────────────────────────────────────────────────┘

Background thread (opt-in, ALERT_INTERVAL > 0):
  Alerter polls all collectors, writes new transitions to DB,
  fires macOS notifications on state changes.

Opt-in external call (EXTERNAL_CALLS=1):
  check_macos_version() → HTTPS GET → gdmf.apple.com
  No machine-identifying data sent.
```

---

## Tech Stack

| Tool / Framework | Role |
|------------------|------|
| **Python 3.10+** | Data collection, routing, background alerter |
| **Flask 3.1** | HTTP routing, Jinja2 templating |
| **Waitress 3.0** | Production WSGI server (replaces Werkzeug dev server) |
| **Jinja2** | HTML templating (bundled with Flask) |
| **SQLite** (stdlib `sqlite3`) | Signal transition history and fix audit log |
| **HTML + CSS + vanilla JS** | Dashboard and history UI; no JS framework |
| **macOS native CLI tools** | Signal collection — zero third-party agent dependencies |
| **`venv`** | Python environment isolation |

---

## Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| `PORT` | `8000` | TCP port the server binds to |
| `REFRESH_INTERVAL` | `0` | Auto-refresh interval in seconds; `0` = off |
| `EXTERNAL_CALLS` | `""` | Set to `1` to enable the macOS Version opt-in signal |
| `ALERT_INTERVAL` | `0` | Background polling interval in seconds; `0` = off |
| `FLASK_DEBUG` | must not be set | App exits with an error if this is set to a truthy value |

---

## Feature Set

### Dashboard (`/`)

- **Summary bar** — counts of FAIL / WARN / UNKNOWN / PASS signals; each is a link to the first card of that status
- **Category sections** — 6 always-on categories; a 7th "External / Opt-in" section appears when `EXTERNAL_CALLS=1`
- **Status sorting** — within each category: FAIL → WARN → UNKNOWN → PASS
- **Status cards** — each shows signal name, status badge, description, raw CLI output (collapsible on PASS cards), and error message if collection failed
- **Urgency tinting** — FAIL cards have a red left border; WARN amber; UNKNOWN yellow; PASS cards have no accent
- **Fix buttons** — appear on applicable signals at applicable statuses; two-step confirmation (click → "Confirm?" + Cancel → execute)
- **Last-checked label** — header shows time elapsed since the page loaded; updates every 5 s
- **Auto-refresh** — optional countdown + automatic page reload when `REFRESH_INTERVAL > 0`

### History (`/history`)

- **Signal transitions table** — one row per signal; shows current status, last changed time (relative + absolute tooltip), and up to N recent PASS↔FAIL/WARN transitions
- **Client-side filter** — type-ahead search narrows the signal transitions table by signal name
- **Remediation attempts table** — every fix attempt logged with time, signal name, and outcome (success badge or failed badge + error message)
- **Freshness label** — header shows time elapsed since the history page loaded
- **Reload button** — navigates to `/history` and resets the freshness label

### Web Application Security

- **CSRF mitigation** — `Origin` header validated on all `POST /fix/<name>` requests; mismatched origin returns HTTP 403
- **HTTP security headers** — `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'self'`, `Referrer-Policy: no-referrer` on all responses
- **Fix audit log** — every fix attempt (success, failure, or user cancel) written to `fix_log` table in SQLite
- **Remediation registry** — fixed command constants only; `/fix/<name>` validates the name against the registry before executing

---

## Data & Privacy

- All signals are collected locally using macOS system tools via `subprocess`
- Status transitions are written to `data/history.db` (local SQLite); the file is excluded from git
- The only outbound network call is the macOS version check to `gdmf.apple.com`, and only when `EXTERNAL_CALLS=1` is explicitly set; no machine-identifying data is included
- The Flask+Waitress server binds to `127.0.0.1` only — not accessible from other devices on the network
- No credentials, tokens, or sensitive user data are collected or stored
- Raw command output displayed in the UI never leaves the machine

---

## Known Limitations

| Limitation | Reason |
|------------|--------|
| SIP, FileVault, Secure Boot have no Fix button | Require Recovery Mode or interactive setup wizard; cannot be scripted via `osascript` |
| Listening Services omits root-owned processes | `lsof` runs without elevated privileges; system processes running as root are not visible |
| Sudo activity not monitored | `COMMAND=` entries go to the BSM audit trail (`/var/audit/`), not the unified log; distinguishing user invocations from ~500 daily background daemon calls is not feasible without root |
| `log show` returns empty output when Full Disk Access is suppressed | Empty output with no header = UNKNOWN, not PASS |
| Screen Lock WARN delay value | `askForPasswordDelay` reflects the screensaver grace period, not the display sleep lock; users should verify in System Settings |
| `'unsafe-inline'` in CSP | Required for inline `<script>` blocks in the templates; mitigated by the localhost-only binding |

---

## Open Questions / Risks

| # | Question / Risk | Status |
|---|-----------------|--------|
| 1 | **Secure Boot data source** | Resolved: `system_profiler SPiBridgeDataType` provides equivalent output to `bputil -d` without root. Field matched by name, not position. |
| 2 | **WSGI server for production use** | Resolved: switched to Waitress 3.0 (Phase 21). Werkzeug dev server no longer used. |
| 3 | **macOS version variance** | Ongoing: parsers match known-good strings rather than fixed field positions; new macOS versions may require updates. |
| 4 | **Port conflicts** | Resolved: `PORT` env var overrides the default (8000). |
| 5 | **SIP in virtual machines** | Ongoing: SIP is disabled by default in some VM configurations. The FAIL status is accurate but context-dependent. |
| 6 | **`spctl --status` stderr output** | Resolved: collectors fall back to stderr when stdout is empty. |
| 7 | **`log show` case-sensitive predicate** | Resolved: case-sensitive `CONTAINS "failed"` used for loginwindow to avoid false positives from clipboard-related log entries. |
