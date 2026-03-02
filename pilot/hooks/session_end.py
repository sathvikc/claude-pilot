#!/usr/bin/env python3
"""SessionEnd hook - stops worker only when no other sessions are active.

Checks session directories directly (no subprocess) for reliability during
shutdown. Only stops the worker when the current session is the last active one.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

SESSIONS_DIR = Path.home() / ".pilot" / "sessions"
SKIP_NAMES = {"default", "pipes"}


def _has_other_active_sessions() -> bool:
    """Check if any other Pilot wrapper sessions are still active.

    Iterates session directories directly (no subprocess) to avoid failures
    during shutdown. Skips the current session via PILOT_SESSION_ID.
    Returns True on any error (safe default: don't stop the worker).
    """
    try:
        if not SESSIONS_DIR.exists():
            return False

        my_session = os.environ.get("PILOT_SESSION_ID", "")

        for entry in SESSIONS_DIR.iterdir():
            if not entry.is_dir() or entry.name in SKIP_NAMES:
                continue
            if entry.name == my_session:
                continue
            try:
                pid = int(entry.name)
            except ValueError:
                continue
            try:
                os.kill(pid, 0)
            except OSError:
                continue

            # Another wrapper PID is alive → another session exists
            return True

        return False
    except OSError:
        # Can't read directory → assume other sessions exist (safe default)
        return True


def main() -> int:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        return 0

    if _has_other_active_sessions():
        return 0

    stop_script = Path(plugin_root) / "scripts" / "worker-service.cjs"
    try:
        subprocess.run(
            ["bun", str(stop_script), "stop"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
