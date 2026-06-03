from unittest.mock import patch
from collectors.auth import check_failed_logins, check_ssh_keys


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


# --- check_failed_logins ---

def test_failed_logins_pass():
    # log show returns a header-only result — no event lines after filtering
    raw = "Timestamp                 Thread     Type\n"
    with patch("collectors.auth.run_cmd", return_value=(raw, None)):
        _ok(check_failed_logins(), "PASS")


def test_failed_logins_warn():
    raw = "Timestamp ...\n2024-01-01 12:00:00 loginwindow: FAILED password attempt\n"
    with patch("collectors.auth.run_cmd", return_value=(raw, None)):
        _ok(check_failed_logins(), "WARN")


def test_failed_logins_unknown_command_error():
    with patch("collectors.auth.run_cmd", return_value=("", "error")):
        _ok(check_failed_logins(), "UNKNOWN")


def test_failed_logins_unknown_empty_output():
    # Empty output with no error means Full Disk Access was denied
    with patch("collectors.auth.run_cmd", return_value=("", None)):
        _ok(check_failed_logins(), "UNKNOWN")


# --- check_ssh_keys (uses tmp_path + Path.home patch) ---

def test_ssh_keys_pass_file_absent(tmp_path):
    with patch("pathlib.Path.home", return_value=tmp_path):
        _ok(check_ssh_keys(), "PASS")


def test_ssh_keys_pass_file_empty(tmp_path):
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "authorized_keys").write_text("")
    with patch("pathlib.Path.home", return_value=tmp_path):
        _ok(check_ssh_keys(), "PASS")


def test_ssh_keys_pass_comments_only(tmp_path):
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "authorized_keys").write_text("# This is a comment\n\n")
    with patch("pathlib.Path.home", return_value=tmp_path):
        _ok(check_ssh_keys(), "PASS")


def test_ssh_keys_warn(tmp_path):
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "authorized_keys").write_text("ssh-rsa AAAAB3NzaC1yc2E user@host\n")
    with patch("pathlib.Path.home", return_value=tmp_path):
        _ok(check_ssh_keys(), "WARN")


def test_ssh_keys_unknown_oserror(tmp_path):
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()
    (ssh_dir / "authorized_keys").write_text("ssh-rsa AAAA user@host\n")
    with patch("pathlib.Path.read_text", side_effect=OSError("Permission denied")):
        with patch("pathlib.Path.home", return_value=tmp_path):
            _ok(check_ssh_keys(), "UNKNOWN")
