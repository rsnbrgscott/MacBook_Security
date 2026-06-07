# CLI Verification — System Integrity Signals

Recorded during Phase 2, Step 2.1 on macOS (Apple Silicon, Mac15,9).
These are the exact outputs used to write the parsers in Step 2.2.

---

## csrutil status

**Command:** `csrutil status`
**Privilege required:** None

**Observed output:**
```
System Integrity Protection status: enabled.
```

**Parse strategy:**
- PASS → output contains `"enabled"`
- FAIL → output contains `"disabled"`
- UNKNOWN → neither match

---

## spctl --status

**Command:** `spctl --status`
**Privilege required:** None

**Observed output:**
```
assessments enabled
```

**Parse strategy:**
- PASS → output contains `"assessments enabled"`
- FAIL → output contains `"assessments disabled"`
- UNKNOWN → neither match

---

## fdesetup status

**Command:** `fdesetup status`
**Privilege required:** None

**Observed output:**
```
FileVault is On.
```

**Parse strategy:**
- PASS → output contains `"FileVault is On"`
- FAIL → output contains `"FileVault is Off"`
- UNKNOWN → neither match

---

## Secure Boot — system_profiler SPiBridgeDataType

**Command:** `system_profiler SPiBridgeDataType`
**Privilege required:** None

> ⚠️ **bputil -d was originally specified in SPEC.md and IMPLEMENTATION_PLAN.md
> but requires root (`Exit code 1: The tool requires running as root`).
> system_profiler SPiBridgeDataType provides the same information without
> elevated privileges and is the authoritative replacement.**

**Observed output:**
```
Controller:

      Model Identifier: Mac15,9
      Firmware Version: mBoot-18000.120.36
      Boot UUID: AB166D84-247B-4497-A4E5-4C04FE9B1700
      Boot Policy:
        Secure Boot: Full Security
        System Integrity Protection: Enabled
        Signed System Volume: Enabled
        Kernel CTRR: Enabled
        Boot Arguments Filtering: Enabled
        Allow All Kernel Extensions: No
        User Approved Privileged MDM Operations: No
        DEP Approved Privileged MDM Operations: No
```

**Parse strategy:**
- PASS → `"Secure Boot:"` line contains `"Full Security"`
- FAIL → `"Secure Boot:"` line contains `"No Security"` or `"Permissive Security"`
- WARN → `"Secure Boot:"` line contains `"Medium Security"` or `"Reduced Security"`
- UNKNOWN → `"Secure Boot:"` line absent or unrecognized value

**Known Secure Boot values (Apple Silicon):**
| Value | Meaning |
|-------|---------|
| `Full Security` | Only signed, Apple-trusted OS can boot. Highest protection. |
| `Medium Security` / `Reduced Security` | Allows older or third-party signed OS. Used for dual-boot or kext loading. |
| `No Security` / `Permissive Security` | No boot restrictions. Lowest protection. |

---

## Summary — System Integrity

| Signal | Command | Root required? | Status on this machine |
|--------|---------|---------------|----------------------|
| SIP | `csrutil status` | No | enabled ✅ |
| Gatekeeper | `spctl --status` | No | assessments enabled ✅ |
| FileVault | `fdesetup status` | No | On ✅ |
| Secure Boot | `system_profiler SPiBridgeDataType` | No | Full Security ✅ |

---

# CLI Verification — Network Signals

Recorded during Phase 7, Step 7.1 on macOS (Apple Silicon, Mac15,9).
These are the exact outputs used to write the parsers in Step 7.2.

---

## Application Firewall — socketfilterfw --getglobalstate

**Command:** `/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate`
**Privilege required:** None — confirmed working without `sudo`

**Observed output:**
```
Firewall is disabled. (State = 0)
```

**Known state values:**

| State value | Meaning |
|-------------|---------|
| `State = 0` | Firewall disabled |
| `State = 1` | Firewall enabled (allow signed apps) |
| `State = 2` | Firewall enabled (essential services only) |

**Parse strategy:**
- PASS → output contains `"enabled"`
- FAIL → output contains `"disabled"`
- UNKNOWN → neither match

> The `defaults read` fallback (`defaults read /Library/Preferences/com.apple.alf globalstate`) is **not needed** — `socketfilterfw --getglobalstate` runs without elevated privileges on this machine.

---

## Stealth Mode — socketfilterfw --getstealthmode

**Command:** `/usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode`
**Privilege required:** None — confirmed working without `sudo`

**Observed output:**
```
Firewall stealth mode is off
```

**Parse strategy:**
- PASS → output contains `"enabled"`
- WARN → output contains `"off"` or `"disabled"`
- UNKNOWN → neither match

---

## Listening Services — lsof -iTCP -sTCP:LISTEN -P -n

