# MacBook Security Dashboard — Implementation Plan

This document breaks the project into phases, each composed of single-session steps. Every step ends with a concrete validation check. Each phase ends with a phase-level integration validation.

Phases 1–5 deliver and harden the MVP. Phases 6–14 correspond to the future phases defined in `SPEC.md` and are planned at a higher level of detail — they will be elaborated before implementation begins.

---

## Phase 1 — Project Scaffold

**Goal:** Establish the directory structure, Python environment, and project skeleton so all future work has a consistent home.

---

### Step 1.1 — Create directory structure ✅

Create the following layout inside the repo root:

```
MacBook_Security/
├── docs/                  # (already exists)
├── src/
│   ├── collectors/        # One module per signal category
│   └── app.py             # Flask entry point
├── templates/             # Jinja2 HTML templates
├── static/
│   └── style.css          # Dashboard stylesheet
├── requirements.txt
└── README.md              # (already exists — update in Step 1.3)
```

**Validation:** Run `find . -type d` from the repo root and confirm all directories exist.

---

### Step 1.2 — Initialize Python virtual environment and dependencies ✅

- Create a `venv` at the repo root: `python3 -m venv .venv`
- Add `Flask` as the only dependency in `requirements.txt`
- Install dependencies: `pip install -r requirements.txt`
- Add `.venv/` to `.gitignore`

**Validation:** Run `.venv/bin/python -c "import flask; print(flask.__version__)"` — a version string confirms Flask installed correctly.

---

### Step 1.3 — Update README with run instructions ✅

Update `README.md` to include:
- What the project is (one sentence)
- Prerequisites (Python 3.x, macOS Apple Silicon)
- How to set up the environment (`python3 -m venv`, `pip install`)
- How to run the dashboard (`python src/app.py`)
- How to open it in a browser (`http://127.0.0.1:5000`)

**Validation:** Follow the README instructions from scratch in a clean terminal session and confirm they produce a working result (once the app exists in later phases). For now: confirm the file is written and readable.

---

### Phase 1 Integration Validation

- [x] `find . -type d` shows `src/`, `src/collectors/`, `templates/`, `static/`
- [x] `.venv/bin/python -c "import flask"` exits with no error
- [x] `requirements.txt` exists and lists Flask
- [x] `.gitignore` excludes `.venv/`
- [x] `README.md` contains setup and run instructions

---

## Phase 2 — CLI Verification & Data Collection Layer

**Goal:** Verify that each macOS command produces parseable output on this machine, then write a collector module for each signal. This phase has no UI — output is validated by running Python directly.

> **Why verify before coding?** The `bputil` tool in particular has undocumented output. Running the commands first prevents writing a parser against assumptions that don't hold on this machine.

---

### Step 2.1 — Manually verify CLI commands ✅

Run each of the following in Terminal and record the exact output:

| Command | Expected output contains | Result |
|---------|--------------------------|--------|
| `csrutil status` | `System Integrity Protection status: enabled` (or `disabled`) | ✅ enabled |
| `spctl --status` | `assessments enabled` (or `disabled`) | ✅ assessments enabled |
| `fdesetup status` | `FileVault is On` (or `Off`) | ✅ FileVault is On |
| ~~`bputil -d`~~ `system_profiler SPiBridgeDataType` | `Secure Boot: Full Security` | ✅ Full Security |

> ⚠️ `bputil -d` requires root (exit code 1). Replaced with `system_profiler SPiBridgeDataType`, which provides equivalent output without elevated privileges. SPEC.md updated accordingly. Full outputs recorded in `docs/cli_verification.md`.

**Validation:** All four commands run without error. Paste the raw output into a scratch note — it will be used to write the parsers in Step 2.2.

---

### Step 2.2 — Write the system integrity collector module ✅

Create `src/collectors/system_integrity.py` with four functions:

```
check_sip()         → { "status": "PASS"|"FAIL"|"UNKNOWN", "raw": str, "error": str|None }
check_gatekeeper()  → same shape
check_filevault()   → same shape
check_secure_boot() → same shape
```

Rules for every collector function:
- Use `subprocess.run()` with a timeout; never `shell=True`
- Parse stdout using string matching against known-good phrases (not field position)
- On any exception or unrecognized output, return `status: "UNKNOWN"` with the error captured in the `error` field — never raise or crash

**Validation:** Run `python src/collectors/system_integrity.py` (add a `__main__` block that calls all four functions and prints results). All four return dicts with the correct keys; none raise an exception.

---

### Step 2.3 — Write a collector registry ✅

Create `src/collectors/__init__.py` that exposes a single function:

```python
def run_all_collectors() -> list[dict]:
    ...
```

This function calls all registered collector modules and returns a list of results. The list structure (not hardcoded imports) is what allows new signal categories to be added in future phases without touching the Flask app.

**Validation:** Run `python -c "from src.collectors import run_all_collectors; print(run_all_collectors())"` from the repo root. Output is a list of four dicts, each with `status`, `raw`, and `error` keys.

---

### Phase 2 Integration Validation

- [x] All four CLI commands run successfully in Terminal
- [x] `src/collectors/system_integrity.py` exists with four collector functions
- [x] Each function returns the correct dict shape on the target machine
- [x] `src/collectors/__init__.py` exposes `run_all_collectors()`
- [x] `run_all_collectors()` returns exactly four results, none with unhandled exceptions

---

## Phase 3 — Flask App & Routing

**Goal:** Stand up the Flask application with a single route that collects data and passes it to a template. No UI polish yet — the goal is a working data pipeline from CLI tools to the browser.

---

### Step 3.1 — Create the Flask application entry point ✅

Create `src/app.py`:
- Import Flask and `run_all_collectors`
- Define a single route: `GET /`
- Route handler calls `run_all_collectors()`, passes results to `render_template("dashboard.html", signals=results)`
- Bind to `127.0.0.1` only (not `0.0.0.0`)
- Port configurable via `PORT` environment variable, defaulting to `5000`
- Print a startup warning to stdout: `"Dashboard running at http://127.0.0.1:{PORT} — local access only"`

**Validation:** `python src/app.py` starts without error and prints the startup warning.

---

### Step 3.2 — Create a minimal placeholder template ✅

Create `templates/dashboard.html` with:
- Valid HTML5 boilerplate
- A heading: "MacBook Security Dashboard"
- A loop over `signals` that renders each signal's name and raw status as plain text
- A link or button labeled "Refresh" that navigates to `/`

No styling yet — this is a data-pipeline check, not a UI step.

**Validation:** Open `http://127.0.0.1:5000` in a browser. The page loads, shows four signal names, and each displays a status value (`PASS`, `FAIL`, or `UNKNOWN`). The Refresh link reloads the page and re-runs the checks.

---

### Phase 3 Integration Validation

- [x] `python src/app.py` starts, prints startup warning, and stays running
- [x] `GET http://127.0.0.1:5000/` returns HTTP 200
- [x] Page displays four signals with status values
- [x] Refresh reloads the page and re-runs all collectors (verified via curl — live data confirmed)
- [ ] Server is not accessible from another device on the local network (bind address is `127.0.0.1`)

---

## Phase 4 — Dashboard UI

**Goal:** Replace the placeholder template with a complete, styled dashboard. Four status cards with color coding, signal descriptions, raw output display, and a proper refresh button.

---

### Step 4.1 — Design the status card component ✅

Each card must display:
- Signal name (e.g., "System Integrity Protection")
- One-line description of what it protects
- Status badge: **PASS** / **FAIL** / **UNKNOWN**
- The raw command output (small monospace text, below the badge)

Define a card layout in `templates/dashboard.html` using a Jinja2 `for` loop over `signals`. No inline styles — use CSS classes only.

**Validation:** The template renders four visually distinct cards with all required fields populated. No broken layout or missing data.

---

### Step 4.2 — Write the stylesheet ✅

Create `static/style.css`:
- Page: dark or neutral background, centered content, readable font
- Cards: rounded corners, drop shadow, fixed minimum width, clear visual separation
- Status badge color coding:
  - PASS → green background
  - FAIL → red background
  - UNKNOWN → yellow/amber background
- Raw output block: monospace font, muted color, smaller size
- Refresh button: clearly styled, prominent placement

**Validation:** Load the dashboard in a browser. All four cards display with correct badge colors matching their actual status. The page is readable without zooming. The refresh button is visually distinct.

---

### Step 4.3 — Add signal metadata to collector output ✅ (completed as prerequisite for Step 4.1)

Update each collector function to include two additional fields in its return dict:
- `"name"`: human-readable signal name (e.g., `"FileVault"`)
- `"description"`: one-line explanation of what the signal protects

This keeps all signal knowledge in the collector layer, not the template.

**Validation:** Re-run `run_all_collectors()` and confirm each dict now includes `name` and `description`. Dashboard cards display the correct names and descriptions without hardcoding them in the template.

---

### Phase 4 Integration Validation

- [x] All four cards render with name, description, status badge, and raw output
- [x] Badge colors are correct for each signal's actual status
- [x] Raw output is visible and legible
- [x] Refresh button reloads the page and updates data
- [x] Page renders correctly at normal browser zoom (no overflow or broken layout)

---

## Phase 5 — Error Handling, Hardening & Documentation

**Goal:** Make the application robust to failure, safe to run, and easy to pick up after a break. This phase produces the finished MVP.

---

### Step 5.1 — Error handling pass ✅

Review each collector function and verify:
- A subprocess timeout does not crash the app (returns UNKNOWN)
- A command not found (e.g., `bputil` missing) does not crash the app (returns UNKNOWN)
- Unexpected output format (unrecognized string) returns UNKNOWN, not FAIL
- The `error` field captures the failure reason as a string

Test by temporarily breaking one collector (e.g., change the command name to something invalid) and confirm the card shows UNKNOWN rather than a 500 error.

**Validation:** Dashboard loads successfully with all four cards even when one collector is forced to fail. The broken card shows UNKNOWN with a non-empty `error` field.

---

### Step 5.2 — Configurable port and environment variable support ✅

- Confirm `PORT` env var overrides the default port (`PORT=8080 python src/app.py` starts on 8080)
- Add a check that prevents Flask from running in debug mode when launched normally (debug mode auto-reloads and can expose stack traces)

**Validation:** `PORT=8080 python src/app.py` starts on port 8080. `http://127.0.0.1:8080` loads the dashboard. Default launch uses port 5000.

---

### Step 5.3 — Finalize README ✅

