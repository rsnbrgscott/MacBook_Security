# Known Limitations

Issues that are acknowledged, understood, and not currently planned for remediation unless noted. Each entry records what the limitation is, why it exists, and (where applicable) what it would take to resolve it.

---

## Platform

### Apple Silicon only

The Secure Boot check uses `system_profiler SPiBridgeDataType`, which surfaces the T2 / Apple Silicon security chip state. This tool is not available on Intel Macs. The dashboard is untested on Intel hardware; other signals may work, but Secure Boot will return UNKNOWN.

**Path to resolve:** Identify an Intel-compatible equivalent command and add a runtime branch based on `platform.processor()`.

---

## Privilege model

### No `sudo` in the read path

All collector commands run as the current user with no elevated privileges. This is a deliberate design constraint: keeping collectors unprivileged limits the blast radius of any bug (injection, path traversal, unexpected exception) in the read path.

The consequence is that several signals are either absent or incomplete:

| Signal | What is missed | Root-free alternative |
|--------|---------------|----------------------|
| Listening Services | Root-owned processes (e.g. system daemons) do not appear in `lsof` output | None identified; `lsof` without root is inherently incomplete |
| Sudo activity | The BSM audit trail (`/var/audit/`) requires root to read | None identified; unified log surfaces only background daemon calls |
| TCC / app permissions | Reading another user's TCC database requires root | `tccutil` can reset permissions but cannot query them without root |

**Path to resolve:** Run a privileged `LaunchDaemon` (installed separately, `UserName: root`) that exposes a local socket or file the unprivileged Flask process reads. This isolates privilege to a small, auditable daemon rather than granting it to the web process. This is a significant architectural addition; see the discussion in `docs/IMPLEMENTATION_PLAN.md § Phase 24` for more context.

### Sudo activity is not monitored

`sudo`'s audit record (the specific command that was run) is written to the BSM audit trail at `/var/audit/`, which requires root to read. The macOS unified log surfaces approximately 500+ sudo-related entries per day, but these are all background system daemon invocations (McAfee, Docker, and similar) and cannot be distinguished from user-initiated `sudo` commands. Adding a signal that returned WARN on every page load due to daemon noise would be misleading.

**Path to resolve:** Requires a privileged daemon (see above) or a future macOS API that exposes user-initiated sudo calls without root access.

---

## Signal-specific

### Listening Services — root-owned processes not visible

`lsof -iTCP -sTCP:LISTEN` runs without elevated privileges. Processes listening on a port while running as root (e.g. system daemons, VPN clients) do not appear in the output. A root-owned listener on an external interface would not trigger the WARN status.

### Software update and screen lock signals rely on `defaults` absence semantics

`AutomaticCheckEnabled`, `CriticalUpdateInstall`, and `askForPasswordDelay` are only written to disk when explicitly changed from Apple's defaults. Absence of these keys is treated as PASS — macOS uses its built-in secure defaults (updates on, immediate lock). If a preference management tool (MDM, manual `defaults write`) has written `0` to any of these keys, the signal correctly reflects it.

This means the signal cannot detect a situation where Apple changes its default in a future OS version to a less secure value, because the key would still be absent.

### Screen Lock — requires Automation access to System Events

`check_screen_lock` uses `osascript` to query `System Events` for the `require password to wake` property. If Automation access to System Events is revoked in **System Settings → Privacy & Security → Automation**, this collector returns UNKNOWN rather than the actual lock state.

### Screensaver Idle Timeout — MDM/configuration profile override not detected

`check_screensaver_idle_timeout` reads `idleTime` from the ByHost preference domain (`defaults -currentHost read com.apple.screensaver idleTime`). This is the key written by System Settings when the user manually configures a screensaver timeout.

An MDM configuration profile that enforces the screensaver timeout through a managed preference writes to the Managed preference domain rather than the ByHost domain and may not update the ByHost key. In that case the signal may return FAIL or WARN while the device-level policy enforces a stricter timeout.

**Path to resolve:** Read the managed preference domain (`defaults read /Library/Managed\ Preferences/com.apple.screensaver idleTime`) as a fallback; if a managed value is present, prefer it. Requires testing in a managed environment.

### Admin Group Members — fixed system account filter list

`check_admin_group_members` filters a hardcoded set of known system accounts (`root`, `_mbsetupuser`, `_uucp`, `_networkd`) before comparing the remaining members to the current user. If a future macOS version introduces a new system account not in this list, it would appear as a human member and produce a false WARN.

**Path to resolve:** Replace the static filter with a dynamic check — compare against `dscl . list /Users` entries whose `UniqueID` is below 500 (system accounts on macOS use UIDs below 500 by convention). This makes the filter self-maintaining across OS updates.

### Wi-Fi Security — point-in-time snapshot; current network only; no Fix button

`check_wifi_security` reads the security protocol of the Wi-Fi network the machine is associated with at the moment the page loads. If Wi-Fi is off or the machine is connected via Ethernet only, the signal returns PASS — it cannot assess networks the user typically connects to but isn't currently on.

No Fix button is provided. The encryption protocol (WPA2, WPA3, etc.) is a setting on the access point/router, not on this machine. Upgrading from WPA2 to WPA3 requires changing the wireless router's configuration.

### DNS Configuration — IPv6 router addresses may trigger false WARN; static DoH allowlist

