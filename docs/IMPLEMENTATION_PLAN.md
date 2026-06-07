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
- [x] Server is not accessible from another device on the local network (bind address is `127.0.0.1`)

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
- [x] Status change on second+ poll fires one macOS notification per changed signal
- [x] All transitions (PASS→FAIL, FAIL→PASS, PASS→WARN, WARN→PASS, any→UNKNOWN) generate a notification
- [x] Unchanged signals produce no notification
- [x] Background thread is daemon — `Ctrl-C` exits cleanly
- [x] Exception in background thread does not crash the app or break page loads
- [x] `ALERT_INTERVAL=abc` exits with a clear error message
- [x] `ALERT_INTERVAL=0` (default): startup log says "alerting: off", no thread started
- [x] Page loads work normally with alerting running (no deadlock, no slowdown)
- [x] External signals (macOS Version) included in alerts when both `ALERT_INTERVAL` and `EXTERNAL_CALLS` are set
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
- [x] Status change on page load writes new row, transition appears in `/history`
- [x] Alert thread writes transitions to DB when `ALERT_INTERVAL` is set
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

### Step 15.1 — Verify CLI commands for software hygiene signals ✅

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

**Validation:** ✅ All viable data sources identified. On/off state output recorded for each setting. Absent-key semantics decided and documented.

Key decisions made during verification:
- **Auto-updates:** `AutomaticCheckEnabled` absent = PASS (macOS default; `softwareupdate --schedule` confirms effective state). Remediation via osascript writes key successfully (exit 0).
- **Root certs:** Switched from `security find-certificate` (false positives on Apple/macOS-managed certs) to `security dump-trust-settings -d`. Empty output = PASS; any trust overrides = WARN.
- **Screen lock:** `askForPassword` is never written to disk on macOS 26 — use `osascript` System Events API (`require password to wake`) instead. Delay key absent = 0s delay = PASS.

---

### Step 15.2 — Write the software hygiene collector module ✅

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

### Step 15.3 — Register hygiene collectors and update remediations ✅

Update `src/collectors/__init__.py` to import and append the three hygiene collectors to `_COLLECTORS`. If remediations were confirmed viable, add to `src/remediations/__init__.py`.

**Validation:** Collector count increments by 3. Dashboard loads with new signal cards. Remediation button (if added) appears only on the FAIL auto-updates card.

---

### Step 15.4 — End-to-end dashboard check ✅

Launch the app and verify:
- All three new cards render with correct status matching the current machine state.
- Toggle a software update setting off in System Settings → General → Software Update; confirm the card reflects FAIL after a page refresh.
- If remediations were added: test the Fix button for auto-updates end-to-end.
- Force one new collector to fail; confirm UNKNOWN and no regressions.

**Validation:** New cards render correctly. Real system state changes are reflected on reload. No regressions in existing signals.

---

### Step 15.5 — Update README and documentation ✅

- Add signals under a new `### Software Hygiene` heading in the Signals monitored section of `README.md`.
- Document Known Limitations for any absent-key behavior that is ambiguous (e.g., if `defaults` key absence cannot be reliably distinguished from "feature disabled").
- Confirm `docs/cli_verification.md` has the Phase 15 section.

**Validation:** README accurately describes each new signal and its status logic.

---

### Phase 15 Integration Validation

- [x] `check_auto_updates` returns FAIL when `AutomaticCheckEnabled = 0`
- [x] `check_auto_updates` returns WARN when check is enabled but `CriticalUpdateInstall = 0`
- [x] `check_auto_updates` returns PASS when both `AutomaticCheckEnabled = 1` and `CriticalUpdateInstall = 1`
- [x] `check_root_certificates` returns PASS when System keychain has no entries
- [x] `check_root_certificates` returns WARN when any certificate is present; raw output shows certificate names
- [x] `check_screen_lock` returns FAIL when `askForPassword = 0`
- [x] `check_screen_lock` returns WARN when `askForPassword = 1` but `askForPasswordDelay > 0`
- [x] `check_screen_lock` returns PASS when `askForPassword = 1` and `askForPasswordDelay = 0`
- [x] All three signals degrade to UNKNOWN (not a crash) when their data sources are unavailable
- [x] Auto-update remediation (if added) works end-to-end via osascript auth dialog
- [x] All existing signal cards render correctly — no regressions
- [x] No collector calls `sudo`
- [x] `docs/cli_verification.md` has Phase 15 section with on/off state output recorded

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

### Step 16.1 — Add CSRF origin validation to `/fix` ✅

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

### Step 16.2 — Add HTTP security headers ✅

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

### Step 16.3 — Create the fix audit log ✅

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

### Step 16.4 — Surface fix log in the history page ✅

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

### Step 16.5 — End-to-end hardening test ✅

Walk through the complete hardening validation:

1. Confirm all four security headers appear in responses for `/`, `/history`, and `/fix/<signal>`.
2. Confirm a POST with a wrong `Origin` header returns HTTP 403 and does not invoke `run_fix()`.
3. Confirm a POST with no `Origin` header proceeds normally to registry lookup (returns 404 for an unknown signal).
4. Confirm the dashboard Fix button still works end-to-end (it sends a same-origin `fetch()` which the Origin check allows).
5. Trigger a fix attempt, cancel it at the auth dialog, then navigate to `/history` — the failed attempt appears in the Remediation Attempts section.
6. Confirm no regressions: all signal cards load, auto-refresh works, signal transitions still appear in the history table.

**Validation:** All six steps complete without error.

---

### Step 16.6 — Update README and documentation ✅

- Add a `## Security` section to `README.md` documenting the CSRF mitigation (Origin validation), the four HTTP security headers, and the fix audit log.
- Update the `## Remediations` section to note that all fix attempts are logged and visible at `/history`.
- Add a Known Limitations entry noting that `'unsafe-inline'` is present in the CSP because of inline scripts in the template, and that moving scripts to `static/` files is the path to a stricter policy.
- Confirm `docs/cli_verification.md` has the Phase 16 section with curl validation output.

**Validation:** README accurately describes all three hardening features.

---

### Phase 16 Integration Validation

- [x] `X-Frame-Options: DENY` present on all responses (`/`, `/history`, `/fix`)
- [x] `X-Content-Type-Options: nosniff` present on all responses
- [x] `Content-Security-Policy` header present on all responses; `default-src 'self'` blocks external resource loading
- [x] `Referrer-Policy: no-referrer` present on all responses
- [x] POST to `/fix` with a mismatched `Origin` header returns HTTP 403, does not invoke `run_fix()`
- [x] POST to `/fix` with the correct `Origin` proceeds to registry lookup as before
- [x] POST to `/fix` with no `Origin` header proceeds to registry lookup as before
- [x] Every fix attempt (success, failure, or cancel) creates a row in the `fix_log` table
- [x] `/history` page displays recent fix attempts with relative timestamps and outcomes
- [x] All existing signal cards, auto-refresh, and the signal-transitions history table function correctly — no regressions
- [x] No Flask `SECRET_KEY` required by this implementation
- [x] `'unsafe-inline'` CSP allowance documented in Known Limitations with the tightening path noted
- [x] README documents CSRF mitigation approach, security headers, and fix audit log
- [x] `docs/cli_verification.md` has Phase 16 curl validation output

---

## Phase 17 — Dashboard Card Improvements

**Goal:** Improve individual signal card usability — visual urgency hierarchy, readable raw output, actionable fix buttons, and a page-level freshness indicator — without changing the flat grid structure (that is Phase 19).

Files changed: `templates/dashboard.html`, `static/style.css`

---

### Step 17.1 — Card urgency tinting ✅

Add a 3px left border to each card whose color reflects its status. PASS cards receive no accent border (the default card border remains).

In `static/style.css`, add per-status modifiers after the `.card` block:

```css
.card--fail    { border-left: 3px solid var(--badge-fail-bg); }
.card--warn    { border-left: 3px solid var(--badge-warn-bg); }
.card--unknown { border-left: 3px solid var(--badge-unknown-bg); }
```

In `templates/dashboard.html`, change `<div class="card">` to:

```html
<div class="card card--{{ signal.status | lower }}">
```

**Validation:** Load the dashboard. FAIL cards have a red left border, WARN cards amber, UNKNOWN yellow, PASS cards show only the default `var(--bg-card-border)` border on all sides.

---

### Step 17.2 — Raw output: max-height with scroll ✅

Constrain the `.raw-output` pre block so long outputs (Listening Services, Launch Agents) scroll within the card rather than expanding it indefinitely.

In `static/style.css`, add to the `.raw-output` rule:

```css
max-height: 8rem;
overflow-y: auto;
```

**Validation:** Open the dashboard and find a signal with multi-line raw output (e.g., Listening Services or User Launch Agents). The pre block is capped at 8 rem height and scrolls vertically. Short single-line outputs are unaffected.

---

### Step 17.3 — Collapsible raw output for PASS cards ✅

Wrap the raw output in a `<details>/<summary>` element. On PASS cards, the block is collapsed by default. On FAIL/WARN/UNKNOWN cards, it is expanded by default.

In `templates/dashboard.html`, replace:

```html
<pre class="raw-output">{{ signal.raw }}</pre>
```

with:

```html
<details class="raw-details"{% if signal.status != 'PASS' %} open{% endif %}>
  <summary class="raw-summary">Raw output</summary>
  <pre class="raw-output">{{ signal.raw }}</pre>
</details>
```

In `static/style.css`, add:

```css
.raw-details {
  font-size: 0.75rem;
}
.raw-summary {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 0.2rem 0;
  user-select: none;
}
.raw-summary:hover {
  color: var(--text-primary);
}
```

**Validation:** PASS cards show only the "Raw output" disclosure triangle (collapsed). FAIL/WARN/UNKNOWN cards show the raw output block expanded. Clicking the summary toggles correctly in both directions.

---

### Step 17.4 — Collapsible description on PASS cards ✅

On PASS cards, the description is visually de-emphasised and toggled via a small info button. On FAIL/WARN/UNKNOWN cards, the description is always visible as it provides action context.

In `templates/dashboard.html`, replace:

```html
<p class="signal-description">{{ signal.description }}</p>
```

with:

```html
{% if signal.status == 'PASS' %}
<details class="desc-details">
  <summary class="desc-summary">What this checks</summary>
  <p class="signal-description">{{ signal.description }}</p>
</details>
{% else %}
<p class="signal-description">{{ signal.description }}</p>
{% endif %}
```

In `static/style.css`, add:

```css
.desc-details {
  font-size: 0.875rem;
}
.desc-summary {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.8rem;
  user-select: none;
}
.desc-summary:hover {
  color: var(--text-primary);
}
```

**Validation:** PASS cards show the description collapsed under a "What this checks" disclosure. FAIL/WARN/UNKNOWN cards show the description text unconditionally. Clicking the summary on a PASS card expands the description.

---

### Step 17.5 — Fix button prominence ✅

Replace the ghost-style fix button with a solid amber/orange accent so it is clearly the primary action on a FAIL or WARN card.

In `static/style.css`, add a new variable:

```css
--fix-btn-bg:       #b45309;
--fix-btn-bg-hover: #92400e;
--fix-btn-text:     #fffbeb;
```

Update the `.fix-btn` rule:

```css
.fix-btn {
  align-self: flex-start;
  padding: 0.35rem 0.9rem;
  background-color: var(--fix-btn-bg);
  color: var(--fix-btn-text);
  border: none;
  border-radius: var(--radius);
  font-family: var(--font-sans);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}
.fix-btn:hover {
  background-color: var(--fix-btn-bg-hover);
}
.fix-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
```

**Validation:** Fix buttons on FAIL/WARN cards render as solid amber buttons. Hover darkens the background. Disabled state is visually distinct.

---

### Step 17.6 — Inline two-step fix confirmation ✅

Replace the `confirm()` dialog with an in-button two-step flow: first click sets the button to a "Confirm?" state with a Cancel link; second click on the button submits. Pressing Cancel or clicking elsewhere restores the original label.

In `templates/dashboard.html`, replace the entire fix-button JS block with:

```js
(function () {
  document.querySelectorAll('.fix-btn').forEach(function (btn) {
    var label = btn.dataset.label;
    var confirming = false;
    var cancelLink = null;

    function reset() {
      confirming = false;
      btn.textContent = label;
      btn.disabled = false;
      if (cancelLink && cancelLink.parentNode) {
        cancelLink.parentNode.removeChild(cancelLink);
      }
      cancelLink = null;
    }

    function submit() {
      btn.disabled = true;
      btn.textContent = 'Applying…';
      if (cancelLink && cancelLink.parentNode) {
        cancelLink.parentNode.removeChild(cancelLink);
      }
      cancelLink = null;
      fetch('/fix/' + encodeURIComponent(btn.dataset.signal), { method: 'POST' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success) {
            btn.textContent = 'Applied — reloading…';
            setTimeout(function () { location.reload(); }, 1000);
          } else {
            alert('Could not apply fix: ' + (data.error || 'Unknown error'));
            reset();
          }
        })
        .catch(function (err) {
          alert('Request failed: ' + err);
          reset();
        });
    }

    btn.addEventListener('click', function () {
      if (confirming) {
        submit();
      } else {
        confirming = true;
        btn.textContent = 'Confirm?';
        cancelLink = document.createElement('button');
        cancelLink.textContent = 'Cancel';
        cancelLink.className = 'fix-cancel';
        cancelLink.addEventListener('click', function (e) {
          e.stopPropagation();
          reset();
        });
        btn.insertAdjacentElement('afterend', cancelLink);
      }
    });
  });
})();
```

In `static/style.css`, add:

```css
.fix-cancel {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  padding: 0.35rem 0.5rem;
  font-family: var(--font-sans);
}
.fix-cancel:hover {
  color: var(--text-primary);
}
```

**Validation:** Click a Fix button → label changes to "Confirm?" and a Cancel button appears. Click Cancel → both elements restore to original state. Click Confirm? → button shows "Applying…", disabled. On success: "Applied — reloading…" appears for ~1 s then page reloads. On failure: alert shows, button restores.

---

### Step 17.7 — "Last checked" timestamp in header ✅

Display a muted "Last checked: just now" line in the header that reflects when the page was rendered. Because Flask renders the page on each request, this timestamp corresponds to the moment the collectors ran.

In `templates/dashboard.html`, add inside `.header-controls` (before the nav links):

```html
<span class="last-checked" id="last-checked-label">Just now</span>
```

Add a small JS block that counts up from 0 seconds after page load and updates the label every minute:

```js
(function () {
  var el = document.getElementById('last-checked-label');
  var loaded = Date.now();
  function update() {
    var secs = Math.round((Date.now() - loaded) / 1000);
    if (secs < 60) {
      el.textContent = 'Just now';
    } else {
      var mins = Math.floor(secs / 60);
      el.textContent = 'Last checked: ' + mins + ' min' + (mins !== 1 ? 's' : '') + ' ago';
    }
  }
  setInterval(update, 30000);
})();
```

In `static/style.css`, add:

```css
.last-checked {
  font-size: 0.75rem;
  color: var(--text-muted);
}
```

**Validation:** On page load, the label reads "Just now". After 60+ seconds without a reload (disable auto-refresh), the label updates to "Last checked: 1 min ago". With auto-refresh active, the label resets to "Just now" on each reload.

---

### Phase 17 Integration Validation

- [x] FAIL cards have a red left border, WARN cards amber, UNKNOWN yellow, PASS cards have no left accent border
- [x] Raw output blocks have `max-height: 8rem` and scroll vertically when content overflows
- [x] Raw output is collapsed (`<details>` closed) on PASS cards and expanded on FAIL/WARN/UNKNOWN cards
- [x] Description text is collapsed on PASS cards and always visible on FAIL/WARN/UNKNOWN cards
- [x] Fix buttons render as solid amber, not ghost style
- [x] First click on Fix button shows "Confirm?" + Cancel; Cancel restores original label
- [x] Confirming a fix shows "Applying…" (disabled) then "Applied — reloading…" for ~1 s before reload
- [x] "Just now" label appears in the header on every page load
- [x] No regressions in auto-refresh countdown, History nav link, or Refresh button
- [x] All 19 always-on signal cards render correctly; opt-in signal card renders correctly when `EXTERNAL_CALLS=1`

---

## Phase 18 — History Page + Cross-Page Infrastructure

**Goal:** Improve the `/history` page (absolute timestamps, client-side filter, section subtitle) and add two cross-page improvements (favicon, mid-range responsive breakpoint) that touch both templates.

Files changed: `templates/history.html`, `templates/dashboard.html`, `static/style.css`

---

### ✅ Step 18.1 — Absolute timestamps on hover (history page)

Pass the raw Unix timestamp alongside the relative string so the full ISO date/time is available as a tooltip. Update `get_summary()` and `get_fix_log()` to include a `ts_iso` field.

In `src/history/__init__.py`:

1. In `get_fix_log()`, add `"ts_iso"` to each dict:

```python
import datetime
...
"ts_iso": datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
```

2. In `get_summary()`, add `"last_changed_iso"` to each result dict (only when `len(entries) > 1`):

```python
"last_changed_iso": datetime.datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d %H:%M:%S") if len(entries) > 1 else None,
```

Also add `"ts_iso"` to each transition dict:

```python
"ts_iso": datetime.datetime.fromtimestamp(entries[i][0]).strftime("%Y-%m-%d %H:%M:%S"),
```

In `templates/history.html`:

- On the `ht-changed` cell in the signal transitions table, add `title="{{ row.last_changed_iso }}"` when the value is present.
- On each `ht-when` span in transition rows, add `title="{{ t.ts_iso }}"`.
- On `ht-changed` cells in the fix log table, add `title="{{ entry.ts_iso }}"`.

**Validation:** Hover over a relative-time cell in either table — a tooltip shows the absolute date/time string (e.g., "2026-06-02 14:33:07").

---

### ✅ Step 18.2 — Client-side filter for signal transitions table

Add a plain text input above the signal transitions table. Typing filters rows by signal name (case-insensitive substring match) without a page reload.

In `templates/history.html`, add above the signal transitions `<table>`:

```html
<div class="filter-bar">
  <input type="search" id="signal-filter" class="filter-input" placeholder="Filter by signal name…" autocomplete="off">
</div>
```

Add a `<script>` block at the bottom of `<body>`:

```js
(function () {
  var input = document.getElementById('signal-filter');
  if (!input) return;
  var rows = document.querySelectorAll('#signal-history-body tr');
  input.addEventListener('input', function () {
    var q = input.value.toLowerCase();
    rows.forEach(function (row) {
      var name = (row.querySelector('.ht-name') || {}).textContent || '';
      row.style.display = name.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
    });
  });
})();
```

Add `id="signal-history-body"` to the signal transitions `<tbody>`.

In `static/style.css`, add:

