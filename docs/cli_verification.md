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
