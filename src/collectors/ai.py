"""AI security signal collectors: shell config key exposure, history key exposure,
local AI server network exposure.

No sudo required. All filesystem reads use pathlib; subprocess is only used for lsof.

History format note: zsh_history may be plain commands or extended format
(': <ts>:<elapsed>;<cmd>'). Both are handled by stripping the prefix before
pattern matching.
"""

import pathlib
import re

try:
    from .utils import run_cmd_rc, make_result
except ImportError:
    from utils import run_cmd_rc, make_result  # noqa: F401 — direct script execution

# ---------------------------------------------------------------------------
# Shell config signal
# ---------------------------------------------------------------------------

_SHELL_CONFIG_FILES = [
    pathlib.Path("~/.zshrc").expanduser(),
    pathlib.Path("~/.zprofile").expanduser(),
    pathlib.Path("~/.zshenv").expanduser(),
    pathlib.Path("~/.bashrc").expanduser(),
    pathlib.Path("~/.bash_profile").expanduser(),
    pathlib.Path("~/.profile").expanduser(),
]

_KEY_NAMES = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "CLAUDE_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "COHERE_API_KEY",
    "GROQ_API_KEY",
    "MISTRAL_API_KEY",
    "HUGGINGFACE_HUB_TOKEN",
    "TOGETHER_API_KEY",
    "REPLICATE_API_TOKEN",
    "PERPLEXITY_API_KEY",
]

_KEY_NAME_PATTERN = re.compile(
    r"(?:export\s+)?(" + "|".join(_KEY_NAMES) + r")\s*="
)


def check_ai_keys_shell_config() -> dict:
    """Check shell config files for plaintext AI API key variable assignments.

    Scans ~/.zshrc, ~/.zprofile, ~/.zshenv, ~/.bashrc, ~/.bash_profile, ~/.profile.
    Absent files are silently skipped. Reports key variable names and filenames
    only — never the key values themselves.

    PASS    — no AI key variable names found in any config file
    WARN    — one or more AI key exports or assignments detected
    UNKNOWN — every candidate file failed to read (e.g. permissions error)
    """
    name = "AI API Keys in Shell Config"
    desc = (
        "AI API keys stored in shell config files are readable by any process "
        "running as this user and are frequently committed to git by accident. "
        "Keys should live in a password manager or secrets vault, not dotfiles."
    )

    hits = []       # list of "filename: KEY_NAME" strings (no values)
    files_read = 0

    for path in _SHELL_CONFIG_FILES:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            # Absent or unreadable — expected for most files on most machines.
            continue
        files_read += 1
        for line in text.splitlines():
            m = _KEY_NAME_PATTERN.search(line)
            if m:
                hits.append(f"{path}: {m.group(1)}")

    if files_read == 0:
        return make_result(name, desc, "UNKNOWN", "",
                           "No shell config files could be read.")

    if not hits:
        return make_result(name, desc, "PASS",
                           "No AI API key variables found in shell config files.")

    return make_result(name, desc, "WARN", "\n".join(hits))


# ---------------------------------------------------------------------------
# Shell history signal
# ---------------------------------------------------------------------------

_HISTORY_FILES = [
    pathlib.Path("~/.zsh_history").expanduser(),
    pathlib.Path("~/.bash_history").expanduser(),
]

# Extended zsh history prefix: ': <timestamp>:<elapsed>;'
_ZSH_EXTENDED_PREFIX = re.compile(r"^: \d+:\d+;")

# Value-pattern regexes — match key material, not key names
_KEY_VALUE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),           # OpenAI key prefix
    re.compile(r"sk-ant-api[0-9]{2}-"),             # Anthropic key prefix
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),           # Google API key prefix
]