```css
.filter-bar {
  margin-bottom: 0.75rem;
}
.filter-input {
  background-color: var(--bg-card);
  border: 1px solid var(--bg-card-border);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 0.875rem;
  padding: 0.4rem 0.75rem;
  width: 16rem;
  outline: none;
}
.filter-input:focus {
  border-color: var(--text-muted);
}
```

**Validation:** Type a partial signal name in the filter box. Only matching rows remain visible. Clearing the input restores all rows. No page reload occurs.

---

### ✅ Step 18.3 — Remediation Attempts subtitle

Add a subtitle paragraph below the "Recent Remediation Attempts" heading, matching the style of the signal history subtitle.

In `templates/history.html`, after the `<h2>Recent Remediation Attempts</h2>` element, add:

```html
<p class="history-subtitle">Each fix attempt is recorded regardless of outcome, including user cancellations. Entries are displayed newest first.</p>
```

**Validation:** The Remediation Attempts section shows the subtitle in muted text, visually consistent with the Signal History subtitle above.

---

### ✅ Step 18.4 — Favicon

Add an inline SVG shield favicon to both pages so the app is identifiable in a browser tab.

In both `templates/dashboard.html` and `templates/history.html`, add inside `<head>`:

```html
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2315803d'><path d='M12 2L4 6v6c0 5.25 3.5 10.15 8 11.35C16.5 22.15 20 17.25 20 12V6l-8-4z'/></svg>">
```

**Validation:** Both browser tabs show a green shield icon in the tab bar. No additional static file is created.

---

### ✅ Step 18.5 — Mid-range responsive breakpoint

Add a 720px breakpoint so the card grid uses a single column in split-screen window widths, not just at sub-480px.

In `static/style.css`, update the existing `@media` block to also cover 720px:

```css
@media (max-width: 720px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  .card-grid {
    grid-template-columns: 1fr;
  }
}
```

**Validation:** Resize the browser window to ~700px wide. Cards stack in a single column. At full width (>720px), the auto-fill grid resumes. The 480px header stacking still works.

---

### Phase 18 Integration Validation

- [x] Hovering over any relative-time cell in the signal transitions table shows a tooltip with the absolute date/time
- [x] Hovering over relative-time cells in the Remediation Attempts table shows tooltips
- [x] Typing in the filter box hides non-matching signal rows; clearing restores all rows
- [x] The Remediation Attempts section has a subtitle paragraph in muted text
- [x] Both browser tabs (dashboard and history) show a green shield favicon
- [x] At ~700px window width, the card grid stacks to a single column
- [x] At full width, the card grid uses the auto-fill multi-column layout
- [x] No regressions on the signal transitions table or fix log table

---

## Phase 19 — Dashboard Structure: Summary Bar, Category Groupings, Status Sorting

**Goal:** Restructure the dashboard's card grid into labelled category sections, add a summary bar for at-a-glance posture, and sort cards within each category by severity (FAIL → WARN → UNKNOWN → PASS).

Files changed: `src/collectors/__init__.py`, `src/app.py`, `templates/dashboard.html`, `static/style.css`

---

### ✅ Step 19.1 — Add `CATEGORIES` constant to `src/collectors/__init__.py`

Add a module-level list that defines the display order and membership of each signal category. The names must exactly match the `name` key returned by each collector.

```python
CATEGORIES: list[tuple[str, list[str]]] = [
    ("System Integrity", ["System Integrity Protection", "Gatekeeper", "FileVault", "Secure Boot"]),
    ("Network", ["Application Firewall", "Stealth Mode", "Listening Services"]),
    ("Persistence", ["User Launch Agents", "Global Launch Agents", "Launch Daemons", "Login Items"]),
    ("Authentication", ["Failed Logins", "SSH Authorized Keys"]),
    ("Sharing & Remote Access", ["Remote Login", "Screen Sharing / Remote Management", "AirDrop Receiver Mode"]),
    ("Software Hygiene", ["Automatic Updates", "Root Certificate Trust", "Screen Lock"]),
]
```

Signals not listed in `CATEGORIES` (currently only "macOS Version") are rendered in an "External / Opt-in" section.

**Validation:** `from collectors import CATEGORIES` succeeds in a Python REPL. `len(CATEGORIES)` is 6. The flat list of all names has 19 entries matching the 19 always-on signal names exactly.

---

### ✅ Step 19.2 — Register `status_sort` Jinja2 filter in `src/app.py`

After `app = Flask(...)`, add:

```python
@app.template_filter('status_sort')
def _status_sort(signals_list):
    order = {'FAIL': 0, 'WARN': 1, 'UNKNOWN': 2, 'PASS': 3}
    return sorted(signals_list, key=lambda s: order.get(s.get('status', ''), 4))
```

**Validation:** `{{ [{'status':'PASS'},{'status':'FAIL'}] | status_sort }}` in a test template returns FAIL first.

---

### ✅ Step 19.3 — Pass category data to the dashboard template

In `src/app.py`, update the `dashboard()` route's `render_template` call to pass category metadata:

```python
from collectors import run_all_collectors, CATEGORIES

@app.route("/")
def dashboard():
    signals = run_all_collectors(external=app.config["EXTERNAL_CALLS"])
    store_snapshot(signals)
    cat_names = frozenset(n for _, names in CATEGORIES for n in names)
    return render_template(
        "dashboard.html",
        signals=signals,
        refresh_interval=app.config["REFRESH_INTERVAL"],
        remediations=REMEDIATIONS,
        categories=CATEGORIES,
        categorized_names=cat_names,
    )
```

**Validation:** `curl -s http://127.0.0.1:8000/ | grep -c 'card'` returns the same count as before (all signals still render).

---

### ✅ Step 19.4 — Restructure `templates/dashboard.html` with category sections

Replace `<main class="card-grid">` with a `.dashboard-main` container that loops over categories, rendering a heading and an inner `.card-grid` for each. Sort cards within each category via the `status_sort` filter. Append uncategorized signals in an "External / Opt-in" section.

```html
<main class="dashboard-main">
  {% for category_name, category_signal_names in categories %}
    {% set cat_signals = signals | selectattr('name', 'in', category_signal_names) | list %}
    {% if cat_signals %}
    <section class="signal-category">
      <h2 class="category-heading">{{ category_name }}</h2>
      <div class="card-grid">
        {% for signal in cat_signals | status_sort %}
        <div class="card card--{{ signal.status | lower }}">
          ... (card contents unchanged) ...
        </div>
        {% endfor %}
      </div>
    </section>
    {% endif %}
  {% endfor %}

  {% set uncategorized = signals | rejectattr('name', 'in', categorized_names) | list %}
  {% if uncategorized %}
  <section class="signal-category">
    <h2 class="category-heading">External / Opt-in</h2>
    <div class="card-grid">
      {% for signal in uncategorized | status_sort %}
      <div class="card card--{{ signal.status | lower }}">
        ... (card contents unchanged) ...
      </div>
      {% endfor %}
    </div>
  </section>
  {% endif %}
</main>
```

**Validation:** Dashboard renders six sections with category headings. Each section's cards are sorted FAIL → WARN → UNKNOWN → PASS. No signal is missing or duplicated. With `EXTERNAL_CALLS=1`, a seventh "External / Opt-in" section appears.

---

### ✅ Step 19.5 — Add summary bar

Add a compact status count row between the header and the first category section. Each count is a clickable anchor that jumps to the first card of that status in document order (i.e., the first FAIL across all categories, which due to sorting will appear early).

In `templates/dashboard.html`, compute counts and emit anchor IDs from Python-side data. Since Jinja2 does not support mutable state across loop iterations cleanly, pass pre-computed counts from `app.py`:

In `src/app.py`, within the `dashboard()` route, compute counts after collecting:

```python
from collections import Counter
status_counts = Counter(s['status'] for s in signals)
```

Pass `status_counts=status_counts` to `render_template`.

In `templates/dashboard.html`, add after the `<header>` and before `<main>`:

```html
<div class="summary-bar">
  {% for status in ['FAIL', 'WARN', 'UNKNOWN', 'PASS'] %}
  {% set count = status_counts.get(status, 0) %}
  <a class="summary-item summary-item--{{ status | lower }}"
     href="#status-first-{{ status | lower }}">
    <span class="summary-count">{{ count }}</span>
    <span class="summary-label">{{ status }}</span>
  </a>
  {% endfor %}
</div>
```

Add `id="status-first-{{ signal.status | lower }}"` to the first card of each status encountered across the full sorted render. Use a `namespace` to track which status IDs have been emitted:

```jinja2
{% set ns = namespace(seen_fail=false, seen_warn=false, seen_unknown=false, seen_pass=false) %}
```

Inside the card loop, before the opening `<div class="card ...">`:

```jinja2
{% if signal.status == 'FAIL' and not ns.seen_fail %}
  {% set ns.seen_fail = true %}{% set anchor = 'status-first-fail' %}
{% elif signal.status == 'WARN' and not ns.seen_warn %}
  {% set ns.seen_warn = true %}{% set anchor = 'status-first-warn' %}
{% elif signal.status == 'UNKNOWN' and not ns.seen_unknown %}
  {% set ns.seen_unknown = true %}{% set anchor = 'status-first-unknown' %}
{% elif signal.status == 'PASS' and not ns.seen_pass %}
  {% set ns.seen_pass = true %}{% set anchor = 'status-first-pass' %}
{% else %}
  {% set anchor = '' %}
{% endif %}
<div class="card card--{{ signal.status | lower }}"{% if anchor %} id="{{ anchor }}"{% endif %}>
```

The `namespace` must be declared once before the outer `{% for category_name, ... %}` loop so the first-occurrence tracking spans all categories.

In `static/style.css`, add:

```css
/* ── Summary bar ───────────────────────────────────────────────────────── */
.summary-bar {
  display: flex;
  gap: 1rem;
  max-width: 960px;
  margin: 0 auto 1.5rem;
  flex-wrap: wrap;
}
.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 1.25rem;
  border-radius: var(--radius);
  text-decoration: none;
  background-color: var(--bg-card);
  border: 1px solid var(--bg-card-border);
  min-width: 5rem;
  transition: border-color 0.15s ease;
}
.summary-item:hover {
  border-color: var(--text-muted);
}
.summary-count {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.1;
}
.summary-label {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin-top: 0.15rem;
}
.summary-item--fail   .summary-count { color: var(--badge-fail-bg); }
.summary-item--warn   .summary-count { color: var(--badge-warn-bg); }
.summary-item--unknown .summary-count { color: var(--badge-unknown-bg); }
.summary-item--pass   .summary-count { color: var(--badge-pass-bg); }
.summary-item--fail   .summary-label { color: var(--badge-fail-bg); }
.summary-item--warn   .summary-label { color: var(--badge-warn-bg); }
.summary-item--unknown .summary-label { color: var(--badge-unknown-bg); }
.summary-item--pass   .summary-label { color: var(--badge-pass-bg); }
```

**Validation:** A four-item summary bar appears between the header and the first category section. Counts match the actual number of signals at each status. Clicking a non-zero count scrolls to the first card of that status. Zero counts display "0" but clicking a zero-count link has no scroll effect (no matching anchor).

---

### ✅ Step 19.6 — CSS for category structure

In `static/style.css`, add:

```css
/* ── Dashboard main with categories ───────────────────────────────────── */
.dashboard-main {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.category-heading {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--bg-card-border);
  margin-bottom: 1rem;
}
```

Remove (or leave harmlessly) the `max-width` and `margin` from `.card-grid` since those are now on `.dashboard-main`. The `display: grid` rule on `.card-grid` remains unchanged.

**Validation:** Each category section has a small-caps muted heading with a horizontal rule beneath it. Sections are separated by visible vertical space. The card grid inside each section behaves identically to the pre-phase flat grid.

---

### Phase 19 Integration Validation

- [x] `CATEGORIES` is importable from `collectors` and lists all 19 always-on signal names across 6 categories
- [x] Dashboard renders exactly 6 category sections with correct headings
- [x] Cards within each category are sorted FAIL → WARN → UNKNOWN → PASS
- [x] No signal is missing; no signal appears more than once
- [x] With `EXTERNAL_CALLS=1`, a seventh "External / Opt-in" section appears with the macOS Version card
- [x] Summary bar shows correct counts for each status
- [x] Clicking a non-zero count in the summary bar scrolls to the first card of that status
- [x] All Phase 17 card-level styles (tinting, collapsible raw/description, fix button) work inside the new category structure
- [x] `app.py` changes are limited to: `CATEGORIES` import, `status_sort` filter registration, `status_counts` computation, and updated `render_template` call
- [x] No regressions in auto-refresh, fix flow, History nav link, or Refresh button

---

## Phase 20 — History Page Parity

**Goal:** Bring `/history` to the same level of structural and visual polish as the dashboard. Four specific gaps exist after Phase 19: (1) the history page's two sections are unstyled flat `<h2>` elements with no structural wrapping, while the dashboard uses `<section>` + `.category-heading`; (2) the header lacks a freshness indicator and a reload button; (3) the tables have no row hover state and no protection against horizontal overflow on narrow screens; (4) the fix log outcome column embeds error text directly inside a badge, making long messages awkward.

Files changed: `templates/history.html`, `static/style.css`

---

### ✅ Step 20.1 — Section structure: wrap, heading style, remove inline style

Wrap each content section in a `<section class="signal-category">` element to match the dashboard's category section structure. Apply `.category-heading` to both section headings (replacing `.history-title`). This gives both pages the same uppercase, small-caps, border-bottom heading treatment.

Add a flex column layout with gap to `.history-main` so sections are spaced uniformly by the flex parent rather than by heading margin:

In `static/style.css`, update `.history-main`:

```css
.history-main {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}
```

In `templates/history.html`:

- Remove the `.history-title` and `.history-subtitle` classes from the section headings and subtitles; replace section headings with `.category-heading`.
- Remove the inline `style="margin-top:2.5rem;"` attribute from the "Recent Remediation Attempts" heading.
- Wrap the signal transitions section (heading + subtitle + filter bar + table) in `<section class="signal-category">`.
- Wrap the remediation attempts section (heading + subtitle + table) in `<section class="signal-category">`.

The `.history-subtitle` class and rule in `style.css` remain in place — they are still used as the subtitle paragraph style inside each section.

**Validation:** Both section headings render with the same uppercase/border-bottom treatment as dashboard category headings. Vertical spacing between sections matches the dashboard. The inline `style` attribute is gone from the HTML source.

---

### ✅ Step 20.2 — Header parity: reload button and freshness indicator

The dashboard header shows "Last checked: X ago" and a Refresh button. The history page header has only nav links. Add both elements to bring the headers to parity.

In `templates/history.html`, update the `<nav class="header-controls">` block:

```html
<nav class="header-controls">
  <span class="last-checked" id="last-checked-label">Just now</span>
  <a class="nav-link" href="/">Dashboard</a>
  <a class="nav-link nav-link--active" href="/history">History</a>
  <a class="refresh-btn" href="/history">Reload</a>
</nav>
```

Add the same counting JS block used in `dashboard.html` at the bottom of `<body>` (the script that updates `#last-checked-label` every 5 seconds — copy verbatim):

```js
(function () {
  var el = document.getElementById('last-checked-label');
  var loaded = Date.now();
  function update() {
    var secs = Math.round((Date.now() - loaded) / 1000);
    if (secs < 10) {
      el.textContent = 'Just now';
    } else if (secs < 60) {
      el.textContent = 'Loaded: ' + secs + 's ago';
    } else {
      var mins = Math.floor(secs / 60);
      el.textContent = 'Loaded: ' + mins + ' min' + (mins !== 1 ? 's' : '') + ' ago';
    }
  }
  update();
  setInterval(update, 5000);
})();
```

> Note: The label reads "Loaded:" on the history page rather than "Last checked:" to accurately reflect that this timestamp marks when the page data was fetched, not when collectors were last run.

**Validation:** History page header shows "Just now", the two nav links, and a "Reload" button matching the dashboard's Refresh button style. After 10+ seconds without reloading, the label updates to "Loaded: Xs ago". Clicking Reload navigates to `/history` and resets the label.

---

### ✅ Step 20.3 — Table row hover state

Add a subtle background tint on `tbody tr:hover` so the user has visual feedback when scanning rows — matching the interactivity level of the dashboard cards (which have hover effects via box-shadow / border transitions).

In `static/style.css`, add after the `.history-table td` rule:

```css
.history-table tbody tr:hover td {
  background-color: var(--bg-card);
}
```

**Validation:** Hovering over any row in either table (signal transitions or fix log) produces a visible background highlight. The effect does not apply to header rows.

---

### ✅ Step 20.4 — Responsive table overflow wrapper

On narrow screens (< 600px), the history tables contain enough columns that they overflow the viewport horizontally. Wrap each table in a scrollable container.

In `templates/history.html`, wrap each `<table class="history-table">` in:

```html
<div class="table-scroll">
  <table class="history-table">
    ...
  </table>
</div>
```

In `static/style.css`, add:

```css
.table-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
```

**Validation:** Resize the browser to ~400px wide. Each table scrolls horizontally within its container; the page does not grow wider than the viewport. At full width the wrapper is invisible (no visual change).

---

### ✅ Step 20.5 — Fix log outcome column: separate badge from error message

The fix log outcome column currently embeds the error message inside the badge element:

```html
<span class="badge badge--fail">Failed: User canceled.</span>
```

This makes long error messages stretch the badge unpredictably and buries the status signal inside text. Split the column into a status badge and a separate error text:

In `templates/history.html`, replace the outcome cell content:

```html
<td class="ht-transitions">
  {% if entry.success %}
    <span class="badge badge--pass badge--sm">Success</span>
  {% else %}
    <div style="display:flex; flex-direction:column; gap:0.3rem;">
      <span class="badge badge--fail badge--sm">Failed</span>
      {% if entry.error_message %}
      <span class="ht-error-msg">{{ entry.error_message }}</span>
      {% endif %}
    </div>
  {% endif %}
</td>
```

In `static/style.css`, add:

```css
.ht-error-msg {
  font-size: 0.75rem;
  color: var(--text-error);
}
```

**Validation:** A successful fix attempt shows a small green "Success" badge. A failed attempt shows a small red "Failed" badge with the error message below it in muted red text. Neither the badge nor the cell grows unexpectedly wide on long error messages.

---

### Phase 20 Integration Validation

- [x] Both section headings use `.category-heading` — uppercase, small-caps, border-bottom — matching the dashboard
- [x] No inline `style` attributes remain in `history.html`
- [x] `.history-main` uses flex column layout; section spacing is uniform with no per-section margin hacks
- [x] History header shows "Just now" freshness label and a "Reload" button
- [x] Freshness label updates to "Loaded: Xs ago" after 10 seconds; updates to minutes after 60 seconds
- [x] Clicking Reload navigates to `/history` and resets the label
- [x] Hovering over any data row in either table shows a background highlight; header row is unaffected
- [x] At ~400px wide, both tables scroll horizontally within their containers; no page overflow
- [x] Fix log shows a small badge + separate error text row; long error messages do not stretch the badge
- [x] No regressions: signal transition rows, fix log rows, filter input, tooltip hover, and favicon all function correctly

