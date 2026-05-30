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

## Summary

| Signal | Command | Root required? | Status on this machine |
|--------|---------|---------------|----------------------|
| SIP | `csrutil status` | No | enabled ✅ |
| Gatekeeper | `spctl --status` | No | assessments enabled ✅ |
| FileVault | `fdesetup status` | No | On ✅ |
| Secure Boot | `system_profiler SPiBridgeDataType` | No | Full Security ✅ |
