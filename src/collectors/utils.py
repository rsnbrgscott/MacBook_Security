"""Shared utilities for collector modules."""

import subprocess


def run_cmd(cmd: list[str], timeout: int = 10) -> tuple[str, str | None]:
    """Run cmd, return (output, error). Never raises."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        # spctl writes to stderr on some macOS versions; prefer stdout, fall back to stderr.
        output = result.stdout.strip() or result.stderr.strip()
        if not output and result.returncode != 0:
            return "", f"Command exited {result.returncode}: {' '.join(cmd)}"
        return output, None
    except subprocess.TimeoutExpired:
        return "", f"Timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return "", str(e)


def run_cmd_rc(cmd: list[str], timeout: int = 10) -> tuple[str, int, str | None]:
    """Run cmd, return (output, returncode, error). Never raises."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = result.stdout.strip() or result.stderr.strip()
        return output, result.returncode, None
    except subprocess.TimeoutExpired:
        return "", -1, f"Timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return "", -1, f"Command not found: {cmd[0]}"
    except Exception as e:
        return "", -1, str(e)


def make_result(
    name: str,
    description: str,
    status: str,
    raw: str,
    error: str | None = None,
) -> dict:
    """Return a standard signal result dict."""
    return {"name": name, "description": description, "status": status, "raw": raw, "error": error}