---

## Phase 21 — Production WSGI Server (Waitress)

**Goal:** Eliminate the Flask development-server warning that appears at startup and serve the dashboard through a production-grade WSGI server.

**Background:** `app.run()` uses Werkzeug's single-threaded development server, which prints `WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.` on every startup. While this dashboard is local-only, the warning is misleading and unnecessary. Replacing Werkzeug with **Waitress** — a pure-Python WSGI server with no C extensions — silences the warning, handles concurrent requests cleanly, and requires only a one-line change to `app.py`.

**Why Waitress:** pure Python (no compilation, no OS-level dependencies), actively maintained, installable via pip, and works identically on Apple Silicon. The API is a drop-in for `app.run()`.

---

### ✅ Step 21.1 — Add waitress to project dependencies

Add `waitress` to `requirements.txt` and install it into the project virtualenv:

```
waitress==3.0.2
```

Run:

```zsh
.venv/bin/pip install waitress==3.0.2
```

Verify the installed version:

```zsh
.venv/bin/python -c "import waitress; print(waitress.__version__)"
```

**Validation:** Command prints `3.0.2` (or the version installed). No errors.

---

### ✅ Step 21.2 — Replace `app.run()` with `waitress.serve()`

In `src/app.py`, replace the final `app.run(...)` call with a `waitress.serve()` call that binds to the same host and port.

At the top of `src/app.py`, add the import after the existing imports:

```python
from waitress import serve
```

Replace:

```python
app.run(host="127.0.0.1", port=port, debug=False)
```

With:

```python
serve(app, host="127.0.0.1", port=port, threads=4)
```

The `threads=4` value matches the concurrency needs of a single-user local dashboard and is the Waitress default. `debug=False` is dropped because Waitress has no debug mode — it is always production-grade.

**Validation:** Start the app with `.venv/bin/python src/app.py`. The Werkzeug development-server warning is absent. The startup line `Dashboard running at http://127.0.0.1:8000 — local access only…` still prints. Loading `http://127.0.0.1:8000` returns the dashboard correctly.

---

### Phase 21 Integration Validation

- [x] `requirements.txt` lists `waitress` with a pinned version
- [x] `.venv/bin/pip show waitress` confirms it is installed
- [x] Starting the app produces no `WARNING: This is a development server` line
- [x] Dashboard loads at `http://127.0.0.1:8000` and all signals render
- [x] History page loads at `http://127.0.0.1:8000/history`
- [x] Fix button flow works end-to-end (confirm → apply → reload)
- [x] App still binds to `127.0.0.1` only (not `0.0.0.0`)
- [x] `PORT` env var is respected: `PORT=9000 .venv/bin/python src/app.py` serves on port 9000

---

## Phase 22 — DRY Refactor

**Goal:** Eliminate the four concrete duplication patterns found across the collector modules, the dashboard template, and the shared JavaScript. No behavior changes — pure structural cleanup that reduces maintenance surface and the risk of the copies drifting out of sync.

**Findings summary:**

| # | What | Where | Copies |
|---|------|-------|--------|
| A | `_run()` helper (basic variant) | `system_integrity.py`, `network.py`, `persistence.py`, `auth.py` | 4 |
| B | `_run()` helper (returncode variant) | `sharing.py`, `hygiene.py` | 2 |
| C | Signal result dict literal | All 7 collector files | 50+ |
| D | Card rendering block in `dashboard.html` | Lines 44–83 and 94–133 | 2 (40-line block each) |
| E | Elapsed-time JS counter | `dashboard.html` and `history.html` | 2 |

---

### Step 22.1 — Extract `_run()` helpers to `src/collectors/utils.py`

Create `src/collectors/utils.py` with both variants of `_run()` that are currently copy-pasted across all six collector files.

```python
# src/collectors/utils.py

import subprocess


def run_cmd(cmd: list[str], timeout: int = 10) -> tuple[str, str | None]:
    """Run cmd, return (output, error). Never raises."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = result.stdout.strip() or result.stderr.strip()
        if not output and result.returncode != 0:
            return "", f"Command exited {result.returncode}: {' '.join(cmd)}"
        return output, None
    except subprocess.TimeoutExpired:
        return "", f"Timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return "", str(e)


def run_cmd_rc(cmd: list[str], timeout: int = 10) -> tuple[str, int, str | None]:
    """Run cmd, return (output, returncode, error). Never raises."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = result.stdout.strip() or result.stderr.strip()
        return output, result.returncode, None
    except subprocess.TimeoutExpired:
        return "", -1, f"Timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return "", -1, f"Command not found: {cmd[0]}"
    except Exception as e:
        return "", -1, str(e)
```

Names use `run_cmd` / `run_cmd_rc` (public names, no leading underscore) since they are imported across module boundaries.

In each of the six collector files:
- Remove the local `_run()` definition
- Add `from .utils import run_cmd` (or `run_cmd_rc` for sharing/hygiene)
- Rename all call sites from `_run(...)` to `run_cmd(...)` / `run_cmd_rc(...)`

**auth.py note:** `check_failed_logins` calls `_run()` with `timeout=30` (slow `log show` command). After the refactor the call becomes `run_cmd(..., timeout=30)`. The default in `utils.py` stays 10.

**Validation:** Start the app and load the dashboard. All 16 signal cards render with the same statuses as before. No `AttributeError` or import errors in the server log.

---

### Step 22.2 — Add `_result()` factory to `src/collectors/utils.py`

Add a result-builder function to `src/collectors/utils.py`:

```python
def make_result(
    name: str,
    description: str,
    status: str,
    raw: str,
    error: str | None = None,
) -> dict:
    """Return a standard signal result dict."""
    return {"name": name, "description": description, "status": status, "raw": raw, "error": error}
```

In every collector file, replace each `return {"name": name, "description": desc, "status": ..., "raw": ..., "error": ...}` literal with `return make_result(name, desc, status, raw, error)` (or the equivalent inline arguments).

Update the import in each collector file to include `make_result`:

```python
from .utils import run_cmd, make_result          # basic collectors
from .utils import run_cmd_rc, make_result       # sharing, hygiene
```

**Validation:** Dashboard and history page load correctly. All signal statuses and raw outputs are identical to before the refactor. Run each collector module as a script (`python src/collectors/system_integrity.py` etc.) to confirm the smoke-test blocks still print correctly.

---

### Step 22.3 — Extract Jinja2 card macro in `dashboard.html`

Lines 44–83 (categorized signals loop body) and lines 94–133 (uncategorized signals loop body) in `templates/dashboard.html` are byte-for-byte identical. Extract the card HTML into a Jinja2 macro at the top of the template body (after `<body>`, before `<header>`):

```jinja
{% macro render_card(signal, anchor, remediations) %}
<div class="card card--{{ signal.status | lower }}"{% if anchor %} id="{{ anchor }}"{% endif %}>
  <div class="card-header">
    <h2 class="signal-name">{{ signal.name }}</h2>
    <span class="badge badge--{{ signal.status | lower }}">{{ signal.status }}</span>
  </div>
  {% if signal.status == 'PASS' %}
  <details class="desc-details">
    <summary class="desc-summary">What this checks</summary>
    <p class="signal-description">{{ signal.description }}</p>
  </details>
  {% else %}
  <p class="signal-description">{{ signal.description }}</p>
  {% endif %}
  <details class="raw-details"{% if signal.status != 'PASS' %} open{% endif %}>
    <summary class="raw-summary">Raw output</summary>
    <pre class="raw-output">{{ signal.raw }}</pre>
  </details>
  {% if signal.error %}
  <p class="signal-error">Error: {{ signal.error }}</p>
  {% endif %}
  {% set fix = remediations.get(signal.name) %}
  {% if fix and signal.status in fix.applies_to %}
  <button class="fix-btn"
          data-signal="{{ signal.name }}"
          data-label="{{ fix.label }}">{{ fix.label }}</button>
  {% endif %}
</div>
{% endmacro %}
```

The anchor assignment logic (`{% if signal.status == 'FAIL' and not ns.seen_fail %}...`) stays in the loop — it updates the shared `ns` namespace and cannot be moved inside a macro. The resolved `anchor` value is passed into the macro as an argument.

Both loops become:

```jinja
{% for signal in cat_signals | status_sort %}
{% if signal.status == 'FAIL' and not ns.seen_fail %}
  {% set ns.seen_fail = true %}{% set anchor = 'status-first-fail' %}
...
{% endif %}
{{ render_card(signal, anchor, remediations) }}
{% endfor %}
```

**Validation:** All signal cards render identically to before. Summary bar anchor links scroll correctly to the first card of each status. Fix buttons still trigger the confirm flow.

---

### Step 22.4 — Extract JS elapsed-time counter to `static/js/utils.js`

The "time since page loaded" counter IIFE appears in both `dashboard.html` (label prefix `"Last checked:"`) and `history.html` (label prefix `"Loaded:"`). The only difference is the prefix string.

Create `static/js/utils.js`:

```js
function startElapsedCounter(elementId, prefix) {
  var el = document.getElementById(elementId);
  var loaded = Date.now();
  function update() {
    var secs = Math.round((Date.now() - loaded) / 1000);
    if (secs < 10) {
      el.textContent = 'Just now';
    } else if (secs < 60) {
      el.textContent = prefix + ': ' + secs + 's ago';
    } else {
      var mins = Math.floor(secs / 60);
      el.textContent = prefix + ': ' + mins + ' min' + (mins !== 1 ? 's' : '') + ' ago';
    }
  }
  update();
  setInterval(update, 5000);
}
```

In `templates/dashboard.html`, replace the elapsed-counter `<script>` block with:

```html
<script src="/static/js/utils.js"></script>
<script>startElapsedCounter('last-checked-label', 'Last checked');</script>
```

In `templates/history.html`, replace the elapsed-counter `<script>` block with:

```html
<script src="/static/js/utils.js"></script>
<script>startElapsedCounter('last-checked-label', 'Loaded');</script>
```

The existing `Content-Security-Policy` header (`script-src 'self' 'unsafe-inline'`) already permits same-origin script files, so no header changes are needed.

**Validation:** On the dashboard, the header reads "Just now" at load, then "Last checked: Xs ago" after 10 s. On the history page, it reads "Just now" then "Loaded: Xs ago". Behavior is identical to before. No console errors.

---

### Phase 22 Integration Validation

- [x] `src/collectors/utils.py` exists and exports `run_cmd`, `run_cmd_rc`, `make_result`
- [x] No collector file defines its own `_run()` function
- [x] `python src/collectors/system_integrity.py` smoke test prints correct output
- [x] `python src/collectors/network.py` smoke test prints correct output
- [x] `python src/collectors/persistence.py` smoke test prints correct output
- [x] `python src/collectors/auth.py` smoke test prints correct output
- [x] `python src/collectors/sharing.py` smoke test prints correct output
- [x] `python src/collectors/hygiene.py` smoke test prints correct output
- [x] Dashboard loads with all signal cards and correct statuses
- [x] All Fix buttons work end-to-end (confirm → apply → reload)
- [x] Summary bar anchor links scroll to the correct first card of each status
- [x] Dashboard header counter reads "Just now" → "Last checked: Xs ago" → minutes
- [x] History header counter reads "Just now" → "Loaded: Xs ago" → minutes
- [x] `static/js/utils.js` is served at `/static/js/utils.js` (HTTP 200)
- [x] No regressions on the history page filter, tooltips, or fix log table

---

## Phase 23 — Automated Test Suite

Addresses Gap G2.

**Goal:** Add a pytest test suite that verifies the status-logic correctness of every collector module and confirms that the Flask routes are reachable. No real system commands are executed — all subprocess and network calls are mocked at the import-site level.

**Scope:**

1. Test infrastructure — `pytest` added to `requirements.txt`, `pytest.ini` created, `tests/` directory scaffolded.
2. Unit tests — one file per collector module, covering every status branch (PASS / FAIL / WARN / UNKNOWN as applicable). Subprocess collectors mock `run_cmd` / `run_cmd_rc`. Filesystem collectors use `pytest`'s `tmp_path` fixture or `unittest.mock.patch` on `pathlib.Path`. The external collector mocks `urllib.request.urlopen`.
3. Integration smoke tests — Flask test client hits `/` and `/history`; `run_all_collectors` is mocked to return canned data so no collectors run.

**Architecture decisions:**

- Tests live in `tests/` at the repo root; there is no `tests/collectors/` subdirectory (project is small enough for a flat layout).
- `pytest.ini` sets `pythonpath = src` (requires pytest ≥ 7) so collector and app imports work without a `PYTHONPATH` prefix.
- `unittest.mock.patch` from stdlib is used for mocking — no additional `pytest-mock` dependency.
- Each collector imports `run_cmd` / `run_cmd_rc` from `.utils`, so the correct patch target is the import-site binding (e.g., `collectors.network.run_cmd`), not `collectors.utils.run_cmd`.
- The Flask integration fixture mocks `collectors.run_all_collectors` so route tests are fast and deterministic regardless of system state.

---

### Step 23.1 — Add pytest and create test infrastructure

**Add pytest to `requirements.txt`:**

```
pytest==8.3.5
```

Install it:

```zsh
.venv/bin/pip install pytest==8.3.5
```

**Create `pytest.ini` at the repo root:**

```ini
[pytest]
pythonpath = src
testpaths = tests
```

**Create the `tests/` directory with empty `__init__.py` and a `conftest.py`:**

```
tests/
├── __init__.py          # empty
└── conftest.py          # shared fixtures
```

**`tests/conftest.py`** should provide two fixtures:

1. `flask_client` — creates and configures the Flask test client with `EXTERNAL_CALLS=False`, `REFRESH_INTERVAL=0`, `ALERT_INTERVAL=0`, `PORT=8000`; initialises the DB in a temporary file; and patches `collectors.run_all_collectors` to return a minimal list of canned result dicts (one PASS, one FAIL, one WARN, one UNKNOWN) so routes return fast without running real collectors.
2. `canned_results` — the list of dicts used by `flask_client`, also available independently for unit test assertions.

**Canned result shape** (must satisfy the full result schema):

```python
[
    {"name": "Test PASS",    "description": "d", "status": "PASS",    "raw": "ok",   "error": None},
    {"name": "Test FAIL",    "description": "d", "status": "FAIL",    "raw": "bad",  "error": None},
    {"name": "Test WARN",    "description": "d", "status": "WARN",    "raw": "note", "error": None},
    {"name": "Test UNKNOWN", "description": "d", "status": "UNKNOWN", "raw": "",     "error": "err"},
]
```

**Validation:** `pytest --collect-only` exits 0 and reports 0 errors (no tests yet, but the infrastructure is valid).

---

### Step 23.2 — Write unit tests for each collector module

Create one test file per collector module. Each file covers every status branch of every `check_*` function in that module. The complete list is:

| Test file | Functions under test |
|-----------|---------------------|
| `tests/test_system_integrity.py` | `check_sip`, `check_gatekeeper`, `check_filevault`, `check_secure_boot` |
| `tests/test_network.py` | `check_firewall`, `check_stealth_mode`, `check_listening_ports` |
| `tests/test_persistence.py` | `check_user_launch_agents`, `check_global_launch_agents`, `check_launch_daemons`, `check_login_items` |
| `tests/test_auth.py` | `check_failed_logins`, `check_ssh_keys` |
| `tests/test_sharing.py` | `check_remote_login`, `check_screen_sharing`, `check_airdrop` |
| `tests/test_hygiene.py` | `check_auto_updates`, `check_root_certificates`, `check_screen_lock` |
| `tests/test_external.py` | `check_macos_version` |

**Rules for each unit test file:**

- Import the function under test from the appropriate module (e.g., `from collectors.network import check_firewall`).
- Use `unittest.mock.patch` as a decorator or context manager to mock `run_cmd` / `run_cmd_rc` **at the call-site namespace** (e.g., `@patch('collectors.network.run_cmd', return_value=(output, None))`).
- For filesystem-based collectors (`check_user_launch_agents`, `check_global_launch_agents`, `check_launch_daemons`, `check_ssh_keys`, `check_root_certificates`): use `pytest`'s `tmp_path` fixture to create real temporary directories/files rather than mocking `pathlib.Path`.
- For `check_macos_version`: mock `urllib.request.urlopen` to return a fake response with a known JSON payload, and mock `run_cmd` to return a fixed version string.
- Every test function must:
  1. Call the collector function with the mocked dependencies.
  2. Assert `result["status"]` equals the expected value for that branch.
  3. Assert `result["name"]` and `result["description"]` are non-empty strings.
  4. Assert `result["error"] is None` for non-UNKNOWN outcomes; assert `result["error"]` is a non-empty string for UNKNOWN outcomes.

**Status branches to cover per collector:**

| Collector | Branches to cover |
|-----------|------------------|
| `check_sip` | PASS (enabled), FAIL (disabled), UNKNOWN (command error) |
| `check_gatekeeper` | PASS, FAIL, UNKNOWN |
| `check_filevault` | PASS, FAIL, UNKNOWN |
| `check_secure_boot` | PASS, UNKNOWN |
| `check_firewall` | PASS, FAIL, UNKNOWN |
| `check_stealth_mode` | PASS, WARN, UNKNOWN |
| `check_listening_ports` | PASS (all loopback), WARN (external listener), UNKNOWN |
| `check_user_launch_agents` | PASS (empty dir), WARN (plist present) |
| `check_global_launch_agents` | PASS (apple-only), WARN (third-party plist) |
| `check_launch_daemons` | PASS, WARN |
| `check_login_items` | PASS (no items), WARN (items present), UNKNOWN (command error) |
| `check_failed_logins` | PASS (header, no events), WARN (events present), UNKNOWN (empty output) |
| `check_ssh_keys` | PASS (file absent), PASS (file empty), WARN (key lines present), UNKNOWN (OSError) |
| `check_remote_login` | PASS (disabled), FAIL (enabled), UNKNOWN |
| `check_screen_sharing` | PASS, FAIL, UNKNOWN |
| `check_airdrop` | PASS (Off), PASS (Contacts Only), WARN (Everyone), UNKNOWN |
| `check_auto_updates` | PASS, WARN (check on, critical off), FAIL (check off), UNKNOWN |
| `check_root_certificates` | PASS (empty output), WARN (cert present) |
| `check_screen_lock` | PASS, WARN (delay > 0), FAIL (no password), UNKNOWN |
| `check_macos_version` | PASS (current), WARN (minor update), FAIL (major behind), UNKNOWN (network error), UNKNOWN (sw_vers error) |

**Validation:** `pytest tests/` runs all unit tests and passes. No test imports from `app.py` or starts a real server.

