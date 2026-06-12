from unittest.mock import patch
import collectors.ai as ai_module
from collectors.ai import (
    check_ai_keys_shell_config,
    check_ai_keys_shell_history,
    check_local_ai_server,
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
# check_ai_keys_shell_config
# ---------------------------------------------------------------------------

def test_shell_config_no_files_unknown(tmp_path):
    # All paths absent → files_read=0 → UNKNOWN
    with patch.object(ai_module, "_SHELL_CONFIG_FILES", [tmp_path / "nonexistent"]):
        _ok(check_ai_keys_shell_config(), "UNKNOWN")


def test_shell_config_no_keys_pass(tmp_path):
    cfg = tmp_path / ".zshrc"
    cfg.write_text("export PATH=/usr/local/bin\nalias ll='ls -la'\n")
    with patch.object(ai_module, "_SHELL_CONFIG_FILES", [cfg]):
        _ok(check_ai_keys_shell_config(), "PASS")


def test_shell_config_key_found_warn(tmp_path):
    cfg = tmp_path / ".zshrc"
    cfg.write_text("export OPENAI_API_KEY=sk-test1234567890abcdef\n")
    with patch.object(ai_module, "_SHELL_CONFIG_FILES", [cfg]):
        result = check_ai_keys_shell_config()
        _ok(result, "WARN")
        assert "OPENAI_API_KEY" in result["raw"]
        assert "sk-test" not in result["raw"]  # value must never appear


def test_shell_config_key_name_and_filename_in_raw(tmp_path):
    cfg = tmp_path / ".zshrc"
    cfg.write_text("export ANTHROPIC_API_KEY=sk-ant-api03-secret\n")
    with patch.object(ai_module, "_SHELL_CONFIG_FILES", [cfg]):
        result = check_ai_keys_shell_config()
        assert "ANTHROPIC_API_KEY" in result["raw"]
        assert str(cfg) in result["raw"]
        assert "sk-ant-api03-secret" not in result["raw"]


def test_shell_config_non_key_export_pass(tmp_path):
    # Guard against false positives on unrelated exports
    cfg = tmp_path / ".zshrc"
    cfg.write_text("export PATH=/usr/local/bin\nexport HOME=/Users/test\n")
    with patch.object(ai_module, "_SHELL_CONFIG_FILES", [cfg]):
        _ok(check_ai_keys_shell_config(), "PASS")


def test_shell_config_multiple_files_warn(tmp_path):
    f1 = tmp_path / ".zshrc"
    f2 = tmp_path / ".bash_profile"
    f1.write_text("export OPENAI_API_KEY=sk-abc\n")
    f2.write_text("export GROQ_API_KEY=gsk_xyz\n")
    with patch.object(ai_module, "_SHELL_CONFIG_FILES", [f1, f2]):
        result = check_ai_keys_shell_config()
        _ok(result, "WARN")
        assert str(f1) in result["raw"]
        assert str(f2) in result["raw"]


def test_shell_config_bare_assignment_warn(tmp_path):
    # Without 'export' prefix — still a security concern
    cfg = tmp_path / ".zshrc"
    cfg.write_text("GEMINI_API_KEY=AIza-some-key\n")
    with patch.object(ai_module, "_SHELL_CONFIG_FILES", [cfg]):
        result = check_ai_keys_shell_config()
        _ok(result, "WARN")
        assert "GEMINI_API_KEY" in result["raw"]


def test_shell_config_absent_files_skipped_pass(tmp_path):
    # Mix of present (clean) and absent files — absent ones silently skipped
    present = tmp_path / ".zshrc"
    present.write_text("alias gs='git status'\n")
    absent = tmp_path / ".zprofile"
    with patch.object(ai_module, "_SHELL_CONFIG_FILES", [present, absent]):
        _ok(check_ai_keys_shell_config(), "PASS")


# ---------------------------------------------------------------------------
# check_ai_keys_shell_history
# ---------------------------------------------------------------------------

def test_history_no_matches_pass(tmp_path):
    h = tmp_path / ".zsh_history"
    h.write_text("ls -la\ngit status\nbrew update\n")
    with patch.object(ai_module, "_HISTORY_FILES", [h]):
        _ok(check_ai_keys_shell_history(), "PASS")


def test_history_file_absent_pass(tmp_path):
    with patch.object(ai_module, "_HISTORY_FILES", [tmp_path / ".zsh_history"]):
        _ok(check_ai_keys_shell_history(), "PASS")


def test_history_openai_pattern_warn(tmp_path):
    h = tmp_path / ".zsh_history"
    h.write_text('curl https://api.openai.com -H "Authorization: Bearer sk-abcdefghij1234567890XYZ"\n')
    with patch.object(ai_module, "_HISTORY_FILES", [h]):
        result = check_ai_keys_shell_history()
        _ok(result, "WARN")
        assert "sk-abc" not in result["raw"]  # value must never appear


def test_history_count_in_raw(tmp_path):
    h = tmp_path / ".zsh_history"
    h.write_text(
        "curl -H 'Authorization: sk-abcdefghijklmnopqrstuvwxyz1234'\n"
        "echo sk-anotherkey123456789012345\n"
    )
    with patch.object(ai_module, "_HISTORY_FILES", [h]):
        result = check_ai_keys_shell_history()
        _ok(result, "WARN")
        assert "2 pattern match(es)" in result["raw"]


def test_history_extended_zsh_format_warn(tmp_path):
    # Extended history: ': <timestamp>:<elapsed>;<command>'
    h = tmp_path / ".zsh_history"
    h.write_text(": 1717000000:0;curl -H 'Auth: sk-abcdefghijklmnopqrstuvwxyz'\n")
    with patch.object(ai_module, "_HISTORY_FILES", [h]):
        result = check_ai_keys_shell_history()
        _ok(result, "WARN")


def test_history_no_files_at_all_pass(tmp_path):
    # Both history files absent → PASS with "no history files found" message
    with patch.object(ai_module, "_HISTORY_FILES",
                      [tmp_path / ".zsh_history", tmp_path / ".bash_history"]):
        result = check_ai_keys_shell_history()
        _ok(result, "PASS")
        assert "No shell history files found" in result["raw"]


# ---------------------------------------------------------------------------
# check_local_ai_server
# ---------------------------------------------------------------------------

_HEADER = "COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME"
_LOOPBACK = f"{_HEADER}\nollama  123  user  3u  IPv4  abc  0t0  TCP 127.0.0.1:11434 (LISTEN)"
_ALL_IFACES = f"{_HEADER}\nollama  123  user  3u  IPv4  abc  0t0  TCP *:11434 (LISTEN)"

# Ports in _AI_PORTS insertion order: 11434, 1234, 7860, 8080, 3000, 5000, 11435
_NR = ("", 1, None)  # not running (rc=1, no output)

def _expose(port):
    """Return a mock lsof result for a server bound to all interfaces on port."""
    return (f"{_HEADER}\nsrv  1  user  3u  IPv4  abc  0t0  TCP *:{port} (LISTEN)", 0, None)


def test_local_ai_server_not_running_pass():
    # rc=1, empty output → no listener on any port → PASS
    with patch("collectors.ai.run_cmd_rc", return_value=_NR):
        _ok(check_local_ai_server(), "PASS")


def test_local_ai_server_loopback_pass():
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[(_LOOPBACK, 0, None)] + [_NR] * 6):
        result = check_local_ai_server()
        _ok(result, "PASS")
        assert "127.0.0.1:11434" in result["raw"]


