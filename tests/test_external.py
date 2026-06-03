import json
import urllib.error
from unittest.mock import patch, MagicMock
from collectors.external import check_macos_version


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


def _urlopen_mock(data: dict) -> MagicMock:
    """Build a mock that satisfies `with urlopen(...) as resp: resp.read()`."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


_CURRENT = "15.3.1"

_FEED_SAME       = {"PublicAssetSets": {"macOS": [{"ProductVersion": "15.3.1"}]}}
_FEED_MINOR_NEW  = {"PublicAssetSets": {"macOS": [{"ProductVersion": "15.4.0"}]}}
_FEED_MAJOR_NEW  = {"PublicAssetSets": {"macOS": [{"ProductVersion": "16.0.0"}]}}


def test_macos_version_pass():
    with patch("collectors.external._current_version", return_value=(_CURRENT, None)):
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(_FEED_SAME)):
            _ok(check_macos_version(), "PASS")


def test_macos_version_warn_minor_update():
    with patch("collectors.external._current_version", return_value=(_CURRENT, None)):
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(_FEED_MINOR_NEW)):
            _ok(check_macos_version(), "WARN")


def test_macos_version_fail_major_behind():
    with patch("collectors.external._current_version", return_value=(_CURRENT, None)):
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(_FEED_MAJOR_NEW)):
            _ok(check_macos_version(), "FAIL")


def test_macos_version_unknown_network_error():
    with patch("collectors.external._current_version", return_value=(_CURRENT, None)):
        with patch("urllib.request.urlopen",
                   side_effect=urllib.error.URLError("connection refused")):
            _ok(check_macos_version(), "UNKNOWN")


def test_macos_version_unknown_sw_vers_error():
    with patch("collectors.external._current_version",
               return_value=("", "sw_vers returned no output")):
        _ok(check_macos_version(), "UNKNOWN")
