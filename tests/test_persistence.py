import pathlib as _pathlib
from unittest.mock import patch
from collectors.persistence import (
    check_user_launch_agents,
    check_global_launch_agents,
    check_launch_daemons,
    check_login_items,
)


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


# --- check_user_launch_agents (uses tmp_path + Path.home patch) ---

def test_user_launch_agents_pass(tmp_path):
    la_dir = tmp_path / "Library" / "LaunchAgents"
    la_dir.mkdir(parents=True)
    with patch("pathlib.Path.home", return_value=tmp_path):
        _ok(check_user_launch_agents(), "PASS")


def test_user_launch_agents_warn(tmp_path):
    la_dir = tmp_path / "Library" / "LaunchAgents"
    la_dir.mkdir(parents=True)
    (la_dir / "com.example.agent.plist").touch()
    with patch("pathlib.Path.home", return_value=tmp_path):
        _ok(check_user_launch_agents(), "WARN")


# --- check_global_launch_agents (uses tmp_path via Path constructor patch) ---

def _path_redirect(target_str, replacement):
    """Return a side_effect that redirects one absolute path to a tmp dir."""
    def _side_effect(*args):
        if args == (target_str,):
            return replacement
        return _pathlib.Path(*args)
    return _side_effect


def test_global_launch_agents_pass(tmp_path):
    (tmp_path / "com.apple.foo.plist").touch()  # filtered out by filter_apple
    with patch("collectors.persistence.Path",
               side_effect=_path_redirect("/Library/LaunchAgents", tmp_path)):
        _ok(check_global_launch_agents(), "PASS")


def test_global_launch_agents_warn(tmp_path):
    (tmp_path / "com.apple.foo.plist").touch()
    (tmp_path / "com.third-party.agent.plist").touch()
    with patch("collectors.persistence.Path",
               side_effect=_path_redirect("/Library/LaunchAgents", tmp_path)):
        _ok(check_global_launch_agents(), "WARN")


# --- check_launch_daemons (same pattern) ---

def test_launch_daemons_pass(tmp_path):
    (tmp_path / "com.apple.daemon.plist").touch()
    with patch("collectors.persistence.Path",
               side_effect=_path_redirect("/Library/LaunchDaemons", tmp_path)):
        _ok(check_launch_daemons(), "PASS")


def test_launch_daemons_warn(tmp_path):
    (tmp_path / "com.third-party.daemon.plist").touch()
    with patch("collectors.persistence.Path",
               side_effect=_path_redirect("/Library/LaunchDaemons", tmp_path)):
        _ok(check_launch_daemons(), "WARN")


# --- check_login_items ---

def test_login_items_pass():
    with patch("collectors.persistence.run_cmd", return_value=("", None)):
        _ok(check_login_items(), "PASS")


def test_login_items_warn():
    with patch("collectors.persistence.run_cmd",
               return_value=("Dropbox, Zoom", None)):
        _ok(check_login_items(), "WARN")


def test_login_items_unknown():
    with patch("collectors.persistence.run_cmd",
               return_value=("", "osascript error")):
        _ok(check_login_items(), "UNKNOWN")
