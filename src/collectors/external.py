import json
import socket
import subprocess
import urllib.error
import urllib.request

_VERSION_API = "https://gdmf.apple.com/v2/pmv"
_TIMEOUT = 10


def _current_version() -> tuple[str, str | None]:
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
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def _latest_version(current_major: int) -> tuple[str, str | None]:
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
    name = "macOS Version"
    description = (
        "Compares the current macOS version against the latest Apple release "
        "(requires EXTERNAL_CALLS=1)."
    )

    current, err = _current_version()
    if err:
        return {
            "name": name,
            "description": description,
            "status": "UNKNOWN",
            "raw": "",
            "error": f"Could not read current macOS version: {err}",
        }

    current_tuple = _parse_version(current)
    current_major = current_tuple[0] if current_tuple else 0

    # Single HTTP call to get the feed; derive both max_major and latest_in_train
    try:
        req = urllib.request.Request(
            _VERSION_API,
            headers={"User-Agent": "MacBook-Security-Dashboard/1.0"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, socket.timeout) as e:
        return {
            "name": name,
            "description": description,
            "status": "UNKNOWN",
            "raw": f"Current: {current}",
            "error": f"Network error fetching version data: {e}",
        }
    except json.JSONDecodeError as e:
        return {
            "name": name,
            "description": description,
            "status": "UNKNOWN",
            "raw": f"Current: {current}",
            "error": f"Could not parse version API response: {e}",
        }
    except Exception as e:
        return {
            "name": name,
            "description": description,
            "status": "UNKNOWN",
            "raw": f"Current: {current}",
            "error": f"Unexpected error: {e}",
        }

    entries = data.get("PublicAssetSets", {}).get("macOS", [])
    versions = set()
    for entry in entries:
        pv = entry.get("ProductVersion", "")
        if pv:
            versions.add(pv)

    if not versions:
        return {
            "name": name,
            "description": description,
            "status": "UNKNOWN",
            "raw": f"Current: {current}",
            "error": "No macOS versions found in API response",
        }

    parsed = [(v, _parse_version(v)) for v in versions]
    max_major = max(t[0] for _, t in parsed)

    if current_major < max_major:
        latest_overall = max(parsed, key=lambda x: x[1])
        latest = latest_overall[0]
        raw = f"Current: {current}\nLatest:  {latest}"
        return {
            "name": name,
            "description": description,
            "status": "FAIL",
            "raw": raw,
            "error": None,
        }

    same_major = [(v, t) for v, t in parsed if t[0] == current_major]
    if not same_major:
        return {
            "name": name,
            "description": description,
            "status": "UNKNOWN",
            "raw": f"Current: {current}",
            "error": f"macOS {current_major}.x not found in version feed",
        }

    latest_in_train = max(same_major, key=lambda x: x[1])[0]
    raw = f"Current: {current}\nLatest:  {latest_in_train}"

    if current_tuple >= _parse_version(latest_in_train):
        status = "PASS"
    else:
        status = "WARN"

    return {
        "name": name,
        "description": description,
        "status": status,
        "raw": raw,
        "error": None,
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(check_macos_version())