def check_ai_keys_shell_history() -> dict:
    """Check shell history files for AI API key values typed or pasted in the terminal.

    Scans ~/.zsh_history and ~/.bash_history. Absent files are PASS (not UNKNOWN).
    Counts matches only — never includes matched strings in the raw output.

    PASS    — no key value patterns found in any history file
    WARN    — one or more matches found; raw shows file name and count
    UNKNOWN — at least one history file exists but all are completely unreadable
    """
    name = "Shell History Key Exposure"
    desc = (
        "AI API keys pasted or typed in the terminal are saved in shell history "
        "in plaintext. Any process running as this user can read history files. "
        "Rotate any exposed keys immediately."
    )

    hit_lines = []   # "~/.zsh_history: N match(es)" — counts only
    files_seen = 0
    read_errors = []

    for path in _HISTORY_FILES:
        if not path.exists():
            continue  # absent = PASS for that file, not an error
        files_seen += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            read_errors.append(f"{path}: {e}")
            continue

        count = 0
        for line in text.splitlines():
            cmd = _ZSH_EXTENDED_PREFIX.sub("", line)
            for pattern in _KEY_VALUE_PATTERNS:
                if pattern.search(cmd):
                    count += 1
                    break  # one match per line is enough

        if count > 0:
            hit_lines.append(f"{path}: {count} pattern match(es)")

    if files_seen == 0:
        # No history files on this machine at all — not a security concern.
        return make_result(name, desc, "PASS",
                           "No shell history files found.")

    if read_errors and not hit_lines and files_seen == len(read_errors):
        return make_result(name, desc, "UNKNOWN", "",
                           "History file(s) present but unreadable: "
                           + "; ".join(read_errors))

    if not hit_lines:
        return make_result(name, desc, "PASS",
                           "No AI API key patterns found in shell history.")

    return make_result(name, desc, "WARN", "\n".join(hit_lines))


# ---------------------------------------------------------------------------
# Local AI server signal
# ---------------------------------------------------------------------------

_AI_PORTS: dict[int, str] = {
    11434: "Ollama",
    1234: "LM Studio",
    7860: "Gradio / text-generation-webui",
    8080: "open-webui",
    3000: "LocalAI",
    5000: "llama.cpp server",
    11435: "Ollama (alternate port)",
}


def check_local_ai_server() -> dict:
    """Check whether a local AI inference server is bound to all network interfaces.

    Checks seven ports using lsof (no sudo required):
      11434 — Ollama
       1234 — LM Studio
       7860 — Gradio / text-generation-webui
       8080 — open-webui
       3000 — LocalAI
       5000 — llama.cpp server
      11435 — Ollama (alternate port)

    A server bound to 127.0.0.1 is loopback-only and PASS. A server bound to *
    is reachable by any host on the local network and FAIL.

    PASS    — no AI server listening, or all listeners are loopback-only
    FAIL    — at least one AI server is bound to all interfaces
    UNKNOWN — lsof command failed
    """
    name = "Local AI Server Exposure"
    desc = (
        "A local AI model server (Ollama, LM Studio, Gradio, open-webui, LocalAI, "
        "llama.cpp) bound to all interfaces is accessible to any host on your "
        "network and can receive arbitrary prompts. The default is loopback-only; "
        "exposure usually means a host environment variable was set intentionally "
        "or accidentally."
    )

    fail_lines = []
    pass_lines = []
    errors = []

    for port, service in _AI_PORTS.items():
        raw, rc, err = run_cmd_rc(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
            timeout=10,
        )
        if err:
            errors.append(f"{service} (port {port}): {err}")
            continue

        if rc == 1 or not raw:
            # No process listening on this port.
            pass_lines.append(f"{service}: not running (port {port})")
            continue

        if rc != 0:
            errors.append(f"{service} (port {port}): lsof exited {rc}")
            continue

        # Parse data lines (skip header).
        for line in raw.splitlines()[1:]:
            parts = line.split()
            if not parts:
                continue
            name_field = parts[-2] if len(parts) >= 2 else ""
            if name_field.startswith("*:"):
                fail_lines.append(
                    f"{service}: {name_field} (all interfaces — network-accessible)"
                )
            elif "127.0.0.1:" in name_field or "[::1]:" in name_field:
                pass_lines.append(f"{service}: {name_field} (loopback only)")
            else:
                # Unexpected binding — treat conservatively as FAIL.
                fail_lines.append(
                    f"{service}: {name_field} (unknown binding — review)"
                )

    if not fail_lines and not pass_lines and errors:
        return make_result(name, desc, "UNKNOWN", "",
                           "; ".join(errors))

    all_lines = fail_lines + pass_lines
    if errors:
        all_lines.append("Errors: " + "; ".join(errors))

    raw_out = "\n".join(all_lines) if all_lines else \
        "No AI server listening on known ports (11434, 1234, 7860, 8080, 3000, 5000, 11435)."

    if fail_lines:
        return make_result(name, desc, "FAIL", raw_out)

    return make_result(name, desc, "PASS", raw_out)


if __name__ == "__main__":
    checks = [
        ("AI API Keys in Shell Config", check_ai_keys_shell_config),
        ("Shell History Key Exposure", check_ai_keys_shell_history),
        ("Local AI Server Exposure", check_local_ai_server),
    ]
    for label, fn in checks:
        sig = fn()
        print(f"[{sig['status']:^7}] {label}")
        print(f"         raw: {sig['raw']!r}")
        if sig["error"]:
            print(f"         error: {sig['error']}")
        print()
