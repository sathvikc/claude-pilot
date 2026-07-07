"""Tests for the vendored ask-codex app-server clients.

Covers ONLY the Pilot-authored safety modifications (bounded JSON-RPC request
deadlines, per-call terminate opt-out, CODEX_BIN resolution, failed-turn
surfacing) - upstream plumbing stays E2E-covered. The fake "codex" binary
stays alive and never responds, reproducing the live-but-silent app-server
hang the deadline guards against.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import time
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str) -> ModuleType:
    """Import a script file under a unique module name (scripts/ is not a package)."""
    spec = importlib.util.spec_from_file_location(f"ask_codex_{name}", SCRIPTS_DIR / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_child_exits(proc: subprocess.Popen[str]) -> None:
    """The client's child process must be gone (terminated and reaped, no orphan)."""
    proc.wait(timeout=5)


@pytest.fixture()
def silent_server(tmp_path: Path) -> Path:
    """Fake codex binary: accepts the app-server arg, consumes stdin, never responds."""
    stub = tmp_path / "codex-stub"
    stub.write_text("#!/bin/sh\nexec cat >/dev/null\n")
    stub.chmod(0o755)
    return stub


class TestRequestDeadline:
    def test_appserver_request_raises_and_reaps_child_when_server_silent(
        self, silent_server: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CODEX_BIN", str(silent_server))
        mod = _load("codex_appserver")
        srv = mod.AppServer(cwd=str(silent_server.parent))
        with pytest.raises(RuntimeError, match="initialize"):
            srv.request("initialize", deadline=0.2)
        _assert_child_exits(srv.p)

    def test_session_conn_request_raises_and_reaps_child_when_server_silent(
        self, silent_server: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CODEX_BIN", str(silent_server))
        mod = _load("codex_session")
        conn = mod.Conn(on_note=lambda method, params, req_id: None)
        with pytest.raises(RuntimeError, match="initialize"):
            conn.request("initialize", deadline=0.2)
        _assert_child_exits(conn.p)

    def test_no_terminate_flag_keeps_server_alive_for_the_active_turn(
        self, silent_server: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A slow steer/interrupt ack must NOT kill the shared app-server mid-turn."""
        monkeypatch.setenv("CODEX_BIN", str(silent_server))
        mod = _load("codex_session")
        conn = mod.Conn(on_note=lambda method, params, req_id: None)
        try:
            with pytest.raises(RuntimeError, match="turn/steer"):
                conn.request("turn/steer", deadline=0.2, terminate_on_timeout=False)
            assert conn.p.poll() is None  # server survives; only the request gave up
        finally:
            conn.p.terminate()
            _assert_child_exits(conn.p)


class TestVendoredAttribution:
    def test_both_scripts_carry_upstream_attribution_headers(self) -> None:
        """MIT attribution + pinned upstream commit must survive reformat/rename sweeps
        (the header silently vanished once during an automated sweep - this pins it)."""
        for name in ("codex_appserver.py", "codex_session.py"):
            head = (SCRIPTS_DIR / name).read_text()[:600]
            assert "Vendored from https://github.com/FabianWesner/claude-code-codex-skill" in head, name
            assert "MIT License" in head, name
            assert "0250cfc" in head, name


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class TestProcessGroupReap:
    def test_reap_kills_grandchildren_spawned_by_the_server(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Killing only the direct child orphans the app-server's own tool
        subprocesses (Codex review finding). _reap must take down the group."""
        grandchild_pid_file = tmp_path / "grandchild.pid"
        stub = tmp_path / "codex-stub"
        stub.write_text(f"#!/bin/sh\nsleep 300 &\necho $! > {grandchild_pid_file}\nexec cat >/dev/null\n")
        stub.chmod(0o755)
        monkeypatch.setenv("CODEX_BIN", str(stub))
        mod = _load("codex_session")
        conn = mod.Conn(on_note=lambda method, params, req_id: None)
        deadline = time.monotonic() + 5
        while not grandchild_pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        gc_pid = int(grandchild_pid_file.read_text().strip())
        conn._reap()
        _assert_child_exits(conn.p)
        deadline = time.monotonic() + 5
        while _pid_alive(gc_pid) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert not _pid_alive(gc_pid)  # grandchild reaped with the group, not orphaned


class TestSessionFailedTurn:
    def test_turn_failed_writes_error_result_and_clears_active_turn(
        self, silent_server: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("CODEX_BIN", str(silent_server))
        mod = _load("codex_session")
        session_dir = tmp_path / "session"
        args = SimpleNamespace(
            dir=str(session_dir), cwd=str(tmp_path), model="m", effort="e", sandbox="read-only", prompt=None
        )
        sess = mod.Session(args)
        try:
            sess.turn_id = "turn-1"
            sess._on_note("turn/failed", {"error": "401 refresh token revoked"}, None)
            assert sess.turn_id is None  # next `turn:` command must not be rejected as already active
            assert "401 refresh token revoked" in (session_dir / "result.txt").read_text()
        finally:
            sess.conn.p.terminate()
            _assert_child_exits(sess.conn.p)
