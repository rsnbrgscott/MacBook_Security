"""macOS notification sender using osascript's display notification command."""

import subprocess


def send_notification(title: str, message: str) -> None:
    """Send a macOS notification banner via osascript.

    Double-quotes in title/message are replaced with single quotes to avoid
    breaking the AppleScript string literal. Failures are silently ignored so
    that a broken notification path never crashes the alerter thread.
    """
    safe_title = title.replace('"', "'")
    safe_message = message.replace('"', "'")
    script = f'display notification "{safe_message}" with title "{safe_title}"'
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass
