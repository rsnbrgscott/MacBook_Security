"""User Account signal collectors: guest account, login window display, admin group members.

No sudo required. All three signals use defaults(1) or dscl(1) as the current user.
"""

import os

try:
    from .utils import run_cmd_rc, make_result
except ImportError:
    from utils import run_cmd_rc, make_result  # noqa: F401 — direct script execution

_SYSTEM_ACCOUNTS = frozenset({"root", "_mbsetupuser", "_uucp", "_networkd"})


def check_guest_account() -> dict:
    """Check whether the macOS guest account is enabled.

    PASS    — GuestEnabled is 0 or key is absent (macOS default: off)
    FAIL    — GuestEnabled is 1 (guest account enabled)
    UNKNOWN — defaults command failed or returned an unrecognized value
    """
    name = "Guest Account"
    desc = (
        "The guest account allows anyone with physical access to use the machine "
        "under a session not attributed to any named user. macOS erases the guest "
        "home directory on logout, making forensic investigation difficult. "
        "There is rarely a reason to leave this enabled on a personal machine."
    )

    out, rc, err = run_cmd_rc(
        ["defaults", "read", "/Library/Preferences/com.apple.loginwindow", "GuestEnabled"]
    )

    if err:
        return make_result(name, desc, "UNKNOWN", "", err)

    if rc == 1 and "does not exist" in out:
        return make_result(name, desc, "PASS", "GuestEnabled: absent (macOS default: off)")

    if rc == 0:
        val = out.strip()
        if val == "0":
            return make_result(name, desc, "PASS", "GuestEnabled: 0 (off)")
        if val == "1":
            return make_result(name, desc, "FAIL", "GuestEnabled: 1 (enabled)")

    return make_result(name, desc, "UNKNOWN", "",
                       f"Unexpected output (rc={rc}): {out!r}")


def check_login_window_display() -> dict:
    """Check whether the login window shows the user list or a name+password prompt.

    PASS    — SHOWFULLNAME is 1 (name and password prompt — more secure)
    WARN    — SHOWFULLNAME is 0 or key absent (user list visible — information disclosure risk)
    UNKNOWN — defaults command failed or returned an unrecognized value
    """
    name = "Login Window Display"
    desc = (
        "Displaying the user list at the login screen reveals valid account names "
        "to anyone who reaches it — useful for targeted password attacks or "
        "social engineering. Switching to a name-and-password prompt eliminates "
        "this exposure. The macOS default on unmanaged machines is to show the list."
    )

    out, rc, err = run_cmd_rc(
        ["defaults", "read", "/Library/Preferences/com.apple.loginwindow", "SHOWFULLNAME"]
    )

    if err:
        return make_result(name, desc, "UNKNOWN", "", err)

    if rc == 1 and "does not exist" in out:
        return make_result(
            name, desc, "WARN",
            "SHOWFULLNAME: absent (macOS default on unmanaged Macs: user list shown)"
        )

    if rc == 0:
        val = out.strip()
        if val == "1":
            return make_result(name, desc, "PASS", "SHOWFULLNAME: 1 (name and password prompt)")
        if val == "0":
            return make_result(name, desc, "WARN", "SHOWFULLNAME: 0 (user list visible at login screen)")

    return make_result(name, desc, "UNKNOWN", "",
                       f"Unexpected output (rc={rc}): {out!r}")


def check_admin_group_members() -> dict:
    """Check who holds admin privileges on this machine.

    PASS    — only the current user is in the admin group (after filtering system accounts)
    WARN    — multiple human accounts are in the admin group; raw output lists all members
    UNKNOWN — dscl command failed, or output format was unrecognized
    """
    name = "Admin Group Members"
    desc = (
        "Unexpected admin accounts are a common persistence mechanism after a compromise. "
        "An attacker who creates or elevates a user account retains access even after "
        "the initial exploit is patched. Review the listed members and remove any "
        "accounts you do not recognize."
    )

    out, rc, err = run_cmd_rc(["dscl", ".", "read", "/Groups/admin", "GroupMembership"])

    if err or rc != 0:
        detail = err or f"dscl exited {rc}: {out!r}"
        return make_result(name, desc, "UNKNOWN", "", detail)

    # Expected format: "GroupMembership: root scottrosenberg"
    if not out.startswith("GroupMembership:"):
        return make_result(name, desc, "UNKNOWN", "",
                           f"Unrecognized dscl output: {out!r}")

    members_str = out[len("GroupMembership:"):].strip()
    all_members = members_str.split()
    human_members = [m for m in all_members if m not in _SYSTEM_ACCOUNTS]

    if not human_members:
        return make_result(name, desc, "UNKNOWN", "",
                           f"No human accounts found in admin group output: {out!r}")

    current_user = os.environ.get("USER") or ""
    if not current_user:
        cur_out, cur_rc, _ = run_cmd_rc(["id", "-un"])
        current_user = cur_out.strip() if cur_rc == 0 else ""

    if human_members == [current_user]:
        return make_result(name, desc, "PASS", f"Admin group: {current_user} only")

    raw = "Admin group members: " + ", ".join(human_members)
    return make_result(name, desc, "WARN", raw)


if __name__ == "__main__":
    checks = [
        ("Guest Account", check_guest_account),
        ("Login Window Display", check_login_window_display),
        ("Admin Group Members", check_admin_group_members),
    ]
    for label, fn in checks:
        sig = fn()
        print(f"[{sig['status']:^7}] {label}")
        print(f"         raw: {sig['raw']!r}")
        if sig["error"]:
            print(f"         error: {sig['error']}")
        print()
