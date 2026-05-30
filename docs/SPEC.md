# MacBook Security Dashboard — MVP Specification

## Project Overview

This project is a personal, read-only security monitoring dashboard for a MacBook (Apple Silicon, macOS). It collects security-relevant signals from the local machine using native macOS command-line tools, then presents them in a lightweight web UI served on localhost. The primary audience is the owner of the machine. Learning goals are threefold: deepen familiarity with Claude Code as a development environment, gain hands-on experience with dashboard development (Python backend, local web UI), and build practical knowledge of macOS security fundamentals. The MVP is intentionally narrow — one category of signals, one page, no persistence — so the project ships quickly and can be extended incrementally.

---

## Goals & Non-Goals

### MVP Goals
- Display the status of four core macOS system integrity controls: SIP, Gatekeeper, FileVault, and Secure Boot
- Collect data using only native macOS CLI tools (no third-party agents)
- Serve a single-page dashboard on `localhost` using Python
- Support on-demand refresh (user-triggered; no background process)
- Read-only: display status, no remediations
- Strictly local: no data leaves the machine

### Non-Goals (MVP)
- Network monitoring (ports, firewall, outbound connections)
- Persistence monitoring (launch agents/daemons, login items)
- Authentication monitoring (failed logins, sudo activity, SSH keys)
- Remediations or one-click fixes
- Auto-refresh / polling
- External API calls (update version checks, CVE lookups)
- Alerting or push notifications
- Historical data or trend logging
- Authentication to access the dashboard

> **Design principle:** The architecture should keep future expansion low-friction. Each monitoring category (network, persistence, auth) should be addable as a self-contained module without reworking existing code.

---

## Security Signals to Monitor

| Signal | Data Source / Command | Why It Matters | Risk If Misconfigured |
|--------|-----------------------|----------------|-----------------------|
| **SIP** (System Integrity Protection) | `csrutil status` | Prevents modification of protected system files and directories, even by root. A foundational macOS security control introduced in OS X El Capitan. | Malware or a compromised process can alter core OS binaries, inject code into system processes, or persist across reinstalls. |
| **Gatekeeper** | `spctl --status` | Enforces that apps are signed by an Apple-notarized developer before running. Acts as the first line of defense against malicious software downloads. | Unsigned or tampered apps run without warning, bypassing Apple's malware scanning pipeline. |
| **FileVault** | `fdesetup status` | Full-disk encryption for the macOS volume. Protects all data at rest using XTS-AES-128 encryption. | Anyone with physical access to the machine (lost/stolen) can read all data by removing the drive or booting an external OS. |
| **Secure Boot** | `bputil -d` | Ensures only a trusted, Apple-signed operating system loads at startup. On Apple Silicon, this is enforced by the Secure Enclave. | A compromised bootloader or unauthorized OS could persist silently, surviving even a clean macOS reinstall. |

> **Note on Apple Silicon vs. Intel:** `bputil` is specific to Apple Silicon. On Intel Macs, Secure Boot is checked via the `Startup Security Utility` in Recovery Mode and is not easily scriptable. Since this project targets Apple Silicon, `bputil` is the correct tool — but its output should be treated carefully (see Open Questions).

---

## Architecture

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│   Flask (localhost:PORT) + Jinja2 HTML  │
└────────────────┬────────────────────────┘
                 │ on page load / refresh
┌────────────────▼────────────────────────┐
│          Data Collection Layer          │
│  Python module — one function per       │
│  signal; calls macOS CLI via subprocess │
│  and parses stdout into structured data │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          macOS System Tools             │
│  csrutil · spctl · fdesetup · bputil    │
└─────────────────────────────────────────┘

