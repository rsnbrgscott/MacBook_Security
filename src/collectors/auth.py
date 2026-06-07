# Authentication signal collectors for the macOS security dashboard.
# Checks: Failed Logins, SSH Authorized Keys, SSH Key Passphrases,
#         SSH Agent Forwarding, SSH Key Strength.
# `log show` requires Full Disk Access; empty output without an error is treated as UNKNOWN.

import re
import subprocess
from pathlib import Path

try:
    from .utils import run_cmd, make_result
except ImportError:
    from utils import run_cmd, make_result  # noqa: F401 — direct script execution

_SSH_DIR = Path.home() / ".ssh"

# Private key files to skip when scanning ~/.ssh/ for key candidates.
_NON_KEY_NAMES = frozenset({
    "known_hosts", "known_hosts.old",
    "authorized_keys", "authorized_keys2",
    "config", "environment",
})

# Case-sensitive predicates — CONTAINS[c] is intentional.
# loginwindow uses all-caps "FAILED"; sshd uses title-case "Failed"/"Invalid".
# A case-insensitive match would catch unrelated clipboard log entries (false positives).
_FAILED_LOGIN_PREDICATE = (
    '(process == "loginwindow" AND eventMessage CONTAINS "FAILED")'
    ' OR '
    '(process == "sshd" AND (eventMessage CONTAINS "Failed" OR eventMessage CONTAINS "Invalid"))'
)


def check_failed_logins() -> dict:
    """Query the unified log for failed GUI and SSH login attempts in the past 24 hours."""
    name = "Failed Logins"
    desc = (
        "Failed login attempts via the macOS login screen or SSH in the past 24h. "
        "WARN means failures were detected — review if unexpected."
    )
    raw, error = run_cmd(
        ["log", "show", "--predicate", _FAILED_LOGIN_PREDICATE, "--last", "24h", "--style", "compact"],
        timeout=30,
    )
    if error:
        return make_result(name, desc, "UNKNOWN", raw, error)
    # Empty output with no error means Full Disk Access was denied — not a clean result.
    if not raw:
        return make_result(
            name, desc, "UNKNOWN", "",
            "log show returned no output — Full Disk Access may be required",
        )
    lines = [ln for ln in raw.splitlines() if ln.strip() and not ln.startswith("Timestamp")]
    if not lines:
        return make_result(name, desc, "PASS", "No failed login events in past 24h.")
    # Cap displayed output at 20 lines to keep the dashboard readable.
    trimmed = "\n".join(lines[:20])
    suffix = f"\n... ({len(lines) - 20} more lines)" if len(lines) > 20 else ""
    return make_result(name, desc, "WARN", trimmed + suffix)


