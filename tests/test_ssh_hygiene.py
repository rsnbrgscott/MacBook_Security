from unittest.mock import MagicMock, patch
from collectors.auth import (
    check_ssh_key_passphrases,
    check_ssh_agent_forwarding,
    check_ssh_key_strength,
)


def _ok(result, status):
    assert result["status"] == status
    assert result["name"]
    assert result["description"]
    if status == "UNKNOWN":
        assert result["error"]
    else:
        assert result["error"] is None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _proc(returncode=0, stdout=b"", stderr=b""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


def _ssh_config(*lines):
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# check_ssh_key_passphrases tests
# ---------------------------------------------------------------------------

def test_passphrases_ssh_dir_missing_pass(tmp_path):
    with patch("collectors.auth._SSH_DIR", tmp_path / "no_such_dir"):
        result = check_ssh_key_passphrases()
        _ok(result, "PASS")
        assert "No ~/.ssh/ directory" in result["raw"]


def test_passphrases_no_keys_pass(tmp_path):
    # Directory exists but contains only .pub, known_hosts, config — no candidates.
    (tmp_path / "id_ed25519.pub").write_text("ssh-ed25519 AAAA comment\n")
    (tmp_path / "known_hosts").write_text("github.com ssh-rsa AAAA\n")
    (tmp_path / "config").write_text("Host *\n  AddKeysToAgent yes\n")
    with patch("collectors.auth._SSH_DIR", tmp_path):
        result = check_ssh_key_passphrases()
        _ok(result, "PASS")
        assert "No private keys found" in result["raw"]


def test_passphrases_all_protected_pass(tmp_path):
    key = tmp_path / "id_ed25519"
    key.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\n")
    protected = _proc(
        returncode=255,
        stderr=b"Load key: incorrect passphrase supplied to decrypt private key",
    )
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=protected):
        result = check_ssh_key_passphrases()
        _ok(result, "PASS")
        assert "All private keys are passphrase-protected" in result["raw"]


def test_passphrases_unprotected_warn(tmp_path):
    key = tmp_path / "id_ed25519"
    key.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\n")
    unprotected = _proc(returncode=0, stdout=b"ssh-ed25519 AAAAC3Nz comment\n")
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=unprotected):
        result = check_ssh_key_passphrases()
        _ok(result, "WARN")
        assert "id_ed25519" in result["raw"]


def test_passphrases_non_key_files_skipped(tmp_path):
    # "invalid format" exit — not a key file; should not be flagged.
    non_key = tmp_path / "not_a_key"
    non_key.write_text("just some text\n")
    invalid = _proc(returncode=255, stderr=b"Load key: invalid format")
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=invalid):
        result = check_ssh_key_passphrases()
        _ok(result, "PASS")


def test_passphrases_multiple_some_unprotected(tmp_path):
    (tmp_path / "safe_key").write_text("key\n")
    (tmp_path / "risky_key").write_text("key\n")
    risky = _proc(returncode=0, stdout=b"ssh-ed25519 AAAA comment\n")
    safe = _proc(returncode=255, stderr=b"incorrect passphrase supplied to decrypt private key")
    # sorted() order: risky_key (r) before safe_key (s)
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", side_effect=[risky, safe]):
        result = check_ssh_key_passphrases()
        _ok(result, "WARN")
        assert "risky_key" in result["raw"]
        assert "safe_key" not in result["raw"]


# ---------------------------------------------------------------------------
# check_ssh_agent_forwarding tests
# ---------------------------------------------------------------------------

def test_agent_forwarding_no_config_pass(tmp_path):
    with patch("collectors.auth._SSH_DIR", tmp_path):
        result = check_ssh_agent_forwarding()
        _ok(result, "PASS")
        assert "No SSH config file" in result["raw"]


def test_agent_forwarding_no_forward_pass(tmp_path):
    (tmp_path / "config").write_text(_ssh_config(
        "Host github.com",
        "  AddKeysToAgent yes",
        "  IdentityFile ~/.ssh/id_ed25519",
    ))
    with patch("collectors.auth._SSH_DIR", tmp_path):
        result = check_ssh_agent_forwarding()
        _ok(result, "PASS")
        assert "No ForwardAgent entries found" in result["raw"]


