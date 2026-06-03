Add a new security signal to the MacBook Security Dashboard: $ARGUMENTS

Follow the CLAUDE.md workflow exactly — do not skip steps or reorder them.

**Step 1 — Verify the CLI command**
Run the candidate command interactively in the terminal. Confirm the exact output format on this machine. Record the raw output in `docs/cli_verification.md` under a new section for this signal. Never write a parser before seeing real output.

**Step 2 — Write the collector**
Add `check_<name>()` to the appropriate file in `src/collectors/` (or a new file for a new category). The function must return a dict with exactly these keys:
- `name` (str) — display name
- `description` (str) — one-line description
- `status` (str) — one of: `PASS`, `FAIL`, `WARN`, `UNKNOWN`
- `raw` (str) — raw command output for the user to review
- `error` (str | None) — error message if status is UNKNOWN, else None

Rules:
- Never `sudo` in a collector
- Use `subprocess.run()` with a `timeout=`, never `shell=True`
- If output is empty or unrecognized, return `UNKNOWN` with a descriptive `error` — never crash or return 500
- `PASS` = secure/expected state; `FAIL` = direct security concern; `WARN` = notable, user should review; `UNKNOWN` = command failed or output unrecognized

**Step 3 — Register the collector**
Import and append the function to `_COLLECTORS` in `src/collectors/__init__.py`. `app.py` never changes.

**Step 4 — Validate**
Start the app (`PORT=8000 .venv/bin/python src/app.py`), load `http://127.0.0.1:8000/`, and confirm:
- The new signal appears in the dashboard
- Its status matches the expected value given the current machine state
- No existing signals regressed