---

### Step 23.3 — Write integration smoke tests

Create `tests/test_routes.py`. Use the `flask_client` fixture from `conftest.py`.

**Tests to write:**

```python
def test_dashboard_returns_200(flask_client):
    response = flask_client.get("/")
    assert response.status_code == 200

def test_dashboard_contains_signal_names(flask_client):
    response = flask_client.get("/")
    html = response.data.decode()
    assert "Test PASS" in html
    assert "Test FAIL" in html

def test_history_returns_200(flask_client):
    response = flask_client.get("/history")
    assert response.status_code == 200

def test_fix_unknown_signal_returns_404(flask_client):
    response = flask_client.post("/fix/Nonexistent%20Signal")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False

def test_fix_wrong_origin_returns_403(flask_client):
    response = flask_client.post(
        "/fix/Application%20Firewall",
        headers={"Origin": "http://evil.example.com"},
    )
    assert response.status_code == 403

def test_security_headers_present(flask_client):
    response = flask_client.get("/")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "script-src 'self'" in response.headers.get("Content-Security-Policy", "")
    assert response.headers.get("Referrer-Policy") == "no-referrer"
```

**Validation:** `pytest tests/test_routes.py` passes with all six tests green. The test run does not trigger any real osascript dialogs or system commands.

---

### Phase 23 Integration Validation

- [x] `pytest.ini` exists at the repo root with `pythonpath = src` and `testpaths = tests`
- [x] `pytest --collect-only` reports items for all test files without import errors
- [x] `pytest tests/` exits 0 — all tests pass
- [x] No test calls a real system command (all `run_cmd`/`run_cmd_rc`/`urlopen`/filesystem accesses are mocked or use `tmp_path`)
- [x] Unit tests cover every status branch listed in Step 23.2
- [x] `test_dashboard_returns_200` passes without launching a real server
- [x] `test_history_returns_200` passes
- [x] `test_fix_wrong_origin_returns_403` passes (verifies CSRF guard)
- [x] `test_security_headers_present` passes (verifies all four headers)
- [x] `pytest` is listed in `requirements.txt` with a pinned version
- [x] G2 row in the Open Issues table updated to resolved

---

## Phase 24 — AI Security Signals

**Goal:** Add a new "AI Security" category covering three risks that arise from regular AI tool use: API keys stored in shell config files (persistent plaintext exposure), API key values in shell history (exposure from terminal paste), and local LLM servers bound to all network interfaces (network-accessible inference). Each signal follows the same collector shape as all prior phases: `name`, `description`, `status`, `raw`, `error`.

**Signals in scope:**

| Signal | Source | PASS | WARN | FAIL | UNKNOWN |
|--------|--------|------|------|------|---------|
| AI API Keys in Shell Config | `~/.zshrc`, `~/.zprofile`, `~/.zshenv`, `~/.bashrc`, `~/.bash_profile`, `~/.profile` | No AI key variable names found | One or more AI key exports detected | — | OSError on all files checked |
| Shell History Key Exposure | `~/.zsh_history`, `~/.bash_history` | No key value patterns found | One or more key-like strings found | — | All history files unreadable |
| Local AI Server Exposure | `lsof -nP -iTCP:11434 -sTCP:LISTEN` (Ollama), `lsof -nP -iTCP:1234 -sTCP:LISTEN` (LM Studio) | No AI server running, or all bound to loopback | — | Any AI server bound to all interfaces | lsof failed |

> **Why WARN (not FAIL) for shell config keys:** A key in a dotfile is a real security concern — it is exposed to any subprocess and is often accidentally committed to git — but it may be intentional developer configuration. WARN prompts the user to review without declaring a definitive misconfiguration.

> **Why WARN (not FAIL) for shell history:** History files are user-readable and not normally shared. The risk is real (any process running as the user can read history) but softer than an inbound network listener. WARN is the appropriate level.

> **Why FAIL for local server network exposure:** An AI inference server bound to `0.0.0.0` is reachable by any host on the same network and can accept arbitrary prompts. On a personal machine this is almost certainly unintentional. This mirrors the treatment of Remote Login and Screen Sharing in Phase 14: inbound network listeners on personal machines default to FAIL.

> **Key value privacy in raw output:** The shell config and history signals must never include actual key values in the `raw` field. Only filenames, key variable names, and match counts are shown.

> **AI tool coverage — shell config key names:** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `CLAUDE_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `COHERE_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`, `HUGGINGFACE_HUB_TOKEN`, `TOGETHER_API_KEY`, `REPLICATE_API_TOKEN`, `PERPLEXITY_API_KEY`.

> **AI tool coverage — history value patterns:** `sk-[a-zA-Z0-9]{20,}` (OpenAI key prefix), `sk-ant-api[0-9]{2}-` (Anthropic key prefix), `AIza[0-9A-Za-z_-]{35}` (Google API key prefix).

> **Local server ports checked:** Ollama defaults to `11434`; LM Studio defaults to `1234`. Both are checked by the same collector.

---

### Step 24.1 — Verify CLI commands and data sources

Without `sudo`, run each candidate command and record the exact output for both the match and no-match cases:

| Command / Path | What to verify |
|----------------|----------------|
| `grep -n "OPENAI_API_KEY" ~/.zshrc 2>/dev/null` | Does it return the matching line? Exit code when absent or no match? |
| `ls ~/.zshrc ~/.zprofile ~/.zshenv ~/.bashrc ~/.bash_profile ~/.profile 2>&1` | Which files exist on this machine? |
| `wc -l ~/.zsh_history 2>/dev/null` | Is the file readable? What is the format of history entries (`:timestamp:elapsed;command` prefix)? |
| `grep -c "sk-" ~/.zsh_history 2>/dev/null` | Does it exit 1 when there are 0 matches? |
| `lsof -nP -iTCP:11434 -sTCP:LISTEN 2>/dev/null` | Output when Ollama is not running — empty or exit non-zero? |
| `lsof -nP -iTCP:1234 -sTCP:LISTEN 2>/dev/null` | Same for LM Studio port |

For the lsof check: if Ollama is installed, also run `ollama serve` in one terminal and check the lsof output while it is running. Determine the exact format of the `NAME` column: does it say `*:11434` or `0.0.0.0:11434` when bound to all interfaces? Does it say `127.0.0.1:11434` for loopback-only?

For the shell config check: note which of the six candidate files exist on this machine. Absent files must be silently skipped (not an error); only a complete read failure across all files is UNKNOWN.

Record all output in `docs/cli_verification.md` under a new `## Phase 24 — AI Security` heading.

**Step 24.1 outcome:** All commands confirmed working without sudo. Results recorded in `docs/cli_verification.md § Phase 24`.

Key findings:
- **Shell config files present on this machine:** `~/.zshrc`, `~/.bashrc`, `~/.bash_profile`. Absent files (`~/.zprofile`, `~/.zshenv`, `~/.profile`) skipped silently.
- **grep exit codes:** rc=0 on match, rc=1 on no-match, rc=2 on missing file. Decision: use `pathlib.Path.read_text()` + `re.search()` directly — avoids subprocess and keeps key values out of argument strings.
- **zsh_history format on this machine:** plain commands only (no `: ts:elapsed;` prefix — `EXTENDED_HISTORY` not set). Parser must handle both plain and extended formats.
- **Absent history files are PASS** (not UNKNOWN) — many machines have only one shell history file.
- **Ollama is running on this machine:** bound to `127.0.0.1:11434` (loopback-only, PASS). NAME column format for loopback: `127.0.0.1:<port>`. All-interfaces format: `*:<port>` (confirmed from Phase 7 network collector).
- **LM Studio not running:** `lsof -nP -iTCP:1234 -sTCP:LISTEN` exits 1 with no output.

**Validation:** ✅ All commands run without sudo. Output format recorded for all three signals. Absent files and zero-match cases confirmed to degrade gracefully. lsof NAME field format confirmed for both running (loopback) and not-running cases.

---

### Step 24.2 — Write the AI security collector module

Create `src/collectors/ai.py` with three functions:

```
check_ai_keys_shell_config()  → { name, description, status, raw, error }
check_ai_keys_shell_history() → { name, description, status, raw, error }
check_local_ai_server()       → { name, description, status, raw, error }
```

**Status logic:**

| Collector | PASS | WARN | FAIL | UNKNOWN |
|-----------|------|------|------|---------|
| `check_ai_keys_shell_config` | None of the known AI key variable names appear in any shell config file | One or more key variable names found as an export or bare assignment | — | OSError reading all candidate files (individual absent/unreadable files are silently skipped) |
| `check_ai_keys_shell_history` | No key-like value patterns match in any history file | One or more matches found in at least one file | — | All history files unreadable (absent files are PASS, not UNKNOWN) |
| `check_local_ai_server` | No known AI server port has a listener, or all listeners are bound to loopback (`127.0.0.1` / `[::1]`) | — | Any known AI server port is bound to all interfaces (`*`, `0.0.0.0`) | `lsof` failed or exited with an unexpected non-zero code |

**`raw` field content (privacy-preserving):**
- `check_ai_keys_shell_config` PASS: `"No AI API key variables found in shell config files."`
- `check_ai_keys_shell_config` WARN: one `"<filename>: <KEY_NAME>"` line per match — key names only, never values
- `check_ai_keys_shell_history` PASS: `"No AI API key patterns found in shell history."`
- `check_ai_keys_shell_history` WARN: `"~/.zsh_history: <N> pattern match(es)"` — counts only, never matched strings
- `check_local_ai_server` PASS: `"No AI server listening on known ports (11434, 1234)."` or `"Ollama: 127.0.0.1:11434 (loopback only)."`
- `check_local_ai_server` FAIL: `"Ollama: *:11434 (all interfaces — network-accessible)."` with the lsof NAME field

**Implementation rules:**
- `check_ai_keys_shell_config`: use `pathlib.Path` to read each file; `try/except OSError` per file (skip silently); for each line, `re.search(r'(?:export\s+)?(' + '|'.join(_KEY_NAMES) + r')\s*=', line)`; never store or log matched values
- `check_ai_keys_shell_history`: use `pathlib.Path`; `zsh_history` entries use `: <ts>:<elapsed>;<command>` format — strip the `:<ts>:<elapsed>;` prefix before pattern-matching; count matches with `re.search` across the value patterns listed in the phase header; capture counts, not strings
- `check_local_ai_server`: use `subprocess.run()` with `["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"]` for each port in `_AI_PORTS = {11434: "Ollama", 1234: "LM Studio"}`; parse the NAME column from each output line; `*:` or `0.0.0.0:` in NAME → FAIL; `127.0.0.1:` or `[::1]:` → PASS contribution; no output → not running (PASS for that port); first FAIL across any port wins
- All subprocess calls use `run_cmd_rc` / `_run()`; never `shell=True`
- Any unhandled exception → UNKNOWN; never raise or crash

Add a `__main__` block at the bottom.

**Validation:** ✅ `.venv/bin/python src/collectors/ai.py` — all three functions return dicts with the correct keys; none raise an exception. Results on this machine:
- Shell config: PASS (`No AI API key variables found in shell config files.`)
- Shell history: PASS (`No AI API key patterns found in shell history.`)
- Local AI server: PASS (`Ollama: 127.0.0.1:11434 (loopback only)`, LM Studio not running)

WARN path smoke-tested by injecting a temp file with `export OPENAI_API_KEY=sk-...` — status=WARN, key name present in raw, key value absent from raw. History WARN path confirmed with a matching history line — raw shows `1 pattern match(es)`, no key value present.

---

### Step 24.3 — Register AI security collectors

Update `src/collectors/__init__.py`:
- Add `from .ai import check_ai_keys_shell_config, check_ai_keys_shell_history, check_local_ai_server`
- Append all three to `_COLLECTORS`
- Add `("AI Security", ["AI API Keys in Shell Config", "Shell History Key Exposure", "Local AI Server Exposure"])` to the `CATEGORIES` list

No changes to `app.py` or the template.

**Validation:** ✅ `run_all_collectors()` returns 22 results (19 existing always-on + 3 new). All three AI signals return PASS with correct raw output on this machine. All dicts contain the required keys.

---

### Step 24.4 — Add unit tests for the AI security collectors

Add `tests/test_ai.py` following the existing test-file pattern (`mock_run_cmd_rc` fixture from `conftest.py`; `tmp_path` for filesystem tests).

Tests to include:

**`check_ai_keys_shell_config`:**
- `test_shell_config_no_keys_pass` — all config files absent → PASS
- `test_shell_config_key_found_warn` — config file contains `export OPENAI_API_KEY=sk-abc123` → WARN; assert `"sk-abc123"` is NOT in raw
- `test_shell_config_key_name_in_raw` — WARN raw contains filename and `OPENAI_API_KEY` but not the value
- `test_shell_config_non_key_export_pass` — file contains only `export PATH=/usr/local/bin` → PASS (false-positive guard)
- `test_shell_config_multiple_files_warn` — keys found in two different files → WARN; both filenames appear in raw

**`check_ai_keys_shell_history`:**
- `test_history_no_matches_pass` — history file present but contains no key patterns → PASS
- `test_history_file_absent_pass` — history file absent → PASS (not UNKNOWN)
- `test_history_openai_pattern_warn` — history contains `echo sk-abc123456789012345678` → WARN; assert matched string is NOT in raw
- `test_history_count_in_raw` — WARN raw shows a numeric count of matches

**`check_local_ai_server`:**
- `test_local_ai_server_not_running_pass` — lsof exits 1 with no output → PASS
- `test_local_ai_server_loopback_pass` — lsof NAME column shows `127.0.0.1:11434` → PASS
- `test_local_ai_server_all_interfaces_fail` — lsof NAME column shows `*:11434` → FAIL
- `test_local_ai_server_lsof_error_unknown` — lsof command raises an exception → UNKNOWN

**Validation:** ✅ `pytest tests/test_ai.py -v` — 19 tests, all pass. No real shell config or history files read; all filesystem access uses `tmp_path`. Full suite: 96 passed, no regressions.

---

### Step 24.5 — End-to-end dashboard check

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000`.

- Confirm the "AI Security" section appears with three cards under the correct heading.
- Confirm badge colors match the actual machine state for each signal.
- Inspect the raw output of the shell config and history cards — confirm no key values are visible.
- If Ollama is installed: start it in another terminal, refresh the dashboard — Local AI Server Exposure should show FAIL. Stop Ollama, refresh — card returns to PASS.
- Force one AI collector to fail (break its command temporarily); confirm it shows UNKNOWN and all other cards are unaffected; restore.

**Validation:** ✅ All three AI security cards render correctly with live data. Raw output contains no key values. Network-exposure state change is reflected after a page reload. No regressions in any of the 19 existing signal cards. UNKNOWN renders cleanly — 22 total badges present with the broken collector; restored to PASS after fixing.

---

### Step 24.6 — Update README and documentation

- Add signals under a new `### AI Security` heading in the Signals monitored section of `README.md`.
- Add a Known Limitations entry noting that the shell config check covers only the listed key variable names — keys stored under non-standard names, in Keychain, in a password manager CLI, or in project-level `.env` files are not detected. Similarly, the history check covers specific key value patterns; obfuscated or base64-encoded keys are not detected.
- Confirm `docs/cli_verification.md` has the Phase 24 section from Step 24.1.

**Validation:** ✅ README accurately describes each new signal, its status logic, and its detection limitations. Known Limitations entry added for shell config and history detection scope. `ai.py` added to project structure table. `docs/cli_verification.md` has the Phase 24 section.

---

### Phase 24 Integration Validation

- [x] `check_ai_keys_shell_config` returns WARN when a shell config file contains a known AI key variable name
- [x] `check_ai_keys_shell_config` returns PASS when no known AI key variable names are present
- [x] Raw output for `check_ai_keys_shell_config` WARN contains filenames and key variable names but never key values
- [x] `check_ai_keys_shell_history` returns WARN when a history file contains a key-like value pattern
- [x] `check_ai_keys_shell_history` returns PASS when history file is absent
- [x] Raw output for `check_ai_keys_shell_history` WARN shows match counts only, not the matched strings
- [x] `check_local_ai_server` returns FAIL when an AI server is bound to all interfaces
- [x] `check_local_ai_server` returns PASS when bound to loopback only or not running
- [x] All three new signals degrade to UNKNOWN gracefully when their data sources are unavailable — no crash, no 500
- [x] "AI Security" section appears correctly grouped in the dashboard under its category heading
- [x] All 19 existing signal cards render correctly — no regressions
- [x] No collector calls `sudo`
- [x] `pytest tests/test_ai.py` exits 0 — all tests pass
- [x] `docs/cli_verification.md` has the Phase 24 section with command output recorded
- [x] README `### AI Security` section accurately describes each signal and its detection limitations

---

## Phase 25 — User Account Signals

**Goal:** Add a new "User Accounts" category with three signals that expose account-level risks that no existing category covers: an enabled guest account, admin privileges held by unexpected users, and a login window that reveals account names. All three signals are single-command reads with no `sudo` requirement and negligible latency.

**Why this category is needed:**

The dashboard currently monitors what software is running and how the network is configured, but it has no visibility into *who can log in* or *with what privileges*. User account hygiene is a foundational layer of macOS security:

- **Unexpected admin accounts** are the most common persistence mechanism after a compromise. An attacker who creates or elevates a user account retains access even if the initial exploit is patched. There is no existing signal that enumerates admin group membership, so a rogue admin account would go completely undetected.

- **The guest account** allows anyone with physical access to use the machine under a session that is not attributed to any named user. macOS erases the guest home directory on logout, making forensic investigation difficult. On a personally-owned machine there is rarely a reason to leave the guest account enabled, and it is off by default — so a FAIL here reliably indicates a deliberate or accidental configuration change.

- **The login window user list** is a minor but real information-disclosure risk: displaying the list of local accounts to anyone who reaches the login screen reveals valid usernames that can be used in targeted password attacks, phishing, or social engineering. Switching the login window to a name-and-password prompt (the more secure default on managed Macs) eliminates this exposure.

These three checks share a common property: they are each a single `defaults read` or `dscl` call, return in milliseconds, require no elevated privileges, and have unambiguous pass/fail semantics. The implementation effort is low relative to the security value.

**Signals in scope:**

| Signal | Source | PASS | WARN | FAIL | UNKNOWN |
|--------|--------|------|------|------|---------|
| Guest Account | `defaults read /Library/Preferences/com.apple.loginwindow GuestEnabled` | `0` or key absent | — | `1` (enabled) | `defaults` command failed |
| Login Window Display | `defaults read /Library/Preferences/com.apple.loginwindow SHOWFULLNAME` | `1` (name+password) or key absent | `0` (user list shown) | — | `defaults` command failed |
| Admin Group Members | `dscl . read /Groups/admin GroupMembership` | single admin user (current user only) | multiple admin users listed | — | `dscl` command failed |

