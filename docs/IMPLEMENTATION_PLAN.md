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

### Step 5.1 — Error handling pass

Review each collector function and verify:
- A subprocess timeout does not crash the app (returns UNKNOWN)
- A command not found (e.g., `bputil` missing) does not crash the app (returns UNKNOWN)
- Unexpected output format (unrecognized string) returns UNKNOWN, not FAIL
- The `error` field captures the failure reason as a string

Test by temporarily breaking one collector (e.g., change the command name to something invalid) and confirm the card shows UNKNOWN rather than a 500 error.

**Validation:** Dashboard loads successfully with all four cards even when one collector is forced to fail. The broken card shows UNKNOWN with a non-empty `error` field.

---

### Step 5.2 — Configurable port and environment variable support

- Confirm `PORT` env var overrides the default port (`PORT=8080 python src/app.py` starts on 8080)
- Add a check that prevents Flask from running in debug mode when launched normally (debug mode auto-reloads and can expose stack traces)

**Validation:** `PORT=8080 python src/app.py` starts on port 8080. `http://127.0.0.1:8080` loads the dashboard. Default launch uses port 5000.

---

### Step 5.3 — Finalize README

Update `README.md` to include:
- Prerequisites (Python 3.x, macOS Apple Silicon)
- Setup steps (clone, venv, pip install)
- How to run (`python src/app.py`)
- How to change the port (`PORT=8080 python src/app.py`)
- What each signal means (brief, one line each)
- Known limitations (Apple Silicon only, no persistence, no remediations)

**Validation:** Follow the README instructions in a clean terminal session (fresh shell, no active venv). The dashboard starts and loads correctly.

---

### Step 5.4 — End-to-end MVP test

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

- [ ] All four cards render with live data on a clean launch
- [ ] Forced collector failure produces UNKNOWN card, not a crash
- [ ] `PORT` env var correctly overrides the default port
- [ ] Flask is not running in debug mode by default
- [ ] README instructions work from a clean terminal session
- [ ] No hardcoded paths, credentials, or machine-specific values in any file

---

## Phase 6 — Polling / Auto-Refresh

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 2`.

**Goal:** Add configurable auto-refresh so the dashboard updates on a fixed interval without requiring a manual page reload.

**Planned scope:**
- Abstract the refresh trigger behind a configurable strategy (on-demand vs. polling)
- Add a visible refresh interval indicator to the UI
- Make the interval configurable (env var or UI control)
- On-demand mode remains the default and must continue to work unchanged

---

## Phase 7 — Network Signals

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 3`.

**Goal:** Add a second signal category: network activity.

**Planned signals:** Listening ports (`lsof`), firewall state (`socketfilterfw`), active outbound connections.

**Key constraint:** `socketfilterfw` requires elevated privileges — the privilege model must be resolved before implementation.

---

## Phase 8 — Persistence Signals

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 4`.

**Goal:** Add launch agents/daemons and login items monitoring.

**Planned signals:** `launchctl list`, `~/Library/LaunchAgents`, `/Library/LaunchAgents`, `/Library/LaunchDaemons`, login items.

---

## Phase 9 — Authentication Signals

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 5`.

**Goal:** Add authentication event monitoring.

**Planned signals:** Failed login attempts, sudo activity, authorized SSH keys.

**Key constraint:** `log show` queries may require Full Disk Access — the permission model must be resolved before implementation.

---

## Phase 10 — Remediations

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 6`.

**Goal:** Add read-write mode with one-click fixes for common misconfigurations.

**Key constraint:** Remediations require elevated privileges and introduce risk of unintended system changes. A privilege escalation design (e.g., `sudo` prompt, privileged helper) must be specified before implementation.

---

## Phase 11 — External Calls

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 7`.

**Goal:** Optionally enrich the dashboard with data from public APIs (macOS version checks, CVE lookups). User-configurable opt-in required — external calls must never happen without explicit user consent.

---

## Phase 12 — Alerting

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 8`.

**Goal:** Notify the user when a signal changes state (e.g., FileVault turns off). macOS native notifications preferred.

---

## Phase 13 — History & Trends

> Detailed step planning will be done before this phase begins. Spec reference: `SPEC.md § Future Phases — Phase 9`.

**Goal:** Persist check results to a local SQLite database and display a trend view showing how signals have changed over time.

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
