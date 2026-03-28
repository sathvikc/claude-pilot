#!/usr/bin/env python3
"""Guard: blocks /spec when in plan mode, warns when not in bypassPermissions mode.

Uses the permission_mode common input field from Claude Code hooks to detect
the current runtime permission mode (plan, default, acceptEdits, dontAsk,
bypassPermissions).
"""

from __future__ import annotations

import json
import sys


def run_spec_mode_guard() -> int:
    """Check permission mode before allowing /spec invocation."""
    try:
        hook_data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    prompt = hook_data.get("prompt", "").strip()
    permission_mode = hook_data.get("permission_mode", "")

    if not prompt.startswith("/spec"):
        return 0

    if permission_mode == "plan":
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "[Pilot] /spec cannot run in Plan mode. "
                        "Press Shift+Tab to cycle to 'Bypass Permissions' mode, then try again."
                    ),
                }
            )
        )
        sys.stderr.write("\033[0;31m[Pilot] /spec blocked: Plan mode is incompatible with /spec workflow\033[0m\n")
        return 2

    if permission_mode and permission_mode != "bypassPermissions":
        sys.stderr.write(
            f"\033[0;33m[Pilot] Warning: /spec works best in 'Bypass Permissions' mode "
            f"(current: {permission_mode}). Press Shift+Tab to switch.\033[0m\n"
        )
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": (
                            f"NOTE: Current permission mode is '{permission_mode}'. "
                            "For uninterrupted /spec execution, 'bypassPermissions' mode is recommended "
                            "(Shift+Tab to cycle). In the current mode the workflow may pause for "
                            "permission prompts. Briefly warn the user, then proceed with the workflow."
                        ),
                    }
                }
            )
        )

    return 0


if __name__ == "__main__":
    sys.exit(run_spec_mode_guard())