def test_local_ai_server_all_interfaces_fail():
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[(_ALL_IFACES, 0, None)] + [_NR] * 6):
        result = check_local_ai_server()
        _ok(result, "FAIL")
        assert "*:11434" in result["raw"]


def test_local_ai_server_lsof_error_unknown():
    # All ports error → UNKNOWN
    with patch("collectors.ai.run_cmd_rc",
               return_value=("", -1, "lsof: command not found")):
        _ok(check_local_ai_server(), "UNKNOWN")


def test_local_ai_server_second_port_fail():
    # Port 11434 not running, port 1234 bound to all interfaces → FAIL
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[_NR, _expose(1234)] + [_NR] * 5):
        result = check_local_ai_server()
        _ok(result, "FAIL")
        assert "*:1234" in result["raw"]


def test_local_ai_server_gradio_exposed_fail():
    # Port 7860 (index 2) bound to all interfaces → FAIL
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[_NR, _NR, _expose(7860)] + [_NR] * 4):
        result = check_local_ai_server()
        _ok(result, "FAIL")
        assert "*:7860" in result["raw"]
        assert "Gradio" in result["raw"]


def test_local_ai_server_open_webui_exposed_fail():
    # Port 8080 (index 3) bound to all interfaces → FAIL
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[_NR, _NR, _NR, _expose(8080)] + [_NR] * 3):
        result = check_local_ai_server()
        _ok(result, "FAIL")
        assert "*:8080" in result["raw"]
        assert "open-webui" in result["raw"]


def test_local_ai_server_localai_exposed_fail():
    # Port 3000 (index 4) bound to all interfaces → FAIL
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[_NR, _NR, _NR, _NR, _expose(3000)] + [_NR] * 2):
        result = check_local_ai_server()
        _ok(result, "FAIL")
        assert "*:3000" in result["raw"]
        assert "LocalAI" in result["raw"]


def test_local_ai_server_llamacpp_exposed_fail():
    # Port 5000 (index 5) bound to all interfaces → FAIL
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[_NR, _NR, _NR, _NR, _NR, _expose(5000), _NR]):
        result = check_local_ai_server()
        _ok(result, "FAIL")
        assert "*:5000" in result["raw"]
        assert "llama.cpp" in result["raw"]


def test_local_ai_server_ollama_alt_exposed_fail():
    # Port 11435 (index 6) bound to all interfaces → FAIL
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[_NR] * 6 + [_expose(11435)]):
        result = check_local_ai_server()
        _ok(result, "FAIL")
        assert "*:11435" in result["raw"]
        assert "Ollama (alternate port)" in result["raw"]


def test_local_ai_server_all_new_ports_not_running_pass():
    # All five new ports (7860, 8080, 3000, 5000, 11435) return rc=1 → PASS
    with patch("collectors.ai.run_cmd_rc",
               side_effect=[_NR] * 7):
        result = check_local_ai_server()
        _ok(result, "PASS")
        assert "not running (port 7860)" in result["raw"]
        assert "not running (port 8080)" in result["raw"]
        assert "not running (port 3000)" in result["raw"]
        assert "not running (port 5000)" in result["raw"]
        assert "not running (port 11435)" in result["raw"]