def check_ssh_keys() -> dict:
    """Check ~/.ssh/authorized_keys for any keys that permit remote login to this machine."""
    name = "SSH Authorized Keys"
    desc = (
        "Keys in ~/.ssh/authorized_keys that allow remote login to this machine. "
        "WARN means remote key-based access is enabled — review if unexpected."
    )
    path = Path.home() / ".ssh" / "authorized_keys"
    try:
        if not path.exists():
            return make_result(name, desc, "PASS", "No authorized keys found.")
        # Skip blank lines and comments — only count active key entries.
        lines = [ln for ln in path.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
        if not lines:
            return make_result(name, desc, "PASS", "No authorized keys found.")
        return make_result(name, desc, "WARN", "\n".join(lines))
    except OSError as e:
        return make_result(name, desc, "UNKNOWN", "", str(e))


def check_ssh_key_passphrases() -> dict:
    """Check whether any private keys in ~/.ssh/ lack passphrase protection."""
    name = "SSH Key Passphrases"
    desc = (
        "Private keys in ~/.ssh/ without a passphrase are single-file credentials — "
        "anyone who reads the file has the credential. "
        "WARN means one or more keys have no passphrase."
    )
    try:
        if not _SSH_DIR.is_dir():
            return make_result(name, desc, "PASS", "No ~/.ssh/ directory found")
        candidates = [
            p for p in _SSH_DIR.iterdir()
            if p.is_file() and not p.suffix == ".pub" and p.name not in _NON_KEY_NAMES
        ]
    except OSError as e:
        return make_result(name, desc, "UNKNOWN", "", str(e))

    if not candidates:
        return make_result(name, desc, "PASS", "No private keys found")

    unprotected = []
    for path in sorted(candidates):
        try:
            result = subprocess.run(
                ["ssh-keygen", "-y", "-f", str(path)],
                input=b"",
                capture_output=True,
                timeout=3,
            )
        except Exception as e:
            return make_result(name, desc, "UNKNOWN", "", f"ssh-keygen error: {e}")
        if result.returncode == 0:
            unprotected.append(path.name)
        # exit 255 + "incorrect passphrase" → protected key → skip (safe)
        # exit 255 + "invalid format"        → not a key file → skip

    if unprotected:
        return make_result(name, desc, "WARN",
                           "Unprotected keys: " + ", ".join(unprotected))
    return make_result(name, desc, "PASS", "All private keys are passphrase-protected")


def check_ssh_agent_forwarding() -> dict:
    """Check ~/.ssh/config for ForwardAgent yes entries."""
    name = "SSH Agent Forwarding"
    desc = (
        "ForwardAgent yes in ~/.ssh/config lets a remote host use your local SSH agent "
        "to authenticate to other systems. If the remote host is compromised, "
        "it can impersonate you to any system that trusts those keys."
    )
    config_path = _SSH_DIR / "config"
    try:
        if not config_path.exists():
            return make_result(name, desc, "PASS", "No SSH config file")
        text = config_path.read_text(errors="replace")
    except OSError as e:
        return make_result(name, desc, "UNKNOWN", "", str(e))

    current_host = "*"
    forwarding_hosts = []
    for line in text.splitlines():
        stripped = line.strip()
        host_match = re.match(r"^Host\s+(.+)", stripped, re.IGNORECASE)
        if host_match:
            current_host = host_match.group(1).strip()
            continue
        if re.match(r"^ForwardAgent\s+yes\s*$", stripped, re.IGNORECASE):
            forwarding_hosts.append(current_host)

    if forwarding_hosts:
        return make_result(name, desc, "WARN",
                           "ForwardAgent yes for: " + ", ".join(forwarding_hosts))
    return make_result(name, desc, "PASS", "No ForwardAgent entries found")


def check_ssh_key_strength() -> dict:
    """Check the algorithm and bit-length of public keys in ~/.ssh/."""
    name = "SSH Key Strength"
    desc = (
        "Weak SSH key algorithms (DSA, RSA < 2048) can be broken by well-resourced attackers. "
        "RSA ≥ 3072 or Ed25519 is recommended."
    )
    try:
        if not _SSH_DIR.is_dir():
            return make_result(name, desc, "PASS", "No ~/.ssh/ directory found")
        pub_keys = sorted(_SSH_DIR.glob("*.pub"))
    except OSError as e:
        return make_result(name, desc, "UNKNOWN", "", str(e))

    if not pub_keys:
        return make_result(name, desc, "PASS", "No public keys found")

    worst = "PASS"
    details = []
    for path in pub_keys:
        try:
            result = subprocess.run(
                ["ssh-keygen", "-l", "-f", str(path)],
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            return make_result(name, desc, "UNKNOWN", "", f"ssh-keygen error: {e}")
        line = result.stdout.decode(errors="replace").strip()
        if not line:
            continue
        try:
            bits = int(line.split()[0])
        except (ValueError, IndexError):
            bits = 0
        algo_match = re.search(r"\((\w+)\)\s*$", line)
        algo = algo_match.group(1).upper() if algo_match else "UNKNOWN"

        if algo == "DSA" or (algo == "RSA" and bits < 2048):
            classification = "FAIL"
        elif algo == "RSA" and bits < 3072:
            classification = "WARN"
        else:
            classification = "PASS"

        if classification == "FAIL" or (classification == "WARN" and worst == "PASS"):
            worst = classification
        details.append(f"{path.name}: {algo} {bits}-bit ({classification})")

    raw = "; ".join(details)
    return make_result(name, desc, worst, raw)


if __name__ == "__main__":
    # Quick smoke-test: run this file directly to see current signal output.
    checks = [
        ("Failed Logins", check_failed_logins),
        ("SSH Authorized Keys", check_ssh_keys),
        ("SSH Key Passphrases", check_ssh_key_passphrases),
        ("SSH Agent Forwarding", check_ssh_agent_forwarding),
        ("SSH Key Strength", check_ssh_key_strength),
    ]
    for label, fn in checks:
        result = fn()
        preview = result["raw"][:120].replace("\n", " ").strip()
        ellipsis = "..." if len(result["raw"]) > 120 else ""
        print(f"[{result['status']:^7}] {label}")
        print(f"         raw: {preview!r}{ellipsis}")
        if result["error"]:
            print(f"         error: {result['error']}")
        print()
