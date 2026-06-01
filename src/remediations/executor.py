import subprocess
from . import REMEDIATIONS


def run_fix(signal_name: str) -> dict:
    if signal_name not in REMEDIATIONS:
        return {"success": False, "output": "", "error": f"No remediation available for '{signal_name}'"}

    cmd = REMEDIATIONS[signal_name]["cmd"]
    try:
        result = subprocess.run(
            ["osascript", "-e", f'do shell script "{cmd}" with administrator privileges'],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout.strip(), "error": None}
        stderr = result.stderr.strip()
        if "User canceled" in stderr:
            return {"success": False, "output": "", "error": "Cancelled."}
        return {"success": False, "output": "", "error": stderr or f"Command exited {result.returncode}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Timed out after 30s — auth dialog may still be open"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