Update `README.md` to include:
- Prerequisites (Python 3.x, macOS Apple Silicon)
- Setup steps (clone, venv, pip install)
- How to run (`python src/app.py`)
- How to change the port (`PORT=8080 python src/app.py`)
- What each signal means (brief, one line each)
- Known limitations (Apple Silicon only, no persistence, no remediations)

**Validation:** Follow the README instructions in a clean terminal session (fresh shell, no active venv). The dashboard starts and loads correctly.

---

### Step 5.4 — End-to-end MVP test ✅

Run through the complete user flow:
1. Clone/open the repo in a fresh terminal
2. Follow README setup instructions
3. Launch the app
4. Confirm all four cards load with correct statuses
5. Click Refresh — data reloads
6. Force one collector to fail — card shows UNKNOWN gracefully
7. Stop the server (`Ctrl-C`) — no errors

**Validation:** All seven steps above complete without error. The MVP is shippable.

---

### Phase 5 Integration Validation

- [x] All four cards render with live data on a clean launch
- [x] Forced collector failure produces UNKNOWN card, not a crash
- [x] `PORT` env var correctly overrides the default port
- [x] Flask is not running in debug mode by default
- [x] README instructions work from a clean terminal session
- [x] No hardcoded paths, credentials, or machine-specific values in any file

---

## Phase 6 — Polling / Auto-Refresh

**Goal:** Add configurable auto-refresh so the dashboard updates on a fixed interval without requiring a manual page reload. On-demand mode (the MVP default) must continue to work unchanged.

> **Refresh strategy:** Auto-refresh is implemented in the browser via a JavaScript countdown that calls `location.reload()`. The server needs no new routes — it only passes the configured interval to the template. This keeps Flask stateless and makes the refresh model transparent and easy to reason about.

---

### Step 6.1 — Add REFRESH_INTERVAL support to app.py ✅

- Read `REFRESH_INTERVAL` env var; default `0` (off)
- Validate it is a non-negative integer; exit with a clear error if not
- Pass `refresh_interval` to `render_template` so the template can act on it

**Validation:** `REFRESH_INTERVAL=30 .venv/bin/python src/app.py` starts without error. `curl http://127.0.0.1:8000/` returns a page containing `30` where the interval is rendered. Default launch passes `0`.

---

### Step 6.2 — Add countdown indicator and auto-reload to the template ✅

Update `templates/dashboard.html` and `static/style.css`:
- If `refresh_interval > 0`: show a visible indicator in the header (e.g. "Auto-refresh: 30s") with a live countdown
- A small vanilla JS block decrements the countdown each second and calls `location.reload()` when it reaches zero
- If `refresh_interval == 0`: indicator is hidden; behavior is identical to the MVP

**Validation:** With `REFRESH_INTERVAL=10`, open the dashboard in a browser. The countdown ticks from 10 to 0 and the page reloads. Without `REFRESH_INTERVAL`, no indicator appears and nothing changes.

---

### Step 6.3 — Update README ✅

Add `REFRESH_INTERVAL` to the environment variables table with its default and valid values.

**Validation:** README accurately describes the feature; a reader can enable auto-refresh using only the README.

---

### Phase 6 Integration Validation

- [x] Default launch (no `REFRESH_INTERVAL`) behaves identically to the MVP — no indicator, no auto-reload
- [x] `REFRESH_INTERVAL=10` shows countdown and reloads the page when it reaches zero
- [x] `REFRESH_INTERVAL=0` explicitly disables auto-refresh (same as default)
- [x] Invalid value (e.g. `REFRESH_INTERVAL=abc`) exits with a clear error message
- [x] Manual Refresh button still works in both modes

---

## Phase 7 — Network Signals

Spec reference: `SPEC.md § Future Phases — Phase 3`.

**Goal:** Add a second signal category covering the macOS Application Firewall and listening service exposure. Each network signal follows the same collector shape as system integrity: `name`, `description`, `status`, `raw`, `error`.

**Signals in scope:**

| Signal | Command | Status logic |
|--------|---------|-------------|
| Application Firewall | `socketfilterfw --getglobalstate` | PASS = enabled, FAIL = disabled |
| Stealth Mode | `socketfilterfw --getstealthmode` | PASS = enabled, WARN = disabled |
| Listening Services | `lsof -iTCP -sTCP:LISTEN -P -n` | PASS = all loopback-only, WARN = any external-facing listener |

> Active outbound connections are deferred — they produce high-churn output with no reliable PASS/FAIL boundary and are better suited to a later history/alerting phase.

> **Privilege model:** `socketfilterfw` read-only flags (`--getglobalstate`, `--getstealthmode`) do not require `sudo` on modern macOS. If either exits non-zero without elevated privileges, fall back to `defaults read /Library/Preferences/com.apple.alf` (key `globalstate`: 0 = off, 1 = on, 2 = block all). This fallback reads saved policy, not real-time kernel state — document the distinction in Known Limitations if used.

---

### Step 7.1 — Resolve the privilege model and verify CLI commands ✅

Run each command in Terminal **without** `sudo` and record the exact output:

| Command | Expected output contains | Run without sudo? |
|---------|--------------------------|------------------|
| `/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate` | `enabled` or `disabled` | TBD — record result |
| `/usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode` | `enabled` or `disabled` | TBD — record result |
| `lsof -iTCP -sTCP:LISTEN -P -n` | Lines with `LISTEN` | Yes (own processes only without root) |

If either `socketfilterfw` flag fails without root, switch to the `defaults read` fallback and note it in `docs/cli_verification.md` and README Known Limitations.

Record exact output in `docs/cli_verification.md` under a new `## Phase 7 — Network` heading. This output drives the parsers written in Step 7.2.

**Validation:** All commands produce parseable output without `sudo`. Exact output is recorded in `docs/cli_verification.md`.

---

### Step 7.2 — Write the network collector module ✅

Create `src/collectors/network.py` with three functions:

```
check_firewall()        → { name, description, status, raw, error }
check_stealth_mode()    → { name, description, status, raw, error }
check_listening_ports() → { name, description, status, raw, error }
```

**Status logic:**

| Collector | PASS | WARN | FAIL | UNKNOWN |
|-----------|------|------|------|---------|
| `check_firewall` | Firewall enabled | — | Firewall disabled | Command failed or unrecognized output |
| `check_stealth_mode` | Stealth mode enabled | Stealth mode disabled | — | Command failed or unrecognized output |
| `check_listening_ports` | All listeners bound to loopback (`127.0.0.1` / `::1`) | One or more listeners bound to `0.0.0.0` / `*` / all interfaces | — | `lsof` failed or returned no parseable output |

Rules (same as system integrity collectors):
- Use `subprocess.run()` with a timeout; never `shell=True`
- Parse by string matching, not field position
- Any exception or unrecognized output → `UNKNOWN` with error captured; never raise

**Validation:** Add a `__main__` block and run `.venv/bin/python src/collectors/network.py`. All three functions return dicts with the correct keys; none raise an exception.

---

### Step 7.3 — Register network collectors ✅

Update `src/collectors/__init__.py` to import and append the three network collectors to `_COLLECTORS`. No changes to `app.py` or the template — the modular registry picks them up automatically.

**Validation:** `.venv/bin/python -c "from src.collectors import run_all_collectors; print(len(run_all_collectors()))"` prints `7`. All seven dicts contain the required keys.

---

### Step 7.4 — End-to-end dashboard check ✅

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000` in a browser.

- Confirm all seven cards render (4 system integrity + 3 network)
- Confirm badge colors match each signal's actual status
- Temporarily rename one network command in the collector to force a failure; confirm that card shows UNKNOWN and the other six are unaffected; restore the command

**Validation:** All seven cards render with correct data and the forced failure degrades gracefully.

---

### Step 7.5 — Update README and documentation ✅

- Add the three new signals to the "Signals monitored" table in `README.md`
- Add a Known Limitations entry if the `defaults read` fallback was used (noting it reflects saved policy, not real-time kernel state)
- Confirm `docs/cli_verification.md` has the Phase 7 section from Step 7.1

**Validation:** README signals table has seven rows. `docs/cli_verification.md` has the Phase 7 section.

---

### Phase 7 Integration Validation

- [x] All three network collector functions return the correct dict shape
- [x] `check_firewall` status matches the actual firewall state in System Settings → Network → Firewall
- [x] `check_stealth_mode` status matches the actual stealth mode setting
- [x] `check_listening_ports` correctly returns WARN if any listener is bound to a non-loopback interface
- [x] All seven cards render in the dashboard with no layout regressions from Phase 6
- [x] Badge colors are correct for all seven signals
- [x] Forced network collector failure shows UNKNOWN; other six cards unaffected
- [x] No collector calls `sudo` — all commands run without elevated privileges
- [x] README signals table reflects all seven monitored signals

---

## Phase 8 — Persistence Signals

Spec reference: `SPEC.md § Future Phases — Phase 4`.

**Goal:** Add a third signal category covering the most common macOS persistence mechanisms: launch agents, launch daemons, and login items. Each signal follows the same collector shape as prior phases: `name`, `description`, `status`, `raw`, `error`.

**Signals in scope:**

| Signal | Source | PASS | WARN | UNKNOWN |
|--------|--------|------|------|---------|
| User Launch Agents | `~/Library/LaunchAgents/` | Directory empty | Any `.plist` files present | Directory unreadable |
| Global Launch Agents | `/Library/LaunchAgents/` | Empty or Apple-only entries | Non-Apple entries present | Directory unreadable |
| Launch Daemons | `/Library/LaunchDaemons/` | Empty or Apple-only entries | Non-Apple entries present | Directory unreadable |
| Login Items | `osascript` or `sfltool dumpbtm` | No items registered | Items present | Command failed / permission denied |

> **Why WARN and not FAIL for non-empty results:** Legitimate software (Homebrew updater, backup agents, printer drivers) routinely installs launch agents and daemons. A WARN badge means "items are present — review them," not "something is wrong." This distinction should be reflected in each card description.

> **Non-Apple filtering:** For `/Library/LaunchAgents` and `/Library/LaunchDaemons`, entries with filenames prefixed `com.apple.` are expected Apple system items and are excluded from the WARN count. Only third-party entries trigger WARN.

> **Implementation note:** Persistence signals read filesystem directories, not subprocess output. The collector module will use Python's `pathlib` directly rather than the `_run()` / `subprocess` pattern used in prior phases. Error handling uses `try/except OSError` instead of `TimeoutExpired` / `FileNotFoundError`.

> **Login items:** The CLI approach varies by macOS version. `osascript -e 'tell application "System Events" to get the name of every login item'` works on older macOS but may require Automation permission on Ventura+. `sfltool dumpbtm` covers the Background Task Manager items added in Ventura. Step 8.1 determines which method works on this machine without a permission prompt.

---

### Step 8.1 — Verify data sources and resolve the privilege model ✅

Without `sudo`, run and record the exact output of each candidate command and directory listing:

| Source | Command / Path | Privilege needed |
|--------|---------------|-----------------|
| User launch agents | `ls ~/Library/LaunchAgents/` | None (user-owned) |
| Global launch agents | `ls /Library/LaunchAgents/` | None (world-readable) |
| Launch daemons | `ls /Library/LaunchDaemons/` | None (world-readable) |
| Login items (legacy) | `osascript -e 'tell application "System Events" to get the name of every login item'` | TBD — may prompt |
| Login items (modern) | `sfltool dumpbtm` | TBD — run and record |

Decision rule for login items: use whichever method returns output without a permission prompt or TCC dialog. If neither works cleanly, document it as a known limitation and omit the Login Items card from this phase.

Record all output in `docs/cli_verification.md` under a new `## Phase 8 — Persistence` heading.

