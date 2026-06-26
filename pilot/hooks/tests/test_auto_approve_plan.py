"""Tests for auto_approve_plan hook - auto-approves ExitPlanMode and requests bypassPermissions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent / "auto_approve_plan.py"


def _run() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout


class TestAutoApprovePlan:
    def test_exits_zero(self):
        code, _ = _run()
        assert code == 0

    def test_outputs_valid_json(self):
        _, stdout = _run()
        data = json.loads(stdout.strip())
        assert isinstance(data, dict)

    def test_behavior_is_allow(self):
        _, stdout = _run()
        data = json.loads(stdout.strip())
        decision = data["hookSpecificOutput"]["decision"]
        assert decision["behavior"] == "allow"

    def test_hook_event_name(self):
        _, stdout = _run()
        data = json.loads(stdout.strip())
        assert data["hookSpecificOutput"]["hookEventName"] == "PermissionRequest"

    def test_requests_bypass_permissions(self):
        _, stdout = _run()
        data = json.loads(stdout.strip())
        perms = data["hookSpecificOutput"]["decision"]["updatedPermissions"]
        assert any(p.get("type") == "setMode" and p.get("mode") == "bypassPermissions" for p in perms)

    def test_message_does_not_claim_plan_approval(self):
        """The decision message must NOT signal that the plan is approved.

        Regression guard: emitting "Plan auto-approved" made agents misread the
        auto-allowed ExitPlanMode (a model-switch/permission action) as the user
        approving the plan, so they skipped the real /spec approval gate
        (spec-plan/steps/12-approval.md). The message must perform the permission
        action while explicitly disclaiming plan approval.
        """
        _, stdout = _run()
        data = json.loads(stdout.strip())
        message = data["hookSpecificOutput"]["decision"]["message"].lower()
        assert "approved" not in message, f"misleading approval wording: {message!r}"
        assert "not plan approval" in message, f"missing disclaimer: {message!r}"