> **Why FAIL for Guest Account:** The guest account is off by default on macOS. A value of `1` means it was explicitly enabled (or re-enabled by a software change). Physical access to a guest session is a meaningful risk on a personal machine. There is no defensive reason to leave it enabled if it is not actively used.

> **Why WARN (not FAIL) for Login Window Display:** Showing the user list is the macOS default on non-managed machines and is not itself a breach — it is an information-disclosure risk. Many users have never changed this setting and the risk depends on context (home machine vs. office). WARN prompts review without overstating the severity.

> **Why WARN for Admin Group Members:** The presence of multiple admin accounts is not automatically wrong — a developer may have a separate admin account by design, or an MDM may have provisioned one. The signal cannot distinguish legitimate from rogue accounts. WARN with the full member list lets the user make the judgment call. A machine with only the current user in the admin group returns PASS.

> **Key absent semantics:** For Guest Account, key absent means the macOS default (off) applies → PASS. For Login Window Display, key absent means the system default (user list visible) applies on unmanaged Macs → WARN, matching the live behavior. This differs from the auto-updates and screen lock signals where absence means the secure default is active; here, the default is the less secure option on personal machines.

---

### Step 25.1 — Verify CLI commands

Run each candidate command without `sudo` and record the exact output for both the match and no-match cases:

| Command | What to verify |
|---------|----------------|
| `defaults read /Library/Preferences/com.apple.loginwindow GuestEnabled` | Output when guest is off (`0`, `1`, or key-not-found error)? Exit code in each case? |
| `defaults read /Library/Preferences/com.apple.loginwindow SHOWFULLNAME` | Output when the user list is shown vs. name+password? Key absent behavior? |
| `dscl . read /Groups/admin GroupMembership` | Exact output format — does it use `GroupMembership:` or `GroupMembership:\n`? Are usernames space-separated? |
| `dscl . read /Groups/admin GroupMembership 2>&1; echo "rc=$?"` | Exit code when the group exists; what happens if `/Groups/admin` is missing (should never occur on macOS but defensive check)? |
| `id -un` | Confirm this returns the current user's short name for the admin-count comparison |

For the `dscl` check: confirm the exact field name (`GroupMembership` vs `GroupMembershipUsers`) and whether the current user's short name matches one of the listed members character-for-character. Note whether system accounts (e.g. `root`, `_mbsetupuser`) appear in the list.

Record all output in `docs/cli_verification.md` under a new `## Phase 25 — User Accounts` heading.

**Validation:** All commands run without `sudo` and produce parseable output. Key-absent and exit-code behavior confirmed for both `defaults` calls. Admin group membership format confirmed. Results recorded in `docs/cli_verification.md § Phase 25`.

---

### Step 25.2 — Write the User Accounts collector module

Create `src/collectors/accounts.py` with three functions:

```
check_guest_account()          → { name, description, status, raw, error }
check_login_window_display()   → { name, description, status, raw, error }
check_admin_group_members()    → { name, description, status, raw, error }
```

**`check_guest_account`:**
- Command: `["defaults", "read", "/Library/Preferences/com.apple.loginwindow", "GuestEnabled"]`
- Use `run_cmd_rc` to capture stdout, return code, and error.
- `rc == 1` and output contains `"does not exist"` → key absent → PASS (`"GuestEnabled: absent (macOS default: off)"`)
- `rc == 0` and value `"0"` → PASS (`"GuestEnabled: 0 (off)"`)
- `rc == 0` and value `"1"` → FAIL (`"GuestEnabled: 1 (enabled)"`)
- Any other combination → UNKNOWN

**`check_login_window_display`:**
- Command: `["defaults", "read", "/Library/Preferences/com.apple.loginwindow", "SHOWFULLNAME"]`
- `rc == 1` and output contains `"does not exist"` → key absent → WARN (`"SHOWFULLNAME: absent (macOS default on unmanaged Macs: user list shown)"`)
- `rc == 0` and value `"1"` → PASS (`"SHOWFULLNAME: 1 (name and password prompt)"`)
- `rc == 0` and value `"0"` → WARN (`"SHOWFULLNAME: 0 (user list visible at login screen)"`)
- Any other combination → UNKNOWN

**`check_admin_group_members`:**
- Command: `["dscl", ".", "read", "/Groups/admin", "GroupMembership"]`
- Parse the `GroupMembership:` line; strip the field label; split the remaining space-separated usernames.
- Filter out known system accounts: `root`, `_mbsetupuser`, `_uucp`, `_networkd` (expand based on Step 25.1 findings).
- Get current user via `os.environ.get("USER") or run_cmd(["id", "-un"])[0].strip()`.
- `human_members == [current_user]` → PASS (`"Admin group: <username> only"`)
- `len(human_members) > 1` → WARN with the full member list
- `human_members == []` → UNKNOWN (no recognizable members — output format may have changed)
- `dscl` command fails → UNKNOWN

Add a `__main__` block at the bottom for direct smoke-testing.

**Validation:** `.venv/bin/python src/collectors/accounts.py` — all three functions return dicts with the correct five keys; none raise an exception. Status values match the actual state of this machine.

---

### Step 25.3 — Register User Account collectors

Update `src/collectors/__init__.py`:
- Add `from .accounts import check_guest_account, check_login_window_display, check_admin_group_members`
- Append all three to `_COLLECTORS`
- Add `("User Accounts", ["Guest Account", "Login Window Display", "Admin Group Members"])` to the `CATEGORIES` list, positioned after `"Authentication"` and before `"Sharing & Remote Access"`

No changes to `app.py` or the template.

**Validation:** `run_all_collectors()` returns 25 results (22 existing always-on + 3 new). All three User Account signals return dicts with the correct keys. The `CATEGORIES` list produces the correct grouping order on the dashboard.

---

### Step 25.4 — Add unit tests for the User Account collectors

Add `tests/test_accounts.py` following the existing test-file pattern (use `mock_run_cmd_rc` fixture from `conftest.py`).

**`check_guest_account` tests:**
- `test_guest_account_key_absent_pass` — `rc=1`, output contains `"does not exist"` → PASS
- `test_guest_account_disabled_pass` — `rc=0`, value `"0"` → PASS
- `test_guest_account_enabled_fail` — `rc=0`, value `"1"` → FAIL
- `test_guest_account_unexpected_value_unknown` — `rc=0`, value `"yes"` → UNKNOWN
- `test_guest_account_command_error_unknown` — `run_cmd_rc` returns a non-empty error string → UNKNOWN

**`check_login_window_display` tests:**
- `test_login_window_key_absent_warn` — `rc=1`, output contains `"does not exist"` → WARN
- `test_login_window_name_password_pass` — `rc=0`, value `"1"` → PASS
- `test_login_window_user_list_warn` — `rc=0`, value `"0"` → WARN
- `test_login_window_command_error_unknown` — error string returned → UNKNOWN

**`check_admin_group_members` tests:**
- `test_admin_group_single_user_pass` — `GroupMembership: scottrosenberg`, `USER=scottrosenberg` → PASS
- `test_admin_group_multiple_users_warn` — `GroupMembership: scottrosenberg backdoor`, `USER=scottrosenberg` → WARN; both usernames appear in raw
- `test_admin_group_system_accounts_filtered` — `GroupMembership: scottrosenberg root _mbsetupuser`, `USER=scottrosenberg` → PASS (system accounts excluded)
- `test_admin_group_command_error_unknown` — `dscl` returns a non-empty error → UNKNOWN
- `test_admin_group_empty_members_unknown` — `GroupMembership:` with no names → UNKNOWN

**Validation:** `pytest tests/test_accounts.py -v` — all tests pass. Full suite passes with no regressions.

---

### Step 25.5 — End-to-end dashboard check

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000`.

- Confirm the "User Accounts" section appears with three cards under the correct heading, positioned between "Authentication" and "Sharing & Remote Access".
- Confirm badge colors match the actual machine state for each signal.
- Smoke-test the FAIL path for Guest Account: temporarily set `defaults write /Library/Preferences/com.apple.loginwindow GuestEnabled -bool true` (requires admin password), refresh the dashboard — Guest Account card should show FAIL. Restore with `defaults write /Library/Preferences/com.apple.loginwindow GuestEnabled -bool false`.
- Force one accounts collector to fail; confirm it shows UNKNOWN and all other cards are unaffected; restore.

**Validation:** All three User Account cards render correctly with live data. FAIL state for Guest Account is visually confirmed. No regressions in any of the 22 existing signal cards. 25 total badges present and correctly grouped.

---

### Step 25.6 — Update README and documentation

- Add signals under a new `### User Accounts` section in the Signals monitored table in `README.md`.
- Add a Known Limitations entry for `check_admin_group_members` noting that it filters a fixed list of known system accounts — a future macOS version introducing a new system account not in the filter list could produce a false WARN.
- Confirm `docs/cli_verification.md` has the Phase 25 section from Step 25.1.
- Update `docs/SIGNAL_GAPS.md` — mark the User Accounts gap as addressed in Phase 25.

**Validation:** README accurately describes each new signal and its status logic. `accounts.py` added to project structure table. `docs/cli_verification.md` has the Phase 25 section.

---

### Phase 25 Integration Validation

- [x] `check_guest_account` returns PASS when `GuestEnabled` is `0` or absent
- [x] `check_guest_account` returns FAIL when `GuestEnabled` is `1`
- [x] `check_login_window_display` returns PASS when `SHOWFULLNAME` is `1`
- [x] `check_login_window_display` returns WARN when `SHOWFULLNAME` is `0` or absent
- [x] `check_admin_group_members` returns PASS when only the current user is in the admin group
- [x] `check_admin_group_members` returns WARN when additional human users are present, with their names in `raw`
- [x] Known system accounts (`root`, `_mbsetupuser`, etc.) are excluded from the admin member count
- [x] All three signals degrade to UNKNOWN gracefully when their commands fail — no crash, no 500
- [x] "User Accounts" section appears between "Authentication" and "Sharing & Remote Access" in the dashboard
- [x] All 22 existing signal cards render correctly — no regressions
- [x] No collector calls `sudo`
- [x] `pytest tests/test_accounts.py` exits 0 — all tests pass
- [x] Full test suite (`pytest`) exits 0 — no regressions
- [x] `docs/cli_verification.md` has the Phase 25 section with command output recorded
- [x] README `### User Accounts` section accurately describes each signal

---

## Phase 26 — Screensaver Idle Timeout

**Goal:** Add a single "Screensaver Idle Timeout" signal to the existing Software Hygiene category. The signal closes the remaining gap in lock coverage: `check_screen_lock` confirms that the machine requires a password immediately on wake, but nothing checks *how long the machine sits idle before the screensaver (and thus the lock) engages*. A 30-minute idle timeout means the screen is reachable for 30 minutes while unattended — `check_screen_lock` returns PASS throughout.

**Why this signal is needed:**

The three existing Software Hygiene signals (`check_automatic_updates`, `check_root_certificates`, `check_screen_lock`) leave one gap: idle-to-lock time. `check_screen_lock` reads `askForPassword` (password required on wake) and `askForPasswordDelay` (grace period after wake before the password prompt appears — should be 0). Neither controls when the screensaver fires in the first place.

`defaults -currentHost read com.apple.screensaver idleTime` is a single millisecond read with no privileges required and unambiguous numeric output. The `-currentHost` flag is required because the key lives in the ByHost preference domain, not the standard per-user domain. The key is absent until the user opens System Settings → Screen Saver; absent means the screensaver is disabled → FAIL.

**Signal in scope:**

| Signal | Source | PASS | WARN | FAIL | UNKNOWN |
|--------|--------|------|------|------|---------|
| Screensaver Idle Timeout | `defaults -currentHost read com.apple.screensaver idleTime` | 0 < value ≤ 600 s | value > 600 s (> 10 min) | `0` or key absent | `defaults` failed or returned non-integer output |

> **Why FAIL for value `0`:** `0` means "Never" in System Settings — the screensaver (and auto-lock) will never engage by idle timeout alone. This is a direct security gap regardless of other lock settings.

> **Why FAIL for key absent:** The key is written only after the user configures a screensaver timeout in System Settings. Absent means the screensaver has never been configured and behaves identically to `0`.

> **Why WARN for > 600 s:** A timeout over 10 minutes is a meaningful unattended exposure window. It is not definitively wrong (some workflows require longer), so WARN prompts review without overstating severity.

> **Why PASS for 0 < value ≤ 600 s:** Ten minutes is a conventional upper bound for acceptable idle-lock time on a personal machine. Shorter is always better, but ≤ 10 min is a defensible baseline.

---

### Step 26.1 — Verify CLI command

Run the following without `sudo` and record exact output:

| Command | What to verify |
|---------|----------------|
| `defaults -currentHost read com.apple.screensaver idleTime` | Exact output (integer seconds) when a timeout is configured |
| `defaults -currentHost read com.apple.screensaver idleTime; echo "rc=$?"` | Exit code when key present; exit code when key absent |
| `defaults -currentHost read com.apple.screensaver idleTime 2>&1` | Exact error string when key absent (expected: `"does not exist"`) |
| `defaults read com.apple.screensaver idleTime 2>&1` | Confirm the non-`-currentHost` domain returns a different (or absent) value — to verify `-currentHost` is required |

Also check: does `stderr` contain the `"does not exist"` string, or `stdout`, or both? The Phase 25 `defaults` calls found the error on `stdout` when captured with `2>&1`; confirm the same behavior here.

Record all output in `docs/cli_verification.md` under a new `## Phase 26 — Screensaver Idle Timeout` heading.

**Validation:** ✅ Command runs without `sudo`. Exit code and output confirmed for key-present and key-absent cases. Confirmed `-currentHost` is required (non-host domain also returns absent on this machine, confirming ByHost is the correct read target). Error string (`"does not exist"`) is on **stderr only** — `stdout` is empty when the key is absent; `out` must not be checked. When key is present, `stdout` is a bare integer (e.g. `"300\n"`); `stderr` is empty. Results recorded in `docs/cli_verification.md § Phase 26`.

Key findings:
- **Baseline state on this machine:** key absent in both ByHost and standard domain (screensaver never configured via System Settings).
- **rc=0:** key present; `stdout.strip()` is a parseable integer.
- **rc=1 + `"does not exist"` in stderr:** key absent → FAIL.
- **rc=1 without that string:** unexpected error → UNKNOWN.
- **Value 0 confirmed:** `defaults -currentHost write com.apple.screensaver idleTime -int 0` → read returns `"0"`, rc=0.
- **Value 1800 confirmed:** read returns `"1800"`, rc=0.
- **Machine restored:** key deleted with `defaults -currentHost delete`; confirmed absent again.

---

### Step 26.2 — Add the collector to `hygiene.py`

Add `check_screensaver_idle_timeout()` to `src/collectors/hygiene.py` alongside the three existing Software Hygiene checks.

**`check_screensaver_idle_timeout`:**
- Command: `["defaults", "-currentHost", "read", "com.apple.screensaver", "idleTime"]`
- Use `run_cmd_rc` to capture stdout, return code, and stderr.
- `rc != 0` and (`out` + `err`) contains `"does not exist"` → key absent → FAIL; raw: `"idleTime: absent (screensaver not configured; screen will not auto-lock on idle)"`
- `rc != 0` (other failure) → UNKNOWN; `error`: the captured stderr or stdout
- `rc == 0` and `out.strip()` cannot be parsed as `int` → UNKNOWN; `error`: `"Non-integer value: <value>"`
- `rc == 0` and `int(value) == 0` → FAIL; raw: `"idleTime: 0 (Never — screen will not auto-lock on idle)"`
- `rc == 0` and `0 < int(value) <= 600` → PASS; raw: `"idleTime: <N> s"`
- `rc == 0` and `int(value) > 600` → WARN; raw: `"idleTime: <N> s (> 10 min recommended maximum)"`

Use `make_result()` for all return paths. Follow the `timeout=5` convention used in the other `hygiene.py` checks.

Extend the existing `__main__` block in `hygiene.py` to call and print `check_screensaver_idle_timeout()`.

**Validation:** ✅ `.venv/bin/python -c "from src.collectors.hygiene import check_screensaver_idle_timeout; import json; print(json.dumps(check_screensaver_idle_timeout(), indent=2))"` — returns a dict with the correct five keys and a status that matches the actual machine state.

Results on this machine (key absent at baseline):
- Absent → `FAIL`, raw: `"idleTime: absent (screensaver not configured; screen will not auto-lock on idle)"`
- `idleTime=300` → `PASS`, raw: `"idleTime: 300 s"`
- `idleTime=600` → `PASS` (boundary)
- `idleTime=601` → `WARN` (boundary), raw: `"idleTime: 601 s (> 10 min recommended maximum)"`
- `idleTime=0` → `FAIL`, raw: `"idleTime: 0 (Never — screen will not auto-lock on idle)"`

---

### Step 26.3 — Register the collector

Update `src/collectors/__init__.py`:
- Add `check_screensaver_idle_timeout` to the existing `from .hygiene import ...` line
- Append `check_screensaver_idle_timeout` to `_COLLECTORS` immediately after `check_screen_lock`
- Add `"Screensaver Idle Timeout"` to the `"Software Hygiene"` entry in `CATEGORIES` (last in the list for that category)

No changes to `app.py` or the template.

**Validation:** ✅ `run_all_collectors()` returns 26 results (25 existing + 1 new). `"Screensaver Idle Timeout"` appears in the `"Software Hygiene"` group with `status=FAIL` (key absent on this machine). Result dict contains the required five keys.

---

### Step 26.4 — Add unit tests

Add `tests/test_screensaver.py` following the existing test-file pattern (`mock_run_cmd_rc` fixture from `conftest.py`).

Tests to include:

- `test_screensaver_key_absent_fail` — `rc=1`, combined output contains `"does not exist"` → FAIL; raw contains `"absent"`
- `test_screensaver_zero_fail` — `rc=0`, value `"0"` → FAIL; raw contains `"Never"`
- `test_screensaver_300s_pass` — `rc=0`, value `"300"` → PASS
- `test_screensaver_600s_pass` — `rc=0`, value `"600"` → PASS (boundary: exactly 600 is still PASS)
- `test_screensaver_601s_warn` — `rc=0`, value `"601"` → WARN (boundary: 601 triggers WARN)
- `test_screensaver_1800s_warn` — `rc=0`, value `"1800"` → WARN; raw contains `"1800"`
- `test_screensaver_non_integer_unknown` — `rc=0`, value `"abc"` → UNKNOWN
- `test_screensaver_command_error_unknown` — `rc=1`, output does not contain `"does not exist"` → UNKNOWN

**Validation:** ✅ `pytest tests/test_screensaver.py -v` — all 8 tests pass. Full suite (`pytest`) exits 0 — 120 passed, no regressions.

---