**Validation:** All chosen data sources return output without `sudo` or a permission dialog. Output recorded in `docs/cli_verification.md`.

---

### Step 8.2 — Write the persistence collector module ✅

Create `src/collectors/persistence.py` with collector functions matching the number of viable signals confirmed in Step 8.1 (three minimum, four if login items is clean):

```
check_user_launch_agents()    → { name, description, status, raw, error }
check_global_launch_agents()  → { name, description, status, raw, error }
check_launch_daemons()        → { name, description, status, raw, error }
check_login_items()           → { name, description, status, raw, error }  # if viable
```

**Status logic:**

| Collector | PASS | WARN | UNKNOWN |
|-----------|------|------|---------|
| `check_user_launch_agents` | `~/Library/LaunchAgents/` empty or absent | Any `.plist` files present | `OSError` reading directory |
| `check_global_launch_agents` | `/Library/LaunchAgents/` empty or only `com.apple.*` entries | Non-`com.apple.*` entries present | `OSError` reading directory |
| `check_launch_daemons` | `/Library/LaunchDaemons/` empty or only `com.apple.*` entries | Non-`com.apple.*` entries present | `OSError` reading directory |
| `check_login_items` | No items returned | One or more items returned | Command failed or permission denied |

**`raw` field content:**
- PASS: `"No entries found."` (or `"Apple system entries only."` for filtered directories)
- WARN: newline-separated list of entry names
- UNKNOWN: the exception or error message

**Implementation rules:**
- Use `pathlib.Path` for directory reads; no `subprocess` for directory signals
- Wrap all filesystem access in `try/except OSError`; never raise
- Login items (if included): use `subprocess.run()` via `_run()`, same as prior collectors
- Card descriptions must communicate that WARN is informational, not a definitive failure

**Validation:** Add a `__main__` block and run `.venv/bin/python src/collectors/persistence.py`. All functions return dicts with the correct keys; none raise an exception.

---

### Step 8.3 — Register persistence collectors ✅

Update `src/collectors/__init__.py` to import and append the persistence collectors to `_COLLECTORS`. No changes to `app.py` or the template.

**Validation:** `.venv/bin/python -c "from src.collectors import run_all_collectors; print(len(run_all_collectors()))"` prints `10` (or `11` if login items is included). All dicts contain the required keys.

---

### Step 8.4 — End-to-end dashboard check ✅

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000` in a browser.

- Confirm all cards render (7 existing + 3 or 4 new)
- Confirm badge colors match actual state on this machine
- Force one persistence collector to fail (introduce an `OSError` by pointing at a nonexistent path); confirm it shows UNKNOWN and other cards are unaffected; restore

**Validation:** All cards render with correct data and the forced failure degrades gracefully.

---

### Step 8.5 — Update README and documentation ✅

- Add persistence signals to the "Signals monitored" section in `README.md` under a new `### Persistence` heading
- Add a Known Limitations entry if login items were omitted (explaining why and which macOS version constraint applies)
- Confirm `docs/cli_verification.md` has the Phase 8 section from Step 8.1

**Validation:** README signals section has a Persistence subsection. `docs/cli_verification.md` has the Phase 8 section.

---

### Phase 8 Integration Validation

- [x] All persistence collector functions return the correct dict shape
- [x] `check_user_launch_agents` status reflects actual contents of `~/Library/LaunchAgents/`
- [x] `check_global_launch_agents` filters `com.apple.*` entries correctly (Apple entries do not trigger WARN)
- [x] `check_launch_daemons` filters `com.apple.*` entries correctly
- [x] Login items signal included if viable, omitted with a documented limitation if not
- [x] All new cards render in the dashboard with no layout regressions
- [x] Badge colors are correct for all signals
- [x] Forced persistence collector failure shows UNKNOWN; other cards unaffected
- [x] No collector calls `sudo` — all data sources readable without elevated privileges
- [x] README persistence section accurately describes each signal

---

## Phase 9 — Authentication Signals

Spec reference: `SPEC.md § Future Phases — Phase 5`.

**Goal:** Add a third signal category covering recent authentication events and SSH key exposure. Each signal follows the same collector shape as prior phases: `name`, `description`, `status`, `raw`, `error`.

**Signals in scope:**

| Signal | Source | PASS | WARN | UNKNOWN |
|--------|--------|------|------|---------|
| Failed Logins | `log show` (loginwindow + sshd) | No failures in past 24h | One or more failures | Command failed, timed out, or completely empty output |
| SSH Authorized Keys | `~/.ssh/authorized_keys` | File absent or empty | File has one or more key entries | `OSError` reading the file |

> **Sudo activity omitted (Step 9.1 finding):** `sudo`'s audit record (the `COMMAND=` message) is written to the BSM audit trail (`/var/audit/`), which requires root to read. It does not appear in the unified log at any log level. The only sudo data in the unified log without root is ~563 undifferentiated background system process invocations per day (from McAfee, Docker, and other daemons), which cannot be distinguished from user invocations. Deferred to a future phase if a root-free data source is identified. Documented in Known Limitations.

> **Why WARN and not FAIL for log-based signals:** A failed login may be the user mistyping a password. WARN means "activity was detected — review if unexpected." FAIL is reserved for clear misconfigurations (e.g., FileVault off).

> **FDA suppression mitigation:** `log show` returns a header line even when there are no matching events. If the output is completely empty (no header), that indicates FDA suppression or a broken log query — return UNKNOWN. The header-present / data-absent state is the expected PASS case.

> **SSH Authorized Keys:** `~/.ssh/authorized_keys` is a plain file read — no subprocess, no log access, no FDA concern. File absent on this machine → PASS.

> **Time window:** Fixed at 24h for the `log show` signal.

---

### Step 9.1 — Verify CLI commands and resolve the privilege model ✅

Without `sudo`, run each candidate command and record the exact output:

| Command | What to look for |
|---------|-----------------|
| `log show --predicate 'process == "loginwindow" AND eventMessage CONTAINS "FAILED"' --last 24h --style compact` | Any output at all — even an empty-but-headed table confirms access |
| `log show --predicate 'process == "sshd" AND (eventMessage CONTAINS "Failed" OR eventMessage CONTAINS "Invalid")' --last 24h --style compact` | Same |
| `log show --predicate 'process == "sudo"' --last 1h --style compact` | Canary: confirms log access is working even if no failures occurred |
| `ls -la ~/.ssh/authorized_keys 2>&1` | Exists / absent / permissions |

**Decision rules:**
- If `log show` exits non-zero → document the error; plan to return UNKNOWN for that signal.
- If `log show` exits zero but produces *no output at all* (not even a header line) → FDA-suppressed; return UNKNOWN.
- If `log show` exits zero with a header line but no data rows → command works, no matching events in window; PASS logic is safe.

**Step 9.1 outcome:** All candidate commands confirmed working without `sudo` or a permission dialog. Sudo activity omitted — see signal table above and `docs/cli_verification.md § Phase 9`. All output recorded.

Record all output in `docs/cli_verification.md` under a new `## Phase 9 — Authentication` heading.

**Validation:** ✅ All commands run without a permission dialog. Output recorded. Sudo activity omission documented.

---

### Step 9.2 — Write the authentication collector module ✅

Create `src/collectors/auth.py` with two functions:

```
check_failed_logins()  → { name, description, status, raw, error }
check_ssh_keys()       → { name, description, status, raw, error }
```

**Status logic:**

| Collector | PASS | WARN | UNKNOWN |
|-----------|------|------|---------|
| `check_failed_logins` | `log show` exits 0, header line present, no failure events in 24h | One or more failure events found | Exit non-zero, timeout, or completely empty output (no header line) |
| `check_ssh_keys` | `~/.ssh/authorized_keys` absent or empty | File has one or more non-comment, non-empty lines | `OSError` reading the file |

**`raw` field content:**
- PASS (`check_failed_logins`): `"No failed login events in past 24h."`
- WARN (`check_failed_logins`): the matching log lines (first 20 lines if many)
- PASS (`check_ssh_keys`): `"No authorized keys found."`
- WARN (`check_ssh_keys`): the file contents (each key line)
- UNKNOWN: the error or empty-output message

**Implementation rules:**
- `check_failed_logins`: use `subprocess.run()` via `_run()` with a 30s timeout; never `shell=True`
- Predicate: `(process == "loginwindow" AND eventMessage CONTAINS "FAILED") OR (process == "sshd" AND (eventMessage CONTAINS "Failed" OR eventMessage CONTAINS "Invalid"))` — loginwindow uses case-sensitive uppercase "FAILED" to avoid matching unrelated messages (e.g. CFPasteboard errors that contain "Failed")
- Parse by checking if any non-header, non-empty lines are present — do not rely on exit code alone
- If output is completely empty (no header line at all), return UNKNOWN with `error="log show returned no output — Full Disk Access may be required"`
- `check_ssh_keys`: use `pathlib.Path`; wrap in `try/except OSError`; skip lines that are blank or start with `#`
- Card descriptions must communicate that WARN is informational

**Validation:** Add a `__main__` block and run `.venv/bin/python src/collectors/auth.py`. Both functions return dicts with the correct keys; neither raises an exception.

---

### Step 9.3 — Register authentication collectors ✅

Update `src/collectors/__init__.py` to import and append the two auth collectors to `_COLLECTORS`. No changes to `app.py` or the template.

