"""Tests for spec_mode_guard hook — blocks /spec in plan mode, warns in non-bypass mode."""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

from spec_mode_guard import run_spec_mode_guard


def _run_with_input(prompt: str, permission_mode: str) -> tuple[int, str]:
    """Simulate hook invocation. Returns (exit_code, stdout_output)."""
    hook_data = {"prompt": prompt, "permission_mode": permission_mode}
    stdin = StringIO(json.dumps(hook_data))
    with patch("sys.stdin", stdin), patch("sys.stdout", new_callable=StringIO) as stdout:
        code = run_spec_mode_guard()
        return code, stdout.getvalue()


class TestPlanModeBlocking:
    """Plan mode must hard-block /spec."""

    def test_blocks_spec_in_plan_mode(self):
        code, output = _run_with_input("/spec fix login bug", "plan")
        assert code == 2
        result = json.loads(output)
        assert result["decision"] == "block"
        assert "Plan mode" in result["reason"]
        assert "Shift+Tab" in result["reason"]

    def test_blocks_bare_spec_in_plan_mode(self):
        code, output = _run_with_input("/spec", "plan")
        assert code == 2
        result = json.loads(output)
        assert result["decision"] == "block"

    def test_blocks_spec_with_path_in_plan_mode(self):
        code, output = _run_with_input("/spec docs/plans/my-plan.md", "plan")
        assert code == 2


class TestBypassPermissionsAllowed:
    """/spec in bypassPermissions mode passes through silently."""

    def test_allows_spec_in_bypass_mode(self):
        code, output = _run_with_input("/spec fix login bug", "bypassPermissions")
        assert code == 0
        assert output == ""

    def test_allows_bare_spec_in_bypass_mode(self):
        code, output = _run_with_input("/spec", "bypassPermissions")
        assert code == 0
        assert output == ""


class TestNonBypassWarning:
    """Non-bypass modes get a warning but are not blocked."""

    def test_warns_in_default_mode(self):
        code, output = _run_with_input("/spec fix bug", "default")
        assert code == 0
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "default" in ctx
        assert "bypassPermissions" in ctx
        assert "proceed" in ctx.lower()

    def test_warns_in_accept_edits_mode(self):
        code, output = _run_with_input("/spec fix bug", "acceptEdits")
        assert code == 0
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "acceptEdits" in ctx
        assert "proceed" in ctx.lower()

    def test_warns_in_dont_ask_mode(self):
        code, output = _run_with_input("/spec fix bug", "dontAsk")
        assert code == 0
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "dontAsk" in ctx
        assert "proceed" in ctx.lower()

    def test_warning_does_not_block(self):
        """Non-bypass modes must NOT instruct the LLM to stop."""
        for mode in ("default", "acceptEdits", "dontAsk"):
            code, output = _run_with_input("/spec fix bug", mode)
            assert code == 0
            ctx = json.loads(output)["hookSpecificOutput"]["additionalContext"]
            assert "Do NOT" not in ctx
            assert "STOP" not in ctx


class TestNonSpecPrompts:
    """Non-/spec prompts pass through regardless of mode."""

    def test_allows_regular_prompt_in_plan_mode(self):
        code, output = _run_with_input("fix the login bug", "plan")
        assert code == 0
        assert output == ""

    def test_allows_regular_prompt_in_default_mode(self):
        code, output = _run_with_input("explain this code", "default")
        assert code == 0
        assert output == ""

    def test_allows_other_commands_in_plan_mode(self):
        code, output = _run_with_input("/setup-rules", "plan")
        assert code == 0
        assert output == ""

    def test_allows_create_skill_in_plan_mode(self):
        code, output = _run_with_input("/create-skill", "plan")
        assert code == 0
        assert output == ""


class TestEdgeCases:
    """Edge cases and malformed input."""

    def test_handles_invalid_json(self):
        stdin = StringIO("not json")
        with patch("sys.stdin", stdin):
            assert run_spec_mode_guard() == 0

    def test_handles_empty_stdin(self):
        stdin = StringIO("")
        with patch("sys.stdin", stdin):
            assert run_spec_mode_guard() == 0

    def test_handles_missing_prompt(self):
        stdin = StringIO(json.dumps({"permission_mode": "plan"}))
        with patch("sys.stdin", stdin), patch("sys.stdout", new_callable=StringIO):
            assert run_spec_mode_guard() == 0

    def test_handles_missing_permission_mode(self):
        code, output = _run_with_input("/spec fix bug", "")
        assert code == 0
        assert output == ""

    def test_handles_empty_prompt(self):
        code, output = _run_with_input("", "plan")
        assert code == 0
        assert output == ""