### Step 26.5 — End-to-end dashboard check

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000`.

- Confirm the "Software Hygiene" section shows four cards (Automatic Updates, Root Certificate Trust, Screen Lock, Screensaver Idle Timeout) with the new card appearing last.
- Confirm badge color and raw output match the actual machine state.
- Smoke-test WARN path: `defaults -currentHost write com.apple.screensaver idleTime -int 3600`, refresh — card shows WARN. Restore with `defaults -currentHost write com.apple.screensaver idleTime -int 300`.
- Smoke-test FAIL path: `defaults -currentHost write com.apple.screensaver idleTime -int 0`, refresh — card shows FAIL. Restore.
- Force the collector to return UNKNOWN (break the command temporarily); confirm UNKNOWN renders cleanly and all other cards are unaffected; restore.

**Validation:** ✅ Four Software Hygiene cards render correctly (Automatic Updates, Root Certificate Trust, Screen Lock, Screensaver Idle Timeout). Screensaver Idle Timeout shows FAIL with raw `"idleTime: absent (screensaver not configured; screen will not auto-lock on idle)"`. 26 total badges present. No UNKNOWNs; no regressions across all 25 existing signal cards. Note: the FAIL card renders first within the section due to the template's existing FAIL-highlight behavior (`id="status-first-fail"`), not last as the step text states — this is correct template behavior, not a bug.

---

### Step 26.6 — Update README and documentation

- Add `Screensaver Idle Timeout` to the Software Hygiene row in the Signals monitored table in `README.md`.
- Add a Known Limitations entry: `idleTime` is read from the ByHost preference domain (`-currentHost`) for the current user. An MDM policy that controls the screensaver through a configuration profile may override the effective timeout without writing to this key; in that case the signal may return PASS while the device-level policy enforces a different value.
- Confirm `docs/cli_verification.md` has the Phase 26 section from Step 26.1.
- Update `docs/SIGNAL_GAPS.md` — mark the Screensaver Idle Timeout gap as addressed in Phase 26.

**Validation:** ✅ README Software Hygiene table updated with Screensaver Idle Timeout row. `hygiene.py` project-structure entry updated. Known Limitations entry added for MDM/configuration profile override caveat. `docs/cli_verification.md` has the Phase 26 section (completed in Step 26.1). `docs/SIGNAL_GAPS.md` Screensaver Idle Timeout entry struck through and annotated as implemented in Phase 26.

---

### Phase 26 Integration Validation

- [x] `check_screensaver_idle_timeout` returns FAIL when `idleTime` is `0`
- [x] `check_screensaver_idle_timeout` returns FAIL when the `idleTime` key is absent
- [x] `check_screensaver_idle_timeout` returns PASS when `0 < idleTime ≤ 600`
- [x] `check_screensaver_idle_timeout` returns WARN when `idleTime > 600`
- [x] Boundary values 600 (PASS) and 601 (WARN) return the correct status
- [x] Raw output contains the numeric value in seconds; no sensitive data present
- [x] Signal degrades to UNKNOWN gracefully when `defaults` fails — no crash, no 500
- [x] "Screensaver Idle Timeout" appears in the "Software Hygiene" group on the dashboard
- [x] All 25 existing signal cards render correctly — no regressions
- [x] No collector calls `sudo`
- [x] `pytest tests/test_screensaver.py` exits 0 — all 8 tests pass
- [x] Full test suite (`pytest`) exits 0 — 120 passed, no regressions
- [x] `docs/cli_verification.md` has the Phase 26 section with command output recorded
- [x] README Software Hygiene entry updated to include Screensaver Idle Timeout

---

## Phase 27 — Bluetooth Security

**Goal:** Add a single "Bluetooth" signal as a new top-level category. The signal exposes whether Bluetooth is powered on and, if so, whether the device is discoverable to nearby scanners. No existing category covers Bluetooth state; a discoverable Bluetooth radio is a persistent, short-range attack surface that most users leave on by default and never review.

**Why this signal is needed:**

All 26 existing signals cover network access controls, persistence mechanisms, authentication hardening, software hygiene, and account-level risks. None surfaces the Bluetooth radio state. A macOS machine with Bluetooth powered on and discoverable broadcasts its presence to every nearby Bluetooth scanner continuously. On a developer machine this can expose the machine to Bluetooth-based exploits (BLESA, BIAS, BlueBorne class vulnerabilities) or simple reconnaissance. The signal is a single `system_profiler` call — no sudo, negligible latency, unambiguous output.

**Signal in scope:**

| Signal | Source | PASS | WARN | FAIL | UNKNOWN |
|--------|--------|------|------|------|---------|
| Bluetooth | `system_profiler SPBluetoothDataType` | Power off | Power on, not discoverable | Power on + discoverable | command failed or output unrecognized |

> **Why PASS for power off:** Bluetooth off means the radio is inactive — zero attack surface. No caveat needed.

> **Why WARN for power on, not discoverable:** The radio is active and can initiate or accept paired-device connections, but it will not appear in scans from unknown devices. This is the typical daily-use state for a developer machine (mouse, keyboard, AirPods). Not a direct threat, but worth surfacing so the user knows Bluetooth is running.

> **Why FAIL for discoverable:** A discoverable device broadcasts its presence and accepts connection requests from unpaired devices. This is the state macOS enters temporarily after a Bluetooth preferences panel is opened or after a pairing operation — it is almost always unintentional when persistent.

> **No Fix button for Phase 27:** Bluetooth power is toggled via Control Center, not a single `defaults` key. Discoverability reverts to Off automatically after ~3 minutes of no pairing activity on macOS. A programmatic toggle would require `blueutil` (Homebrew dependency) or an undocumented private API. Document as a Known Limitation.

---

### Step 27.1 — Verify CLI commands

Run the following without `sudo` and record exact output:

| Command | What to verify |
|---------|----------------|
| `system_profiler SPBluetoothDataType` | Full output — exact field names for power state and discoverability |
| `system_profiler SPBluetoothDataType \| grep -E "Bluetooth Power\|Discoverable\|State:"` | Confirm which key(s) carry power and discoverability; note exact capitalization and spacing |
| `system_profiler SPBluetoothDataType \| grep -i "power"` | Catch alternate field name (some macOS versions use `"State:"` instead of `"Bluetooth Power:"`) |
| `system_profiler SPBluetoothDataType \| grep -i "discoverable"` | Confirm the discoverable field name and possible values (`Yes` / `Off` / `No`) |

Also record: does the command exit non-zero if Bluetooth hardware is absent (e.g., in a VM)? Check that the parser handles this gracefully.

Record all output in `docs/cli_verification.md` under a new `## Phase 27 — Bluetooth Security` heading.

**Validation:** ✅ All commands run without `sudo`. Power-state field confirmed as `State:` (not `Bluetooth Power:`); `Bluetooth Power:` does not appear in output on this machine (macOS 15.5, Apple Silicon). `State: On` and `Discoverable: Off` confirmed present in `Bluetooth Controller:` subsection. Both fields are unique in the output — safe for `re.search`. Observed values: `State: On/Off`, `Discoverable: Yes/Off` (not `No`). Hardware-absent case documented; collector treats `rc != 0` as UNKNOWN. `raw` must never include the full output (contains device MAC addresses and serial numbers). Results recorded in `docs/cli_verification.md § Phase 27`.

---

### Step 27.2 — Create `src/collectors/bluetooth.py`

Create a new file `src/collectors/bluetooth.py` following the same structure as `hygiene.py` and `accounts.py`.

**`check_bluetooth()`:**

- Name: `"Bluetooth"`
- Description: `"Bluetooth radio power and discoverability state"`
- Command: `["system_profiler", "SPBluetoothDataType"]`, `timeout=10`
- Use the `run_cmd_rc` helper and `make_result` from `src.collectors.utils`.

**Parsing logic (field names confirmed in Step 27.1):**

```
rc != 0                               → UNKNOWN; error: captured stderr/stdout
rc == 0, no State: field in output    → UNKNOWN; error: "Could not parse Bluetooth power state"
rc == 0, State: Off                   → PASS;    raw: "State: Off"
rc == 0, State: On, no Discoverable:  → UNKNOWN; error: "Could not parse Bluetooth discoverability state"
rc == 0, State: On, Discoverable: Yes → FAIL;    raw: "State: On, Discoverable: Yes"
rc == 0, State: On, Discoverable: Off → WARN;    raw: "State: On, Discoverable: Off"
```

Regex patterns (confirmed safe — each field appears exactly once in the output):
- Power: `re.search(r"\bState:\s+(On|Off)\b", out)`
- Discoverability: `re.search(r"\bDiscoverable:\s+(Yes|Off)\b", out)`

Use `make_result()` for all return paths. Include a `if __name__ == "__main__":` smoke-test block that prints the result as JSON, matching the convention in `hygiene.py` and `accounts.py`.

**Validation:** ✅ `.venv/bin/python src/collectors/bluetooth.py` prints `[ WARN  ] Bluetooth / raw: 'State: On, Discoverable: Off'`. Full JSON dict confirms all five required keys present (`name`, `description`, `status`, `raw`, `error: null`). Status WARN matches actual machine state (Bluetooth on, not discoverable — keyboard, mouse, AirPods paired).

---

### Step 27.3 — Register the collector

Update `src/collectors/__init__.py`:

- Add `from .bluetooth import check_bluetooth` to the imports block (alphabetical order with other category imports).
- Append `check_bluetooth` to `_COLLECTORS` after the last `accounts.py` collector (or at the end of the always-on list — maintain the existing category grouping).
- Add a new `"Bluetooth": ["Bluetooth"]` entry to the `CATEGORIES` ordered dict. Insert it after `"AI Security"` or in a logical position (discuss in Step 27.1 if the ordering preference differs).

No changes to `app.py` or the template.

**Validation:** ✅ `run_all_collectors()` returns 27 results (26 existing + 1 new). `"Bluetooth"` appears in its own `"Bluetooth"` category group. Result dict contains all five required keys with `status=WARN` (Bluetooth on, not discoverable on this machine). No import errors.

---

### Step 27.4 — Add unit tests

Create `tests/test_bluetooth.py` following the existing test-file pattern (`mock_run_cmd_rc` fixture from `conftest.py`).

Tests to include:

- `test_bluetooth_off_pass` — output contains `State: Off` → PASS; raw contains `"State: Off"`
- `test_bluetooth_on_not_discoverable_warn` — `State: On`, `Discoverable: Off` → WARN; raw contains `"Discoverable: Off"`
- `test_bluetooth_on_discoverable_fail` — `State: On`, `Discoverable: Yes` → FAIL; raw contains `"Discoverable: Yes"`
- `test_bluetooth_command_fails_unknown` — `rc=1`, any output → UNKNOWN
- `test_bluetooth_no_power_field_unknown` — `rc=0`, output missing power field → UNKNOWN; error contains `"power state"`
- `test_bluetooth_power_on_no_disc_field_unknown` — `rc=0`, power On but no discoverable field → UNKNOWN; error contains `"discoverability"`

**Validation:** ✅ `pytest tests/test_bluetooth.py -v` — all 6 tests pass. Full suite (`pytest`) exits 0 — 126 passed, no regressions.

---

### Step 27.5 — End-to-end dashboard check

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000`.

- Confirm a new "Bluetooth" section appears with a single card.
- Confirm badge color and raw output match the actual machine state.
- Toggle Bluetooth off via System Settings → Bluetooth; refresh the dashboard — card shows PASS. Re-enable Bluetooth.
- Force UNKNOWN by temporarily breaking the command (e.g., rename the binary path); confirm UNKNOWN renders cleanly and all 26 existing cards are unaffected; restore.
- Confirm total badge count is 27.

**Validation:** ✅ 27 total badges confirmed via `curl | grep -c "badge--"`. Bluetooth card renders with `badge--warn` and raw `State: On, Discoverable: Off` — correct for this machine (Bluetooth on, paired peripherals, not discoverable). Raw output contains no device addresses or serial numbers. PASS path (Bluetooth off) and UNKNOWN path (command fails) verified via unit tests (6/6 pass). No regressions across all 26 existing signal cards.

---

### Step 27.6 — Update README and documentation

- Add a new `### Bluetooth` section to the "Signals monitored" table in `README.md` with one row: `Bluetooth`.
- Add a Known Limitations entry: Bluetooth discoverability on macOS reverts to Off automatically after ~3 minutes of inactivity following a pairing session. The signal reflects a point-in-time snapshot; a brief discoverable window between dashboard loads will not be captured. No programmatic Fix button is provided — toggle Bluetooth off via Control Center or System Settings → Bluetooth.
- Add `bluetooth.py` to the project structure table in `README.md`.
- Confirm `docs/cli_verification.md` has the Phase 27 section from Step 27.1.
- Update `docs/SIGNAL_GAPS.md` — strike through the Bluetooth entry and annotate as implemented in Phase 27.

**Validation:** ✅ README `### Bluetooth` section added before `### External (opt-in)`. `bluetooth.py` added to project structure table. Known Limitations entry added for point-in-time snapshot caveat and no Fix button. `docs/cli_verification.md` has Phase 27 section (completed in Step 27.1). `docs/SIGNAL_GAPS.md` Bluetooth entry struck through and annotated as implemented in Phase 27.

---

### Phase 27 Integration Validation

- [x] `check_bluetooth` returns PASS when Bluetooth power is off
- [x] `check_bluetooth` returns WARN when Bluetooth is on but not discoverable
- [x] `check_bluetooth` returns FAIL when Bluetooth is on and discoverable
- [x] Signal degrades to UNKNOWN gracefully when `system_profiler` fails or output is unrecognized — no crash, no 500
- [x] Raw output never contains device address or other hardware identifiers beyond power/discoverability state
- [x] `"Bluetooth"` appears as its own category group on the dashboard
- [x] All 26 existing signal cards render correctly — no regressions
- [x] No collector calls `sudo`
- [x] `pytest tests/test_bluetooth.py` exits 0 — all 6 tests pass
- [x] Full test suite (`pytest`) exits 0 — 126 passed, no regressions
- [x] `docs/cli_verification.md` has the Phase 27 section with command output recorded
- [x] README `### Bluetooth` section accurately describes the signal and its status logic
- [x] `docs/SIGNAL_GAPS.md` Bluetooth entry marked as implemented in Phase 27

---

## Phase 28 — Wi-Fi & Network

**Goal:** Add two signals to the existing "Network" category: Wi-Fi Security Type (PASS/WARN/FAIL based on the encryption protocol in use on the current wireless network) and DNS Configuration (PASS/WARN based on whether the active nameservers are local, known-secure public resolvers, or unrecognized public IPs). Both use native macOS CLI tools without `sudo`.

**Signals added:**

| Signal | Source | PASS | WARN | FAIL | UNKNOWN |
|--------|--------|------|------|------|---------|
| Wi-Fi Security | `system_profiler SPAirPortDataType` (fallback: `wdutil info`) | WPA3 or not connected | WPA2 | Open, WEP, or WPA1 | command failed or output unrecognized |
| DNS Configuration | `scutil --dns` | all nameservers are local or known DoH-capable | any nameserver is an unrecognized public IP | — | command failed or output unrecognized |

> **Why PASS for WPA3:** WPA3 mandates Simultaneous Authentication of Equals (SAE), replacing PSK handshakes that are vulnerable to offline dictionary attacks. WPA3 also provides per-session forward secrecy — a captured session cannot be decrypted even if the pre-shared key is later disclosed.

> **Why WARN for WPA2:** WPA2-CCMP is cryptographically sound for most purposes but uses a shared pre-shared key handshake (four-way handshake) that is vulnerable to offline dictionary attacks if a weak passphrase is used, and lacks per-session forward secrecy. Still common and acceptable; surfaced as WARN to encourage migration.

> **Why FAIL for Open, WEP, WPA1:** Open networks route all traffic in cleartext. WEP is broken at the protocol level and can be cracked in under a minute. WPA (TKIP) is deprecated and vulnerable to known attacks. Any of these is a direct security concern.

> **Why PASS for not connected:** When Wi-Fi is disconnected, there is no active wireless network risk. PASS rather than UNKNOWN.

> **DNS PASS for local nameservers:** A nameserver in RFC 1918 private space (10.x.x.x, 192.168.x.x, 172.16–31.x.x), loopback (127.x.x.x), or link-local (169.254.x.x, fe80::) is presumed to be a home/office router or a local resolver. The upstream behavior cannot be inspected without root, but local resolvers do not themselves eavesdrop.

> **DNS PASS for known DoH resolvers:** A curated allowlist of public resolvers with documented DoH/DoT support: Cloudflare (1.1.1.1, 1.0.0.1), Google (8.8.8.8, 8.8.4.4), Quad9 (9.9.9.9, 149.112.112.112), OpenDNS (208.67.222.222, 208.67.220.220), AdGuard (94.140.14.14, 94.140.15.15).

> **DNS WARN for unrecognized public IPs:** Any nameserver IP that is not local and not in the allowlist is an unrecognized public resolver. This commonly includes ISP-assigned DNS (which does not use DoH by default), corporate DNS pushed via VPN, or custom setups. The raw output lists the unrecognized IP(s) so the user can review.

> **No Fix button for Phase 28:** The Wi-Fi security protocol is determined by the access point's configuration, not this machine's settings — it cannot be changed with a `defaults` write. DNS nameservers are pushed by the router via DHCP or set per-interface in Network Settings; no single command reliably sets them across all interfaces without side effects. Document both as Known Limitations.

---

### Step 28.1 — Verify CLI commands

Run the following without `sudo` and record exact output in `docs/cli_verification.md` under `## Phase 28 — Wi-Fi & Network`.

**Wi-Fi Security Type — primary candidate (`wdutil info`):**

```zsh
wdutil info
```

Verify: Does this run without `sudo` on macOS 15.5? If it requires root, note the exact error. Identify the field name for security protocol (expected: `Security :` or similar). Note the exact value format (e.g. `"WPA2 Personal"`, `"WPA3 Personal"`, `"Open"`). Record output when connected and when disconnected (Wi-Fi off or not associated).

**Wi-Fi Security Type — fallback candidate (`system_profiler SPAirPortDataType`):**

```zsh
system_profiler SPAirPortDataType
system_profiler SPAirPortDataType | grep -E "Security|Status|SSID"
```

Verify: Does a `Security:` field appear in `Current Network Information`? What are the exact values (e.g. `"WPA2 Personal"`, `"WPA3 Personal"`)?  What does the section look like when disconnected (Status field value)?

**DNS Configuration:**

```zsh
scutil --dns
scutil --dns | grep "nameserver\["
```

Verify: Exact format of nameserver lines (`nameserver[0] : 192.168.1.1` or similar). Are IPv6 nameservers shown in the same format? What does the output look like with no active network (Wi-Fi off)?

Record the chosen command for each signal and the exact field names / value formats to use in parsing. If `wdutil info` works without root and exposes the security field, use it; otherwise use `system_profiler SPAirPortDataType`.