**Validation:** `.venv/bin/python -c "from src.collectors import run_all_collectors; print(len(run_all_collectors()))"` prints `13`. All dicts contain the required keys.

---

### Step 9.4 — End-to-end dashboard check ✅

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000` in a browser.

- Confirm all 13 cards render (11 existing + 2 auth)
- Confirm badge colors match actual state on this machine
- Force `check_ssh_keys` to fail by temporarily pointing it at a non-readable path (triggers `OSError`); confirm it shows UNKNOWN and other 12 cards are unaffected; restore

**Validation:** All 13 cards render with correct data and the forced failure degrades gracefully.

---

### Step 9.5 — Update README and documentation ✅

- Add the two new signals to `README.md` under a new `### Authentication` heading in the Signals monitored section
- Add a Known Limitations entry for sudo activity explaining why it was omitted (BSM audit requires root; unified log only shows background system calls)
- Confirm `docs/cli_verification.md` has the Phase 9 section from Step 9.1

**Validation:** README signals section has an Authentication subsection. Known Limitations mentions sudo activity. `docs/cli_verification.md` has the Phase 9 section.

---

### Phase 9 Integration Validation

- [x] Both auth collector functions return the correct dict shape
- [x] `check_failed_logins` returns PASS (no failures in 24h on this machine)
- [x] Completely empty `log show` output (no header) → `check_failed_logins` returns UNKNOWN, not a misleading PASS
- [x] `check_ssh_keys` returns PASS (`~/.ssh/authorized_keys` absent on this machine)
- [x] All 13 cards render in the dashboard with no layout regressions
- [x] Badge colors are correct for all signals
- [x] Forced `check_ssh_keys` failure shows UNKNOWN; other 12 cards unaffected
- [x] No collector calls `sudo`
- [x] README authentication section accurately describes each signal
- [x] Known Limitations documents why sudo activity was omitted

---

## Phase 10 — Remediations

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 6`.

**Goal:** Add one-click Fix buttons to cards whose misconfiguration can be corrected with a single, safe, reversible command. Privilege escalation uses macOS's built-in `osascript` auth dialog — no `sudoers` modifications required.

**Signals with remediations in this phase:**

| Signal | Current status | Fix command | Applies when |
|--------|---------------|-------------|-------------|
| Application Firewall | FAIL | `socketfilterfw --setglobalstate on` | FAIL |
| Stealth Mode | WARN | `socketfilterfw --setstealthmode on` | WARN |

> **Why only these two:** Both commands are single-flag toggles that enable a security feature, are fully reversible from System Settings, and require no interactive input beyond the auth dialog. SIP and Secure Boot require Recovery Mode and cannot be toggled from a running OS. FileVault enrollment is interactive (generates a recovery key, requires password input) — better done via System Settings. Gatekeeper is currently PASS on this machine so its remediation cannot be tested end-to-end; it is deferred to a future update.

> **Privilege model — `osascript`:** `osascript -e 'do shell script "<cmd>" with administrator privileges'` triggers the standard macOS "enter your password" dialog. It requires no `sudoers` changes, integrates with Touch ID, and is the canonical macOS pattern for one-off privileged operations from a user-facing app. Each Fix click triggers one auth prompt for that specific action.

> **Security constraints:** The command string passed to `do shell script` is a fixed constant defined in the remediations registry — never derived from user input. The `/fix/<signal_name>` route validates the name against the registry before any command is executed. There is no "fix all" batch action.

> **Architecture:** Remediations live in a new `src/remediations/` module (separate from collectors, which remain read-only). `app.py` imports the registry to add the `/fix` route and to pass fix availability to the template. Collectors are not modified.

---

### Step 10.1 — Verify remediation commands and confirm the privilege model ✅

Run each candidate command interactively in Terminal using `osascript` to confirm the auth dialog appears and the command succeeds:

```zsh
# Test the auth dialog pattern with a safe read-only command first
osascript -e 'do shell script "whoami" with administrator privileges'

# Firewall toggle (this will actually enable the firewall — restore if needed)
osascript -e 'do shell script "/usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on" with administrator privileges'

# Stealth mode toggle (this will actually enable stealth mode — restore if needed)
osascript -e 'do shell script "/usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on" with administrator privileges'
```

Also test the cancel path: run one of the above and click Cancel in the dialog. Record the exact exit code and stderr — this is the error the `/fix` route must handle gracefully.

Record all output in `docs/cli_verification.md` under a new `## Phase 10 — Remediations` heading.

**Validation:** Auth dialog appears for each command. Commands succeed when confirmed. Cancel produces a non-zero exit and a known error message (expected: `"User canceled."`). All output recorded.

---

### Step 10.2 — Create the remediations module ✅

Create `src/remediations/__init__.py` with a `REMEDIATIONS` registry:

```python
REMEDIATIONS = {
    "Application Firewall": {
        "label": "Enable Firewall",
        "cmd": "/usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on",
        "applies_to": {"FAIL"},
    },
    "Stealth Mode": {
        "label": "Enable Stealth Mode",
        "cmd": "/usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on",
        "applies_to": {"WARN"},
    },
}
```

Create `src/remediations/executor.py` with one function:

```python
def run_fix(signal_name: str) -> dict:
    # Returns {"success": bool, "output": str, "error": str | None}
```

**Implementation rules for `run_fix`:**
- Look up `signal_name` in `REMEDIATIONS`; return `{"success": False, "error": "Unknown signal"}` if not found
- Run via `osascript -e 'do shell script "<cmd>" with administrator privileges'` using `subprocess.run()` with a 30s timeout
- On exit 0: return `{"success": True, "output": stdout.strip(), "error": None}`
- On non-zero exit: parse stderr for `"User canceled."` and surface a clean message; otherwise return the raw error
- Never `shell=True`; never interpolate user input into the command string

**Validation:** `python -c "from src.remediations.executor import run_fix; print(run_fix('Application Firewall'))"` — auth dialog appears, command runs, returns `{"success": True, ...}`.

---

### Step 10.3 — Add `POST /fix/<signal_name>` route to app.py ✅

Update `src/app.py`:
- Import `REMEDIATIONS` and `run_fix`
- Add route: `POST /fix/<path:signal_name>` — validates name against registry, calls `run_fix`, returns JSON
- On unknown signal name: return `{"success": False, "error": "No remediation available for this signal"}` with HTTP 404
- On success or known failure (user cancelled, command failed): return HTTP 200 with the result dict — let the client decide how to surface the error

**Validation:** `curl -s -X POST http://127.0.0.1:8000/fix/Unknown` returns HTTP 404 with a JSON error body. `curl -s -X POST "http://127.0.0.1:8000/fix/Application%20Firewall"` triggers the auth dialog and returns `{"success": true, ...}`.

---

### Step 10.4 — Add Fix buttons to the dashboard template and stylesheet ✅

Update `templates/dashboard.html`:
- Accept a new template variable `remediations` (the `REMEDIATIONS` dict, passed from `app.py`)
- For each signal card: if `signal.name` is in `remediations` and `signal.status` is in `remediations[signal.name].applies_to`, render a Fix button
- Button label comes from `remediations[signal.name].label`
- On click: `confirm()` with the message `"Enable [label]? macOS will prompt for your password."` — abort if cancelled
- On confirm: `fetch('POST /fix/<signal_name>')`, parse JSON response
  - Success → reload the page (re-runs all collectors, card updates to new status)
  - Error → show `alert()` with the error message (simple, no new UI components)

Update `static/style.css`:
- Fix button: secondary style — visually distinct from Refresh, smaller, placed below the status badge
- Should not dominate the card; this is an optional action, not the primary content

**Validation:** Dashboard loads. Fix button appears on Application Firewall (FAIL) and Stealth Mode (WARN) cards only. Clicking Fix on Application Firewall triggers the confirm dialog, then the auth dialog, then reloads — card now shows PASS. No Fix button appears on PASS cards.

---

### Step 10.5 — End-to-end test ✅

Walk through the complete remediation flow:

1. Launch app, confirm Application Firewall shows FAIL with a Fix button
2. Click Fix → confirm dialog → auth dialog → page reloads → card shows PASS
3. Re-open System Settings → Network → Firewall and confirm the firewall is now on
4. Disable the firewall in System Settings → refresh the dashboard → card shows FAIL again
5. Repeat for Stealth Mode (WARN → fix → WARN disappears)
6. Test the cancel path: click Fix → confirm → cancel the auth dialog → error alert shown, card unchanged
7. Test the unknown-signal path: `curl -X POST http://127.0.0.1:8000/fix/Nonexistent` → 404 JSON

**Validation:** All seven steps complete without error. The dashboard correctly reflects real system state after each change.

---

### Step 10.6 — Update README and documentation ✅

- Add a `## Remediations` section to `README.md` explaining which signals have Fix buttons, what each fix does, and that macOS will prompt for a password
- Add a Known Limitations entry noting which signals do not have Fix buttons and why (SIP/Secure Boot require Recovery Mode; FileVault is interactive)
- Confirm `docs/cli_verification.md` has the Phase 10 section from Step 10.1

**Validation:** README accurately describes the remediation feature. `docs/cli_verification.md` has the Phase 10 section.

---

### Phase 10 Integration Validation

- [x] `REMEDIATIONS` registry contains exactly two entries (Application Firewall, Stealth Mode)
- [x] `run_fix("Application Firewall")` triggers auth dialog and returns `{"success": True, ...}` on confirm
- [x] `run_fix("Application Firewall")` returns a clean error on cancel — not a crash
- [x] `POST /fix/<unknown>` returns HTTP 404 with JSON error body
- [x] Fix button appears on Application Firewall (FAIL) and Stealth Mode (WARN) only
- [x] Fix button does not appear on PASS cards
- [x] Clicking Fix → confirm → auth → page reloads with updated card status
- [x] Clicking Fix → confirm → cancel auth → error alert shown, card unchanged, no crash
- [x] All 13 existing cards continue to render correctly (no regressions)
- [x] No command string is derived from user input — only registry constants are executed
- [x] README Remediations section accurately describes the feature
- [x] Known Limitations documents which signals lack Fix buttons and why

---

## Phase 11 — External Calls

> Spec reference: `SPEC.md § Future Phases — Phase 7`.

**Goal:** Add a macOS Version signal that compares the current OS version against the latest Apple release. External calls are disabled by default; the user opts in via `EXTERNAL_CALLS=1`. CVE lookups are explicitly out of scope for this phase.

