"""Tests for session_end hook — worker stop behavior with direct filesystem checks."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import session_end


def test_returns_early_without_plugin_root():
    """Should return 0 when CLAUDE_PLUGIN_ROOT is not set."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("CLAUDE_PLUGIN_ROOT", None)
        result = session_end.main()

    assert result == 0


def test_skips_stop_when_other_sessions_active(tmp_path: Path):
    """Should skip worker stop when other Pilot sessions are running."""
    base = tmp_path / "sessions"
    (base / "1001").mkdir(parents=True)
    (base / "2002").mkdir(parents=True)

    with (
        patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": "/fake/plugin", "PILOT_SESSION_ID": "1001"}),
        patch.object(session_end, "SESSIONS_DIR", base),
        patch("session_end.os.kill", return_value=None),
        patch("session_end.subprocess.run") as mock_run,
    ):
        result = session_end.main()

    assert result == 0
    mock_run.assert_not_called()


def test_stops_worker_when_no_other_sessions(tmp_path: Path):
    """Should stop worker when this is the only active session."""
    base = tmp_path / "sessions"
    (base / "1001").mkdir(parents=True)

    with (
        patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": "/fake/plugin", "PILOT_SESSION_ID": "1001"}),
        patch.object(session_end, "SESSIONS_DIR", base),
        patch("session_end.subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
    ):
        result = session_end.main()

    assert result == 0
    mock_run.assert_called_once()
    assert "stop" in str(mock_run.call_args)


def test_stops_worker_when_zero_sessions(tmp_path: Path):
    """Should stop worker and return 0 when no sessions exist at all."""
    base = tmp_path / "sessions"
    base.mkdir(parents=True)

    with (
        patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": "/fake/plugin", "PILOT_SESSION_ID": "1001"}),
        patch.object(session_end, "SESSIONS_DIR", base),
        patch("session_end.subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
    ):
        result = session_end.main()

    assert result == 0
    mock_run.assert_called_once()


def test_safe_default_on_directory_error():
    """Should NOT stop worker when directory can't be read (safe default)."""
    mock_dir = MagicMock()
    mock_dir.exists.side_effect = OSError("permission denied")

    with (
        patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": "/fake/plugin", "PILOT_SESSION_ID": "1001"}),
        patch.object(session_end, "SESSIONS_DIR", mock_dir),
        patch("session_end.subprocess.run") as mock_run,
    ):
        result = session_end.main()

    assert result == 0
    mock_run.assert_not_called()


def test_skips_dead_pid_sessions(tmp_path: Path):
    """Should not count dead PID directories as active sessions."""
    base = tmp_path / "sessions"
    (base / "1001").mkdir(parents=True)  # current
    (base / "9999").mkdir(parents=True)  # dead

    def kill_side_effect(pid: int, _sig: int) -> None:
        if pid == 9999:
            raise OSError("No such process")

    with (
        patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": "/fake/plugin", "PILOT_SESSION_ID": "1001"}),
        patch.object(session_end, "SESSIONS_DIR", base),
        patch("session_end.os.kill", side_effect=kill_side_effect),
        patch("session_end.subprocess.run", return_value=MagicMock(returncode=0)) as mock_run,
    ):
        result = session_end.main()

    assert result == 0
    mock_run.assert_called_once()
    assert "stop" in str(mock_run.call_args)