def test_agent_forwarding_present_warn(tmp_path):
    (tmp_path / "config").write_text(_ssh_config(
        "Host bastion.example.com",
        "  ForwardAgent yes",
        "  User deploy",
    ))
    with patch("collectors.auth._SSH_DIR", tmp_path):
        result = check_ssh_agent_forwarding()
        _ok(result, "WARN")
        assert "bastion.example.com" in result["raw"]


def test_agent_forwarding_case_insensitive(tmp_path):
    (tmp_path / "config").write_text(_ssh_config(
        "Host jumpbox",
        "  forwardagent Yes",
    ))
    with patch("collectors.auth._SSH_DIR", tmp_path):
        result = check_ssh_agent_forwarding()
        _ok(result, "WARN")
        assert "jumpbox" in result["raw"]


def test_agent_forwarding_multiple_hosts(tmp_path):
    (tmp_path / "config").write_text(_ssh_config(
        "Host safe.example.com",
        "  AddKeysToAgent yes",
        "Host risky.example.com",
        "  ForwardAgent yes",
        "Host also-risky.example.com",
        "  ForwardAgent yes",
    ))
    with patch("collectors.auth._SSH_DIR", tmp_path):
        result = check_ssh_agent_forwarding()
        _ok(result, "WARN")
        assert "risky.example.com" in result["raw"]
        assert "also-risky.example.com" in result["raw"]
        assert "safe.example.com" not in result["raw"]


# ---------------------------------------------------------------------------
# check_ssh_key_strength tests
# ---------------------------------------------------------------------------

def test_strength_no_pub_keys_pass(tmp_path):
    with patch("collectors.auth._SSH_DIR", tmp_path):
        result = check_ssh_key_strength()
        _ok(result, "PASS")
        assert "No public keys found" in result["raw"]


def test_strength_ed25519_pass(tmp_path):
    (tmp_path / "id_ed25519.pub").write_text("ssh-ed25519 AAAA comment\n")
    out = b"256 SHA256:abc comment (ED25519)\n"
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=_proc(stdout=out)):
        result = check_ssh_key_strength()
        _ok(result, "PASS")
        assert "ED25519" in result["raw"]


def test_strength_rsa_4096_pass(tmp_path):
    (tmp_path / "id_rsa.pub").write_text("ssh-rsa AAAA comment\n")
    out = b"4096 SHA256:abc comment (RSA)\n"
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=_proc(stdout=out)):
        _ok(check_ssh_key_strength(), "PASS")


def test_strength_rsa_3072_pass(tmp_path):
    (tmp_path / "id_rsa.pub").write_text("ssh-rsa AAAA comment\n")
    out = b"3072 SHA256:abc comment (RSA)\n"
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=_proc(stdout=out)):
        _ok(check_ssh_key_strength(), "PASS")


def test_strength_rsa_2048_warn(tmp_path):
    (tmp_path / "id_rsa.pub").write_text("ssh-rsa AAAA comment\n")
    out = b"2048 SHA256:abc comment (RSA)\n"
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=_proc(stdout=out)):
        result = check_ssh_key_strength()
        _ok(result, "WARN")
        assert "RSA" in result["raw"]


def test_strength_dsa_fail(tmp_path):
    (tmp_path / "id_dsa.pub").write_text("ssh-dsa AAAA comment\n")
    out = b"1024 SHA256:abc comment (DSA)\n"
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=_proc(stdout=out)):
        result = check_ssh_key_strength()
        _ok(result, "FAIL")
        assert "DSA" in result["raw"]


def test_strength_rsa_1024_fail(tmp_path):
    (tmp_path / "id_rsa.pub").write_text("ssh-rsa AAAA comment\n")
    out = b"1024 SHA256:abc comment (RSA)\n"
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", return_value=_proc(stdout=out)):
        result = check_ssh_key_strength()
        _ok(result, "FAIL")


def test_strength_worst_wins(tmp_path):
    # Two keys: one Ed25519 (PASS), one DSA (FAIL) — overall must be FAIL.
    (tmp_path / "id_ed25519.pub").write_text("x\n")
    (tmp_path / "id_dsa.pub").write_text("x\n")
    ed_out = b"256 SHA256:abc comment (ED25519)\n"
    dsa_out = b"1024 SHA256:def comment (DSA)\n"
    with patch("collectors.auth._SSH_DIR", tmp_path), \
         patch("collectors.auth.subprocess.run", side_effect=[
             _proc(stdout=ed_out), _proc(stdout=dsa_out)
         ]):
        result = check_ssh_key_strength()
        _ok(result, "FAIL")