**Scope decision:** One signal only — macOS version currency. CVE lookups require per-signal NVD/OSV queries and a caching strategy; they belong in a future iteration once the external call infrastructure is proven.

**Data source:** Two candidates to evaluate in Step 11.1:
- **Apple GDMF** (`https://gdmf.apple.com/v2/pmv`) — Apple's authoritative feed used by MDM solutions. Returns JSON listing the latest public macOS versions by major release train.
- **Sofa Feed** (`https://sofa.macadmins.io/v1/macos_data_feed.json`) — community-maintained, richer metadata (security notes, CVEs), more developer-friendly JSON shape.

**Opt-in mechanism:** `EXTERNAL_CALLS=1` environment variable (consistent with `PORT` and `REFRESH_INTERVAL`). When not set, external collectors are not registered and their cards do not appear — no stub, no placeholder. When enabled, a startup log line confirms it.

**Architecture:** External collectors live in `src/collectors/external.py`. `run_all_collectors()` gains an `external: bool` parameter; `app.py` passes it based on the env var. This keeps all startup configuration in `app.py` and avoids side effects at import time.

**HTTP:** `urllib.request` from the stdlib — no new dependency. Fixed 10s timeout. Any network error or timeout returns `UNKNOWN` with a descriptive message; never crashes or returns HTTP 500.

**Privacy constraint:** The version check is a plain `GET` request. No machine-identifying data is transmitted beyond a standard `User-Agent` header. This must be verified in Step 11.1 and documented in README.

**Latency note:** When `EXTERNAL_CALLS=1` is set, page load blocks until the HTTP call returns (up to 10s on failure). This is acceptable for a personal on-demand dashboard.

---

### Step 11.1 — Verify the version API and privacy model ✅

Test both candidate APIs and choose one. For each:

```zsh
# GDMF
curl -s "https://gdmf.apple.com/v2/pmv" | python3 -m json.tool | head -60

# Sofa Feed
curl -s "https://sofa.macadmins.io/v1/macos_data_feed.json" | python3 -m json.tool | head -80
```

For the chosen API, confirm:
1. The JSON shape is stable enough to parse reliably (field names, nesting)
2. The response includes at minimum: the latest macOS version string and release date
3. No identifying data is sent in the request (inspect with `curl -v`)
4. The response includes the current major release train (macOS 15 / Sequoia at time of writing)

Also confirm the current macOS version command:
```zsh
sw_vers -productVersion   # e.g., "15.5"
sw_vers -buildVersion     # e.g., "24F74"
```

Document the chosen API, the full response shape, and the request headers in `docs/cli_verification.md` under a new `## Phase 11 — External Calls` heading.

**Validation:** Both APIs return parseable JSON. Chosen API identified. Request headers confirmed to contain no machine-identifying data. Results recorded.

---

### Step 11.2 — Design the version comparison logic ✅

Determine the status mapping:

| Current vs latest | Status | Rationale |
|-------------------|--------|-----------|
| Current version = latest in its release train | PASS | Machine is fully up to date |
| Minor update available (e.g., 15.4 → 15.5) | WARN | Update available; not a security emergency but worth knowing |
| Running a prior major release (e.g., 14.x when 15.x is current) | FAIL | End-of-support risk; Apple typically stops backporting security patches |
| API unreachable / timeout / parse failure | UNKNOWN | Degrade gracefully |

Version comparison rules:
- Use `tuple(int(x) for x in version.split('.'))` for reliable numeric comparison
- Never assume fixed number of components (macOS versions are sometimes `X.Y`, sometimes `X.Y.Z`)
- The "latest in its release train" concept: if on 15.x, compare only against the latest 15.x release (Apple does not force major upgrades)

Document the chosen status mapping in `docs/cli_verification.md`.

**Validation:** Logic table is clear and handles edge cases (two-part vs three-part versions, major vs minor comparison).

---

### Step 11.3 — Create `src/collectors/external.py` ✅

Implement `check_macos_version() -> dict`:

```python
import json
import subprocess
import urllib.request

_VERSION_API = "https://..."   # URL chosen in Step 11.1
_TIMEOUT = 10

def _current_version() -> tuple[str, str | None]:
    """Returns (version_string, error). Never raises."""
    ...

def _latest_version() -> tuple[str, str | None]:
    """GET the version API, parse, return (version_string, error). Never raises."""
    ...

def check_macos_version() -> dict:
    name = "macOS Version"
    description = "Compares the current macOS version against the latest Apple release."
    ...
```

Implementation rules:
- `urllib.request.urlopen` with `timeout=_TIMEOUT`; wrap in `try/except` catching `urllib.error.URLError`, `socket.timeout`, `json.JSONDecodeError`, and bare `Exception`
- Never `shell=True`
- Raw output: show both current and latest version strings (e.g., `"Current: 15.4\nLatest:  15.5"`)
- If current version cannot be read (subprocess failure): return UNKNOWN immediately without making the network call

**Validation:** `python -c "from src.collectors.external import check_macos_version; import pprint; pprint.pprint(check_macos_version())"` returns a correctly structured dict with the right status for the current machine state.

---

### Step 11.4 — Register external collectors conditionally ✅

Update `src/collectors/__init__.py`:

```python
from .external import check_macos_version

_EXTERNAL_COLLECTORS = [
    check_macos_version,
]

def run_all_collectors(external: bool = False) -> list[dict]:
    collectors = _COLLECTORS + (_EXTERNAL_COLLECTORS if external else [])
    return [fn() for fn in collectors]
```

Update `src/app.py`:
- Read `EXTERNAL_CALLS` at startup: any value other than `"1"` means disabled
- Store as `app.config["EXTERNAL_CALLS"]`
- Pass to `run_all_collectors(external=app.config["EXTERNAL_CALLS"])`
- Add to the startup log line: `", external calls: on"` / `", external calls: off"`

**Validation:** Launch with `EXTERNAL_CALLS=1` — macOS Version card appears. Launch without — card absent. No regressions on the 13 existing cards.

---

### Step 11.5 — End-to-end test ✅

1. Launch with `EXTERNAL_CALLS=1 .venv/bin/python src/app.py` — confirm startup log says "external calls: on"
2. Dashboard loads — confirm macOS Version card appears, shows correct current and latest versions in raw output, status is PASS or WARN as expected
3. Launch without `EXTERNAL_CALLS` — confirm macOS Version card is absent, 13 other cards load normally
4. Simulate API failure: temporarily patch `_VERSION_API` to a bad URL, reload — confirm UNKNOWN, no crash, no HTTP 500
5. `curl -s -X POST http://127.0.0.1:8000/fix/macOS%20Version` — confirm 404 JSON (no remediation for this signal)

**Validation:** All five steps complete without error.

---

### Step 11.6 — Update README and documentation ✅

- Add `macOS Version` to the Signals monitored table under a new `### External (opt-in)` subsection
- Add `EXTERNAL_CALLS` to the Environment variables table: default `""` (disabled), `"1"` to enable
- Add a `## Privacy` section (or update the existing prose) explaining: when `EXTERNAL_CALLS=1`, the dashboard makes one GET request per page load to [API URL]; no machine-identifying data is sent; the response is only used to compare version strings
- Update Known Limitations to remove or update the "Read-only" note if still present

**Validation:** README accurately describes the opt-in mechanism, the API called, and the privacy model.

---

### Phase 11 Integration Validation

- [x] `EXTERNAL_CALLS=1` env var enables the macOS Version card
- [x] Without `EXTERNAL_CALLS=1`, macOS Version card does not appear (no stub or placeholder)
- [x] Card shows correct current macOS version in raw output
- [x] Card shows PASS when running the latest release in the current major train
- [x] Card shows WARN when a minor update is available (26.5 → 26.5.1)
- [x] Card shows FAIL when running a prior major release
- [x] Network error or timeout returns UNKNOWN, not a crash or HTTP 500
- [x] Timeout is ≤ 10s — page load does not block indefinitely on failure
- [x] GET request sends no machine-identifying data (verified via `curl -v`)
- [x] Startup log states whether external calls are enabled
- [x] All 13 existing cards render correctly with and without `EXTERNAL_CALLS=1`
- [x] `POST /fix/macOS Version` returns HTTP 404 JSON
- [x] README documents the env var, the API endpoint, and the privacy model

---

## Phase 12 — Alerting

Spec reference: `SPEC.md § Future Phases — Phase 8`.

**Goal:** Notify the user when a signal changes state. A background polling thread runs `run_all_collectors()` on a configurable interval and fires a macOS native notification for any status transition in either direction. Opt-in via `ALERT_INTERVAL` env var; disabled by default. State is in-memory only (reset on restart; first poll is always silent).

**Architecture:**
- New module `src/alerting/` — thread management, in-memory state, change detection
- `src/alerting/notifier.py` — `send_notification()` via `osascript display notification`
- `app.py` reads `ALERT_INTERVAL`, starts alerter thread at startup if > 0

---

### Step 12.1 — Verify the notification command ✅

```zsh
osascript -e 'display notification "FileVault is off" with title "Security Alert: FileVault"'
```

Exit 0, notification banner appeared. No permission dialog required. Output recorded in `docs/cli_verification.md § Phase 12`.

---

### Step 12.2 — Create `src/alerting/notifier.py` ✅

`send_notification(title, message)` wraps `osascript display notification`. Sanitises `"` → `'` in both arguments. Swallows all exceptions so notification failure never crashes the background thread.

**Validation:** Import and call `send_notification("Test", "hello")` — notification appears.

---

### Step 12.3 — Create `src/alerting/__init__.py` ✅

`start_alerter(interval, external)` spawns a daemon thread. Thread calls `run_all_collectors()` every `interval` seconds. First poll: `old_status is None` → state initialised, no notifications. Subsequent polls: any changed signal fires one notification.

**Validation:** Import and inspect the module — no errors.

---

### Step 12.4 — Update `src/app.py` ✅

- Refactored `_get_refresh_interval()` into generic `_get_int_env(name)` used by both `REFRESH_INTERVAL` and `ALERT_INTERVAL`
- Reads `ALERT_INTERVAL`; if > 0, calls `start_alerter()` before Flask starts serving
- Startup log line now includes `", alerting: every {n}s"` or `", alerting: off"`

**Validation:** `ALERT_INTERVAL=60` → startup log shows "alerting: every 60s". Default → "alerting: off". Invalid value → clear error + exit 1.

---

### Step 12.5 — End-to-end test ✅