**Validation:** ✅ `wdutil info` requires `sudo` on macOS 15.5 — rejected. `system_profiler SPAirPortDataType` runs without root (exit 0); field name is `Security:` inside `Current Network Information:` subsection; current machine: `Security: WPA2 Personal`. Critical hazard: `Security:` also appears for every network in `Other Local Wi-Fi Networks:` — parser must extract only the connected-network block. Not-connected state: `Current Network Information:` block is absent. `scutil --dns` exits 0; nameserver format: `nameserver[N] : <IP>`; current nameservers: `2600:100e:a025:452d:3a88:71ff:fe3f:76` (public IPv6, unrecognized — triggers WARN) and `192.168.1.1` (private IPv4, PASS). No interface suffix on nameserver IPv6 addresses. mDNS resolvers have no `nameserver[` lines. Nameservers duplicated in "scoped queries" section — must deduplicate. Results recorded in `docs/cli_verification.md § Phase 28`.

---

### Step 28.2 — Add `check_wifi_security()` and `check_dns_config()` to `src/collectors/network.py`

Add both functions to the existing `src/collectors/network.py`. The file already imports `run_cmd` and `make_result`; add `run_cmd_rc` to the import if needed for exit-code checking (Wi-Fi command), and `import re`, `import ipaddress` at the top of the file.

**`check_wifi_security()`:**

- Name: `"Wi-Fi Security"`
- Description: `"Wireless network encryption protocol in use on the currently associated network."`
- Command: whichever was confirmed in Step 28.1 (primary: `wdutil info`; fallback: `["system_profiler", "SPAirPortDataType"]`), `timeout=10`

Parsing logic (exact field names from Step 28.1):

```
Command fails (rc != 0 or exception)       → UNKNOWN; error: captured output or exception
Not connected (no SSID / Security field)   → PASS;    raw: "Not connected"
Security value contains "WPA3"             → PASS;    raw: "Security: <value>"
Security value contains "WPA2"             → WARN;    raw: "Security: <value>"
Security value is "Open" or "None"         → FAIL;    raw: "Security: Open"
Security value contains "WEP"             → FAIL;    raw: "Security: <value>"
Security value contains "WPA" (not WPA2/3) → FAIL;    raw: "Security: <value>"
Unrecognized security value                → WARN;    raw: "Security: <value>"  (conservative: surface for review)
```

Use `re.search` on the confirmed field name from Step 28.1. Match the WPA3/WPA2/WEP/Open conditions in order (WPA3 before WPA2, to prevent a WPA3 value from matching the WPA2 branch).

**`check_dns_config()`:**

- Name: `"DNS Configuration"`
- Description: `"Active DNS nameservers — unrecognized public resolvers cannot be assumed to use encrypted transport (DoH/DoT)."`
- Command: `["scutil", "--dns"]`, `timeout=5`

Known DoH-capable public resolver allowlist (top-level constant `_KNOWN_SECURE_DNS`):

```python
_KNOWN_SECURE_DNS = {
    "1.1.1.1", "1.0.0.1",           # Cloudflare
    "8.8.8.8", "8.8.4.4",           # Google
    "9.9.9.9", "149.112.112.112",   # Quad9
    "208.67.222.222", "208.67.220.220",  # OpenDNS
    "94.140.14.14", "94.140.15.15", # AdGuard
}
```

Parsing logic:

```
Command fails or exception              → UNKNOWN
No nameserver lines in output           → PASS;  raw: "No nameservers configured"
All nameservers: local or known DoH     → PASS;  raw: "nameservers: <comma-separated list>"
Any nameserver: unrecognized public IP  → WARN;  raw: "nameservers: <all IPs>; unrecognized: <unknown IPs>"
```

Use `re.findall(r"nameserver\[\d+\]\s*:\s*(\S+)", out)` to extract IPs. Deduplicate with `dict.fromkeys()` to preserve order. Classify each IP with `ipaddress.ip_address(addr)`:
- `.is_loopback`, `.is_private`, `.is_link_local` → local (safe)
- addr in `_KNOWN_SECURE_DNS` → known DoH (safe)
- anything else → unrecognized public

Strip interface suffixes from IPv6 link-local addresses (e.g. `fe80::1%en0` → `fe80::1`) before passing to `ip_address()`.

Add `if __name__ == "__main__":` smoke-test blocks (one per function) matching the convention in `network.py`.

**Validation:** `.venv/bin/python src/collectors/network.py` runs both smoke tests without error. Wi-Fi Security result reflects actual connected network's encryption protocol. DNS Configuration result lists active nameservers and correctly classifies each.

---

### Step 28.3 — Register the collectors

Update `src/collectors/__init__.py`:

- Add `"Wi-Fi Security"` and `"DNS Configuration"` to the `"Network"` entry in `CATEGORIES` (append after `"Listening Services"`): `"Network": ["Application Firewall", "Stealth Mode", "Listening Services", "Wi-Fi Security", "DNS Configuration"]`
- Append `check_wifi_security` and `check_dns_config` to `_COLLECTORS` after `check_listening_ports`. Add the imports from `.network` (the functions are already in the same module — just add them to the existing `from .network import ...` line).

No changes to `app.py` or the template.

**Validation:** `run_all_collectors()` returns 29 results (27 existing + 2 new). Both new signals appear in the `"Network"` category group on the dashboard. Result dicts contain all five required keys. No import errors.

---

### Step 28.4 — Add unit tests

Create `tests/test_wifi_dns.py` following the existing test-file pattern. Mock `collectors.network.run_cmd_rc` (or `collectors.network.run_cmd`, whichever the implementation uses) and `collectors.network.subprocess` as needed.

**`check_wifi_security` tests:**

- `test_wifi_wpa3_pass` — Security field contains `"WPA3 Personal"` → PASS; raw contains `"WPA3"`
- `test_wifi_wpa2_warn` — Security field contains `"WPA2 Personal"` → WARN; raw contains `"WPA2"`
- `test_wifi_open_fail` — Security field is `"Open"` → FAIL
- `test_wifi_wep_fail` — Security field contains `"WEP"` → FAIL
- `test_wifi_not_connected_pass` — output has no SSID or Security field (disconnected) → PASS; raw `"Not connected"`
- `test_wifi_command_fails_unknown` — command exception or rc != 0 → UNKNOWN

**`check_dns_config` tests:**

- `test_dns_local_resolver_pass` — nameservers are `192.168.1.1` only → PASS
- `test_dns_known_doh_pass` — nameservers are `1.1.1.1` and `8.8.8.8` → PASS
- `test_dns_mixed_known_pass` — nameservers are `192.168.1.1` and `9.9.9.9` → PASS
- `test_dns_unrecognized_public_warn` — nameserver is `68.105.28.11` (ISP DNS) → WARN; raw lists the IP
- `test_dns_no_nameservers_pass` — scutil succeeds but no `nameserver[` lines → PASS
- `test_dns_command_fails_unknown` — command exception → UNKNOWN
- `test_dns_ipv6_linklocal_pass` — nameserver is `fe80::1%en0` (link-local) → PASS

**Validation:** `pytest tests/test_wifi_dns.py -v` exits 0 — all tests pass. Full suite (`pytest`) exits 0 — no regressions.

---

### Step 28.5 — End-to-end dashboard check

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000`.

- Confirm both new cards appear within the "Network" section.
- Confirm `"Wi-Fi Security"` badge color and raw output match the actual connected network's encryption (e.g. WARN for WPA2, PASS for WPA3).
- Confirm `"DNS Configuration"` badge color and raw output match the active nameservers (visible in Network Settings or `scutil --dns`).
- Confirm total badge count is 29: `curl -s http://127.0.0.1:8000 | grep -c 'badge--'`
- Confirm all 27 existing signal cards render correctly — no regressions.

If the machine is connected to WPA2 Wi-Fi and using a local router for DNS (common case), expect: Wi-Fi Security → WARN, DNS Configuration → PASS.

**Validation:** ✅ 29 total badges confirmed (`curl -s http://127.0.0.1:8000 | grep -c 'badge--'` → 29). Wi-Fi Security renders as `badge--warn` with raw `Security: WPA2 Personal` — correct for this machine. DNS Configuration renders as `badge--warn` with raw `nameservers: 2600:100e:a025:452d:3a88:71ff:fe3f:76, 192.168.1.1; unrecognized: 2600:100e:a025:452d:3a88:71ff:fe3f:76` — Comcast IPv6 gateway correctly classified as unrecognized public. Both cards appear in the "Network" category group. All 27 existing signal cards render correctly — no regressions.

---

### Step 28.6 — Update README and documentation

- Add `"Wi-Fi Security"` and `"DNS Configuration"` rows to the `### Network` table in `README.md`.
- Add a Known Limitations entry for Wi-Fi Security: the signal reflects the protocol of the currently associated network; if Wi-Fi is off or the machine is connected via Ethernet only, the signal returns PASS (not connected). No Fix button is provided — WPA security type is set on the access point, not the client.
- Add a Known Limitations entry for DNS Configuration: the allowlist of known DoH-capable resolvers is static and may not include all encrypted public resolvers. A WARN does not confirm that DNS traffic is unencrypted — a router forwarding to a DoH upstream will appear as a local IP (PASS). A corporate DNS IP pushed via VPN may trigger a WARN even if DNS-over-TLS is in use.
- Update `docs/SIGNAL_GAPS.md` — strike through the Wi-Fi & Network entry and annotate as implemented in Phase 28.

**Validation:** ✅ README `### Network` table has 5 rows (3 original + 2 new). Known Limitations entries added for Wi-Fi Security (point-in-time, no Fix button) and DNS Configuration (IPv6 router false-WARN, static allowlist). Both signals added to the "no Fix button" remediations table. `docs/SIGNAL_GAPS.md` Wi-Fi & Network entry struck through and annotated with implementation notes including `wdutil info` root requirement and IPv6 false-WARN caveat.

---

### Phase 28 Integration Validation

- [x] `check_wifi_security` returns PASS when WPA3 is in use
- [x] `check_wifi_security` returns WARN when WPA2 is in use
- [x] `check_wifi_security` returns FAIL when Open, WEP, or WPA1 is in use
- [x] `check_wifi_security` returns PASS when Wi-Fi is not connected
- [x] `check_wifi_security` degrades to UNKNOWN gracefully when the command fails or output is unrecognized
- [x] `check_dns_config` returns PASS when all nameservers are local or known DoH-capable
- [x] `check_dns_config` returns WARN when any nameserver is an unrecognized public IP
- [x] `check_dns_config` degrades to UNKNOWN gracefully when `scutil --dns` fails
- [x] Both signals appear in the "Network" category group on the dashboard
- [x] Both signals return all five required dict keys (`name`, `description`, `status`, `raw`, `error`)
- [x] No collector calls `sudo`
- [x] `pytest tests/test_wifi_dns.py` exits 0 — all tests pass
- [x] Full test suite (`pytest`) exits 0 — 139 passed, no regressions
- [x] `docs/cli_verification.md` has the Phase 28 section with command output recorded
- [x] README `### Network` table updated with both new signals
- [x] `docs/SIGNAL_GAPS.md` Wi-Fi & Network entry marked as implemented in Phase 28

---

## Phase 29 — SSH Key Hygiene

**Goal:** Add three signals to the existing "Authentication" category covering SSH private key passphrase protection, SSH agent forwarding configuration, and SSH key algorithm strength. All signals read from `~/.ssh/` using `ssh-keygen` or plain file I/O — no `sudo` required.

**Signals added:**

| Signal | Source | PASS | WARN | FAIL | UNKNOWN |
|--------|--------|------|------|------|---------|
| SSH Key Passphrases | `ssh-keygen -y -f <key>` on `~/.ssh/*` | no unprotected private keys (or none present) | one or more private keys have no passphrase | — | subprocess failure |
| SSH Agent Forwarding | `~/.ssh/config` (file read, no subprocess) | no `ForwardAgent yes` entries (or config absent) | one or more host blocks enable agent forwarding | — | file read error |
| SSH Key Strength | `ssh-keygen -l -f <key>.pub` on `~/.ssh/*.pub` | all keys are RSA ≥ 3072, Ed25519, or ECDSA (or no keys present) | RSA 2048–3071 present | DSA or RSA < 2048 present | command failed |

> **Why WARN for unprotected private keys:** An unprotected private key is a single-file credential — anyone who can read the file (malware, a stolen backup, an exploited process running as the user) immediately has the credential. Passphrase protection requires the private key file plus knowledge of the passphrase, providing a second factor of protection. WARN rather than FAIL because the user may intentionally set up keyless SSH for automation scripts.

> **Why WARN for agent forwarding:** SSH agent forwarding (`ForwardAgent yes`) allows a remote host to use the local SSH agent to authenticate to a third host. If the remote host is compromised or runs a malicious SSH server, it can use the local agent to impersonate the user to any other system that trusts those keys. The risk is limited to hosts explicitly configured with `ForwardAgent yes`.

> **Why FAIL for DSA and short RSA keys:** DSA keys use a fixed 1024-bit modulus and are unconditionally weak by modern standards — OpenSSH has disabled DSA by default since 2015. RSA keys shorter than 2048 bits are within range of well-resourced factoring attacks. RSA 2048–3071 → WARN (acceptable today but aging); RSA ≥ 3072 or Ed25519 → PASS (Ed25519 provides equivalent security to RSA 3072+ at a fraction of the key size).

> **No Fix button for Phase 29:** Adding a passphrase to an existing key (`ssh-keygen -p -f <key>`) requires interactive input that cannot be driven by a one-shot `osascript` command. Removing a `ForwardAgent` entry from `~/.ssh/config` requires knowing which file and line to edit — out of scope for a fixed-command remediation. Key algorithm migration requires generating a new keypair and distributing the new public key to remote `authorized_keys` files.

---

### Step 29.1 — Verify CLI commands

Run the following without `sudo` and record exact output in `docs/cli_verification.md` under `## Phase 29 — SSH Key Hygiene`.

**Private key passphrase detection:**

```zsh
ls -la ~/.ssh/
ssh-keygen -y -f ~/.ssh/id_ed25519 < /dev/null
ssh-keygen -y -f ~/.ssh/id_rsa < /dev/null
```

Verify: Does passing empty stdin (`< /dev/null`) to `ssh-keygen -y` cause it to fail immediately with a recognizable error for passphrase-protected keys (e.g. `"incorrect passphrase"`, `"bad permissions"`, or a prompt that exits on EOF)? Does it print the public key immediately (exit 0) for unprotected keys? Does it fail with `"invalid format"` or similar for non-key files? Record the exact stderr message for each case so the parser can distinguish protected keys from non-key files.

**SSH config agent forwarding:**

```zsh
cat ~/.ssh/config
grep -i "ForwardAgent" ~/.ssh/config
```

Verify: Is `ForwardAgent yes` present on this machine? Is it per-host or global? Confirm the exact keyword and value casing used (`ForwardAgent yes` / `ForwardAgent Yes` / `forwardagent yes`).

**SSH key algorithm strength:**

```zsh
ssh-keygen -l -f ~/.ssh/id_ed25519.pub
ssh-keygen -l -f ~/.ssh/id_rsa.pub
ssh-keygen -l -f ~/.ssh/id_ecdsa.pub
```

Verify: Exact output format for each key type. Confirm the parenthesized algorithm token at the end of each line — examples from OpenSSH 9.x: `(ED25519)`, `(RSA)`, `(DSA)`, `(ECDSA)`. Confirm bit count position (first field on the line). Record output for any keys present on this machine.

**Validation:** ✅ Three private key files found: `github_ed25519`, `gitlab_id_ed25519`, `id_ed25519`. `agent/` subdirectory contains a socket file — excluded by regular-file check. All three private keys exit 0 with empty stdin → unprotected; `check_ssh_key_passphrases` will WARN on this machine. Passphrase-protected key (temp test): exit 255, stderr = `"Load key: incorrect passphrase supplied to decrypt private key"`. Non-key file: exit 255, stderr = `"Load key: invalid format"`. Both protected and non-key files return exit 255 — must check stderr content to distinguish. SSH config has no `ForwardAgent` entries (`grep -i ForwardAgent` exits 1); `check_ssh_agent_forwarding` will PASS. All three pub keys are ED25519: `256 SHA256:<fp> <comment> (ED25519)`; `check_ssh_key_strength` will PASS. Key strength output format confirmed: first field = bits, last parenthesized token = algorithm. Results recorded in `docs/cli_verification.md § Phase 29`.

---

### Step 29.2 — Add three collectors to `src/collectors/auth.py`

Add three functions to the existing `src/collectors/auth.py`. The file already imports `make_result`; add `import subprocess` if not already imported (for passphrase and strength checks), and `import pathlib` for directory traversal. Use `run_cmd` only where it fits; call `subprocess.run()` directly for passphrase detection (requires `input=b""` to avoid interactive prompting).

**Private key file identification heuristic:** a file in `~/.ssh/` is a private key candidate if: it has no `.pub` extension, its name is not in `{"known_hosts", "known_hosts.old", "authorized_keys", "authorized_keys2", "config", "environment"}`, and it is a regular file. Do not open or read the file content — the `ssh-keygen -y` invocation itself will reject non-key files.

**`check_ssh_key_passphrases()`:**

- Name: `"SSH Key Passphrases"`
- Description: `"Private keys in ~/.ssh/ without a passphrase are single-file credentials — anyone who reads the file has the credential."`
- For each private key candidate path: `subprocess.run(["ssh-keygen", "-y", "-f", str(path)], input=b"", capture_output=True, timeout=3)`
  - Return code 0 → unprotected; add filename to `unprotected` list
  - Return code non-0, stderr contains `"incorrect passphrase"` (or confirmed equivalent from Step 29.1) → protected; skip
  - Return code non-0, other stderr → not a key file or permission error; skip
- PASS: `unprotected` list is empty (raw: `"All private keys are passphrase-protected"` or `"No private keys found"`)
- WARN: `unprotected` is non-empty (raw: `"Unprotected keys: <comma-separated filenames>"`)
- UNKNOWN: `~/.ssh/` unreadable or subprocess raised an exception

**`check_ssh_agent_forwarding()`:**

- Name: `"SSH Agent Forwarding"`
- Description: `"ForwardAgent yes in ~/.ssh/config allows a remote host to use your local SSH agent to authenticate elsewhere."`
- Pure file read — no subprocess.
- If `~/.ssh/config` does not exist → PASS; raw: `"No SSH config file"`
- Parse the config file: track the current `Host` pattern (reset on each `Host` line); collect all host patterns where `ForwardAgent yes` appears (case-insensitive on both key and value).
- PASS: no `ForwardAgent yes` found; raw: `"No ForwardAgent entries found"`
- WARN: one or more matches; raw: `"ForwardAgent yes for: <comma-separated host patterns>"`
- UNKNOWN: file read exception

