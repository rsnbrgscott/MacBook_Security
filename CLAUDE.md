# CLAUDE.md — MacBook Security Dashboard

## What this project is

A personal macOS security monitoring dashboard (Flask, local only, Apple Silicon). It collects security signal status using native macOS CLI tools and displays them on a single page at `http://127.0.0.1:8000`. Two signals have one-click Fix buttons that escalate via `osascript` with administrator privileges.

**Platform:** macOS Apple Silicon only. Python 3.10+ (Homebrew: `/opt/homebrew/bin/python3`).

## Running the app

```zsh
.venv/bin/python src/app.py
```

Environment variables: `PORT` (default 8000), `REFRESH_INTERVAL` (default 0, seconds). `FLASK_DEBUG` must not be set.

## Project workflow

Each phase follows this sequence:

1. **Plan** — elaborate steps in `docs/IMPLEMENTATION_PLAN.md` before writing any code
2. **Verify CLI commands** — run candidate commands interactively in Terminal; record output in `docs/cli_verification.md` under the appropriate phase heading
3. **Implement** — one step at a time, each ending with a concrete validation check
4. **Integration validation** — run all checklist items at the end of each phase
5. **Commit** — one commit per completed phase

## Current state

**Completed phases:**
- Phase 1–5: Project scaffold, MVP (4 system integrity signals), dark-mode UI
- Phase 6: Auto-refresh with configurable countdown
- Phase 7 (implementation plan numbering): Network signals — Application Firewall, Stealth Mode, Listening Services
- Phase 8: Persistence signals — User Launch Agents, Global Launch Agents, Launch Daemons, Login Items
- Phase 9: Authentication signals — Failed Logins, SSH Authorized Keys
- Phase 10: Remediations — Fix buttons for Application Firewall (FAIL) and Stealth Mode (WARN)

**13 signals total.** All phases 1–10 are committed.

**Next phases (stub only, not started):**
- Phase 11: External Calls (macOS update check, CVE lookups — opt-in only)
- Phase 12: Alerting (macOS native notifications on state change)
- Phase 13: History & Trends (SQLite, trend view)

## Adding a new signal (collector)

1. Add a `check_<name>()` function to the appropriate file in `src/collectors/`, or create a new file for a new category.
2. Return a dict with exactly these keys: `name` (str), `description` (str), `status` (str), `raw` (str), `error` (str | None).
3. Import and append to `_COLLECTORS` in `src/collectors/__init__.py`. `app.py` never changes.

**Status values and their meanings:**
- `PASS` — the control is in its secure/expected state
- `FAIL` — the control is off or misconfigured; a direct security concern
- `WARN` — notable but not necessarily wrong; user should review (e.g., third-party launch agents present)
- `UNKNOWN` — command failed, timed out, or output was unrecognized; never mislead with PASS

**Collector rules:**
- Never `sudo`. If a signal requires root, document it as a Known Limitation.
- Use `subprocess.run()` with a `timeout`; never `shell=True`.
- If output is empty or unrecognized, return `UNKNOWN` with a descriptive `error` — never crash or return 500.
- `log show` returns an empty string (no header) when Full Disk Access is suppressed. Empty output with no header = `UNKNOWN`, not `PASS`.
- Always verify the exact output format interactively on the target machine before writing the parser. Record results in `docs/cli_verification.md`.

## Adding a remediation

Add an entry to `REMEDIATIONS` in `src/remediations/__init__.py`:

```python
"Signal Name": {
    "label": "Human-readable button label",
    "cmd": "/full/path/to/command --flag value",
    "applies_to": {"FAIL"},   # set of statuses that show the button
},
```

The `cmd` value must be a fixed constant — never derived from user input or the request. The `/fix/<signal_name>` route in `app.py` validates the name against the registry before executing anything.

**Privilege model:** `executor.py` wraps the command in `osascript -e 'do shell script "..." with administrator privileges'`. This triggers the standard macOS password dialog. No `sudoers` changes. Touch ID works. Cancel returns exit 1 + `"User canceled."` in stderr.

**Only add remediations for commands that are:** single-flag toggles, fully reversible from System Settings, and testable end-to-end on this machine. SIP and Secure Boot require Recovery Mode. FileVault enrollment is interactive.

## Cross-phase constraints (must hold in every phase)

- Flask always binds to `127.0.0.1`, never `0.0.0.0`
- No HTTP calls to external hosts unless Phase 11 is active and user has opted in
- Collectors are read-only — all write operations go in `src/remediations/`
- `app.py` should not need to change when adding a new signal category
- `FLASK_DEBUG` must not be set at startup; the app exits with an error if it is

## Known gotchas

- **`spctl --status` writes to stderr** on some macOS versions. The `_run()` helper in each collector falls back to stderr if stdout is empty.
- **`stealth mode` output is `"Firewall stealth mode is on"`**, not `"enabled"`. Both strings must be checked.
- **`sudo` activity is not available without root.** `COMMAND=` entries go to the BSM audit trail (`/var/audit/`), not the unified log. The unified log surfaces ~500 background daemon sudo calls per day that cannot be distinguished from user invocations.
- **Global Launch Agents and Launch Daemons filter `com.apple.*`** entries — only third-party entries are shown. User Launch Agents do not filter.
- **`lsof` runs without elevated privileges**, so system-owned listening processes (running as root) do not appear in the Listening Services output.
- **Persistence signals return `WARN` when entries are present** — this is expected on most machines. The raw output lets the user review which entries exist.
- **`log show` predicates must be case-sensitive for loginwindow.** Case-insensitive `CONTAINS[c] "failed"` matches clipboard-related log entries (`"Failed to set up CFPasteboardRef"`), causing false positive WARNs.

## Key files

| File | Purpose |
|------|---------|
| `src/collectors/__init__.py` | Collector registry — the only file to edit when adding/removing signals |
| `src/remediations/__init__.py` | REMEDIATIONS registry — edit to add/remove Fix buttons |
| `src/remediations/executor.py` | `run_fix()` — privilege escalation logic; do not change the osascript pattern |
| `docs/IMPLEMENTATION_PLAN.md` | Source of truth for phase status and step-by-step plans |
| `docs/cli_verification.md` | Raw command output recorded during development; one section per phase |