1. `ALERT_INTERVAL=60` → startup log correct; page loads at 200
2. Default launch → "alerting: off" in startup log
3. `ALERT_INTERVAL=abc` → clear error message, exit 1
4. `ALERT_INTERVAL=0` → "alerting: off", no thread started

---

### Step 12.6 — Update README and documentation ✅

- Added `ALERT_INTERVAL` to the Environment Variables table
- Added `## Alerting` section explaining all-transitions behaviour, silent first poll, and osascript delivery
- Added example launch command
- Recorded Phase 12 verification in `docs/cli_verification.md`

---

### Phase 12 Integration Validation

- [x] `ALERT_INTERVAL=60` starts alerter (startup log says "alerting: every 60s")
- [x] First poll does not fire any notification (state initialised silently)
- [ ] Status change on second+ poll fires one macOS notification per changed signal
- [ ] All transitions (PASS→FAIL, FAIL→PASS, PASS→WARN, WARN→PASS, any→UNKNOWN) generate a notification
- [ ] Unchanged signals produce no notification
- [x] Background thread is daemon — `Ctrl-C` exits cleanly
- [ ] Exception in background thread does not crash the app or break page loads
- [x] `ALERT_INTERVAL=abc` exits with a clear error message
- [x] `ALERT_INTERVAL=0` (default): startup log says "alerting: off", no thread started
- [x] Page loads work normally with alerting running (no deadlock, no slowdown)
- [ ] External signals (macOS Version) included in alerts when both `ALERT_INTERVAL` and `EXTERNAL_CALLS` are set
- [x] README documents `ALERT_INTERVAL`; startup log reflects current config

---

## Phase 13 — History & Trends

Spec reference: `SPEC.md § Future Phases — Phase 9`.

**Goal:** Persist signal results to a local SQLite database and display a state-change log at `/history` showing when each signal last changed status and its recent transitions. Only status transitions are stored (not every identical snapshot). Retention is 30 days.

**Architecture:**
- New module `src/history/` — `init_db()`, `store_snapshot()`, `get_summary()`
- DB at `data/history.db` (auto-created; `data/` in `.gitignore`)
- `store_snapshot()` called from the Flask `/` route and from the alerting thread's poll loop
- New route `GET /history` renders `templates/history.html`

---

### Step 13.1 — Verify SQLite availability ✅

```zsh
.venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version)"
# → 3.53.1
```

sqlite3 is stdlib — no new dependency. Recorded in `docs/cli_verification.md § Phase 13`.

---

### Step 13.2 — Create `src/history/__init__.py` ✅

- `init_db()` — creates `data/history.db` and schema; called once at app startup
- `store_snapshot(results)` — transition-only writes; 30-day pruning on each call; thread-safe via `threading.Lock`
- `_relative_time(ts)` — formats Unix timestamp as "2 hours ago", "3 days ago", etc.
- `get_summary()` — returns list of per-signal dicts with `name`, `last_status`, `last_changed`, `transitions` (last 5, pre-formatted)

**Validation:** 2-call test confirms transition-only behaviour — 13 rows after two loads with identical statuses. ✅

---

### Step 13.3 — Update `src/app.py` ✅

- Import `init_db`, `store_snapshot`, `get_summary` from `history`
- Call `init_db()` at startup (before alerter thread starts)
- Call `store_snapshot(signals)` in `/` route after collecting
- Add `GET /history` route: `render_template("history.html", summary=get_summary())`

---

### Step 13.4 — Update `src/alerting/__init__.py` ✅

In `_poll_loop`, after `_process(results)`, import and call `store_snapshot(results)` inside a try/except so a DB error never kills the alert thread.

---

### Step 13.5 — Create `templates/history.html` ✅

State-change log table: Signal | Current Status | Last Changed | Recent Transitions. Empty state with link to dashboard if no history recorded. Matching dark-mode style.

---

### Step 13.6 — Update templates and CSS ✅

- `dashboard.html`: added "History" nav link in header
- `style.css`: `.nav-link`, `.history-table`, `.ht-*`, `.badge--sm` styles

---

### Step 13.7 — Add `data/` to `.gitignore` ✅

---

### Step 13.8 — End-to-end test ✅

- First load: 13 rows written, one per signal
- Second load (same statuses): 0 new rows (transition-only confirmed)
- `/history` returns 200, renders table with "no changes recorded" for all signals (correct — no transitions yet)

---

### Step 13.9 — Update README and documentation ✅

See README: `/history` route, DB location, retention policy, project structure updated.

---

### Phase 13 Integration Validation

- [x] `data/history.db` created automatically on first launch
- [x] First dashboard load writes 13 initial snapshot rows
- [x] Second load with same statuses writes 0 new rows (transition-only)
- [x] `/history` renders correctly — table with signal rows, "no changes recorded" for unmodified signals
- [ ] Status change on page load writes new row, transition appears in `/history`
- [ ] Alert thread writes transitions to DB when `ALERT_INTERVAL` is set
- [x] DB not checked into git (`data/` in `.gitignore`)
- [x] Rows older than 30 days are pruned on each write
- [x] DB error / `_conn is None` does not crash page loads or alert thread
- [x] README documents `/history` route and `data/history.db`

---

## Phase 14 — Sharing & Remote Access Signals

Security review finding: June 2026.

**Goal:** Add signals for macOS sharing services that create inbound network attack surface. Remote Login, Screen Sharing, and Remote Management are default-off but are frequently enabled accidentally during setup or by software installers. AirDrop set to "Everyone" is the most common unintentional wireless exposure on personal machines.

**Signals in scope:**

| Signal | Source | PASS | WARN | FAIL | UNKNOWN |
|--------|--------|------|------|------|---------|
| Remote Login (SSH Server) | `launchctl` or `defaults` | Disabled | — | Enabled (sshd accepting connections) | Command failed or unrecognized output |
| Screen Sharing | `launchctl` or `defaults` | Disabled | — | Enabled | Command failed |
| AirDrop Receiver Mode | `defaults read com.apple.NetworkBrowser` or `com.apple.sharingd` | Off or Contacts Only | Everyone | — | Command failed |

> **Why FAIL (not WARN) for Remote Login and Screen Sharing:** Unlike persistence signals (where WARN reflects "may be intentional"), a running SSH server or screen-sharing service creates an authenticated inbound network listener. On a personal machine, this is a direct exposure, not an advisory. A user who set it up intentionally will see FAIL and can account for it; the false-negative (missing an unintentional listener) is far more dangerous than the false-positive.

> **Remote Management vs Screen Sharing:** macOS Remote Management (ARD) subsumes Screen Sharing when both are enabled. Step 14.1 determines whether they are exposed by the same launchd label. If so, merge them into one signal; if separate, create two.

> **Remediations:** The fix commands (`launchctl disable system/com.apple.sshd && launchctl stop system/com.apple.sshd`) require admin privileges. Step 14.1 confirms whether these are wrappable in `osascript do shell script` as a single compound command. If confirmed, remediations are added in this phase. If the multi-command pattern proves unreliable, they are deferred to a later phase.

---

### Step 14.1 — Verify CLI commands for sharing service state ✅

Without `sudo`, run each candidate command and record the exact output for both the on and off state of each service. Toggle each service in System Settings → General → Sharing to capture both states.

| Command | What to verify |
|---------|----------------|
| `launchctl print-disabled system` | Does output clearly show enabled/disabled state of `com.apple.sshd` and `com.apple.screensharing` without sudo? |
| `launchctl print system/com.apple.sshd` | Does exit code or output differ when Remote Login is on vs off? |
| `defaults read /Library/Preferences/com.apple.RemoteLogin RemoteLoginEnabled` | Readable without sudo? Values? |
| `defaults read com.apple.NetworkBrowser BrowseAllInterfaces` | Is this the AirDrop discoverability key? Values when off / Contacts Only / Everyone? |
| `defaults read com.apple.sharingd DiscoverableMode` | Same question for newer macOS. Values: 0 = off, 2 = contacts only, 3 = everyone? |
| `launchctl print system/com.apple.screensharing` | Readable without sudo? Differs on/off? |

**Decision rules:**
- Use `launchctl print-disabled system` if it clearly distinguishes enabled/disabled without sudo; fall back to `defaults read` on known preference files if not.
- If neither works for a given service without root, mark that signal as deferred and document the limitation.
- For AirDrop: test both `com.apple.NetworkBrowser` and `com.apple.sharingd`; use whichever returns a stable, parseable value.
- For Remote Management: if it shares a launchd label with Screen Sharing, merge them into one signal.

Also test whether the remediation commands work via osascript:
```zsh
osascript -e 'do shell script "launchctl disable system/com.apple.sshd && launchctl stop system/com.apple.sshd" with administrator privileges'
```
Record exit code, stdout, and stderr. If it exits 0 and the service actually stops, add remediations for Remote Login (and Screen Sharing if analogous) to `src/remediations/__init__.py` in Step 14.2.

Record all output in `docs/cli_verification.md` under a new `## Phase 14 — Sharing & Remote Access` heading.

**Validation:** ✅ On/off state output recorded for all services. All commands work without sudo. Service label discovery: macOS 26 uses `com.openssh.sshd` (not `com.apple.sshd`); Screen Sharing uses `com.apple.screensharing` and merges with Remote Management (same label). AirDrop uses `defaults read com.apple.sharingd DiscoverableMode` with string values "Off" / "Contacts Only" / "Everyone". Results recorded in `docs/cli_verification.md § Phase 14`.

---

### Step 14.2 — Write the sharing collector module ✅

Create `src/collectors/sharing.py` with collector functions for each viable signal confirmed in Step 14.1 (minimum: Remote Login and AirDrop; Screen Sharing and Remote Management if confirmed parseable):

```
check_remote_login()     → { name, description, status, raw, error }
check_screen_sharing()   → { name, description, status, raw, error }   # if viable
check_airdrop()          → { name, description, status, raw, error }
```

**Status logic:**

| Collector | PASS | WARN | FAIL | UNKNOWN |
|-----------|------|------|------|---------|
| `check_remote_login` | Service confirmed disabled | — | Service confirmed enabled | Command failed or output unrecognized |
| `check_screen_sharing` | Service confirmed disabled | — | Service confirmed enabled | Command failed or output unrecognized |
| `check_airdrop` | Off or Contacts Only | Set to Everyone | — | Command failed or output unrecognized |

Implementation rules (same as prior collectors):
- Use `subprocess.run()` with a timeout for `launchctl` / `defaults` calls; never `shell=True`
- Any exception or unrecognized output → `UNKNOWN` with error captured; never raise

