# MacBook Security Monitoring Notes

## Overview

This document outlines the security areas to monitor on a macOS system, organized by category. It serves as the foundation for a security monitoring dashboard.

---

## 1. System Integrity

- **SIP (System Integrity Protection)** — Verify SIP is enabled (`csrutil status`)
- **Gatekeeper** — Confirm Gatekeeper is enforcing app signing (`spctl --status`)
- **FileVault** — Confirm full-disk encryption is active (`fdesetup status`)
- **Secure Boot** — Check firmware security settings (Apple Silicon: `bputil -d`)
- **OS version** — Track current macOS version and available updates

---

## 2. Network Activity

- **Active connections** — Open network connections by process (`lsof -i`, `netstat`)
- **Listening ports** — Services accepting inbound connections
- **DNS queries** — Unusual or unexpected domains being resolved
- **Firewall status** — macOS Application Firewall enabled and configured
- **VPN status** — Whether a VPN is active

---

## 3. Processes & Executables

- **Running processes** — Unexpected or unsigned processes
- **Launch agents/daemons** — Items in `~/Library/LaunchAgents`, `/Library/LaunchAgents`, `/Library/LaunchDaemons`
- **Login items** — Apps configured to start at login
- **Unsigned/ad-hoc signed binaries** — Executables lacking Apple or developer signatures

---

## 4. User Accounts & Authentication

- **User accounts** — List of local accounts, admin membership
- **Sudo access** — Who has sudo rights, recent sudo usage (`/var/log/auth.log` or `log show`)
- **SSH keys** — Authorized keys in `~/.ssh/`
- **Failed login attempts** — Authentication failures in system logs
- **Last login times** — Per-user login history

---

## 5. File System

- **SUID/SGID binaries** — Executables with elevated permission bits
- **World-writable directories** — Directories any user can write to
- **Recently modified system files** — Changes to `/etc`, `/usr`, `/bin`, `/sbin`
- **Hidden files in home directory** — Unexpected dotfiles or directories
- **Quarantine flags** — Files downloaded from the internet

---

## 6. Logs & Audit Trail

- **Unified log (OSLog)** — System and security events (`log show`)
- **Security audit log** — `/var/audit/` (if BSM auditing is enabled)
- **Install log** — `/var/log/install.log` for software installs
- **Crash reports** — Unexpected crashes in `~/Library/Logs/DiagnosticReports`

---

## 7. Application Security

- **Installed applications** — Inventory of apps in `/Applications` and `~/Applications`
- **App permissions** — Camera, microphone, screen recording, full disk access (TCC database)
- **Browser extensions** — Extensions installed across browsers
- **Outdated software** — Applications with known CVEs or pending updates

---

## 8. Hardware & Peripheral Access

- **USB devices** — Connected USB devices (`system_profiler SPUSBDataType`)
- **Bluetooth devices** — Paired and connected devices
- **Thunderbolt/DMA devices** — Devices with direct memory access

---

## 9. Encryption & Certificates

- **Keychain items** — Unexpected certificates or credentials
- **Root certificates** — Untrusted or custom root CAs installed
- **Certificate transparency** — TLS certificate anomalies

---

## 10. Threat Indicators

- **Known malware signatures** — File hashes against threat intel
- **IOCs from recent macOS threats** — Malicious paths, process names, domains
- **XProtect/MRT status** — Apple's built-in malware removal tool version and last run

---

## Data Sources (macOS Commands & APIs)

| Area | Primary Source |
|------|---------------|
| SIP / Gatekeeper | `csrutil`, `spctl` |
| FileVault | `fdesetup` |
| Network | `lsof`, `netstat`, `pfctl` |
| Processes | `ps`, `launchctl` |
| Logs | `log show`, `/var/log/` |
| File system | `find`, `stat` |
| Users | `dscl`, `last`, `who` |
| Hardware | `system_profiler` |
| App permissions | `tccutil`, TCC database |

---

## Dashboard Priorities (MVP)

1. SIP / FileVault / Gatekeeper status (pass/fail)
2. Listening ports and active outbound connections
3. Launch agents and login items
4. Recent authentication failures
5. Admin accounts and sudo activity
6. OS and software update status
