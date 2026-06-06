# Signal Gaps & Improvement Areas

Identified gaps in coverage and improvements to existing signals. Entries are ordered within each section by estimated implementation effort (low → high). All proposed signals must satisfy the collector contract: no `sudo`, `subprocess.run()` with timeout, return `PASS/FAIL/WARN/UNKNOWN`.

---

## Missing signals

### ~~User Accounts~~ *(implemented — Phase 25)*

Guest Account, Login Window Display, and Admin Group Members implemented in `src/collectors/accounts.py`. See Phase 25 in `docs/IMPLEMENTATION_PLAN.md`.

---

### Screensaver Idle Timeout *(add to Software Hygiene)*

- Command: `defaults -currentHost read com.apple.screensaver idleTime`
- Logic: `0` (never) → FAIL; `> 600` (more than 10 min) → WARN; `<= 600` and `> 0` → PASS
- Notes: `check_screen_lock` already verifies that a password is required and that the delay after wake is 0, but never checks how long until the screensaver engages. A machine with a 30-minute idle timeout is effectively unprotected for that window even if the lock-on-wake settings are correct. Key absent = screensaver disabled → FAIL.

---

### Bluetooth *(new category)*

**Bluetooth Power & Discoverability**
- Command: `system_profiler SPBluetoothDataType` (no external dependency)
- Logic: power off → PASS; power on + not discoverable → WARN; power on + discoverable → FAIL
- Notes: A discoverable Bluetooth device is an attack surface. `blueutil` gives cleaner output but requires Homebrew. `system_profiler` is always present. Parse `"State: On/Off"` and `"Discoverable: Yes/No"` from output.

---

### Wi-Fi & Network *(add to Network)*

**Current Wi-Fi Security Type**
- Command: `wdutil info` (requires no root on macOS 13+; parses `Security` field)
- Logic: Open or WEP → FAIL; WPA2 → WARN; WPA3 → PASS; not connected → PASS
- Notes: Connected to an open network routes all traffic in cleartext. WEP is cryptographically broken.

**DNS Configuration**
- Command: `scutil --dns`
- Logic: WARN if any nameserver is a cleartext public resolver that has no known DoH/DoT support; PASS if using a local resolver or known secure resolver
- Notes: Detection of "secure" resolvers requires a maintained allowlist (1.1.1.1, 8.8.8.8, 9.9.9.9, 208.67.222.222). False-positive risk is high; consider WARN-always with raw output for user review instead.

---

### SSH Key Hygiene *(add to Authentication)*

**SSH Private Key Passphrase Protection**
- Command: `ssh-keygen -y -f <keyfile>` on each private key file in `~/.ssh/`; a key with no passphrase returns the public key immediately (exit 0, no prompt); a protected key prompts for input (exit 1 or hangs — use `timeout`)
- Logic: any unprotected private key → WARN with filenames; all protected or no keys → PASS
- Notes: An unprotected private key is a single-file credential — anyone who reads the file has the credential. Requires careful timeout handling to avoid hanging on passphrase-protected keys. Do not include key material in `raw`.

**SSH Agent Forwarding in Config**
- Command: read `~/.ssh/config`; parse for `ForwardAgent yes`
- Logic: any host entry with `ForwardAgent yes` → WARN with matching host blocks; none → PASS
- Notes: Agent forwarding to an untrusted host lets that host use your local keys. This is a pure file read — no subprocess needed.

**SSH Key Algorithm Strength**
- Command: `ssh-keygen -l -f <public key>` for each key in `~/.ssh/`
- Logic: DSA or RSA < 2048 bits → FAIL; RSA 2048–3071 → WARN; RSA ≥ 3072, Ed25519, ECDSA-521 → PASS
- Notes: DSA keys are unconditionally weak. Older RSA keys (1024-bit) are factored by state actors.

---

## Improvements to existing signals

### Listening Services — add UDP

Current `check_listening_ports` uses `-iTCP -sTCP:LISTEN` and misses UDP services entirely. mDNS (5353), accidentally exposed media servers, and some VPN software listen on UDP.

- Add a second `lsof` call: `lsof -iUDP -P -n` and filter for external bindings
- Merge results into the existing signal or split into a separate "UDP Listeners" signal

### Local AI Server — expand port coverage

Currently covers Ollama (11434) and LM Studio (1234) only. Common additions:

| Port | Service |
|------|---------|
| 7860 | Gradio / text-generation-webui |
| 8080 | open-webui |
| 3000 | LocalAI |
| 5000 | llama.cpp HTTP server (common wrapper default) |
| 11435 | Ollama alternate port |

Add to `_AI_PORTS` dict in `src/collectors/ai.py`.

### Root Certificate Trust — add user domain

`check_root_certificates` calls `security dump-trust-settings -d` (system domain only). Custom CAs installed per-user via `security add-trusted-cert` land in the user domain (`-u`) and are currently invisible.

- Add a second call: `security dump-trust-settings -u`
- WARN if either domain has custom trust anchors; PASS if both are empty

### AI Key Detection — scan `.env` files

Shell config files are checked, but `.env` files in `~/`, `~/Desktop`, and `~/Documents` are common holders of AI keys and are frequently committed to git. This is acknowledged in `KNOWN_LIMITATIONS.md` as the most common real-world exposure vector.

- Extend `check_ai_keys_shell_config` (or add a separate `check_ai_keys_env_files`) to scan `.env` in the home directory and one level of subdirectories under `~/Desktop` and `~/Documents`
- Apply the same `_KEY_NAME_PATTERN` regex; report filename + key name, never the value

### Failed Logins — configurable lookback window

The 24-hour `--last 24h` window is hardcoded. An attack that ended 25 hours ago produces PASS. The `--last` argument to `log show` accepts `Nd` (days) and other durations.

- Read a `FAILED_LOGIN_LOOKBACK` environment variable (default `24h`); validate against an allowlist of accepted `log show` duration strings before passing to subprocess
- Surface the active window in the `description` field so the dashboard shows what period is covered

---

## Ruled out / already documented

| Area | Reason |
|------|--------|
| TCC permissions per app (camera, mic, full disk access) | Requires root or Full Disk Access to read `/Library/Application Support/com.apple.TCC/TCC.db`; documented in KNOWN_LIMITATIONS.md |
| Sudo activity | BSM audit trail requires root; unified log surfaces only daemon calls; documented in KNOWN_LIMITATIONS.md |
| Homebrew outdated packages | `brew outdated` takes 5–10 seconds minimum; adds unacceptable latency to every page load; consider as an async/cached signal in a future phase |
| Quarantine xattr on downloads | High noise ratio; most downloaded files are quarantined by default; exceptions require user judgment |
