Start a new implementation phase for the MacBook Security Dashboard: $ARGUMENTS

Follow the CLAUDE.md phase workflow exactly — present each step for approval before proceeding to the next.

**Step 1 — Plan**
Add detailed steps to `docs/IMPLEMENTATION_PLAN.md` under a new phase heading. Include: goal, signals or features being added, exact CLI commands to verify, collector/remediation changes, and a validation checklist. Stop here and wait for approval before writing any code.

**Step 2 — Verify CLI commands**
Run each candidate command interactively. Record exact output in `docs/cli_verification.md` under a new heading for this phase. Never write a parser without first seeing real output on this machine.

**Step 3 — Implement**
One step at a time. Each step ends with a concrete validation check (curl the dashboard, show command output, or take a screenshot). Do not batch steps.

**Step 4 — Integration validation**
Run all checklist items from the plan. Confirm every new signal/feature works and no existing signals regressed.

**Step 5 — Commit**
One commit for the completed phase. Message format: `Phase <N> — <short description>`

Cross-phase constraints (must hold throughout):
- Flask binds to `127.0.0.1` only, never `0.0.0.0`
- No external HTTP calls unless `EXTERNAL_CALLS=1` is set
- Collectors are read-only — all write operations go in `src/remediations/`
- `app.py` must not change when adding a new signal category
- `FLASK_DEBUG` must not be set at startup; the app exits with an error if it is