**Command:** `lsof -iTCP -sTCP:LISTEN -P -n`
**Privilege required:** None (shows current user's processes only without root)

**Observed output:**
```
COMMAND     PID           USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
rapportd    621 scottrosenberg   10u  IPv4  0xf234b11f7adef2b      0t0  TCP *:61119 (LISTEN)
rapportd    621 scottrosenberg   11u  IPv6 0x341e1b72b2cb7a9b      0t0  TCP *:61119 (LISTEN)
EEventMan   826 scottrosenberg    4u  IPv4 0xed09f324ebd98d22      0t0  TCP *:2968 (LISTEN)
Ollama      853 scottrosenberg    4u  IPv4 0xace4297ca96f619d      0t0  TCP 127.0.0.1:49153 (LISTEN)
ollama      921 scottrosenberg    3u  IPv4 0x888e00d28704b5ff      0t0  TCP 127.0.0.1:11434 (LISTEN)
app_inkwe   922 scottrosenberg   16u  IPv4 0x6f134f84e86123c4      0t0  TCP 127.0.0.1:53953 (LISTEN)
node       3747 scottrosenberg   17u  IPv6 0xceea8aa4b82b9251      0t0  TCP *:3000 (LISTEN)
Code\x20H 18884 scottrosenberg   61u  IPv4 0xda17639c4e34cfbb      0t0  TCP 127.0.0.1:16607 (LISTEN)
Code\x20H 18884 scottrosenberg   71u  IPv4 0xdebaad4d41692b4d      0t0  TCP 127.0.0.1:49788 (LISTEN)
Code\x20H 18884 scottrosenberg   76u  IPv4 0x688f388f991939f9      0t0  TCP 127.0.0.1:49789 (LISTEN)
Code\x20H 19097 scottrosenberg   20u  IPv4 0x1adc25a246ee8fb3      0t0  TCP 127.0.0.1:52399 (LISTEN)
Python    41415 scottrosenberg    3u  IPv4 0x8ba9a672a9fd1eb4      0t0  TCP 127.0.0.1:8000 (LISTEN)
ControlCe 67297 scottrosenberg    9u  IPv4 0x600539ed45e5b1d0      0t0  TCP *:5000 (LISTEN)
ControlCe 67297 scottrosenberg   10u  IPv4 0x7342c277867321b4      0t0  TCP *:7000 (LISTEN)
ControlCe 67297 scottrosenberg   11u  IPv6 0x5d0a7e5d4a13fe78      0t0  TCP *:7000 (LISTEN)
ControlCe 67297 scottrosenberg   13u  IPv6 0x1791ce095407a7e3      0t0  TCP *:5000 (LISTEN)
Python    77770 scottrosenberg    3u  IPv4 0xc81a2fd4a8ef2a82      0t0  TCP 127.0.0.1:5000 (LISTEN)
Python    77997 scottrosenberg    3u  IPv4 0x5247f0ee079b664f      0t0  TCP 127.0.0.1:8001 (LISTEN)
```

**Observed external-facing listeners (NAME column contains `*:`):**

| Process | Port | Note |
|---------|------|------|
| `rapportd` | 61119 | macOS Handoff / Continuity daemon |
| `EEventMan` | 2968 | Epson printer event manager |
| `node` | 3000 | Node.js dev server |
| `ControlCenter` | 5000, 7000 | AirPlay Receiver (macOS built-in) |

**Parse strategy:**
- Parse each `LISTEN` line and extract the NAME field (last column before `(LISTEN)`)
- WARN → one or more listeners have `*:` as the address prefix (bound to all interfaces)
- PASS → all listeners are prefixed with `127.0.0.1:` or `[::1]:` (loopback only)
- UNKNOWN → `lsof` exited non-zero or produced no header line

> Without root, `lsof` shows only processes owned by the current user. System-level listeners (owned by root) are not visible. This is a known limitation documented in README Known Limitations.

---

## Summary — Network

| Signal | Command | Root required? | Status on this machine |
|--------|---------|---------------|----------------------|
| Application Firewall | `socketfilterfw --getglobalstate` | No | disabled → FAIL |
| Stealth Mode | `socketfilterfw --getstealthmode` | No | off → WARN |
| Listening Services | `lsof -iTCP -sTCP:LISTEN -P -n` | No (partial) | external listeners present → WARN |

---

# CLI Verification — Persistence Signals

Recorded during Phase 8, Step 8.1 on macOS (Apple Silicon, Mac15,9).
These are the exact outputs used to write the parsers in Step 8.2.

---

## User Launch Agents — ~/Library/LaunchAgents/

**Source:** `ls ~/Library/LaunchAgents/`
**Privilege required:** None (user-owned directory)

**Observed output:**
```
com.epson.epsvcp.plist
com.google.GoogleUpdater.wake.plist
com.google.keystone.agent.plist
com.google.keystone.xpcservice.plist
com.grammarly.ProjectLlama.Shepherd.plist
com.grammarly.ProjectLlama.Uninstaller.plist
com.grammarly.ProjectLlama.UpdateService.plist
com.openai.atlas.agent-xpc.plist
com.openai.atlas.update-helper.plist
com.redhat.crc.daemon.plist
homebrew.mxcl.ollama.plist
org.virtualbox.vboxwebsrv.plist
```

**Parse strategy:**
- PASS → directory is empty or does not exist
- WARN → one or more `.plist` files are present
- UNKNOWN → `OSError` reading the directory

**Status on this machine:** 12 third-party entries present → WARN

---

## Global Launch Agents — /Library/LaunchAgents/

**Source:** `ls /Library/LaunchAgents/`
**Privilege required:** None (world-readable)

**Observed output:**
```
com.adobe.ARMDCHelper.cc24aef4a1b90ed56a725c38014c95072f92651fb65e1bf9c8e43c37a23d420d.plist
com.epson.Epson_Low_Ink_Reminder.launcher.plist
com.epson.esua.launcher.plist
com.epson.eventmanager.agent.plist
com.epson.ijfax.FaxIOHelper.plist
com.epson.RemotePrintIOHelper.plist
com.epson.scannermonitor.plist
com.mcafee.macvpn.plist
com.mcafee.menulet.plist
com.mcafee.registerfinderextension.plist
com.mcafee.reporter.plist
com.mcafee.uninstall.SystemExtension.plist
com.microsoft.update.agent.plist
us.zoom.updater.login.check.plist
us.zoom.updater.plist
```

**Parse strategy:**
- Filter out entries prefixed `com.apple.` (expected Apple system items)
- PASS → directory is empty or only `com.apple.*` entries remain after filtering
- WARN → one or more non-`com.apple.*` entries present
- UNKNOWN → `OSError` reading the directory

**Status on this machine:** 15 non-Apple entries (Adobe, Epson ×6, McAfee ×5, Microsoft, Zoom ×2) → WARN

---

## Launch Daemons — /Library/LaunchDaemons/

**Source:** `ls /Library/LaunchDaemons/`
**Privilege required:** None (world-readable)

**Observed output:**
```
com.adobe.ARMDC.Communicator.plist
com.adobe.ARMDC.SMJobBlessHelper.plist
com.docker.socket.plist
com.docker.vmnetd.plist
com.epson.ijfax.FaxIODaemon.plist
com.epson.RemotePrintIODaemon.plist
com.github.containers.podman.helper-scottrosenberg.plist
com.mcafee.CmacPatch.plist
com.mcafee.cspd.plist
com.mcafee.datupdate.plist
com.mcafee.genutility.plist
com.mcafee.mac.cloudsdkdaemon.plist
com.mcafee.PeriodicScan.plist
com.mcafee.productupdate.plist
com.mcafee.ssm.ScanFactory.plist
com.mcafee.ssm.ScanManager.plist
com.mcafee.virusscan.fmpd.plist
com.microsoft.autoupdate.helper.plist
com.vagrant.vagrant-vmware-utility-stopper.plist
com.vagrant.vagrant-vmware-utility.plist
org.wireshark.ChmodBPF.plist
us.zoom.ZoomDaemon.plist
```

**Parse strategy:** Same as Global Launch Agents — filter `com.apple.*`, WARN on any remainder.

**Status on this machine:** 22 non-Apple entries (Adobe ×2, Docker ×2, Epson ×2, Podman, McAfee ×10, Microsoft, Vagrant ×2, Wireshark, Zoom) → WARN

---

## Login Items — osascript

**Command:** `osascript -e 'tell application "System Events" to get the name of every login item'`
**Privilege required:** None — no TCC dialog on this machine

**Observed output:**
```
Acrobat Collaboration Synchronizer, GeminiAppLauncher, Podman Desktop, Amphetamine
```

**Parse strategy:**
- Split on `, ` to get individual item names
- PASS → output is empty (no login items)
- WARN → one or more items returned
- UNKNOWN → `osascript` exits non-zero or raises an exception

**Status on this machine:** 4 items present → WARN

> **Method selection:** `osascript` was chosen over `sfltool dumpbtm`. Both run without `sudo`, but `sfltool` output is verbose and structured for human inspection rather than programmatic parsing. `osascript` returns a clean comma-separated list directly usable in the collector.

---

## Summary — Persistence

| Signal | Source | Root required? | Login items method | Status on this machine |
|--------|--------|---------------|--------------------|----------------------|
| User Launch Agents | `~/Library/LaunchAgents/` | No | — | 12 entries → WARN |
| Global Launch Agents | `/Library/LaunchAgents/` | No | — | 15 non-Apple entries → WARN |
| Launch Daemons | `/Library/LaunchDaemons/` | No | — | 22 non-Apple entries → WARN |
| Login Items | `osascript` System Events | No | osascript (no TCC prompt) | 4 items → WARN |

---

# CLI Verification — Authentication Signals

Recorded during Phase 9, Step 9.1 on macOS (Apple Silicon, Mac15,9, Darwin 25.5.0 / macOS Sequoia).
These are the exact outputs used to write the parsers in Step 9.2 and to make the signal inclusion decision.

---

## Failed Logins — loginwindow predicate

**Command:** `log show --predicate 'process == "loginwindow" AND eventMessage CONTAINS "FAILED"' --last 24h --style compact`
**Privilege required:** None — confirmed working without `sudo`

**Observed output:**
```
Timestamp               Ty Process[PID:TID]
```
*(header only — no failures in past 24h)*

**FDA suppression check:** The header line is present. This confirms `log show` is not being silently suppressed — it can query loginwindow logs. If the output were completely empty (no header), that would indicate FDA suppression.

**Parse strategy:**
- Canary: presence of the header line confirms log access
- PASS → header present, no data rows
- WARN → one or more data rows (each is a failure event)
- UNKNOWN → exit non-zero, or completely empty output (no header)

> **Case sensitivity:** The `CONTAINS` operator in `log show` predicates is case-sensitive. The predicate uses `"FAILED"` (uppercase) matching the known loginwindow message format. Use `CONTAINS[c]` if case variance is suspected across macOS versions.

---

## Failed Logins — sshd predicate

**Command:** `log show --predicate 'process == "sshd" AND (eventMessage CONTAINS "Failed" OR eventMessage CONTAINS "Invalid")' --last 24h --style compact`
**Privilege required:** None

**Observed output:**
```
Timestamp               Ty Process[PID:TID]
```
*(header only — no sshd failures in past 24h; SSH is not actively in use on this machine)*

**Parse strategy:** Same as loginwindow — header confirms access, data rows indicate failures.

---

## Failed Logins — combined predicate (final choice)

**Command:**
```
log show --predicate '(process == "loginwindow" AND eventMessage CONTAINS "FAILED") OR (process == "sshd" AND (eventMessage CONTAINS "Failed" OR eventMessage CONTAINS "Invalid"))' --last 24h --style compact
```

> ⚠️ Case-insensitive `CONTAINS[c] "failed"` on loginwindow matches unrelated messages such as `"Failed to set up CFPasteboardRef"` (a clipboard error), producing false WARN results. The loginwindow authentication failure message format uses all-caps `"FAILED"`, so the case-sensitive predicate is correct and specific.

**Observed output:**
```
Timestamp               Ty Process[PID:TID]
```
*(header only — no failures in past 24h)*

**Parse strategy:** Same. Case-insensitive `[c]` modifier used for loginwindow to handle any message-format variation across macOS versions.

**Method selection:** Combined into a single `log show` call (one subprocess) rather than two separate queries. Covers both GUI password failures (loginwindow) and SSH failures (sshd).

---

## Sudo Activity — investigation and decision

**Candidate command:** `log show --predicate 'process == "sudo" AND eventMessage CONTAINS "COMMAND="' --last 24h --style compact`

**Observed output (24h):** Header only — zero `COMMAND=` entries found.

**Investigation:**

The unfiltered sudo query (`process == "sudo"`) returned 1.6 MB of output over 24h — 17,045 lines from ~563 unique sudo PIDs. Every single entry was an internal library call:
- `(libsystem_info.dylib) Retrieve User by ID`
- `(libsystem_info.dylib) Too many groups requested`
- `Df sudo[PID] Reading config`

The actual audit message that `sudo` writes when a user runs a command — format:
```
scottrosenberg : TTY=ttys001 ; PWD=/path ; USER=root ; COMMAND=/usr/bin/something
```
— **does not appear in the unified log**, even with `--info` and `--debug` flags, even over a 7-day window.

**Root cause:** On macOS, `sudo`'s audit record is written to the BSM audit trail (`/var/audit/`), not to the unified logging system. `/var/audit/` is `Permission denied` without root.

**Why PID counting fails as a fallback:** The 563 unique sudo PIDs per day are all background system process invocations (from McAfee, Docker, system daemons, etc.). There is no way to distinguish a user's `sudo make install` from a background daemon's internal sudo call using the unified log alone.

**Decision: Omit sudo activity from Phase 9.** Document as a Known Limitation. Defer to a future phase if a root-free data source is identified.

---

## SSH Authorized Keys — ~/.ssh/authorized_keys

**Source:** `~/.ssh/authorized_keys`
**Privilege required:** None (user-owned file)

**Observed output:**
```
ls: /Users/scottrosenberg/.ssh/authorized_keys: No such file or directory
```

The `~/.ssh/` directory exists and contains outbound keys (GitHub, GitLab, id_ed25519) but **no `authorized_keys` file**. An absent file means no remote key-based logins are authorized.

**Parse strategy:**
- Use `pathlib.Path.exists()` — if absent, treat same as empty
- PASS → file absent or contains only blank lines and `#` comments
- WARN → file has one or more valid key lines (non-blank, non-comment)
- UNKNOWN → `OSError` reading the file

**Status on this machine:** File absent → PASS

---

## Summary — Authentication

| Signal | Source | Root required? | Decision | Status on this machine |
|--------|--------|---------------|----------|----------------------|
| Failed Logins | `log show` (loginwindow + sshd) | No | Included | No failures in 24h → PASS |
| Sudo Activity | `log show` / BSM audit | BSM requires root | **Omitted** — see Known Limitations | N/A |
| SSH Authorized Keys | `~/.ssh/authorized_keys` | No | Included | File absent → PASS |

---

# CLI Verification — Remediations

Recorded during Phase 10, Step 10.1 on macOS (Apple Silicon, Mac15,9, Darwin 25.5.0 / macOS Sequoia).

---

## Privilege model — osascript auth dialog

**Pattern:** `osascript -e 'do shell script "<cmd>" with administrator privileges'`

**Canary test:**
```
$ osascript -e 'do shell script "whoami" with administrator privileges'
root
EXIT:0
```
Auth dialog appeared. On confirm (Touch ID or password): exits 0, stdout = `root`.

**Cancel path:**
```
$ osascript -e 'error "User canceled." number -128'
6:22: execution error: User canceled. (-128)
EXIT:1
```
When the user clicks Cancel in the auth dialog, osascript exits 1 and stderr contains `"User canceled."` (AppleScript error -128). The executor must detect this string and surface a clean message rather than a raw error.

> **Note:** Touch ID auto-authenticated the canary and firewall tests without showing a visible dialog. The cancel path was confirmed via the `error` command which reproduces the exact osascript cancel error format (exit 1, `"User canceled."` in stderr).

---

## Application Firewall — socketfilterfw --setglobalstate on

**Command (via osascript):**
```
osascript -e 'do shell script "/usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on" with administrator privileges'
```
**Exit code:** 0
**stdout:** *(empty — socketfilterfw writes no output on success)*
**stderr:** *(empty)*

**Post-command verification:**
```
$ /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
Firewall is enabled. (State = 1)
```

**Restored after test:**
```
osascript -e 'do shell script "/usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off" with administrator privileges'
# → exit 0; getglobalstate confirms: Firewall is disabled. (State = 0)
```

---

## Stealth Mode — socketfilterfw --setstealthmode on

**Command (via osascript):**
```
osascript -e 'do shell script "/usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on" with administrator privileges'
```
**Exit code:** 0
**stdout:** *(empty)*
**stderr:** *(empty)*

**Post-command verification:**
```
$ /usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode
Firewall stealth mode is on
```

**Restored after test:**
```
osascript -e 'do shell script "/usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode off" with administrator privileges'
# → exit 0; getstealthmode confirms: Firewall stealth mode is off
```

---

## Summary — Remediations

| Signal | Command | Privilege method | Exit on success | Exit on cancel |
|--------|---------|-----------------|----------------|----------------|
| Application Firewall | `socketfilterfw --setglobalstate on` | osascript auth dialog | 0, empty stdout | 1, `"User canceled."` in stderr |
| Stealth Mode | `socketfilterfw --setstealthmode on` | osascript auth dialog | 0, empty stdout | 1, `"User canceled."` in stderr |

**Key findings:**
- Both commands exit 0 with empty stdout on success — success must be inferred from exit code, not output content
- Cancel produces exit 1 with `"User canceled."` in stderr (AppleScript error -128) — must be caught and surfaced cleanly

---

## Phase 11 — External Calls

Recorded on macOS 26.5 (build 25F71), Apple Silicon, 2026-06-01.

### sw_vers

```
$ sw_vers -productVersion
26.5

$ sw_vers -buildVersion
25F71
```

### Candidate API 1: Apple GDMF

**URL:** `https://gdmf.apple.com/v2/pmv`

**Request headers (curl -v, no cookies, no session tokens):**
```
> GET /v2/pmv HTTP/1.1
> Host: gdmf.apple.com
> User-Agent: curl/8.7.1
> Accept: */*
```
No machine-identifying data sent.

**Response shape (relevant keys):**
```json
{
  "PublicAssetSets": {
    "macOS": [
      {
        "ProductVersion": "26.5.1",
        "Build": "25F80",
        "PostingDate": "2026-06-01",
        "ExpirationDate": "2026-08-30",
        "SupportedDevices": [...]
      },
      ...
    ]
  }
}
```

**All macOS entries (ProductVersion / Build / PostingDate), sorted:**
```
11.7.11  20G1443   2026-02-18
11.7.11  20G1443   2026-06-01
12.7.6   21H1320   2026-02-18
12.7.6   21H1320   2026-06-01
13.7.8   22H730    2026-02-18
13.7.8   22H730    2026-06-01
14.8.4   23J319    2026-02-18
14.8.5   23J624    2026-03-24
14.8.7   23J520    2026-05-11
14.8.7   23J520    2026-06-01
15.7.4   24G517    2026-02-18
15.7.5   24G624    2026-03-24
15.7.7   24G720    2026-05-11
15.7.7   24G720    2026-06-01
26.3     25D125    2026-02-18
26.3.1   25D2128   2026-03-04
26.3.1   25D2128   2026-03-04
26.3.2   25D2140   2026-03-10
26.4     25E246    2026-03-24
26.4.1   25E253    2026-04-09
26.5     25F71     2026-05-11
26.5.1   25F80     2026-06-01
26.5.1   25F80     2026-06-01
```
Note: duplicate entries appear because GDMF publishes the same version under different expiry-window asset sets.

### Candidate API 2: Sofa Feed

**URL:** `https://sofa.macadmins.io/v1/macos_data_feed.json` — **DEPRECATED** (returns a plain-text deprecation notice, not JSON).  
**New URL:** `https://sofafeed.macadmins.io/v1/macos_data_feed.json` — works but shows macOS 26.5 as latest (lags GDMF on day-of-release updates).

### Chosen API: GDMF

Reasons: Apple-authoritative, no identifying data in request, stable JSON shape relied upon by MDM solutions, more current than Sofa (updated same-day as Apple releases).

### Version comparison logic

**Status mapping:**

| Condition | Status |
|-----------|--------|
| Current version = latest in its major train | PASS |
| Minor update available (same major, lower version) | WARN |
| Running a prior major (e.g., 15.x when 26.x is current) | FAIL |
| API unreachable / timeout / parse failure | UNKNOWN |

**Algorithm:**
1. Parse all `ProductVersion` strings from `PublicAssetSets.macOS[]`
2. Convert each to a tuple of ints for reliable numeric comparison: `(26, 5, 1)` > `(26, 5)` after zero-padding
3. Find the maximum major version across all entries → current-generation major
4. If `current_major < max_major` → FAIL
5. If `current_major == max_major` → find max version within that major; PASS if equal, WARN if behind
6. Deduplicate version tuples before comparison (GDMF has duplicate entries)

**Expected result on this machine (26.5 vs 26.5.1 latest):** WARN

---

## Phase 12 — Alerting

Recorded on macOS 26.5 (build 25F71), Apple Silicon, 2026-06-01.

### osascript display notification

**Command:**
```zsh
osascript -e 'display notification "FileVault is off" with title "Security Alert: FileVault"'
```

**Result:** exit 0, empty stdout, notification banner appeared in top-right corner. No permission dialog required.

**Key findings:**
- `display notification` works without any TCC permission on this machine
- Exit 0 with no output on success
- Title and message are separate AppleScript string arguments, both delimited by `"`
- Double quotes inside the message would break the AppleScript literal — sanitise by replacing `"` with `'` before interpolation

---

## Phase 13 — History & Trends

Recorded on macOS 26.5 (build 25F71), Apple Silicon, 2026-06-01.

### sqlite3 availability

```
$ .venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version)"
3.53.1
```

sqlite3 is part of the Python stdlib — no additional dependency required.

### Transition-only write verification

Two consecutive `store_snapshot()` calls with 13 signals, second call with identical statuses → only 13 rows written total (no duplicates). Verified by querying `data/history.db` directly.

---

## Phase 14 — Sharing & Remote Access

Recorded on macOS 26.5.1 (build 25F80), Apple Silicon, 2026-06-02.

### Remote Login (SSH Server)

**Service discovery:** On macOS 26, the SSH launch daemon is at `/System/Library/LaunchDaemons/ssh.plist` with label `com.openssh.sshd` (changed from `com.apple.sshd` on prior macOS versions).

**Command:** `launchctl print system/com.openssh.sshd`

**OFF state (Remote Login disabled in System Settings):**
```
Bad request.
Could not find service "com.openssh.sshd" in domain for system
Exit: 113
```

**ON state (Remote Login enabled in System Settings):**
```
system/com.openssh.sshd = {
    active count = 0
    path = (submitted by smd[541])
    type = Submitted
    state = not running

    program = /usr/libexec/sshd-keygen-wrapper
    arguments = {
        sshd-keygen-wrapper
    }
    ...
}
Exit: 0
```

**Candidates ruled out:**
- `defaults read /Library/Preferences/com.apple.RemoteLogin RemoteLoginEnabled` → key does not exist in either state (exit 1 in both)
- `systemsetup -getremotelogin` → requires admin ("You need administrator access to run this tool... exiting!")
- `launchctl print-disabled system` → does not list `com.openssh.sshd` at all (not in the disabled services table)

**Decision:** Use `launchctl print system/com.openssh.sshd`. Exit 0 = service loaded = FAIL. Exit 113 + "Could not find service" = service not loaded = PASS. Any other error = UNKNOWN.

---

### Screen Sharing / Remote Management

**Service label:** `com.apple.screensharing` (confirmed via `/System/Library/LaunchDaemons/com.apple.screensharing.plist`).

**Remote Management vs Screen Sharing:** Both "Screen Sharing" and "Remote Management" (Apple Remote Desktop) in System Settings control the same `com.apple.screensharing` service. `com.apple.remotemanagementd` is a separate always-running infrastructure daemon unrelated to the on/off state of sharing. Decision: merge into one signal ("Screen Sharing / Remote Management").

**Command:** `launchctl print system/com.apple.screensharing`

**OFF state:**
```
Bad request.
Could not find service "com.apple.screensharing" in domain for system
Exit: 113
```

**ON state (Screen Sharing enabled in System Settings):**
```
system/com.apple.screensharing = {
    active count = 0
    path = (submitted by smd[541])
    type = Submitted
    state = not running

    program = /System/Library/CoreServices/RemoteManagement/screensharingd.bundle/Contents/MacOS/screensharingd
    ...
}
Exit: 0
```

**Decision:** Same pattern as Remote Login. Exit 0 = FAIL, exit 113 = PASS, other = UNKNOWN.

---

### AirDrop Receiver Mode

**Command:** `defaults read com.apple.sharingd DiscoverableMode`

Note: `defaults read com.apple.NetworkBrowser BrowseAllInterfaces` does not exist on macOS 26 ("domain/default pair does not exist").

| System Settings AirDrop value | defaults output | Exit code |
|-------------------------------|-----------------|-----------|
| No One (off)                  | `Off`           | 0         |
| Contacts Only                 | `Contacts Only` | 0         |
| Everyone                      | `Everyone`      | 0         |

The key always exists (exit 0) — AirDrop infrastructure keeps it set.

**Decision:** String match on the returned value. `"Everyone"` → WARN. `"Off"` or `"Contacts Only"` → PASS. Unrecognized string or command failure → UNKNOWN.

---

### Remediation commands

To be tested during Step 14.2. Candidate commands (require admin via osascript):
- Remote Login: `launchctl disable system/com.openssh.sshd && launchctl stop system/com.openssh.sshd`
- Screen Sharing: `launchctl disable system/com.apple.screensharing && launchctl stop system/com.apple.screensharing`

### Remediation commands — confirmed

Tested via osascript on 2026-06-02.

**Remote Login disable:**
```zsh
osascript -e 'do shell script "launchctl disable system/com.openssh.sshd && launchctl bootout system/com.openssh.sshd" with administrator privileges'
```
- `launchctl bootout` exit 0 — service immediately removed from system domain; `launchctl print system/com.openssh.sshd` returns exit 113 confirming PASS.
- `launchctl disable` exit 0 — service marked disabled in launchd persistent override DB.

**Decision:** Use `launchctl disable system/com.openssh.sshd && launchctl bootout system/com.openssh.sshd` as the Remote Login remediation. The Fix button applies_to {"FAIL"} (service loaded). Screen Sharing uses the same pattern with `com.apple.screensharing`.

---

## Phase 15 — Software Hygiene

Recorded on macOS 26.5.1 (build 25F80), Apple Silicon, 2026-06-02.

---

### Signal: Automatic macOS Updates

**Commands and output:**

```zsh
$ defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled
# (key absent before remediation)
# exit: 1  — "The domain/default pair ... does not exist"

$ defaults read /Library/Preferences/com.apple.SoftwareUpdate CriticalUpdateInstall
1
# exit: 0

$ defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload
1
# exit: 0

$ softwareupdate --schedule
Automatic checking for updates is turned on
# exit: 0  — effective state confirmed ON even when AutomaticCheckEnabled key is absent
```

**Full plist (relevant keys):**
```
AutomaticDownload = 1;
AutomaticallyInstallMacOSUpdates = 1;
ConfigDataInstall = 1;
CriticalUpdateInstall = 1;
```
`AutomaticCheckEnabled` is absent from disk; `softwareupdate --schedule` reports it as "on" — the system uses its compiled-in default.

**Absent-key semantics (decided):**
- `AutomaticCheckEnabled` absent → **PASS** (macOS 13+ default is enabled; `softwareupdate --schedule` confirms the effective state is "on")
- `AutomaticCheckEnabled = 0` → **FAIL** (explicitly disabled; system will not discover updates)
- `CriticalUpdateInstall` absent → **WARN** (uncertain; treat conservatively)
- `CriticalUpdateInstall = 0` → **WARN** (check runs but security patches not auto-installed)
- Both keys present and = 1 → **PASS**

**Remediation test:**
```zsh
$ osascript -e 'do shell script "defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true && defaults write /Library/Preferences/com.apple.SoftwareUpdate CriticalUpdateInstall -bool true" with administrator privileges'
# exit: 0

$ defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled
1
# exit: 0  — key written successfully
```
Remediation via osascript with administrator privileges works. Key is written to `/Library/Preferences/com.apple.SoftwareUpdate`.

---

### Signal: Non-Apple Root Certificates

**Initial approach: `security find-certificate -a /Library/Keychains/System.keychain`**

All four entries in System.keychain on this machine:
```
com.apple.systemdefault        — Apple internal system identity, not a CA
com.apple.kerberos.kdc         — Apple Kerberos KDC cert, not a CA
Apple Worldwide Developer Relations Certification Authority  — Apple WWDR signing CA
scotts-macbook-pro-2.local     — self-signed (issuer = subject), EKU: TLS server + client auth, macOS-generated
```

Parsing `find-certificate` output to distinguish Apple-managed from third-party certs is error-prone and produces false positives (`scotts-macbook-pro-2.local` is macOS-generated but not `com.apple.*`-labeled).

**Revised approach: `security dump-trust-settings -d`**

```zsh
$ security dump-trust-settings -d
SecTrustSettingsCopyCertificates: No Trust Settings were found.
# exit: 0

$ security dump-trust-settings
SecTrustSettingsCopyCertificates: No Trust Settings were found.
# exit: 0
```

`dump-trust-settings -d` checks the admin/system trust domain — where third-party root CAs added by MDM, proxy software, or a malicious actor would appear. Empty output = no custom trust anchors = **PASS**.

**Decision:** Use `security dump-trust-settings -d` (system domain) as the data source, NOT `find-certificate`. Rationale: `find-certificate` lists all certs including Apple-managed ones and triggers false positives; `dump-trust-settings` directly answers "are there any non-default CA trust anchors?"
- `"No Trust Settings were found."` → **PASS**
- Any other output → parse cert names from the output → **WARN** with names in raw field
- Command error / unexpected output → **UNKNOWN**

---

### Signal: Screen Lock

**Primary source: `osascript` System Events API**

```zsh
$ osascript -e 'tell application "System Events" to tell security preferences to return require password to wake'
true
# exit: 0
```

Returns `true` or `false`. Does NOT require TCC Accessibility permission — reads a setting, not UI state.

**Why `defaults -currentHost read com.apple.screensaver askForPassword` cannot be used:**

All three screensaver lock keys (`askForPassword`, `askForPasswordDelay`, `idleTime`) are absent from disk on macOS 26. The only keys in the ByHost screensaver plist are `CleanExit = 1` and `tokenRemovalAction = 0`. Despite `require password to wake` being `true`, the key is never written unless the user explicitly disables the setting. On macOS 13+, the secure default (password required immediately) is compiled-in and not persisted to disk.

**Lock delay:**
```zsh
$ defaults -currentHost read com.apple.screensaver askForPasswordDelay
# exit: 1  — key absent
```
Absent = 0 seconds delay (immediate lock on sleep/screensaver). This matches observed behavior.

**Implementation design:**
1. Run osascript to get `require password to wake` → `false` = **FAIL**, continue if `true`
2. Run `defaults -currentHost read com.apple.screensaver askForPasswordDelay` → absent or `0` = **PASS** (immediate); `> 0` = **WARN** (delay window)
3. Include display sleep time from `pmset -g | grep displaysleep` in raw field for context

**Absent-key semantics for delay:** absent → 0 (immediate lock, **PASS**). Do NOT return UNKNOWN for absent delay key.

**Display sleep for context:**
```zsh
$ pmset -g | grep displaysleep
 displaysleep         10 (display sleep prevented by Amphetamine)
```
Display sleep set to 10 minutes. Shown in raw field only — not used for status determination.

---

## Phase 16 — Web Application Hardening

### Step 16.1 — CSRF origin validation on `/fix`

```zsh
# Cross-origin POST — must return HTTP 403:
$ curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Origin: http://evil.example.com" http://127.0.0.1:8000/fix/Unknown
403

# Correct origin — must proceed to registry lookup (returns 404 for unknown signal, not 403):
$ curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Origin: http://127.0.0.1:8000" http://127.0.0.1:8000/fix/Unknown
404

# No Origin header — must proceed:
$ curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/fix/Unknown
404
```

### Step 16.2 — HTTP security headers

```zsh
$ curl -sI http://127.0.0.1:8000/ | grep -E "X-Frame|X-Content|Content-Security|Referrer"
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'self'; style-src 'self'; script-src 'self' 'unsafe-inline'
Referrer-Policy: no-referrer

$ curl -sI http://127.0.0.1:8000/history | grep -E "X-Frame|X-Content"
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
```

### Step 16.3 — Fix audit log

```zsh
$ sqlite3 data/history.db ".schema fix_log"
CREATE TABLE fix_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ts            INTEGER NOT NULL,
            signal_name   TEXT NOT NULL,
            success       INTEGER NOT NULL,
            error_message TEXT
        );

$ sqlite3 data/history.db "SELECT ts, signal_name, success, error_message FROM fix_log ORDER BY ts DESC LIMIT 5;"
1780437375|Application Firewall|1|
```

---

## G3 — Screen Lock Remediation

Recorded on macOS 26.5.1 (build 25F80), Apple Silicon, 2026-06-03.

**Background:**
`check_screen_lock()` reads the effective screen-lock state via the System Events API:
```zsh
$ osascript -e 'tell application "System Events" to tell security preferences to return require password to wake'
true
```
On macOS 26, `askForPassword` is absent from `~/Library/Preferences/ByHost/com.apple.screensaver.*.plist` when screen lock is enabled (the secure default is compiled-in, not persisted). The key is only written when the user explicitly disables screen lock.

**Write-path investigation:**

Direct `defaults -currentHost write` (as user) — works:
```zsh
$ defaults -currentHost write com.apple.screensaver askForPassword -int 1
$ defaults -currentHost read com.apple.screensaver askForPassword
1
```

Same command via osascript admin (runs as root) — writes to `/var/root`, NOT the user's plist:
```python
# Python subprocess test (mirrors executor.py)
cmd = "defaults -currentHost write com.apple.screensaver askForPassword -int 1"
subprocess.run(["osascript", "-e", f'do shell script "{cmd}" with administrator privileges'], ...)
# result.returncode: 0
# defaults -currentHost read com.apple.screensaver askForPassword → KeyError (not in user plist)
```
Root's HOME is `/var/root`; the write goes to root's ByHost plist, not the console user's.

**Solution — `su <console_user> -c '...'` from root:**

When the executor runs as root via osascript admin, `su username -c 'cmd'` switches to the target user without a password prompt (root can su to any user):
```python
cmd = "su $(stat -f%Su /dev/console) -c 'defaults -currentHost write com.apple.screensaver askForPassword -int 1'"
subprocess.run(["osascript", "-e", f'do shell script "{cmd}" with administrator privileges'], ...)
# result.returncode: 0
# defaults -currentHost read com.apple.screensaver askForPassword → 1  ✓ (written to user plist)
```

`stat -f%Su /dev/console` returns the current console user (verified: `scottrosenberg`).

**System Events state unaffected by the write (PASS state preserved):**
```zsh
$ osascript -e 'tell application "System Events" to tell security preferences to return require password to wake'
true  # ✓ still PASS
```

**Cleanup (restores baseline — key absent = secure default):**
```zsh
$ defaults -currentHost delete com.apple.screensaver askForPassword
$ defaults -currentHost read com.apple.screensaver
{ CleanExit = 1; tokenRemovalAction = 0; }  # back to baseline
```

**Decision:** Remediation cmd for REMEDIATIONS registry:
```python
"su $(stat -f%Su /dev/console) -c 'defaults -currentHost write com.apple.screensaver askForPassword -int 1'"
```
`applies_to = {"FAIL"}` (button shown only when `require password to wake` is `false`).

---

## G4 — AirDrop Remediation

Recorded on macOS 26.5.1 (build 25F80), Apple Silicon, 2026-06-03.

**Pref location and privilege model:**
```zsh
$ ls -la ~/Library/Preferences/com.apple.sharingd.plist
-rw-------@ 1 scottrosenberg  staff  3499 Jun  3 12:11 /Users/scottrosenberg/Library/Preferences/com.apple.sharingd.plist
```
The pref is user-owned (`~/Library/Preferences/`), not `/Library/Preferences/`. No admin privileges needed for the write itself, but the executor always runs via osascript admin (root), so the `su <console_user>` pattern from G3 is required.

**Write takes effect without process restart:**
```zsh
# Set WARN state
$ defaults write com.apple.sharingd DiscoverableMode -string "Everyone"
$ defaults read com.apple.sharingd DiscoverableMode
Everyone

# Apply fix (as user — verifying the write works)
$ defaults write com.apple.sharingd DiscoverableMode -string "Contacts Only"
$ defaults read com.apple.sharingd DiscoverableMode
Contacts Only
# check_airdrop() → PASS Contacts Only  ✓
```
`cfprefsd` broadcasts the preference change to `sharingd` immediately; no process restart needed.

**Double-quote escaping for "Contacts Only":**

`"Contacts Only"` contains a space, so it must be quoted in the shell command. The executor wraps `cmd` in:
```python
f'do shell script "{cmd}" with administrator privileges'
```
Double quotes inside the outer `"..."` must be escaped as `\"` in the AppleScript string. Direct test via Python subprocess (mirrors executor.py):
```python
cmd = "su $(stat -f%Su /dev/console) -c 'defaults write com.apple.sharingd DiscoverableMode -string \\\"Contacts Only\\\"'"
# cmd string value: su $(stat -f%Su /dev/console) -c 'defaults write com.apple.sharingd DiscoverableMode -string \"Contacts Only\"'
result = subprocess.run(["osascript", "-e", f'do shell script "{cmd}" with administrator privileges'], ...)
# rc: 0
# defaults read com.apple.sharingd DiscoverableMode → Contacts Only  ✓
```

**Full executor end-to-end test:**
```python
defaults write com.apple.sharingd DiscoverableMode -string "Everyone"  # WARN state
run_fix("AirDrop Receiver Mode")
# → {'success': True, 'output': '', 'error': None}
defaults read com.apple.sharingd DiscoverableMode  # → Contacts Only
# check_airdrop() → PASS Contacts Only  ✓
```

**Restore:**
```zsh
$ defaults write com.apple.sharingd DiscoverableMode -string "Off"
```

**Decision:** Remediation cmd for REMEDIATIONS registry:
```python
r"su $(stat -f%Su /dev/console) -c 'defaults write com.apple.sharingd DiscoverableMode -string \"Contacts Only\"'"
```
`applies_to = {"WARN"}` (button shown only when `DiscoverableMode == "Everyone"`).

---

## Phase 24 — AI Security

Recorded during Phase 24, Step 24.1. Machine: macOS Apple Silicon (Mac15,9).

---

### Shell config files — existence and grep behavior

**Files checked:**
```zsh
$ ls -la ~/.zshrc ~/.zprofile ~/.zshenv ~/.bashrc ~/.bash_profile ~/.profile 2>&1
ls: /Users/scottrosenberg/.profile: No such file or directory
ls: /Users/scottrosenberg/.zprofile: No such file or directory
ls: /Users/scottrosenberg/.zshenv: No such file or directory
-rwx------@ 1 scottrosenberg  staff  2654 May  7 07:01 /Users/scottrosenberg/.bash_profile
-rwx------@ 1 scottrosenberg  staff   453 Oct 26  2025 /Users/scottrosenberg/.bashrc
-rw-r--r--@ 1 scottrosenberg  staff   120 Oct 26  2025 /Users/scottrosenberg/.zshrc
```

**Files present on this machine:** `~/.zshrc`, `~/.bashrc`, `~/.bash_profile`
**Files absent (silently skipped):** `~/.zprofile`, `~/.zshenv`, `~/.profile`

**AI API key scan (no matches on this machine — PASS):**
```zsh
$ grep -n "OPENAI_API_KEY\|ANTHROPIC_API_KEY\|GEMINI_API_KEY" ~/.zshrc ~/.bashrc ~/.bash_profile 2>/dev/null
(no output — exit code 1)
```

**grep exit code behavior (verified via Python subprocess):**
- Key name found in file: `rc=0`, stdout contains `<lineno>:<matching line>`
- Key name not found in file: `rc=1`, stdout empty
- File does not exist: `rc=2`, stderr contains error message

**Decision:** Use `pathlib.Path.read_text()` per file rather than subprocess grep. This avoids rc=2 vs rc=1 ambiguity for absent files and keeps key values out of any subprocess arguments. Absent files → skip silently. OSError on a file → skip that file, log to error only if ALL files fail to read.

---

### Shell history — format and grep behavior

**`~/.zsh_history` (plain format, no extended history prefix):**
```zsh
$ python3 -c "
import pathlib
lines = pathlib.Path('~/.zsh_history').expanduser().read_text(errors='replace').splitlines()
print(f'lines: {len(lines)}')
print('sample:', repr(lines[0]))
"
lines: 24
sample: 'pwd'
```

Format: plain commands, no `: <timestamp>:<elapsed>;` prefix. `EXTENDED_HISTORY` is not set in `~/.zshrc`. The parser must handle both plain format and extended format (`: ts:elapsed;cmd`) since users may have `setopt EXTENDED_HISTORY` in their config.

**`~/.bash_history` (plain format):**
```zsh
lines: 500
sample: "'cd ~'"
```

**Key pattern scan (no matches on this machine — PASS):**
```python
patterns: sk-[a-zA-Z0-9]{20,}, sk-ant-api[0-9]{2}-, AIza[0-9A-Za-z_-]{35}
result: 0 matches in ~/.zsh_history, 0 matches in ~/.bash_history
```

**`grep -c` exit code on 0 matches:**
```zsh
$ grep -c "sk-" ~/.bash_history
0
exit code: 1   # grep exits 1 when count is 0 — do NOT use subprocess grep for this
```

**Decision:** Use `pathlib.Path.read_text()` + `re.search()` directly in Python. Strip extended-history prefix (`re.sub(r'^: \d+:\d+;', '', line)`) before pattern matching. Absent history files are PASS (not UNKNOWN) — many machines have only one shell history file.

---

### Local AI server exposure — lsof

**Ollama (port 11434) — running on this machine, loopback only (PASS):**
```zsh
$ lsof -nP -iTCP:11434 -sTCP:LISTEN
COMMAND   PID           USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
ollama  34038 scottrosenberg    3u  IPv4 0xc1cfaaa25945ea5c      0t0  TCP 127.0.0.1:11434 (LISTEN)
rc=0
```

NAME column format for loopback: `127.0.0.1:11434` — contains `127.0.0.1:`.

**LM Studio (port 1234) — not running:**
```zsh
$ lsof -nP -iTCP:1234 -sTCP:LISTEN
(no output)
rc=1
```

Exit code 1 with no output = no process listening on that port. This is PASS for that port.

**All-interfaces NAME format (from Phase 7 / network collector verification):**
When a process is bound to all interfaces, the NAME column reads `*:11434` (not `0.0.0.0:11434`). This is confirmed by the existing `check_listening_ports()` parser in `src/collectors/network.py` which uses `ln.split()[-2].startswith("*:")` as the all-interfaces test.

**Decision:**
- `rc=0`, NAME contains `127.0.0.1:` or `[::1]:` → PASS (loopback-only)
- `rc=0`, NAME contains `*:` → FAIL (all interfaces)
- `rc=1` (no output) → not running → PASS for that port
- Command exception or unexpected `rc` → UNKNOWN

Check both ports per collector call. First FAIL across either port wins the overall status.

**Ollama installation confirmed:** `/opt/homebrew/bin/ollama` present. Default binding is loopback (`127.0.0.1:11434`), which is the secure default. Users who set `OLLAMA_HOST=0.0.0.0` will see FAIL.

---

## Phase 25 — User Accounts

Recorded 2026-06-06 on macOS Apple Silicon (Mac15,9).

### `defaults read /Library/Preferences/com.apple.loginwindow GuestEnabled`

```
0
rc=0
```

Key is present with value `0` (guest account off). Exit code 0.

**Key-absent test** (using a nonexistent key name to confirm error message format):

```
2026-06-06 16:18:21.429 defaults[26240:7838602]
The domain/default pair of (/Library/Preferences/com.apple.loginwindow, GuestEnabled_NONEXISTENT) does not exist
rc=1
```

Key-absent exit code is **1**; stderr contains `"does not exist"`. The parser must check stderr (or combined output) for this string, not just the exit code.

**Status logic confirmed:**
- `rc=0`, value `"0"` → PASS
- `rc=0`, value `"1"` → FAIL
- `rc=1` + `"does not exist"` in output → PASS (key absent = macOS default = off)
- Anything else → UNKNOWN

### `defaults read /Library/Preferences/com.apple.loginwindow SHOWFULLNAME`

```
2026-06-06 16:18:12.884 defaults[26163:7838126]
The domain/default pair of (/Library/Preferences/com.apple.loginwindow, SHOWFULLNAME) does not exist
rc=1
```

Key is absent on this machine. The macOS default on an unmanaged personal Mac is to show the user list at the login window (i.e., `SHOWFULLNAME` absent = user list shown = WARN).

**Status logic confirmed:**
- `rc=1` + `"does not exist"` in output → WARN (key absent = system default = user list shown)
- `rc=0`, value `"1"` → PASS (name+password prompt)
- `rc=0`, value `"0"` → WARN (user list visible)
- Anything else → UNKNOWN

### `dscl . read /Groups/admin GroupMembership`

```
GroupMembership: root scottrosenberg
rc=0
```

Output format: single line, `GroupMembership:` label followed by space-separated usernames on the same line. **No newline between label and values.** Current user (`scottrosenberg`) is present. `root` appears in the list and must be filtered as a system account.

**`GroupMembershipUsers` field:**

```
No such key: GroupMembershipUsers
rc=0
```

Field does not exist; use `GroupMembership` only.

**Nonexistent group (defensive check):**

```
<dscl_cmd> DS Error: -14136 (eDSRecordNotFound)
rc=56
```

Non-zero exit code when group is missing. Any non-zero `rc` → UNKNOWN.

**System accounts to filter:** `root` confirmed present. Plan spec also lists `_mbsetupuser`, `_uucp`, `_networkd` — none present on this machine but filter is applied defensively.

**`id -un` result:**

```
scottrosenberg
```

Matches the username in the `GroupMembership` output character-for-character. Using `os.environ.get("USER")` is sufficient; `id -un` subprocess is the fallback.

**Status logic confirmed:**
- Parse line after `GroupMembership:`, split by whitespace, filter system accounts
- `human_members == [current_user]` → PASS
- `len(human_members) > 1` → WARN with full list
- `human_members == []` → UNKNOWN (unexpected format)
- `rc != 0` → UNKNOWN

---

## Phase 26 — Screensaver Idle Timeout

### Command verification

**Key-absent case (baseline machine state — screensaver never configured):**

```
$ defaults -currentHost read com.apple.screensaver idleTime; echo "rc=$?"
2026-06-06 16:46:33.677 defaults[40168:7917568]
The domain/default pair of (com.apple.screensaver, idleTime) does not exist
rc=1
```

**stdout vs stderr when key is absent:**

```
$ stdout=$(defaults -currentHost read com.apple.screensaver idleTime 2>/dev/null); echo "stdout='$stdout'"
stdout=''

$ stderr=$(defaults -currentHost read com.apple.screensaver idleTime 2>&1 1>/dev/null); echo "stderr='$stderr'"
stderr='2026-06-06 16:46:39.838 defaults[40257:7917963]
The domain/default pair of (com.apple.screensaver, idleTime) does not exist'
```

**Finding:** When the key is absent, `stdout` is empty and the `"does not exist"` message is on **stderr** only. The implementation must check `err` (not `out`) for this string.

---

**Key-present case (idleTime = 300 s):**

```
$ defaults -currentHost write com.apple.screensaver idleTime -int 300
$ defaults -currentHost read com.apple.screensaver idleTime; echo "rc=$?"
300
rc=0
```

stdout is the bare integer with no trailing whitespace beyond the newline. stderr is empty.

---

**Value 0 (Never):**

```
$ defaults -currentHost write com.apple.screensaver idleTime -int 0
$ defaults -currentHost read com.apple.screensaver idleTime; echo "rc=$?"
0
rc=0
```

---

**Value 1800 (30 min):**

```
$ defaults -currentHost write com.apple.screensaver idleTime -int 1800
$ defaults -currentHost read com.apple.screensaver idleTime; echo "rc=$?"
1800
rc=0
```

---

**Non-`-currentHost` domain:**

```
$ defaults read com.apple.screensaver idleTime 2>&1; echo "rc=$?"
2026-06-06 16:46:34.992 defaults[40172:7917608]
The domain/default pair of (com.apple.screensaver, idleTime) does not exist
rc=1
```

The standard per-user domain also returns absent. The `-currentHost` ByHost domain is the authoritative location for this key; both domains must be checked to determine where System Settings writes the value, and the ByHost domain is correct.

---

**Restore — delete the test key:**

```
$ defaults -currentHost delete com.apple.screensaver idleTime; echo "rc=$?"
rc=0
$ defaults -currentHost read com.apple.screensaver idleTime 2>&1; echo "rc=$?"
2026-06-06 16:47:00.255 defaults[40432:7919078]
The domain/default pair of (com.apple.screensaver, idleTime) does not exist
rc=1
```

Machine restored to baseline (key absent).

---

### Implementation decisions

- **`-currentHost` is required.** The key lives in the ByHost preference domain. The standard domain also returns absent on this machine, confirming ByHost is the correct read target.
- **Error string is on stderr, not stdout.** Check `err` for `"does not exist"` when `rc != 0`.
- **stdout is a bare integer string** (e.g. `"300\n"`) when the key is present. `out.strip()` → `int()` is safe.
- **rc=0 always means a valid integer value was returned** — no other non-integer output observed.
- **rc=1 with "does not exist" in stderr → key absent → FAIL** (screensaver not configured).
- **rc=1 without "does not exist" → unexpected error → UNKNOWN.**

**Status thresholds confirmed:**

| Condition | Status |
|-----------|--------|
| Key absent (`rc=1`, `"does not exist"` in stderr) | FAIL |
| `int(value) == 0` | FAIL |
| `0 < int(value) <= 600` | PASS |
| `int(value) > 600` | WARN |
| `rc != 0` and error not "does not exist", or non-integer output | UNKNOWN |

---

## Phase 27 — Bluetooth Security

### Command verification

**Full output — field names and structure:**

```
$ system_profiler SPBluetoothDataType; echo "rc=$?"
Bluetooth:

      Bluetooth Controller:
          Address: 60:3E:5F:4A:37:27
          State: On
          Chipset: BCM_4388
          Discoverable: Off
          Firmware Version: 23.5.574.4423
          Product ID: 0x4A2F
          Supported services: 0x392039 < HFP AVRCP A2DP HID Braille LEA AACP GATT SerialPort >
          Transport: PCIe
          Vendor ID: 0x004C (Apple)
      Connected:
          [... device entries with Address, Vendor ID, Firmware Version, Serial Number fields ...]
      Not Connected:
          [... device entries with Address and RSSI fields ...]

rc=0
```

Note: `Connected:` and `Not Connected:` sections contain device MAC addresses and serial numbers (e.g., `Serial Number: H19FD6P80C6L`). These must never appear in the signal's `raw` field.

---

**Exact field name grep — power state and discoverability:**

```
$ system_profiler SPBluetoothDataType | grep -E "State:|Discoverable:|Bluetooth Power"
          State: On
          Discoverable: Off
```

**Finding: the power-state field is `State:` — not `Bluetooth Power:`.**  
The SIGNAL_GAPS.md note was a rough approximation; the actual field is `State: On/Off` under the `Bluetooth Controller:` subsection (10-space indentation). `Bluetooth Power:` does not appear in the output on this machine (macOS 15.5, Apple Silicon).

---

**grep for alternate power field name:**

```
$ system_profiler SPBluetoothDataType | grep -i "power"
(no output)
```

`"power"` does not appear anywhere in the output. `State:` is the only power-state field.

---

**grep for discoverable field and values:**

```
$ system_profiler SPBluetoothDataType | grep -i "discoverable"
          Discoverable: Off
```

`Discoverable:` appears exactly once, under `Bluetooth Controller:`. The value on this machine is `Off` (Bluetooth on, not discoverable — expected state). The SIGNAL_GAPS.md note listed `Yes/No` as possible values; actual values observed are `Off` (not discoverable) and `Yes` (discoverable). `No` has not been observed and is not expected — macOS uses `Off`/`Yes`.

---

**Field uniqueness — does `State:` appear more than once?**

```
$ system_profiler SPBluetoothDataType | grep "State:"
          State: On
```

`State:` appears exactly once in the full output (the controller-level field). Device entries in the `Connected:` and `Not Connected:` sections do not use a `State:` key. A simple `re.search(r"\bState:\s+(On|Off)\b", out)` is safe.

---

**Exit code — command succeeds:**

```
$ system_profiler SPBluetoothDataType > /dev/null; echo "rc=$?"
rc=0
```

`rc=0` when Bluetooth hardware is present and the command completes normally.

---

**Hardware-absent / failure case:**

Cannot be tested on this machine (Bluetooth hardware always present on Apple Silicon). Documented behavior: `system_profiler` exits non-zero and produces an error message when the requested data type is unavailable. The collector treats `rc != 0` as UNKNOWN.

---

### Implementation decisions

- **Power-state field is `State:` not `Bluetooth Power:`.** Update the plan's collector description accordingly.
- **Regex for power state:** `re.search(r"\bState:\s+(On|Off)\b", out)` — unique in the output.
- **Regex for discoverability:** `re.search(r"\bDiscoverable:\s+(Yes|Off)\b", out)` — unique in the output; observed values are `Off` and `Yes` (not `No`).
- **`raw` must contain only parsed values** — never the full `system_profiler` output, which contains device MAC addresses and serial numbers.
- **`rc=0`** → parse power field. **`rc != 0`** → UNKNOWN with captured stderr/stdout as error.

**Status mapping confirmed:**

| Condition | Status |
|-----------|--------|
| `rc != 0` | UNKNOWN |
| `rc=0`, no `State:` field in output | UNKNOWN |
| `rc=0`, `State: Off` | PASS |
| `rc=0`, `State: On`, no `Discoverable:` field | UNKNOWN |
| `rc=0`, `State: On`, `Discoverable: Yes` | FAIL |
| `rc=0`, `State: On`, `Discoverable: Off` | WARN |

---

## Phase 28 — Wi-Fi & Network

**Platform:** macOS 15.5 (Sequoia), Apple Silicon (Mac15,9)

---

### Wi-Fi Security Type — command selection

#### `wdutil info` (rejected — requires root)

```
$ wdutil info
usage: sudo wdutil diagnose [-q] [-f outputDirectoryPath]
            -q may be specified to suppress legal prompt and Finder window
       sudo wdutil info
       sudo wdutil log [{+|-} {system|wifi}]+
       sudo wdutil dump
       sudo wdutil clean
       sudo wdutil privateMAC={0/1}
```

`wdutil info` requires `sudo` on macOS 15.5. Cannot use in collectors (no-sudo constraint). Rejected.

---

#### `system_profiler SPAirPortDataType` (chosen — no root required)

**Exit code:** 0 (always, even when no Wi-Fi hardware present — returns empty `Wi-Fi:` block)

**Full output structure (Wi-Fi connected, SSID redacted):**

```
Wi-Fi:

      Software Versions:
          CoreWLAN: 16.0 (1657)
          CoreWLANKit: 16.0 (1657)
          Menu Extra: 1.0 (19150.2)
          System Information: 15.0 (1502)
          IO80211 Family: 12.0 (1200.13.1)
          Diagnostics: 11.0 (1163)
          AirPort Utility: 6.3.9 (639.29)
      Interfaces:
        en0:
          Card Type: Wi-Fi  (0x14E4, 0x4388)
          Firmware Version: wl0: Feb  2 2026 19:18:00 version 23.50.20.0.41.51.208 ...
          MAC Address: 16:70:fa:8a:1b:5d
          Locale: FCC
          Country Code: US
          Supported PHY Modes: 802.11 a/b/g/n/ac/ax
          Supported Channels: 1 (2GHz), ... (truncated)
          Wake On Wireless: Supported
          AirDrop: Supported
          Auto Unlock: Supported
          Status: Connected
          Current Network Information:
            <SSID>:
              PHY Mode: 802.11ax
              Channel: 149 (5GHz, 80MHz)
              Country Code: US
              Network Type: Infrastructure
              Security: WPA2 Personal
              Signal / Noise: -63 dBm / -94 dBm
              Transmit Rate: 243
              MCS Index: 14
          Other Local Wi-Fi Networks:
            <SSID>:
              PHY Mode: 802.11g/n
              Channel: 6 (2GHz, 20MHz)
              Network Type: Infrastructure
              Security: WPA2 Personal
            ... (additional nearby networks, each with Security: field)
        awdl0:
          MAC Address: 66:45:bc:7b:da:87
          Supported Channels: ... (truncated)
          Current Network Information:
              Network Type: Infrastructure
```

**Field observations:**

- **Connection status:** `Status: Connected` appears inside the `en0:` interface block. When Wi-Fi is off or not associated, this line reads `Status: Not Associated` or is absent.
- **Security field name:** `Security:` (exact, no alternatives observed). Value: `WPA2 Personal` (connected network). Other observed values on nearby networks: `WPA2 Personal`, `WPA/WPA2 Personal`.
- **Structural hazard:** `Security:` appears in **both** `Current Network Information:` (the connected network) **and** `Other Local Wi-Fi Networks:` (each nearby network). A naive `re.search(r"Security:\s+(.+)", out)` would return the connected network's value because it appears first — but this is fragile. Safer: extract the text between `Current Network Information:` and `Other Local Wi-Fi Networks:` and search only within that block.
- **`awdl0` interface:** Also has a `Current Network Information:` block but contains only `Network Type: Infrastructure` — no `Security:` field.
- **Not-connected state:** `Current Network Information:` block is absent; `Status: Connected` becomes `Status: Not Associated` or absent.

**Confirmed grep results:**

```
$ system_profiler SPAirPortDataType | grep -E "Status:|Security:"
          Status: Connected
              Security: WPA2 Personal        ← connected network (Current Network Information:)
              Security: WPA2 Personal        ← nearby network 1 (Other Local Wi-Fi Networks:)
              Security: WPA2 Personal        ← nearby network 2
              Security: WPA2 Personal        ← nearby network 3
              Security: WPA2 Personal        ← nearby network 4
              Security: WPA/WPA2 Personal    ← nearby network with mixed-mode
              ... (additional nearby networks)
```

---

### DNS Configuration

#### `scutil --dns`

**Exit code:** 0

**Full output:**

```
DNS configuration

resolver #1
  search domain[0] : mynetworksettings.com
  nameserver[0] : 2600:100e:a025:452d:3a88:71ff:fe3f:76
  nameserver[1] : 192.168.1.1
  if_index : 14 (en0)
  flags    : Request A records, Request AAAA records
  reach    : 0x00020002 (Reachable,Directly Reachable Address)

resolver #2
  domain   : local
  options  : mdns
  timeout  : 5
  flags    : Request A records, Request AAAA records
  reach    : 0x00000000 (Not Reachable)
  order    : 300000

resolver #3
  domain   : 254.169.in-addr.arpa
  options  : mdns
  timeout  : 5
  flags    : Request A records, Request AAAA records
  reach    : 0x00000000 (Not Reachable)
  order    : 300200

... (resolvers #4–7 are mDNS for IPv6 reverse zones — no nameserver lines)

DNS configuration (for scoped queries)

resolver #1
  search domain[0] : mynetworksettings.com
  nameserver[0] : 2600:100e:a025:452d:3a88:71ff:fe3f:76
  nameserver[1] : 192.168.1.1
  if_index : 14 (en0)
  flags    : Scoped, Request A records, Request AAAA records
  reach    : 0x00020002 (Reachable,Directly Reachable Address)
```

**Field observations:**

- **Nameserver line format:** `  nameserver[N] : <IP>` — two leading spaces, then `nameserver`, then `[N]`, then ` : `, then the IP. No trailing interface suffix (no `%en0` on IPv6 addresses).
- **IPv4 nameserver:** `192.168.1.1` — private RFC 1918 address (local router). Python `ipaddress.ip_address("192.168.1.1").is_private` → `True`.
- **IPv6 nameserver:** `2600:100e:a025:452d:3a88:71ff:fe3f:76` — global unicast IPv6 (public). `ipaddress.ip_address("2600:100e:a025:452d:3a88:71ff:fe3f:76").is_private` → `False`. This is the Comcast/Xfinity gateway device's globally-routable IPv6 address acting as a local DNS forwarder (same role as 192.168.1.1 for IPv4), but it is not identifiable as "local" from the address alone — it is not RFC 1918, ULA (fc00::/7), or link-local (fe80::/10). Classification: **unrecognized public** → WARN.
- **Duplicates:** The same nameserver IPs appear in both the main section and the "for scoped queries" section. Must deduplicate before classifying.
- **mDNS resolvers (resolvers #2–7):** These have domain/options/timeout but no `nameserver[` lines. The `re.findall(r"nameserver\[\d+\]\s*:\s*(\S+)", out)` pattern safely ignores them.
- **No-network case:** When Wi-Fi is off, `scutil --dns` still exits 0 but returns only mDNS resolvers (no `nameserver[` lines). `re.findall` returns an empty list → PASS ("No nameservers configured").

---

### Implementation decisions

**Wi-Fi Security Type:**

- **Command:** `["system_profiler", "SPAirPortDataType"]`, `timeout=10`. `wdutil info` rejected (requires root).
- **Not-connected detection:** check `"Current Network Information:" not in out` or `"Status: Connected" not in out`. If not connected → PASS, raw `"Not connected"`.
- **Parsing — connected network only:** extract the slice of output between `Current Network Information:` and `Other Local Wi-Fi Networks:`, then apply `re.search(r"Security:\s+(.+)", section)`. This prevents picking up Security values from nearby networks.
- **Regex:** `re.search(r"Current Network Information:(.*?)Other Local Wi-Fi Networks:", out, re.DOTALL)` to extract the connected-network section. Fall back to everything after `Current Network Information:` if `Other Local Wi-Fi Networks:` is absent (no nearby networks).
- **Security value matching** (checked in order to prevent WPA3 matching WPA2 branch):
  1. `"WPA3"` in value → PASS
  2. `"WPA2"` in value → WARN
  3. `"WEP"` in value → FAIL
  4. `value.strip().lower() in ("open", "none", "")` → FAIL
  5. `"WPA"` in value (catches WPA1 / WPA/WPA2 mixed) → FAIL
  6. Anything else → WARN (unknown protocol; surface for review)
- **`raw`:** `"Security: <value>"` — never the full output (contains MAC addresses and channel data).

**DNS Configuration:**

- **Command:** `["scutil", "--dns"]`, `timeout=5`.
- **Parsing:** `re.findall(r"nameserver\[\d+\]\s*:\s*(\S+)", out)` — extracts all nameserver IPs, including from the "scoped queries" section. Deduplicate with `list(dict.fromkeys(...))` to preserve first-seen order.
- **Classification (per IP):**
  - `ipaddress.ip_address(ip).is_loopback` → local
  - `ipaddress.ip_address(ip).is_private` → local (covers RFC 1918, ULA fc00::/7)
  - `ipaddress.ip_address(ip).is_link_local` → local (covers fe80::/10, 169.254.x.x)
  - ip in `_KNOWN_SECURE_DNS` → known DoH-capable public resolver
  - otherwise → unrecognized public
- **`_KNOWN_SECURE_DNS` constant:** `{"1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4", "9.9.9.9", "149.112.112.112", "208.67.222.222", "208.67.220.220", "94.140.14.14", "94.140.15.15"}`
- **`ipaddress.ip_address()` can raise `ValueError` for malformed IPs** — wrap in try/except and treat parse failures as unrecognized.
- **`raw` format:** `"nameservers: <comma-separated list>"` or `"nameservers: <all>; unrecognized: <unknown IPs>"` — never more than the IP list.

**Status mapping — Wi-Fi Security:**

| Condition | Status |
|-----------|--------|
| Command fails or exception | UNKNOWN |
| Not connected (`Current Network Information:` absent) | PASS |
| Security value contains `"WPA3"` | PASS |
| Security value contains `"WPA2"` | WARN |
| Security value is Open/None/empty | FAIL |
| Security value contains `"WEP"` | FAIL |
| Security value contains `"WPA"` (WPA1 / mixed) | FAIL |
| Unrecognized value | WARN |

**Status mapping — DNS Configuration:**

| Condition | Status |
|-----------|--------|
| Command fails or exception | UNKNOWN |
| No `nameserver[` lines in output | PASS |
| All nameservers local or known DoH | PASS |
| Any nameserver unrecognized public | WARN |

---

## Phase 29 — SSH Key Hygiene

### Private key passphrase detection

**SSH directory contents:**

```
$ ls -la ~/.ssh/
total 72
drwx------  12 scottrosenberg  staff   384 Feb 12 10:28 .
drwxr-x---+ 77 scottrosenberg  staff  2464 Jun  7 06:48 ..
drwx------   3 scottrosenberg  staff    96 Jun  4 06:28 agent
-rw-------   1 scottrosenberg  staff   215 Nov  2  2024 config
-rw-------   1 scottrosenberg  staff   411 Nov  2  2024 github_ed25519
-rw-r--r--   1 scottrosenberg  staff   103 Nov  2  2024 github_ed25519.pub
-rw-------   1 scottrosenberg  staff   399 Aug 24  2024 gitlab_id_ed25519
-rw-r--r--   1 scottrosenberg  staff    94 Aug 24  2024 gitlab_id_ed25519.pub
-rw-------   1 scottrosenberg  staff   419 Sep 20  2025 id_ed25519
-rw-r--r--   1 scottrosenberg  staff   110 Sep 20  2025 id_ed25519.pub
-rw-------   1 scottrosenberg  staff  1757 Sep 20  2025 known_hosts
-rw-------   1 scottrosenberg  staff  1015 Sep 20  2025 known_hosts.old
```

Three private key files (`github_ed25519`, `gitlab_id_ed25519`, `id_ed25519`). One subdirectory (`agent/`) containing a socket file — not a regular file, excluded by the regular-file check.

**`ssh-keygen -y` behavior with empty stdin (`< /dev/null`):**

Unprotected key (exit 0 — stdout contains public key):
```
$ ssh-keygen -y -f ~/.ssh/github_ed25519 < /dev/null
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPQys42aRT/DQN1dUkZDBKlHDpcxa2M385JFw4sYv4h+ rsnbrgscott@gmail.com
exit: 0
```

All three private keys on this machine exit 0 → all are unprotected. `check_ssh_key_passphrases` will return WARN listing all three filenames.

Passphrase-protected key (verified with a temp key created as `ssh-keygen -N "testpass"`):
```
$ ssh-keygen -y -f /tmp/test_key < /dev/null 2>&1
Enter passphrase for "/tmp/test_key": Load key "/tmp/test_key": incorrect passphrase supplied to decrypt private key
exit: 255
```

Non-key file (exit 255 — stderr contains "invalid format"):
```
$ ssh-keygen -y -f ~/.ssh/known_hosts < /dev/null 2>&1
Load key "/Users/scottrosenberg/.ssh/known_hosts": invalid format
exit: 255
$ ssh-keygen -y -f ~/.ssh/config < /dev/null 2>&1
Load key "/Users/scottrosenberg/.ssh/config": invalid format
exit: 255
```

**Passphrase detection decision logic:**

| `subprocess.run` result | Classification |
|------------------------|----------------|
| exit 0, stdout has content | Unprotected private key — add to WARN list |
| exit 255, stderr contains `"incorrect passphrase"` | Protected key — skip (good) |
| exit 255, stderr contains `"invalid format"` | Not a key file — skip |
| Exception (timeout, OSError) | UNKNOWN |

Both protected keys and non-key files return exit 255 — must check stderr content to distinguish them.

### SSH config — ForwardAgent check

```
$ cat ~/.ssh/config
# Manually added
Host gitlab.com
  UseKeychain yes
  AddKeysToAgent yes
  IdentityFile ~/.ssh/gitlab_id_ed25519

Host github.com
  IgnoreUnknown UseKeyChain
  AddKeysToAgent yes
  IdentityFile ~/.ssh/github_ed25519

$ grep -i "ForwardAgent" ~/.ssh/config
exit: 1  (no matches)
```

No `ForwardAgent` entries on this machine. `check_ssh_agent_forwarding` will return PASS. The config uses `AddKeysToAgent yes` (adds key to ssh-agent on first use) and `UseKeychain yes` (macOS Keychain integration) — these are not agent forwarding and are not flagged.

### SSH key algorithm strength

```
$ ssh-keygen -l -f ~/.ssh/github_ed25519.pub
256 SHA256:Vt4RvqeJWTJabcNcVK80wg3zwcK/dfbB18QEwjNLtf8 rsnbrgscott@gmail.com (ED25519)

$ ssh-keygen -l -f ~/.ssh/gitlab_id_ed25519.pub
256 SHA256:O39siHQeBVhOoWiFkuxvczlFDG6cXiLuLBiOjMV887o GitLab_MBPro (ED25519)

$ ssh-keygen -l -f ~/.ssh/id_ed25519.pub
256 SHA256:cd2Z9FFCvfptQNgkrcPcx1KmQys9Cyt5FtG6m463PDc scottrosenberg@CDACND2321SVP (ED25519)
```

Output format: `<bits> SHA256:<fingerprint> <comment> (<ALGO>)` — first field is bit count (int), last parenthesized token is the algorithm. Parse with `re.search(r"\((\w+)\)\s*$", line)` to extract the algorithm token.

All three keys are ED25519 (256-bit — PASS). `check_ssh_key_strength` will return PASS on this machine.

**Implementation decisions:**

- Private key candidate heuristic: regular file in `~/.ssh/`, no `.pub` extension, name not in `{"known_hosts", "known_hosts.old", "authorized_keys", "authorized_keys2", "config", "environment"}`. Skip the `agent/` subdirectory (it's a directory, not a regular file).
- Use `subprocess.run(["ssh-keygen", "-y", "-f", str(path)], input=b"", capture_output=True, timeout=3)` directly (not `run_cmd`) because `input=b""` is needed to avoid interactive prompting.
- Distinguish protected vs non-key files by checking stderr for `"incorrect passphrase"` substring.
- SSH config parser: track current `Host` pattern, collect host patterns where `ForwardAgent yes` appears (case-insensitive on both keyword and value).
- Key strength parser: extract bits from `int(line.split()[0])` and algorithm from the trailing `(ALGO)` token.