If Step 14.1 confirmed the osascript remediation pattern works, add entries to `src/remediations/__init__.py` for Remote Login and Screen Sharing (and update `applies_to` to `{"FAIL"}`).

**Validation:** ✅ All three collector functions return correct dicts. Remote Login PASS (disabled), Screen Sharing PASS (disabled), AirDrop PASS ("Off"). Remediations added for Remote Login and Screen Sharing using `launchctl disable && bootout` via osascript — both confirmed working (exit 0, service leaves domain). Collector count: 16.

---

### Step 14.3 — Register sharing collectors ✅

Update `src/collectors/__init__.py` to import and append the new sharing collectors to `_COLLECTORS`. No changes to `app.py` or the template.

**Validation:** ✅ `run_all_collectors()` returns 16 results. All dicts contain the required keys (name, description, status, raw, error).

---

### Step 14.4 — End-to-end dashboard check

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000`.

- Confirm all new cards render with correct badge colors matching actual system state.
- Toggle Remote Login on/off in System Settings → General → Sharing; confirm the card reflects the real state after a page refresh.
- If remediations were added: test the Fix button end-to-end (Fix → auth dialog → page reload → card updates).
- Force one new collector to fail (rename the command); confirm it shows UNKNOWN and other cards are unaffected; restore.

**Validation:** New signal cards render correctly. Real system state changes are reflected on reload. No regressions in existing 13 cards.

---

### Step 14.5 — Update README and documentation

- Add new signals to the "Signals monitored" section under a new `### Sharing & Remote Access` heading.
- If any signals were deferred (not checkable without root), add a Known Limitations entry explaining why.
- If remediations were added, document them in the Remediations section.
- Confirm `docs/cli_verification.md` has the Phase 14 section with on/off state output for each service.

**Validation:** ✅ README accurately describes each new signal and its status logic. Known Limitations updated if any signals were deferred. `docs/cli_verification.md` Phase 14 section confirmed present.

---

### Phase 14 Integration Validation

- [x] `check_remote_login` returns FAIL when Remote Login is enabled in System Settings
- [x] `check_remote_login` returns PASS when Remote Login is disabled
- [x] `check_screen_sharing` (if implemented) returns FAIL when Screen Sharing is enabled; PASS when disabled
- [x] `check_airdrop` returns WARN when AirDrop is set to Everyone
- [x] `check_airdrop` returns PASS when AirDrop is set to Contacts Only or off
- [x] All new signals degrade to UNKNOWN gracefully when their data source is unreadable — no crash, no 500
- [x] All existing 13 cards render correctly — no regressions
- [x] Any signals deferred due to privilege requirements are documented in Known Limitations
- [x] Fix buttons (if added) for Remote Login and Screen Sharing work end-to-end via osascript auth dialog
- [x] No collector calls `sudo`
- [x] `docs/cli_verification.md` has Phase 14 section with on/off states recorded

---

## Phase 15 — Software Hygiene Signals

Security review finding: June 2026.

**Goal:** Add signals for automatic update configuration, non-Apple root certificate trust, and screen lock policy. These three controls are the most common systemic vulnerabilities on personal Macs: unpatched software is the dominant initial access vector; rogue root CAs enable SSL interception; and an unlocked screen is the primary physical access risk.

**Signals in scope:**

| Signal | Source | PASS | WARN | FAIL | UNKNOWN |
|--------|--------|------|------|------|---------|
| Automatic macOS Updates | `defaults read /Library/Preferences/com.apple.SoftwareUpdate` | Periodic check enabled and critical security patches set to auto-install | Check enabled but critical auto-install disabled | Automatic check disabled entirely | Command failed or key absent with ambiguous meaning |
| Non-Apple Root Certificates | `security find-certificate -a /Library/Keychains/System.keychain` | No entries | One or more non-Apple certs present | — | Command failed |
| Screen Lock | `defaults -currentHost read com.apple.screensaver` keys | Password required with zero delay (immediate lock) | Password required but with a delay > 0s | Password not required | Command failed or key absent |

> **Automatic updates rationale:** Three independent defaults keys govern update behavior: `AutomaticCheckEnabled` (does the system check?), `CriticalUpdateInstall` (does it auto-apply security patches?), and `AutomaticDownload` (does it pre-download updates?). FAIL: `AutomaticCheckEnabled = 0` — the system will not discover available updates at all. WARN: check is enabled but `CriticalUpdateInstall = 0` — the user will be notified of security patches but they will not be applied automatically. PASS: both check and critical install are enabled.

> **Non-Apple Root Certificates rationale:** Apple ships its root CA bundle in `/System/Library/Keychains/SystemRootCertificates.keychain` (protected, read-only). The `/Library/Keychains/System.keychain` is where user- or software-installed certificates land. Any entry here with TLS trust authority is a potential interception vector — corporate MitM proxy, malicious CA, or rogue MDM enrollment. `security find-certificate -a /Library/Keychains/System.keychain` lists all entries; any non-empty result is WARN with names shown in the raw field.

> **Screen lock rationale:** `askForPassword = 0` means the screensaver never requires a password — FAIL. `askForPassword = 1` with `askForPasswordDelay = 0` means the lock activates immediately when the screensaver does — PASS. Any delay > 0 is a window of physical access after the screensaver starts but before the lock engages — WARN. Also capture `idleTime` (seconds until screensaver activates; 0 means never) in the raw field so the user can see the full picture.

> **Remediations for auto-updates:** The fix command writes to `/Library/Preferences/com.apple.SoftwareUpdate`, which requires admin. Wrap in `osascript do shell script` for the FAIL case. Confirm in Step 15.1.

---

### Step 15.1 — Verify CLI commands for software hygiene signals

Without `sudo`, run and record the exact output of each command:

| Command | What to verify |
|---------|----------------|
| `defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled` | Readable without sudo? Value when on vs off? Behavior when key is absent? |
| `defaults read /Library/Preferences/com.apple.SoftwareUpdate CriticalUpdateInstall` | Same |
| `defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload` | Same |
| `security find-certificate -a /Library/Keychains/System.keychain 2>&1` | What does each entry look like? How to extract the certificate subject/name? |
| `defaults -currentHost read com.apple.screensaver askForPassword` | Value when password required vs not? Behavior when key absent? |
| `defaults -currentHost read com.apple.screensaver askForPasswordDelay` | Value in seconds? 0 = immediate? Behavior when key absent? |
| `defaults -currentHost read com.apple.screensaver idleTime` | Value in seconds? 0 = never? |

For each defaults key: record what happens when the key is absent (`defaults` exits non-zero with an error). Determine whether absence should be treated as FAIL (the system is using a default that is insecure) or UNKNOWN (cannot determine without more context). Record the decision and rationale.

Also test the auto-update remediation via osascript:
```zsh
osascript -e 'do shell script "defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true && defaults write /Library/Preferences/com.apple.SoftwareUpdate CriticalUpdateInstall -bool true" with administrator privileges'
```
Record exit code and whether the settings take effect.

Record all output in `docs/cli_verification.md` under a new `## Phase 15 — Software Hygiene` heading.

**Validation:** All viable data sources identified. On/off state output recorded for each setting. Absent-key semantics decided and documented.

---

### Step 15.2 — Write the software hygiene collector module

Create `src/collectors/hygiene.py` with three functions:

```
check_auto_updates()        → { name, description, status, raw, error }
check_root_certificates()   → { name, description, status, raw, error }
check_screen_lock()         → { name, description, status, raw, error }
```

**`raw` field content:**
- `check_auto_updates`: show the value of each relevant defaults key (e.g., `"AutomaticCheckEnabled: 1\nCriticalUpdateInstall: 0"`), so the user can see exactly which setting is off.
- `check_root_certificates`: PASS → `"No non-Apple certificates found."`; WARN → certificate subject names, one per line, capped at 10.
- `check_screen_lock`: show all three values together (e.g., `"askForPassword: 1\naskForPasswordDelay: 5\nidleTime: 300"`).

Implementation rules:
- All three use `subprocess.run()` via `_run()` for defaults/security calls; never `shell=True`
- Absent defaults keys: apply the absent-key semantic decided in Step 15.1
- For `check_root_certificates`: parse `security find-certificate` output to extract the common name or subject; never treat a parse failure as PASS

If the auto-update remediation osascript pattern was confirmed in Step 15.1, add an entry to `src/remediations/__init__.py` for the FAIL case (`AutomaticCheckEnabled = 0`). The applies_to set is `{"FAIL"}`.

**Validation:** Add a `__main__` block and run `.venv/bin/python src/collectors/hygiene.py`. All three functions return dicts with the correct keys; none raise an exception.

---

### Step 15.3 — Register hygiene collectors and update remediations

Update `src/collectors/__init__.py` to import and append the three hygiene collectors to `_COLLECTORS`. If remediations were confirmed viable, add to `src/remediations/__init__.py`.

**Validation:** Collector count increments by 3. Dashboard loads with new signal cards. Remediation button (if added) appears only on the FAIL auto-updates card.

---

### Step 15.4 — End-to-end dashboard check

Launch the app and verify:
- All three new cards render with correct status matching the current machine state.
- Toggle a software update setting off in System Settings → General → Software Update; confirm the card reflects FAIL after a page refresh.
- If remediations were added: test the Fix button for auto-updates end-to-end.
- Force one new collector to fail; confirm UNKNOWN and no regressions.

**Validation:** New cards render correctly. Real system state changes are reflected on reload. No regressions in existing signals.

---

### Step 15.5 — Update README and documentation

- Add signals under a new `### Software Hygiene` heading in the Signals monitored section of `README.md`.
- Document Known Limitations for any absent-key behavior that is ambiguous (e.g., if `defaults` key absence cannot be reliably distinguished from "feature disabled").
- Confirm `docs/cli_verification.md` has the Phase 15 section.

**Validation:** README accurately describes each new signal and its status logic.

---

### Phase 15 Integration Validation