`check_dns_config` classifies nameservers as local (RFC 1918, loopback, link-local, ULA fc00::/7) or known-DoH-capable public resolvers. Any other IP is flagged as "unrecognized public" and produces WARN.

**IPv6 home router false-WARN:** Many ISPs (e.g. Comcast/Xfinity) assign globally-routable IPv6 addresses to the home gateway. When that gateway acts as a local DNS forwarder, its IPv6 address appears in `scutil --dns` as a nameserver. Because the address is a global unicast (e.g. `2600:100e::/32`), it is not recognized as a local device and triggers WARN — even though it is functionally equivalent to the router's private IPv4 address (192.168.1.1). There is no reliable way to determine from the IP address alone whether a globally-routable IPv6 belongs to a local device or a remote public server.

**Static DoH allowlist:** The set of known DoH-capable public resolvers is hardcoded (Cloudflare, Google, Quad9, OpenDNS, AdGuard). Regional DoH resolvers, enterprise DoH deployments, NextDNS user-specific endpoints, and any newly launched DoH services not in the list will trigger WARN even if they use encrypted DNS transport.

**Path to resolve (IPv6):** Compare the nameserver IPv6 prefix against the machine's own IPv6 prefix on the active interface (`networksetup -getinfo Wi-Fi` or `ifconfig en0`). If the nameserver shares a /64 with the machine, it is almost certainly a local device. Adds interface-querying complexity without eliminating all ambiguity.

**Path to resolve (allowlist):** Read an additional allowlist from a user-configurable file (e.g. `~/.config/macbook_security/dns_allowlist.txt`). Adds configuration surface without solving the underlying IPv6 problem.

### Bluetooth — point-in-time snapshot; no Fix button

`check_bluetooth` reads the Bluetooth controller state at the moment the page loads. Discoverability on macOS reverts to `Off` automatically after approximately 3 minutes of inactivity following a pairing session. A brief discoverable window that opens and closes between dashboard loads will not be detected.

No Fix button is provided. Bluetooth power is toggled via Control Center or **System Settings → Bluetooth**, and discoverability is not directly settable via a documented command-line interface without third-party tools (e.g. `blueutil`, a Homebrew dependency). Toggle Bluetooth off manually if the signal shows FAIL.

### AI Security signals — limited detection scope

**Shell config check** covers 12 known AI provider key variable names (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, and eight others). Keys stored under non-standard names, loaded via a password manager CLI (e.g. `op run --`), sourced from a `.env` file in a project directory, or set in a tool-specific config file (e.g. `~/.config/gh/hosts.yml`) are not detected.

**Shell history check** covers three key value prefixes: `sk-` (OpenAI), `sk-ant-api` (Anthropic), and `AIza` (Google). Obfuscated, base64-encoded, or otherwise transformed key material is not detected. Keys set via environment variable injection (not typed in the terminal) do not appear in history.

**Local AI server check** covers Ollama (port 11434) and LM Studio (port 1234). Other local inference servers (llama.cpp, text-generation-webui, vLLM, custom setups on non-standard ports) are not checked.

Neither check stores or logs the key values themselves — only filenames, variable names, and match counts appear in raw output.

---

## Remediations

### Most signals have no Fix button

Fix buttons require commands that are single-flag toggles, fully reversible from System Settings, and testable end-to-end without side effects. Several signals cannot meet this bar:

| Signal | Reason no Fix button |
|--------|---------------------|
| SIP | Requires booting into Recovery Mode; cannot be changed from a running OS |
| Secure Boot | Same — Recovery Mode only |
| FileVault | Enrollment generates a recovery key and requires interactive input; must be done via System Settings |
| Gatekeeper | Currently PASS on the target machine; remediation untested end-to-end — deferred |
| Listening Services | No single command to "fix" an arbitrary listening service; remediation is service-specific |
| Persistence signals | Removing launch agents or daemons requires knowing which entries are unwanted — not automatable |
| Authentication signals | Failed logins and SSH authorized keys require user judgment; no safe automated action |
| Wi-Fi Security | Encryption protocol is set on the access point/router, not this machine — no local command changes it |
| DNS Configuration | Nameservers are pushed by DHCP or set per-interface in System Settings → Network; no single command reliably sets them across all interfaces |

---

## Web application

### CSP `'unsafe-inline'` in `script-src`

The `Content-Security-Policy` header currently includes `'unsafe-inline'` in `script-src`. This is because several JavaScript values (refresh interval, fix button labels) are passed as Jinja2 template variables and rendered inline rather than read from `data-*` attributes on DOM elements.

Moving the inline scripts to files in `static/` and reading configuration values from `data-*` attributes would allow `'unsafe-inline'` to be removed, tightening the policy to `script-src 'self'`. This was resolved for the CSP header in Phase 23 (G1) but the underlying template pattern could be further hardened.

---

## Data and access

### Local access only

The Flask server binds exclusively to `127.0.0.1`. It is not reachable from other devices on the network. This is intentional — the dashboard reads local system state and the fix commands execute on the local machine. Remote access is out of scope.

### History is local only

Signal history is stored in `data/history.db` (SQLite, auto-created on first launch, gitignored). Only status transitions are recorded — consecutive identical statuses produce no new rows. Records older than 30 days are pruned automatically on each write. The database never leaves the machine.

---

## Roadmap gaps

Additional signal categories are planned but not yet implemented. See `docs/SPEC.md` for the full roadmap and `docs/IMPLEMENTATION_PLAN.md` for phased build plans.
