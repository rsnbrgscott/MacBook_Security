# Opt-in external signal collector for the macOS security dashboard.
# Makes a single outbound HTTPS request to Apple's GDMF API to compare the
# installed macOS version against the current release train.
# Only included in runs when EXTERNAL_CALLS=1 is set.
#
# Status logic:
#   FAIL  — current major version is behind the latest major (e.g., still on 14 when 15 is out)
#   WARN  — on the correct major but a newer minor/patch is available
#   PASS  — current version matches the latest in this release train
#   UNKNOWN — sw_vers failed, network error, or unrecognised API response

import json
import socket
import subprocess
import urllib.error
import urllib.request

try:
    from .utils import make_result
except ImportError:
    from utils import make_result  # noqa: F401 — direct script execution

# Apple's authoritative software version feed — no identifying data is sent.
_VERSION_API = "https://gdmf.apple.com/v2/pmv"
_TIMEOUT = 10


def _current_version() -> tuple[str, str | None]:
    """Read the installed macOS version string from sw_vers (e.g. '15.3.1')."""
    try:
        result = subprocess.run(
            ["/usr/bin/sw_vers", "-productVersion"],
            capture_output=True, text=True, timeout=5
        )
        version = result.stdout.strip()
        if not version:
            return "", "sw_vers returned no output"
        return version, None
    except Exception as e:
        return "", str(e)


def _parse_version(v: str) -> tuple[int, ...]:
    """Convert a version string like '15.3.1' to a comparable int tuple (15, 3, 1)."""
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def _latest_version(current_major: int) -> tuple[str, str | None]:
    """Fetch the GDMF feed and return the newest version in current_major's release train.

    If current_major is not present in the feed (major version is outdated),
    returns the latest version across all majors so the caller can show a FAIL.
    This function is a helper used only for testing; check_macos_version() makes
    its own single HTTP call to avoid a duplicate request.
    """
    try:
        req = urllib.request.Request(
            _VERSION_API,
            headers={"User-Agent": "MacBook-Security-Dashboard/1.0"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())

        entries = data.get("PublicAssetSets", {}).get("macOS", [])
        versions = set()
        for entry in entries:
            pv = entry.get("ProductVersion", "")
            if pv:
                versions.add(pv)

        if not versions:
            return "", "No macOS versions found in API response"

        parsed = [(v, _parse_version(v)) for v in versions]
        max_major = max(t[0] for _, t in parsed)

        # FAIL path: return the max major's best version so caller can compare
        same_major = [(v, t) for v, t in parsed if t[0] == current_major]
        if not same_major:
            # current major not in feed at all — return latest overall for FAIL path
            latest = max(parsed, key=lambda x: x[1])
            return latest[0], None

        latest_in_train = max(same_major, key=lambda x: x[1])
        return latest_in_train[0], None

    except (urllib.error.URLError, socket.timeout) as e:
        return "", f"Network error: {e}"
    except json.JSONDecodeError as e:
        return "", f"JSON parse error: {e}"
    except Exception as e:
        return "", f"Unexpected error: {e}"


def _max_major_in_feed() -> tuple[int, str | None]:
    """Return the highest macOS major version number currently listed in the GDMF feed."""
    try:
        req = urllib.request.Request(
            _VERSION_API,
            headers={"User-Agent": "MacBook-Security-Dashboard/1.0"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())

        entries = data.get("PublicAssetSets", {}).get("macOS", [])
        majors = set()
        for entry in entries:
            pv = entry.get("ProductVersion", "")
            if pv:
                t = _parse_version(pv)
                if t:
                    majors.add(t[0])

        if not majors:
            return 0, "No macOS versions found in API response"
        return max(majors), None
    except Exception as e:
        return 0, str(e)


def check_macos_version() -> dict:
    """Compare the installed macOS version to the latest Apple release via the GDMF API."""
    name = "macOS Version"
    description = (
        "Compares the current macOS version against the latest Apple release "
        "(requires EXTERNAL_CALLS=1)."
    )

    current, err = _current_version()
    if err:
        return make_result(name, description, "UNKNOWN", "", f"Could not read current macOS version: {err}")

    current_tuple = _parse_version(current)
    current_major = current_tuple[0] if current_tuple else 0

    # Single HTTP call to get the feed; derive both max_major and latest_in_train
    # from the same payload to avoid two round-trips per page load.
    try:
        req = urllib.request.Request(
            _VERSION_API,
            headers={"User-Agent": "MacBook-Security-Dashboard/1.0"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, socket.timeout) as e:
        return make_result(name, description, "UNKNOWN", f"Current: {current}", f"Network error fetching version data: {e}")
    except json.JSONDecodeError as e:
        return make_result(name, description, "UNKNOWN", f"Current: {current}", f"Could not parse version API response: {e}")
    except Exception as e:
        return make_result(name, description, "UNKNOWN", f"Current: {current}", f"Unexpected error: {e}")

    entries = data.get("PublicAssetSets", {}).get("macOS", [])
    versions = set()
    for entry in entries:
        pv = entry.get("ProductVersion", "")
        if pv:
            versions.add(pv)

    if not versions:
        return make_result(name, description, "UNKNOWN", f"Current: {current}", "No macOS versions found in API response")

    parsed = [(v, _parse_version(v)) for v in versions]
    max_major = max(t[0] for _, t in parsed)

    # FAIL: running an older major release (e.g., macOS 14 when 15 is available).
    if current_major < max_major:
        latest_overall = max(parsed, key=lambda x: x[1])
        latest = latest_overall[0]
        return make_result(name, description, "FAIL", f"Current: {current}\nLatest:  {latest}")

    same_major = [(v, t) for v, t in parsed if t[0] == current_major]
    if not same_major:
        return make_result(name, description, "UNKNOWN", f"Current: {current}", f"macOS {current_major}.x not found in version feed")

    latest_in_train = max(same_major, key=lambda x: x[1])[0]
    raw = f"Current: {current}\nLatest:  {latest_in_train}"

    # WARN: on the right major but a minor/patch update is available.
    # PASS: fully up-to-date within this release train.
    status = "PASS" if current_tuple >= _parse_version(latest_in_train) else "WARN"
    return make_result(name, description, status, raw)


if __name__ == "__main__":
    import pprint
    pprint.pprint(check_macos_version())