Storage: None (MVP is stateless; data is collected fresh on each request)
```

### macOS Permission Implications

| Command | Privilege Required | Notes |
|---------|-------------------|-------|
| `csrutil status` | None | Readable by any user from Terminal |
| `spctl --status` | None | Readable by any user |
| `fdesetup status` | None | Readable by any user (full disk access not required for status) |
| `bputil -d` | None for basic output; some flags require root | ⚠️ Output format and available flags vary; see Open Questions |

> No `sudo` or elevated privileges are required for the MVP read path. The app should **never** request or store credentials.

---

## Tech Stack

| Tool / Framework | Role | Rationale |
|------------------|------|-----------|
| **Python 3** | Data collection + web server | Readable syntax, strong stdlib (`subprocess`, `shlex`), widely used in security tooling — high learning ROI |
| **Flask** | Local HTTP server | Minimal boilerplate, excellent documentation, easy to extend; a common first Python web framework |
| **Jinja2** | HTML templating | Bundled with Flask; separates display logic from data collection cleanly |
| **HTML + CSS** | Dashboard UI | No JS framework for MVP — keeps the frontend trivial and the focus on the backend and security concepts |
| **macOS native CLI tools** | Signal collection | Zero dependencies; `subprocess` calls are transparent and auditable; no third-party agent required |
| **`venv`** | Python environment isolation | Keeps project dependencies separate from system Python; standard Python practice |

---

## MVP Feature Set

1. **Single-page dashboard** served at `http://localhost:<port>` — no login, no routing
2. **Four status cards**, one per signal: SIP, Gatekeeper, FileVault, Secure Boot
3. Each card displays:
   - Signal name and brief description
   - Status indicator: **PASS** / **FAIL** / **UNKNOWN**
   - Raw command output (collapsed or small text) for transparency and learning
4. **Color coding**: green (PASS), red (FAIL), yellow (UNKNOWN or parse error)
5. **Refresh button** — reloads the page, re-runs all checks; no caching
6. **Error handling** — if a command fails or output is unexpected, the card shows UNKNOWN rather than crashing

---

## Future Phases

The following are explicitly out of MVP scope. Each maps to a self-contained module that can be added later.

| Phase | Scope |
|-------|-------|
| **Phase 2 — Refresh modes** | Add configurable polling interval; abstract the current on-demand model behind a refresh strategy interface |
| **Phase 3 — Network signals** | Listening ports (`lsof -i -P -n`), firewall state (`socketfilterfw`), active outbound connections |
| **Phase 4 — Persistence signals** | Launch agents/daemons (`launchctl list`), login items |
| **Phase 5 — Authentication signals** | Failed login attempts, sudo activity (`log show`), authorized SSH keys |
| **Phase 6 — Remediations** | Read-write mode; enable FileVault, toggle Gatekeeper, etc. Requires privilege escalation design |
| **Phase 7 — External calls** | macOS update version check, optional CVE lookups; user-configurable opt-in |
| **Phase 8 — Alerting** | macOS notifications or email when a signal changes state |
| **Phase 9 — History** | Persist check results to a local SQLite database; trend view |

---

## Data & Privacy

- All data is collected locally using macOS system tools via `subprocess`
- No data is written to disk in the MVP (in-memory only, discarded after each response)
- No network calls are made to external services
- The Flask server binds to `127.0.0.1` only — not accessible from other devices on the network
- No credentials, tokens, or sensitive user data are collected or stored
- Raw command output (displayed in the UI) never leaves the machine

---

## Open Questions / Risks

| # | Question / Risk | Notes |
|---|-----------------|-------|
| 1 | **`bputil` output stability** | `bputil -d` output is undocumented by Apple and may vary across macOS versions or security policy configurations. The parser must be written defensively and fall back to UNKNOWN gracefully. Needs manual verification on the target machine before writing the parser. |
| 2 | **Flask dev server exposure** | Flask's built-in server is not hardened for production. Binding to `127.0.0.1` mitigates network exposure, but the app should include a startup warning that it is not intended for multi-user or networked environments. |
| 3 | **macOS version variance** | Command output format for `csrutil`, `spctl`, and `fdesetup` has changed across macOS versions. Parsers should match on known-good strings rather than assuming fixed field positions. |
| 4 | **Port conflicts** | The default port needs to be configurable (env var or CLI flag) to avoid collisions with other local services. |
| 5 | **SIP in virtual machines** | SIP is disabled by default in some VM configurations. The dashboard should note this context if SIP shows as disabled, rather than just showing FAIL. |

---

## Milestones

Ordered build steps for the MVP. Each step should be completable and testable independently.

1. **Project scaffold** — directory structure, `venv`, `requirements.txt`, `README` with run instructions
2. **Data collection module** — one Python function per signal; each returns a structured result (`status`, `raw_output`, `error`)
3. **CLI verification** — run each command manually on the target machine; confirm output is parseable and matches expected format
4. **Flask app skeleton** — single route (`/`) that calls all collectors and passes results to a template
5. **HTML template** — four status cards, placeholder data, basic layout
6. **Wire up data** — connect live collector output to the template; add color coding
7. **Error handling pass** — ensure every card degrades to UNKNOWN cleanly on subprocess failure or unexpected output
8. **End-to-end test** — run the app, verify all four cards render correctly on the target Apple Silicon Mac
9. **Polish & document** — add startup warning about localhost-only use; document how to run in `README`
