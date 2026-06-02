"""Remediation registry: maps signal names to privileged fix commands.

Each key must exactly match the signal name returned by its collector.
The /fix/<signal_name> route in app.py validates against this dict before
executing anything — cmd values are fixed constants, never derived from input.

Entry fields:
  label      — button text shown in the UI
  cmd        — shell command run via osascript with administrator privileges
  applies_to — set of statuses for which the Fix button is shown
"""

_SOCKETFILTERFW = "/usr/libexec/ApplicationFirewall/socketfilterfw"

REMEDIATIONS = {
    "Application Firewall": {
        "label": "Enable Firewall",
        "cmd": f"{_SOCKETFILTERFW} --setglobalstate on",
        # Show the Fix button only when the firewall is confirmed off (FAIL).
        "applies_to": {"FAIL"},
    },
    "Stealth Mode": {
        "label": "Enable Stealth Mode",
        "cmd": f"{_SOCKETFILTERFW} --setstealthmode on",
        # Stealth Mode off is WARN (notable but not a hard failure), so the button
        # appears on WARN rather than FAIL.
        "applies_to": {"WARN"},
    },
    "Remote Login (SSH)": {
        "label": "Disable Remote Login",
        # disable marks the service disabled in launchd's persistent override DB;
        # bootout removes it from the current system domain immediately.
        # The Fix button appears only when the service is confirmed loaded (FAIL).
        "cmd": (
            "launchctl disable system/com.openssh.sshd"
            " && launchctl bootout system/com.openssh.sshd"
        ),
        "applies_to": {"FAIL"},
    },
    "Screen Sharing / Remote Management": {
        "label": "Disable Screen Sharing",
        "cmd": (
            "launchctl disable system/com.apple.screensharing"
            " && launchctl bootout system/com.apple.screensharing"
        ),
        "applies_to": {"FAIL"},
    },
    "Automatic Updates": {
        "label": "Enable Auto-Updates",
        # /Library/Preferences/com.apple.SoftwareUpdate requires root to write;
        # osascript escalates via the standard macOS password dialog.
        "cmd": (
            "defaults write /Library/Preferences/com.apple.SoftwareUpdate"
            " AutomaticCheckEnabled -bool true"
            " && defaults write /Library/Preferences/com.apple.SoftwareUpdate"
            " CriticalUpdateInstall -bool true"
        ),
        "applies_to": {"FAIL"},
    },
}
