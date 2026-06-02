"""Tests for codegraph_init hook — CodeGraph init/sync on SessionStart."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from codegraph_init import (
    INDEX_TIMEOUT_SECONDS,
    REPAIR_TIMEOUT_SECONDS,
    SYNC_TIMEOUT_SECONDS,
    _enable_embeddings,
    _find_codegraph_package_dir,
    _get_project_dir,
    _has_git_commits,
    _is_corrupt_db_error,
    _is_in_git_repo,
    _is_indexed,
    _is_using_wasm_sqlite,
    _kill_group,
    _op_timeout,
    _recover_corrupt_db,
    _repair_native_sqlite,
    _run,
    _run_group,
    main,
)


def _test_lock_dir(home: Path, project_dir: Path) -> Path:
    digest = hashlib.sha256(str(project_dir.resolve()).encode("utf-8")).hexdigest()[:24]
    return home / ".pilot" / "cache" / "codegraph-init" / digest


class TestGitDetection:
    def test_is_in_git_repo_true(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        assert _is_in_git_repo(tmp_path) is True

    def test_is_in_git_repo_false(self, tmp_path: Path) -> None:
        assert _is_in_git_repo(tmp_path) is False

    def test_is_in_git_repo_walks_up(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        assert _is_in_git_repo(subdir) is True

    @patch("codegraph_init.subprocess.run")
    def test_has_git_commits_true(self, mock_run: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        assert _has_git_commits(tmp_path) is True

    @patch("codegraph_init.subprocess.run")
    def test_has_git_commits_false(self, mock_run: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=128)
        assert _has_git_commits(tmp_path) is False

    @patch("codegraph_init.subprocess.run", side_effect=OSError)
    def test_has_git_commits_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        assert _has_git_commits(tmp_path) is False


class TestEnableEmbeddings:
    def test_creates_config_when_exists(self, tmp_path: Path) -> None:
        cg = tmp_path / ".codegraph"
        cg.mkdir()
        config = cg / "config.json"
        config.write_text(json.dumps({"someKey": True}))

        _enable_embeddings(tmp_path)

        data = json.loads(config.read_text())
        assert data["enableEmbeddings"] is True
        assert data["someKey"] is True

    def test_noop_when_already_enabled(self, tmp_path: Path) -> None:
        cg = tmp_path / ".codegraph"
        cg.mkdir()
        config = cg / "config.json"
        config.write_text(json.dumps({"enableEmbeddings": True}))
        mtime_before = config.stat().st_mtime_ns

        _enable_embeddings(tmp_path)

        assert config.stat().st_mtime_ns == mtime_before

    def test_noop_when_no_config(self, tmp_path: Path) -> None:
        _enable_embeddings(tmp_path)


class TestIsIndexed:
    def test_true_when_db_large(self, tmp_path: Path) -> None:
        cg = tmp_path / ".codegraph"
        cg.mkdir()
        db = cg / "codegraph.db"
        db.write_bytes(b"\x00" * 2_000_000)
        assert _is_indexed(tmp_path) is True

    def test_false_when_db_small(self, tmp_path: Path) -> None:
        cg = tmp_path / ".codegraph"
        cg.mkdir()
        db = cg / "codegraph.db"
        db.write_bytes(b"\x00" * 100_000)
        assert _is_indexed(tmp_path) is False

    def test_false_when_no_db(self, tmp_path: Path) -> None:
        assert _is_indexed(tmp_path) is False


class TestCorruptDb:
    def test_detects_malformed(self) -> None:
        assert _is_corrupt_db_error("database disk image is malformed") is True

    def test_detects_not_a_database(self) -> None:
        assert _is_corrupt_db_error("file is not a database") is True

    def test_false_for_normal_error(self) -> None:
        assert _is_corrupt_db_error("command not found") is False

    def test_recover_removes_dir(self, tmp_path: Path) -> None:
        cg = tmp_path / ".codegraph"
        cg.mkdir()
        (cg / "codegraph.db").write_text("corrupt")
        assert _recover_corrupt_db(tmp_path) is True
        assert not cg.exists()

    def test_recover_noop_when_missing(self, tmp_path: Path) -> None:
        assert _recover_corrupt_db(tmp_path) is False


class TestWasmSqliteRepair:
    @patch("codegraph_init.subprocess.run")
    def test_detects_wasm_backend(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"[CodeGraph] Using WASM SQLite backend (native better-sqlite3 unavailable)\n",
            stderr=b"",
        )
        assert _is_using_wasm_sqlite() is True

    @patch("codegraph_init.subprocess.run")
    def test_native_backend_not_wasm(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout=b"CodeGraph Status\n", stderr=b"")
        assert _is_using_wasm_sqlite() is False

    @patch("codegraph_init.subprocess.run", side_effect=OSError)
    def test_wasm_check_error(self, _mock_run: MagicMock) -> None:
        assert _is_using_wasm_sqlite() is False

    @patch("codegraph_init.shutil.which", return_value="/usr/bin/codegraph")
    def test_find_package_dir(self, _mock_which: MagicMock, tmp_path: Path) -> None:
        pkg_dir = tmp_path / "node_modules" / "@colbymchenry" / "codegraph"
        pkg_dir.mkdir(parents=True)
        bin_dir = pkg_dir / "dist" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "codegraph.js").write_text("")
        (pkg_dir / "package.json").write_text(json.dumps({"name": "@colbymchenry/codegraph"}))

        with patch("codegraph_init.Path.resolve", return_value=bin_dir / "codegraph.js"):
            result = _find_codegraph_package_dir()
        assert result == pkg_dir

    @patch("codegraph_init.shutil.which", return_value=None)
    def test_find_package_dir_no_binary(self, _mock_which: MagicMock) -> None:
        assert _find_codegraph_package_dir() is None

    @patch("codegraph_init._run_group")
    @patch("codegraph_init._find_codegraph_package_dir")
    def test_repair_rebuilds_bundled(self, mock_find: MagicMock, mock_group: MagicMock, tmp_path: Path) -> None:
        pkg_dir = tmp_path / "codegraph-pkg"
        pkg_dir.mkdir()
        (pkg_dir / "node_modules" / "better-sqlite3").mkdir(parents=True)
        mock_find.return_value = pkg_dir
        mock_group.return_value = subprocess.CompletedProcess(["npm"], 0, b"", b"")

        assert _repair_native_sqlite() is True
        mock_group.assert_called_once_with(["npm", "rebuild", "better-sqlite3"], pkg_dir, REPAIR_TIMEOUT_SECONDS)

    @patch("codegraph_init._run_group")
    @patch("codegraph_init._find_codegraph_package_dir", return_value=None)
    def test_repair_falls_back_to_global(self, _mock_find: MagicMock, mock_group: MagicMock) -> None:
        mock_group.return_value = subprocess.CompletedProcess(["npm"], 0, b"", b"")
        assert _repair_native_sqlite() is True
        mock_group.assert_called_once_with(
            ["npm", "install", "-g", "better-sqlite3", "--no-audit", "--no-fund"],
            Path.cwd(),
            REPAIR_TIMEOUT_SECONDS,
        )


class TestRun:
    @patch("codegraph_init._run_group")
    def test_success(self, mock_group: MagicMock, tmp_path: Path) -> None:
        mock_group.return_value = subprocess.CompletedProcess(["codegraph", "sync"], 0, b"", b"")
        assert _run(["codegraph", "sync"], tmp_path) is True

    @patch("codegraph_init._run_group")
    def test_failure(self, mock_group: MagicMock, tmp_path: Path) -> None:
        mock_group.return_value = subprocess.CompletedProcess(["codegraph", "sync"], 1, b"", b"")
        assert _run(["codegraph", "sync"], tmp_path) is False

    @patch("codegraph_init._run_group", return_value=None)
    def test_timeout(self, mock_group: MagicMock, tmp_path: Path) -> None:
        # _run_group returns None on timeout/spawn failure.
        assert _run(["codegraph", "sync"], tmp_path) is False


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


_posix_only = pytest.mark.skipif(os.name != "posix", reason="process-group reaping is POSIX-only")


class TestProcessGroupReaping:
    """A timed-out codegraph subprocess must not orphan its worker subtree.

    Regression for the Codex pile-up: subprocess.run(timeout=N) SIGKILLs only the
    direct child, leaving CodeGraph's Node workers running. We model a worker with a
    backgrounded grandchild process; after _run times out it must be dead too.
    """

    @_posix_only
    def test_run_reaps_orphan_grandchild_on_timeout(self, tmp_path: Path) -> None:
        pidfile = tmp_path / "grandchild.pid"
        # Parent shell backgrounds a detached grandchild (stdio redirected so it does
        # not hold the captured pipe open), records its pid, then blocks past timeout.
        script = f'sleep 30 >/dev/null 2>&1 & echo $! > "{pidfile}"; sleep 30'

        grandchild_pid: int | None = None
        try:
            assert _run(["sh", "-c", script], tmp_path, timeout=1) is False

            for _ in range(50):
                if pidfile.exists() and pidfile.read_text().strip():
                    break
                time.sleep(0.1)
            grandchild_pid = int(pidfile.read_text().strip())

            # Give the kill a moment to propagate, then assert the worker is gone.
            for _ in range(50):
                if not _pid_alive(grandchild_pid):
                    break
                time.sleep(0.1)
            assert not _pid_alive(grandchild_pid), (
                f"grandchild {grandchild_pid} survived _run timeout — process tree orphaned"
            )
        finally:
            if grandchild_pid is not None and _pid_alive(grandchild_pid):
                with contextlib.suppress(ProcessLookupError, OSError):
                    os.kill(grandchild_pid, signal.SIGKILL)

    @_posix_only
    def test_run_group_returns_completed_process_on_success(self, tmp_path: Path) -> None:
        result = _run_group(["sh", "-c", "printf out; printf err >&2; exit 0"], tmp_path, 10)
        assert result is not None
        assert result.returncode == 0
        assert result.stdout == b"out"
        assert result.stderr == b"err"

    @_posix_only
    def test_run_group_returns_none_on_spawn_failure(self, tmp_path: Path) -> None:
        assert _run_group(["this-binary-does-not-exist-xyz123"], tmp_path, 10) is None

    def test_kill_group_uses_proc_kill_off_posix(self) -> None:
        # Off POSIX there is no process group; fall back to killing the process itself.
        proc = MagicMock()
        proc.communicate.return_value = (b"", b"")
        with patch("codegraph_init.os.name", "nt"):
            _kill_group(proc)
        proc.kill.assert_called_once()


class TestOpTimeout:
    """The per-op timeout is clamped to the remaining whole-hook budget so reaping
    always runs before the harness can kill the wrapper mid-op (Codex finding)."""

    @patch("codegraph_init.time.monotonic", return_value=1000.0)
    def test_caps_at_op_limit_with_ample_budget(self, _mono: MagicMock) -> None:
        assert _op_timeout(2000.0, 60) == 60

    @patch("codegraph_init.time.monotonic", return_value=1000.0)
    def test_clamps_to_remaining_budget(self, _mono: MagicMock) -> None:
        assert _op_timeout(1030.0, 90) == 30

    @patch("codegraph_init.time.monotonic", return_value=1000.0)
    def test_floors_at_one_when_budget_exhausted(self, _mono: MagicMock) -> None:
        assert _op_timeout(999.0, 60) == 1


class TestGetProjectDir:
    def test_codex_workspace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CODEX_WORKSPACE", "/foo/bar")
        monkeypatch.delenv("CLAUDE_PROJECT_ROOT", raising=False)
        assert _get_project_dir() == Path("/foo/bar")

    def test_claude_project_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CODEX_WORKSPACE", raising=False)
        monkeypatch.setenv("CLAUDE_PROJECT_ROOT", "/baz/qux")
        assert _get_project_dir() == Path("/baz/qux")

    def test_codex_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CODEX_WORKSPACE", "/codex")
        monkeypatch.setenv("CLAUDE_PROJECT_ROOT", "/claude")
        assert _get_project_dir() == Path("/codex")

    def test_falls_back_to_cwd(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CODEX_WORKSPACE", raising=False)
        monkeypatch.delenv("CLAUDE_PROJECT_ROOT", raising=False)
        assert _get_project_dir() == Path.cwd()


class TestMain:
    @patch("codegraph_init.shutil.which", return_value=None)
    def test_noop_when_codegraph_missing(self, mock_which: MagicMock) -> None:
        main()

    @patch("codegraph_init._op_timeout", side_effect=lambda _deadline, cap: cap)
    @patch("codegraph_init._run_group")
    @patch("codegraph_init._is_using_wasm_sqlite", return_value=False)
    @patch("codegraph_init._has_git_commits", return_value=True)
    @patch("codegraph_init.shutil.which", return_value="/usr/bin/codegraph")
    @patch("codegraph_init._get_project_dir")
    def test_init_and_index_fresh_project(
        self,
        mock_dir: MagicMock,
        _mock_which: MagicMock,
        _mock_commits: MagicMock,
        _mock_wasm: MagicMock,
        mock_group: MagicMock,
        _mock_op_timeout: MagicMock,
        tmp_path: Path,
    ) -> None:
        (tmp_path / ".git").mkdir()
        mock_dir.return_value = tmp_path

        def group_side_effect(cmd, cwd, timeout):
            if cmd == ["codegraph", "init"]:
                (tmp_path / ".codegraph").mkdir(exist_ok=True)
                (tmp_path / ".codegraph" / "config.json").write_text("{}")
            return subprocess.CompletedProcess(cmd, 0, b"", b"")

        mock_group.side_effect = group_side_effect
        with patch("codegraph_init.Path.home", return_value=tmp_path):
            main()

        assert call(["codegraph", "init"], tmp_path, 60) in mock_group.call_args_list

    @patch("codegraph_init._op_timeout", side_effect=lambda _deadline, cap: cap)
    @patch("codegraph_init._run_group")
    @patch("codegraph_init._is_using_wasm_sqlite", return_value=False)
    @patch("codegraph_init._has_git_commits", return_value=True)
    @patch("codegraph_init.shutil.which", return_value="/usr/bin/codegraph")
    @patch("codegraph_init._get_project_dir")
    def test_sync_when_already_indexed(
        self,
        mock_dir: MagicMock,
        _mock_which: MagicMock,
        _mock_commits: MagicMock,
        _mock_wasm: MagicMock,
        mock_group: MagicMock,
        _mock_op_timeout: MagicMock,
        tmp_path: Path,
    ) -> None:
        (tmp_path / ".git").mkdir()
        cg = tmp_path / ".codegraph"
        cg.mkdir()
        (cg / "config.json").write_text(json.dumps({"enableEmbeddings": True}))
        (cg / "codegraph.db").write_bytes(b"\x00" * 2_000_000)
        mock_dir.return_value = tmp_path
        mock_group.return_value = subprocess.CompletedProcess(["codegraph", "sync", "-q"], 0, b"", b"")

        with patch("codegraph_init.Path.home", return_value=tmp_path):
            main()

        sync_call = call(["codegraph", "sync", "-q"], tmp_path, SYNC_TIMEOUT_SECONDS)
        assert sync_call in mock_group.call_args_list

    @patch("codegraph_init.subprocess.run")
    @patch("codegraph_init.shutil.which", return_value="/usr/bin/codegraph")
    @patch("codegraph_init._get_project_dir")
    def test_skips_when_same_project_sync_is_already_running(
        self,
        mock_dir: MagicMock,
        _mock_which: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        _test_lock_dir(tmp_path, project).mkdir(parents=True)
        mock_dir.return_value = project

        with patch("codegraph_init.Path.home", return_value=tmp_path):
            main()

        mock_run.assert_not_called()

    @patch("codegraph_init.subprocess.run")
    @patch("codegraph_init.shutil.which", return_value="/usr/bin/codegraph")
    @patch("codegraph_init._get_project_dir")
    def test_skips_non_git_dir(
        self, mock_dir: MagicMock, mock_which: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_dir.return_value = tmp_path
        main()
        mock_run.assert_not_called()

    @patch("codegraph_init._op_timeout", side_effect=lambda _deadline, cap: cap)
    @patch("codegraph_init._recover_corrupt_db", return_value=True)
    @patch("codegraph_init._run", return_value=True)
    @patch("codegraph_init._run_group")
    @patch("codegraph_init._is_using_wasm_sqlite", return_value=False)
    @patch("codegraph_init._has_git_commits", return_value=True)
    @patch("codegraph_init.shutil.which", return_value="/usr/bin/codegraph")
    @patch("codegraph_init._get_project_dir")
    def test_recovers_corrupt_db_on_sync(
        self,
        mock_dir: MagicMock,
        _mock_which: MagicMock,
        _mock_commits: MagicMock,
        _mock_wasm: MagicMock,
        mock_group: MagicMock,
        mock_run: MagicMock,
        mock_recover: MagicMock,
        _mock_op_timeout: MagicMock,
        tmp_path: Path,
    ) -> None:
        (tmp_path / ".git").mkdir()
        cg = tmp_path / ".codegraph"
        cg.mkdir()
        (cg / "config.json").write_text(json.dumps({"enableEmbeddings": True}))
        (cg / "codegraph.db").write_bytes(b"\x00" * 2_000_000)
        mock_dir.return_value = tmp_path
        mock_group.return_value = subprocess.CompletedProcess(
            ["codegraph", "sync", "-q"], 1, b"", b"database disk image is malformed"
        )

        with patch("codegraph_init.Path.home", return_value=tmp_path):
            main()

        mock_recover.assert_called_once_with(tmp_path)
        mock_run.assert_called_once_with(["codegraph", "init", "-i"], tmp_path, INDEX_TIMEOUT_SECONDS)
