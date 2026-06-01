_SOCKETFILTERFW = "/usr/libexec/ApplicationFirewall/socketfilterfw"

REMEDIATIONS = {
    "Application Firewall": {
        "label": "Enable Firewall",
        "cmd": f"{_SOCKETFILTERFW} --setglobalstate on",
        "applies_to": {"FAIL"},
    },
    "Stealth Mode": {
        "label": "Enable Stealth Mode",
        "cmd": f"{_SOCKETFILTERFW} --setstealthmode on",
        "applies_to": {"WARN"},
    },
}