- [ ] `check_auto_updates` returns FAIL when `AutomaticCheckEnabled = 0`
- [ ] `check_auto_updates` returns WARN when check is enabled but `CriticalUpdateInstall = 0`
- [ ] `check_auto_updates` returns PASS when both `AutomaticCheckEnabled = 1` and `CriticalUpdateInstall = 1`
- [ ] `check_root_certificates` returns PASS when System keychain has no entries
- [ ] `check_root_certificates` returns WARN when any certificate is present; raw output shows certificate names
- [ ] `check_screen_lock` returns FAIL when `askForPassword = 0`
- [ ] `check_screen_lock` returns WARN when `askForPassword = 1` but `askForPasswordDelay > 0`
- [ ] `check_screen_lock` returns PASS when `askForPassword = 1` and `askForPasswordDelay = 0`
- [ ] All three signals degrade to UNKNOWN (not a crash) when their data sources are unavailable
- [ ] Auto-update remediation (if added) works end-to-end via osascript auth dialog
- [ ] All existing signal cards render correctly — no regressions
- [ ] No collector calls `sudo`
- [ ] `docs/cli_verification.md` has Phase 15 section with on/off state output recorded

---

## Phase 16 — Web Application Hardening

Security review finding: June 2026.

**Goal:** Harden the dashboard web application against the threats it faces as a locally-served HTTP service. The localhost-only binding is the primary defense, but a browser tab pointing at a malicious page while the dashboard is running is a real threat: cross-origin POST requests to `http://127.0.0.1:8000/fix/<signal>` would trigger the osascript auth dialog without any user intent. This phase adds CSRF mitigation, HTTP security headers, and a remediation audit log.

**Scope:**

1. **CSRF mitigation on `/fix`** — Validate the `Origin` request header. Browsers always send `Origin` on cross-origin POST requests; same-origin requests either send a matching `Origin` or omit it entirely. The rule: if `Origin` is present and does not match `http://127.0.0.1:{port}`, reject with HTTP 403. This requires no session management and no template changes.

2. **HTTP security headers** — Added via an `after_request` hook so they apply to every response:
   - `X-Frame-Options: DENY` — prevents the dashboard from being embedded in a cross-origin iframe (clickjacking)
   - `X-Content-Type-Options: nosniff` — prevents MIME-type sniffing
   - `Content-Security-Policy: default-src 'self'; style-src 'self'; script-src 'self' 'unsafe-inline'` — blocks external resource loading; `'unsafe-inline'` is retained because the templates use inline `<script>` blocks (tightening to nonce-based CSP requires moving those to `static/` files, which is a future improvement noted in Known Limitations)
   - `Referrer-Policy: no-referrer`

3. **Remediation audit log** — Extend `src/history/` with a `fix_log` table that records every fix attempt: timestamp, signal name, outcome (success/fail), and error message. Surface recent entries on the `/history` page.

> **CSRF approach rationale:** Three common approaches are (a) session-based CSRF tokens, (b) custom request header (`X-CSRF-Token`) set by JavaScript, and (c) `Origin` header validation. Option (c) is the lightest and most appropriate for a personal localhost app: it requires no secret key, no session, and no template changes. It is effective because browsers enforce the `Origin` header on cross-origin requests and malicious pages cannot override it. Option (b) is the standard upgrade path if the threat model expands.

> **`SECRET_KEY` implication:** Flask sessions require a `SECRET_KEY`. The chosen CSRF approach (Origin validation) does not use sessions, so no `SECRET_KEY` is needed in this phase. If future phases add session-based features, generate a random key at startup with `secrets.token_hex(32)` — never hardcode it.

> **Inline scripts and CSP:** Moving the two inline `<script>` blocks in `dashboard.html` to `static/` files would allow removing `'unsafe-inline'` from the CSP and is the right long-term direction. It requires passing `refresh_interval` via a `data-*` attribute on a DOM element rather than direct Jinja2 interpolation into script. Deferred to a future phase.

---

### Step 16.1 — Add CSRF origin validation to `/fix`

Update `src/app.py`:
- In the `/fix` route, read `request.headers.get("Origin")`.
- Compute the expected origin: `f"http://127.0.0.1:{port}"` (use the `port` variable already in scope at startup).
- If `Origin` is present and does not equal the expected origin, return HTTP 403 with `{"success": False, "error": "Invalid request origin"}`.
- If `Origin` is absent or matches, proceed as before.
- Store `port` in `app.config["PORT"]` at startup so the route can access it without a closure over a local variable.

**Validation:**
```zsh
# Cross-origin POST — must return HTTP 403:
curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Origin: http://evil.example.com" http://127.0.0.1:8000/fix/Unknown
# Expected: 403

# Correct origin — must proceed to registry lookup (returns 404 for unknown signal, not 403):
curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Origin: http://127.0.0.1:8000" http://127.0.0.1:8000/fix/Unknown
# Expected: 404

# No Origin header (curl default, same as same-origin browser request) — must proceed:
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/fix/Unknown
# Expected: 404
```

Record the curl output in `docs/cli_verification.md` under a new `## Phase 16 — Web Application Hardening` heading.

---

### Step 16.2 — Add HTTP security headers

Update `src/app.py` with an `after_request` handler that adds the four headers to every response:

```python
@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; script-src 'self' 'unsafe-inline'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
```

**Validation:**
```zsh
curl -sI http://127.0.0.1:8000/ | grep -E "X-Frame|X-Content|Content-Security|Referrer"
# All four headers must appear.
curl -sI http://127.0.0.1:8000/history | grep -E "X-Frame|X-Content"
# Headers must also appear on the /history route.
```

---

### Step 16.3 — Create the fix audit log

Extend `src/history/__init__.py`:
- In `init_db()`, create a `fix_log` table if it does not exist: `(id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, signal_name TEXT NOT NULL, success INTEGER NOT NULL, error_message TEXT)`.
- Add `log_fix_attempt(signal_name: str, success: bool, error_message: str | None) -> None`: inserts one row under `_lock`; wraps the entire body in `try/except` so a DB failure never propagates to the caller.

Update `src/app.py` `/fix` route:
- After calling `run_fix(signal_name)` and before returning the response, call `log_fix_attempt(signal_name, result["success"], result.get("error"))`.
- Import `log_fix_attempt` at the top of `app.py` alongside the other history imports.

**Validation:**
```zsh
# Trigger any fix attempt (cancel it at the auth dialog — the attempt is still logged).
# Then inspect the DB:
sqlite3 data/history.db "SELECT ts, signal_name, success, error_message FROM fix_log ORDER BY ts DESC LIMIT 5;"
# One row should appear with the correct signal name and outcome.
```

---

### Step 16.4 — Surface fix log in the history page

Update `src/history/__init__.py`:
- Add `get_fix_log(limit: int = 20) -> list[dict]`: queries the `fix_log` table ordered by `ts DESC`, returns at most `limit` rows formatted as `[{ts_display: str, signal_name: str, success: bool, error_message: str | None}]`. Uses `_relative_time()` for `ts_display`. Returns `[]` if `_conn is None`.

Update `src/app.py` `/history` route:
- Pass `fix_log=get_fix_log()` to `render_template`.

Update `templates/history.html`:
- Add a "Recent Remediation Attempts" section below the signal transition table.
- Columns: Time | Signal | Outcome. Outcome displays "Success" or "Failed: \<error\>" depending on the `success` field.
- If `fix_log` is empty, show "No remediation attempts recorded."

**Validation:** Trigger a fix attempt from the dashboard, then open `/history`. The attempt appears in the Remediation Attempts section with the correct signal name, relative timestamp, and outcome.

---

### Step 16.5 — End-to-end hardening test

Walk through the complete hardening validation:

1. Confirm all four security headers appear in responses for `/`, `/history`, and `/fix/<signal>`.
2. Confirm a POST with a wrong `Origin` header returns HTTP 403 and does not invoke `run_fix()`.
3. Confirm a POST with no `Origin` header proceeds normally to registry lookup (returns 404 for an unknown signal).
4. Confirm the dashboard Fix button still works end-to-end (it sends a same-origin `fetch()` which the Origin check allows).
5. Trigger a fix attempt, cancel it at the auth dialog, then navigate to `/history` — the failed attempt appears in the Remediation Attempts section.
6. Confirm no regressions: all signal cards load, auto-refresh works, signal transitions still appear in the history table.

**Validation:** All six steps complete without error.

---

### Step 16.6 — Update README and documentation

- Add a `## Security` section to `README.md` documenting the CSRF mitigation (Origin validation), the four HTTP security headers, and the fix audit log.
- Update the `## Remediations` section to note that all fix attempts are logged and visible at `/history`.
- Add a Known Limitations entry noting that `'unsafe-inline'` is present in the CSP because of inline scripts in the template, and that moving scripts to `static/` files is the path to a stricter policy.
- Confirm `docs/cli_verification.md` has the Phase 16 section with curl validation output.

**Validation:** README accurately describes all three hardening features.

---

### Phase 16 Integration Validation

- [ ] `X-Frame-Options: DENY` present on all responses (`/`, `/history`, `/fix`)
- [ ] `X-Content-Type-Options: nosniff` present on all responses
- [ ] `Content-Security-Policy` header present on all responses; `default-src 'self'` blocks external resource loading
- [ ] `Referrer-Policy: no-referrer` present on all responses
- [ ] POST to `/fix` with a mismatched `Origin` header returns HTTP 403, does not invoke `run_fix()`
- [ ] POST to `/fix` with the correct `Origin` proceeds to registry lookup as before
- [ ] POST to `/fix` with no `Origin` header proceeds to registry lookup as before
- [ ] Every fix attempt (success, failure, or cancel) creates a row in the `fix_log` table
- [ ] `/history` page displays recent fix attempts with relative timestamps and outcomes
- [ ] All existing signal cards, auto-refresh, and the signal-transitions history table function correctly — no regressions
- [ ] No Flask `SECRET_KEY` required by this implementation
- [ ] `'unsafe-inline'` CSP allowance documented in Known Limitations with the tightening path noted
- [ ] README documents CSRF mitigation approach, security headers, and fix audit log
- [ ] `docs/cli_verification.md` has Phase 16 curl validation output

---

## Appendix — Cross-Phase Design Principles

These constraints apply to every phase and should be checked before any phase is considered complete.

| Principle | What to check |
|-----------|---------------|
| **No data leaves the machine** | No HTTP calls to external hosts unless Phase 11 is active and user has opted in |
| **Binds to 127.0.0.1 only** | Flask `host` argument is never `0.0.0.0` |
| **No elevated privileges in read path** | Collectors must not call `sudo`; if a signal requires it, document it as a known limitation until a privilege model is designed |
| **Graceful degradation** | Any collector failure returns UNKNOWN — never a 500 or unhandled exception |
| **Modular collector registry** | New signal categories register themselves; `app.py` does not need to be modified to add a new category |
| **No debug mode in production** | Flask `debug=True` must never be the default |
