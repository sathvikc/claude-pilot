#!/usr/bin/env python3
"""SessionStart hook (Claude Code only): deliver one-time announcements.

Each announcement is injected into the session via `additionalContext` exactly
once. The hook touches the ack sentinel itself before injecting, so the message
shows once regardless of session outcome -- no AskUserQuestion round-trip needed.

Extensible: add entries to ANNOUNCEMENTS. Stdlib only (package boundary);
never raises.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Ordered list of one-time announcements. Add new entries here; each shows once
# (per machine) until acknowledged. Keep messages ASCII (no-emojis-in-source).
ANNOUNCEMENTS: list[dict[str, str]] = [
    {
        "id": "model-switching-modes",
        "message": (
            "Pilot Shell -- Model Switching now has three modes: Automated (default), Manual, Off.\n\n"
            "What changed: the 9.12 window-scoped Fable/Opus pin machinery has been removed --\n"
            "it remapped model aliases across ALL sessions (a Fable planning session could pull\n"
            "your other sessions' Opus to Fable too). Pilot no longer touches those aliases, so\n"
            "/model always means what it says.\n\n"
            "The modes (Console -> Settings -> Model Switching):\n"
            "  - Automated (default): /spec runs on `opusplan` -- Opus plans, Sonnet executes,\n"
            "    switched automatically. Requires /model opusplan (Pilot sets it for you). A new\n"
            "    pre-flight check warns when your context is too large for the Opus plan leg\n"
            "    (where Claude Code would otherwise silently keep planning on Sonnet).\n"
            "  - Manual: you pick models yourself with /model. /spec pauses once after plan\n"
            "    approval so you can switch to your implementation model.\n"
            "  - Off: no model management, no prompts -- everything runs on your active /model.\n\n"
            "Your existing setting migrated: Model Switching ON -> Automated, OFF -> Off.\n\n"
            "Docs: https://pilot-shell.com/docs/features/model-routing"
        ),
    },
]


def _pilot_dir() -> Path:
    return Path.home() / ".pilot"


def _ack_path(announce_id: str, base: Path) -> Path:
    """Ack sentinel path: ``<base>/.announce-<id>-ack``."""
    return base / f".announce-{announce_id}-ack"


def pending(base: Path, announcements: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return announcements whose ack sentinel does not yet exist."""
    result: list[dict[str, str]] = []
    for a in announcements:
        try:
            if not _ack_path(a["id"], base).exists():
                result.append(a)
        except OSError:
            result.append(a)
    return result


def render_context(pending_list: list[dict[str, str]]) -> str:
    """Build the SessionStart additionalContext for the pending announcements.

    Empty string when nothing is pending.
    Ack sentinels are touched by the hook before this context is injected.
    """
    if not pending_list:
        return ""
    blocks: list[str] = [
        "[Pilot one-time announcement] Display the following announcement(s) to "
        "the user as clearly formatted text output. "
        "Do NOT use AskUserQuestion. "
        "Just show the announcement text, then continue with the user's request."
    ]
    for a in pending_list:
        blocks.append(f"\n--- Announcement ---\n{a['message']}")
    return "\n".join(blocks)


def main() -> None:
    # Claude Code only -- Codex has no SessionStart announcement channel here.
    if not os.environ.get("CLAUDE_CODE_ENTRYPOINT"):
        return
    try:
        base = _pilot_dir()
        pending_list = pending(base, ANNOUNCEMENTS)
        ctx = render_context(pending_list)
        if not ctx:
            return
        # Touch ack sentinels now so each announcement shows exactly once.
        for a in pending_list:
            try:
                _ack_path(a["id"], base).touch()
            except OSError:
                pass
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": ctx,
                    }
                }
            )
        )
    except Exception:
        # SessionStart hook: never raise / never block the session.
        return


if __name__ == "__main__":
    main()