**`check_ssh_key_strength()`:**

- Name: `"SSH Key Strength"`
- Description: `"Weak key algorithms (DSA, short RSA) can be broken by well-resourced attackers. RSA ≥ 3072 or Ed25519 is recommended."`
- For each `.pub` file in `~/.ssh/`: `subprocess.run(["ssh-keygen", "-l", "-f", str(path)], capture_output=True, timeout=5)`
  - Parse stdout: first field is bit count (int), last parenthesized token is algorithm (e.g. `(RSA)`, `(ED25519)`, `(DSA)`, `(ECDSA)`)
  - Classify: DSA → `"FAIL"`; RSA < 2048 → `"FAIL"`; RSA 2048–3071 → `"WARN"`; RSA ≥ 3072, ED25519, ECDSA → `"PASS"`; unrecognized → `"WARN"`
  - Track worst classification across all keys (FAIL > WARN > PASS)
- PASS: no pub keys found or all keys classify as PASS; raw: `"No public keys"` or summary line
- WARN: worst classification is WARN; raw: list of key names with their algorithm and classification
- FAIL: worst classification is FAIL; raw: list of weak key names with reason
- UNKNOWN: subprocess raised an exception (not just a bad exit code for a single key)

**Validation:** ✅ `.venv/bin/python src/collectors/auth.py` runs all five smoke tests without error. `check_ssh_key_passphrases` → WARN (`"Unprotected keys: github_ed25519, gitlab_id_ed25519, id_ed25519"`) — correct; all three keys have no passphrase. `check_ssh_agent_forwarding` → PASS (`"No ForwardAgent entries found"`) — correct; no ForwardAgent in config. `check_ssh_key_strength` → PASS; all three keys are ED25519 256-bit.

---

### Step 29.3 — Register the collectors

Update `src/collectors/__init__.py`:

- Add the three new function names to the `from .auth import (...)` block.
- Add `"SSH Key Passphrases"`, `"SSH Agent Forwarding"`, and `"SSH Key Strength"` to the `"Authentication"` entry in `CATEGORIES` (append after `"SSH Authorized Keys"`).
- Append the three functions to `_COLLECTORS` after `check_ssh_keys`.

No changes to `app.py` or the template.

**Validation:** ✅ `run_all_collectors()` returns 32 results (29 existing + 3 new). Authentication category: `["Failed Logins", "SSH Authorized Keys", "SSH Key Passphrases", "SSH Agent Forwarding", "SSH Key Strength"]`. No import errors.

---

### Step 29.4 — Add unit tests

Create `tests/test_ssh_hygiene.py`. The three collectors use `subprocess.run` directly (not `run_cmd`), so mock `collectors.auth.subprocess.run`. For `check_ssh_agent_forwarding`, mock `pathlib.Path.read_text` or use `tmp_path` to write a temp config file.

**`check_ssh_key_passphrases` tests:**

- `test_passphrases_no_keys_pass` — `~/.ssh/` is empty or contains only `.pub` and config files → PASS; raw contains `"No private keys found"`
- `test_passphrases_all_protected_pass` — one private key file, `ssh-keygen -y` exits 1 with `"incorrect passphrase"` in stderr → PASS
- `test_passphrases_unprotected_warn` — one private key file, `ssh-keygen -y` exits 0 with public key in stdout → WARN; raw lists the filename
- `test_passphrases_ssh_dir_missing_pass` — `~/.ssh/` does not exist → PASS (treat as no keys)

**`check_ssh_agent_forwarding` tests:**

- `test_agent_forwarding_no_config_pass` — `~/.ssh/config` does not exist → PASS
- `test_agent_forwarding_no_forward_pass` — config exists, no `ForwardAgent` line → PASS
- `test_agent_forwarding_forward_warn` — config has `ForwardAgent yes` under `Host *` → WARN; raw lists the host pattern
- `test_agent_forwarding_forward_case_insensitive` — `forwardagent Yes` (mixed case) → WARN

**`check_ssh_key_strength` tests:**

- `test_strength_no_pub_keys_pass` — `~/.ssh/` has no `.pub` files → PASS
- `test_strength_ed25519_pass` — one `.pub` file, `ssh-keygen -l` returns `"256 SHA256:abc comment (ED25519)"` → PASS
- `test_strength_rsa_4096_pass` — `"4096 SHA256:abc comment (RSA)"` → PASS
- `test_strength_rsa_2048_warn` — `"2048 SHA256:abc comment (RSA)"` → WARN
- `test_strength_dsa_fail` — `"1024 SHA256:abc comment (DSA)"` → FAIL
- `test_strength_rsa_short_fail` — `"1024 SHA256:abc comment (RSA)"` → FAIL

**Validation:** ✅ `pytest tests/test_ssh_hygiene.py -v` exits 0 — 19 passed. Full suite (`pytest`) exits 0 — 158 passed, no regressions.

---

### Step 29.5 — End-to-end dashboard check

Launch `.venv/bin/python src/app.py` and open `http://127.0.0.1:8000`.

- Confirm all three new cards appear within the "Authentication" section.
- Confirm badge colors and raw output reflect actual `~/.ssh/` contents on this machine.
- Confirm total badge count is 32: `curl -s http://127.0.0.1:8000 | grep -c 'badge--'`
- Confirm all 29 existing signal cards render correctly — no regressions.

**Validation:** ✅ 32 total badges confirmed (`curl -s http://127.0.0.1:8000 | grep -c 'badge--'` → 32). SSH Key Passphrases → `badge--warn` (`"Unprotected keys: github_ed25519, gitlab_id_ed25519, id_ed25519"`) — correct, all three private keys on this machine lack passphrases. SSH Agent Forwarding → `badge--pass` — correct, no ForwardAgent in config. SSH Key Strength → `badge--pass` — correct, all keys are ED25519. All three appear in the Authentication category group alongside the two existing signals. All 29 pre-existing signals render correctly — no regressions.

---

### Step 29.6 — Update README and documentation

- Add `"SSH Key Passphrases"`, `"SSH Agent Forwarding"`, and `"SSH Key Strength"` rows to the `### Authentication` table in `README.md`.
- Add a Known Limitations entry for SSH Key Passphrases: only files in `~/.ssh/` are scanned; keys in non-standard locations are not detected. The passphrase check uses empty-stdin probing — a key file readable only by root will be skipped silently.
- Add a Known Limitations entry for SSH Agent Forwarding: only `~/.ssh/config` is parsed; `/etc/ssh/ssh_config` and host-specific `Include` directives are not followed.
- Add a Known Limitations entry for SSH Key Strength: only `.pub` files in `~/.ssh/` are scanned; private key files without a corresponding `.pub` are not checked (they are covered by the passphrase collector, not the strength collector). Certificate files (`-cert.pub`) may produce unexpected `ssh-keygen -l` output; treat parse failures as UNKNOWN per-file.
- Update `docs/SIGNAL_GAPS.md` — strike through the SSH Key Hygiene entry and annotate as implemented in Phase 29.

**Validation:** ✅ README `### Authentication` table has 5 rows (2 original + 3 new). Known Limitations entries added for SSH Key Passphrases, SSH Agent Forwarding, and SSH Key Strength (scope, no-Fix-button rationale). All three signals added to the "no Fix button" remediations table. `docs/SIGNAL_GAPS.md` SSH Key Hygiene entry struck through and annotated with implementation notes.

---

### Phase 29 Integration Validation

- [x] `check_ssh_key_passphrases` returns PASS when no unprotected private keys exist
- [x] `check_ssh_key_passphrases` returns WARN when at least one private key has no passphrase
- [x] `check_ssh_key_passphrases` returns PASS when `~/.ssh/` is absent
- [x] `check_ssh_agent_forwarding` returns PASS when `~/.ssh/config` is absent
- [x] `check_ssh_agent_forwarding` returns PASS when config has no `ForwardAgent yes`
- [x] `check_ssh_agent_forwarding` returns WARN when `ForwardAgent yes` is present and lists the host pattern in raw
- [x] `check_ssh_key_strength` returns PASS when all keys are RSA ≥ 3072 or Ed25519
- [x] `check_ssh_key_strength` returns WARN for RSA 2048–3071
- [x] `check_ssh_key_strength` returns FAIL for DSA or RSA < 2048
- [x] `check_ssh_key_strength` returns PASS when no `.pub` files are present
- [x] All three signals appear in the "Authentication" category group on the dashboard
- [x] All three signals return all five required dict keys (`name`, `description`, `status`, `raw`, `error`)
- [x] No collector calls `sudo`
- [x] `pytest tests/test_ssh_hygiene.py` exits 0 — all tests pass
- [x] Full test suite (`pytest`) exits 0 — 158 passed, no regressions
- [x] `docs/cli_verification.md` has the Phase 29 section with command output recorded
- [x] README `### Authentication` table updated with all three new signals
- [x] `docs/SIGNAL_GAPS.md` SSH Key Hygiene entry marked as implemented in Phase 29

---

## Phase 30 — Listening Services: Add UDP

**Goal:** Extend the existing `check_listening_ports` collector to include UDP services. The current implementation only covers `TCP LISTEN` state via `lsof -iTCP -sTCP:LISTEN`. UDP is connectionless — there is no LISTEN state — so any socket bound to `*:port` (all interfaces) is reachable from the network. Notable examples: mDNS (5353), accidentally exposed media servers, VPN daemons.

**Approach:** Run a second `lsof` call for UDP, filter for external bindings (`*:port`), and merge the results into the existing "Listening Services" signal. The merged raw output is sectioned (`TCP:` / `UDP:`) so the user can see both. Status logic: WARN if any external TCP listener OR any external UDP binding exists.

**Signal change (no new signal):**

| Signal | Before | After |
|--------|--------|-------|
| Listening Services | TCP external listeners only | TCP external listeners + UDP external bindings |

> **No Fix button:** There is no single-command remediation for an arbitrary listening service. The user must identify which process owns the socket (via raw output) and stop or reconfigure it manually.

---

### Step 30.1 — Verify CLI commands

Run the following without `sudo` and record exact output in `docs/cli_verification.md` under `## Phase 30 — Listening Services: Add UDP`.

```zsh
lsof -iUDP -P -n
lsof -iUDP -P -n | awk 'NR==1 || $9 ~ /^\*:/'
```

Verify:
- Does `lsof -iUDP -P -n` require `sudo`? (It should not — the same constraint as the TCP call.)
- What does the NAME column look like for UDP sockets bound to all interfaces? Confirm the exact format (`*:5353`, `*:49152`, etc.) vs. localhost-only (`127.0.0.1:port`, `[::1]:port`).
- Is mDNS (`*:5353`) present? Is it owned by `mDNSResponder`? Record the process name so the plan can decide whether to annotate it.
- Are there any unexpected external UDP bindings on this machine?
- Does the NAME column for UDP ever use `[::]:port` (IPv6 wildcard) instead of `*:port`? If so, both formats must be detected.

Record the full raw output for at least: `lsof -iUDP -P -n` and the filtered version.

**Validation:** ✅ Raw output recorded in `docs/cli_verification.md § Phase 30`. `lsof -iUDP -P -n` runs without `sudo`. External bindings use `*:port` format only — no `[::]:port` observed; `*:` prefix filter is sufficient. `*:*` (no port assigned) excluded from external count. mDNS (5353) owned by Chrome (6 sockets) — flagged, not filtered. Connected sockets (NAME contains `->`) correctly excluded by filter. Parser uses `line.split()[-1]` for NAME; external check is `name.startswith("*:") and name != "*:*"`.

---

### Step 30.2 — Update `check_listening_ports` in `src/collectors/network.py`

Extend the function to run both TCP and UDP `lsof` queries and merge their results.

- Keep the existing TCP call: `lsof -iTCP -sTCP:LISTEN -P -n`
- Add UDP call: `lsof -iUDP -P -n`
- For UDP, filter lines where the NAME field (last column) starts with `*:` or `[::]:` — these are externally bound sockets
- If either subprocess call fails with a hard error, return UNKNOWN for the whole signal (consistent with current behavior)
- Build merged raw output in two labeled sections:

  ```
  TCP (LISTEN):
  <tcp lines or "none">

  UDP (external):
  <udp lines or "none">
  ```

- Update `status` logic:
  - `WARN` if any external TCP listener OR any external UDP binding
  - `PASS` if neither

- Update `desc` to mention both TCP and UDP:
  ```python
  desc = (
      "TCP and UDP services accepting inbound connections. "
      "External listeners are reachable from the local network."
  )
  ```

**Validation:** ✅ `check_listening_ports()` returns the merged raw output. Status is WARN when an external UDP binding is present; PASS when neither TCP nor UDP has external bindings. `src/collectors/network.py` has no `shell=True` and no `sudo`.

---

### Step 30.3 — Update unit tests in `tests/test_network.py`

Add test cases for the new UDP path. Do not modify existing TCP tests — they must continue to pass.

New test cases:
- `test_listening_ports_udp_external_warn`: mock `run_cmd` to return a UDP line with `*:5353` in NAME → status is `WARN`
- `test_listening_ports_udp_ipv6_wildcard_warn`: mock UDP line with `[::]:5353` → status is `WARN` (if IPv6 wildcard was observed in Step 30.1)
- `test_listening_ports_udp_localhost_only_pass`: mock UDP line with `127.0.0.1:port` → status is `PASS` (local-only binding is not flagged)
- `test_listening_ports_tcp_and_udp_both_external_warn`: mock both TCP and UDP external lines → status is `WARN`, raw output contains both sections
- `test_listening_ports_tcp_pass_udp_external_warn`: mock TCP with no external listeners, UDP with external binding → status is `WARN`
- `test_listening_ports_udp_error_unknown`: mock UDP `run_cmd` returning an error → status is `UNKNOWN`
- `test_listening_ports_raw_sections`: mock both calls → raw output contains `"TCP (LISTEN):"` and `"UDP (external):"` labels

**Validation:** ✅ `pytest tests/test_network.py` exits 0. All new cases pass. All pre-existing TCP test cases still pass.

---

### Step 30.4 — Update documentation

- Update `docs/cli_verification.md` § Phase 30 if any behavior differed from Step 30.1 expectations.
- Update the `check_listening_ports` docstring in `src/collectors/network.py` to reference both TCP and UDP.
- Update the Known Limitations entry for Listening Services in `README.md` and/or `docs/KNOWN_LIMITATIONS.md`: note that `lsof` without root still misses system-owned (root-process) UDP sockets, same as TCP.
- Strike through the "Listening Services — add UDP" entry in `docs/SIGNAL_GAPS.md` and annotate as implemented in Phase 30.

**Validation:** ✅ `docs/SIGNAL_GAPS.md` entry struck through and annotated. Known Limitations updated. Docstring updated.

---

### Phase 30 Integration Validation

- [x] `check_listening_ports()` returns all five required dict keys (`name`, `description`, `status`, `raw`, `error`)
- [x] Raw output is sectioned with `TCP (LISTEN):` and `UDP (external):` labels
- [x] Status is `WARN` when any external UDP binding (`*:port` or `[::]:port`) is present
- [x] Status is `PASS` when no external TCP or UDP bindings exist
- [x] Status is `UNKNOWN` (not a 500) when either `lsof` call fails
- [x] No `shell=True` and no `sudo` in the collector
- [x] `pytest tests/test_network.py` exits 0 — all new and existing tests pass (18 passed)
- [x] Full test suite (`pytest`) exits 0 — 165 passed, no regressions
- [x] Dashboard renders correctly — "Listening Services" card shows updated description and merged raw output; badge count 32 unchanged
- [x] `docs/cli_verification.md` has Phase 30 section with recorded command output
- [x] `docs/SIGNAL_GAPS.md` "Listening Services — add UDP" entry struck through and annotated with Phase 30

---

## Open Issues

Issues identified after Phase 22. Each entry is classified as **Bug** (incorrect behavior), **Inconsistency** (code style/convention drift), or **Gap** (missing capability documented as a known limitation).

### Bugs

| # | File | Description |
|---|------|-------------|
| ~~B1~~ | ~~`src/collectors/__init__.py:45`~~ | ~~**CATEGORIES name mismatch: "Remote Login" vs "Remote Login (SSH)".**~~ **Resolved.** Changed `"Remote Login"` → `"Remote Login (SSH)"` in the `CATEGORIES` list. |

### Inconsistencies

| # | File | Description |
|---|------|-------------|
| ~~I1~~ | ~~`src/collectors/external.py`~~ | ~~**Not ported to `make_result` in Phase 22.**~~ **Resolved.** Added `make_result` import (with try/except fallback) and replaced all eight manual result dicts in `check_macos_version()` with `make_result(...)` calls. |
| ~~I2~~ | ~~`src/collectors/external.py`~~ | ~~**Dead helper functions: `_latest_version` and `_max_major_in_feed`.**~~ **Resolved.** Both functions deleted; `check_macos_version()` was already self-contained. |

### Gaps

| # | Description | Path to resolve |
|---|-------------|----------------|
| ~~G1~~ | ~~**`'unsafe-inline'` in CSP.**~~ **Resolved.** Extracted all inline scripts to static files (`fix.js`, `countdown.js`, `filter.js`); `utils.js` now auto-inits the elapsed counter from a `data-prefix` attribute. CSP tightened to `script-src 'self'`. |
| ~~G2~~ | ~~**No automated test suite.**~~ **Resolved.** Added 77 pytest tests across 8 files: unit tests for every status branch in all 20 collectors (mocking `run_cmd`/`run_cmd_rc`/`urlopen`; `tmp_path` for filesystem collectors) and 6 integration smoke tests via the Flask test client. |
| ~~G3~~ | ~~**Screen Lock has no Fix button.**~~ **Resolved.** Added `Screen Lock` entry to `REMEDIATIONS` with `applies_to={"FAIL"}`. Because the executor runs as root via osascript admin (HOME=/var/root), a plain `defaults -currentHost write` would target root's ByHost plist instead of the console user's. Fixed using `su $(stat -f%Su /dev/console) -c '...'` so the write runs in the correct user context. Verified end-to-end in `docs/cli_verification.md § G3`. |
| ~~G4~~ | ~~**AirDrop has no Fix button.**~~ **Resolved.** Added `AirDrop Receiver Mode` entry to `REMEDIATIONS` with `applies_to={"WARN"}`. `defaults write com.apple.sharingd DiscoverableMode` takes effect immediately (cfprefsd notifies sharingd; no process restart needed). The pref is user-owned (`~/Library/Preferences/`), so the same `su $(stat -f%Su /dev/console) -c '...'` pattern used in G3 is applied to target the console user from root context. The value `"Contacts Only"` contains a space, so the double quotes are AppleScript-escaped as `\"` within the outer `do shell script "..."` string. Verified end-to-end in `docs/cli_verification.md § G4`. |

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
