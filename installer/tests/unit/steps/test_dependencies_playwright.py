"""Tests for playwright-cli installation functions in dependencies step."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestIsPlaywrightCliReady:
    """Test _is_playwright_cli_ready function."""

    @patch("installer.steps.dependencies._get_playwright_cache_dirs")
    @patch("installer.steps.dependencies.command_exists")
    def test_returns_false_when_command_not_found(self, mock_cmd, _mock_dirs):
        """Returns False when playwright-cli is not installed."""
        from installer.steps.dependencies import _is_playwright_cli_ready

        mock_cmd.return_value = False
        assert _is_playwright_cli_ready() is False
        mock_cmd.assert_called_once_with("playwright-cli")

    @patch("installer.steps.dependencies._get_playwright_cache_dirs")
    @patch("installer.steps.dependencies.command_exists")
    def test_returns_false_when_no_chromium_cache(self, mock_cmd, mock_dirs, tmp_path):
        """Returns False when command exists but no Chromium cache."""
        from installer.steps.dependencies import _is_playwright_cli_ready

        mock_cmd.return_value = True
        empty_cache = tmp_path / "ms-playwright"
        empty_cache.mkdir()
        mock_dirs.return_value = [empty_cache]
        assert _is_playwright_cli_ready() is False

    @patch("installer.steps.dependencies._get_playwright_cache_dirs")
    @patch("installer.steps.dependencies.command_exists")
    def test_returns_true_with_chromium_installed(self, mock_cmd, mock_dirs, tmp_path):
        """Returns True when command exists and Chromium is installed."""
        from installer.steps.dependencies import _is_playwright_cli_ready

        mock_cmd.return_value = True
        cache_dir = tmp_path / "ms-playwright"
        chromium_dir = cache_dir / "chromium-1234"
        chromium_dir.mkdir(parents=True)
        (chromium_dir / "INSTALLATION_COMPLETE").touch()
        mock_dirs.return_value = [cache_dir]
        assert _is_playwright_cli_ready() is True

    @patch("installer.steps.dependencies._get_playwright_cache_dirs")
    @patch("installer.steps.dependencies.command_exists")
    def test_returns_true_with_headless_shell_installed(self, mock_cmd, mock_dirs, tmp_path):
        """Returns True when chromium_headless_shell variant is installed."""
        from installer.steps.dependencies import _is_playwright_cli_ready

        mock_cmd.return_value = True
        cache_dir = tmp_path / "ms-playwright"
        chromium_dir = cache_dir / "chromium_headless_shell-1234"
        chromium_dir.mkdir(parents=True)
        (chromium_dir / "INSTALLATION_COMPLETE").touch()
        mock_dirs.return_value = [cache_dir]
        assert _is_playwright_cli_ready() is True

    @patch("installer.steps.dependencies._get_playwright_cache_dirs")
    @patch("installer.steps.dependencies.command_exists")
    def test_returns_false_when_cache_dirs_dont_exist(self, mock_cmd, mock_dirs, tmp_path):
        """Returns False when cache directories don't exist."""
        from installer.steps.dependencies import _is_playwright_cli_ready

        mock_cmd.return_value = True
        mock_dirs.return_value = [tmp_path / "nonexistent"]
        assert _is_playwright_cli_ready() is False


class TestInstallPlaywrightSystemDeps:
    """Test _install_playwright_system_deps function."""

    @patch("installer.steps.dependencies.subprocess")
    def test_runs_install_deps_command(self, mock_subprocess):
        """Runs npx playwright install-deps."""
        from installer.steps.dependencies import _install_playwright_system_deps

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.run.return_value = mock_result
        assert _install_playwright_system_deps() is True
        mock_subprocess.run.assert_called_once_with(
            ["npx", "-y", "playwright", "install-deps"],
            capture_output=True,
            text=True,
            timeout=300,
        )

    @patch("installer.steps.dependencies.time.sleep")
    @patch("installer.steps.dependencies.subprocess")
    def test_returns_false_on_failure(self, mock_subprocess, _mock_sleep):
        """Returns False when install-deps fails."""
        from installer.steps.dependencies import _install_playwright_system_deps

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.run.return_value = mock_result
        assert _install_playwright_system_deps() is False

    @patch("installer.steps.dependencies.time.sleep")
    @patch("installer.steps.dependencies.subprocess")
    def test_returns_false_on_exception(self, mock_subprocess, _mock_sleep):
        """Returns False when subprocess raises exception."""
        from installer.steps.dependencies import _install_playwright_system_deps

        mock_subprocess.run.side_effect = OSError("command not found")
        assert _install_playwright_system_deps() is False

class TestInstallPlaywrightCli:
    """Test install_playwright_cli function."""

    @patch("installer.steps.dependencies._is_playwright_cli_ready")
    def test_skips_install_when_already_ready(self, mock_ready):
        """Skips installation when playwright-cli is already ready."""
        from installer.steps.dependencies import install_playwright_cli

        mock_ready.return_value = True
        assert install_playwright_cli() is True

    @patch("installer.steps.dependencies._install_playwright_system_deps")
    @patch("installer.steps.dependencies._is_playwright_cli_ready")
    @patch("installer.steps.dependencies._run_bash_with_retry")
    def test_installs_npm_package_and_system_deps(self, mock_run, mock_ready, mock_deps):
        """Installs @playwright/cli@latest via npm then runs install-deps."""
        from installer.steps.dependencies import install_playwright_cli

        mock_ready.side_effect = [False, True]
        mock_run.return_value = True
        mock_deps.return_value = True
        assert install_playwright_cli() is True
        mock_run.assert_called_once_with("npm install -g @playwright/cli@latest")
        mock_deps.assert_called_once()

    @patch("installer.steps.dependencies._is_playwright_cli_ready")
    @patch("installer.steps.dependencies._run_bash_with_retry")
    def test_returns_false_when_npm_fails(self, mock_run, mock_ready):
        """Returns False when npm install fails."""
        from installer.steps.dependencies import install_playwright_cli

        mock_ready.return_value = False
        mock_run.return_value = False
        assert install_playwright_cli() is False

    @patch("installer.steps.dependencies._install_playwright_system_deps")
    @patch("installer.steps.dependencies.subprocess")
    @patch("installer.steps.dependencies._is_playwright_cli_ready")
    @patch("installer.steps.dependencies._run_bash_with_retry")
    def test_installs_browser_and_deps_when_not_ready(self, mock_run, mock_ready, mock_subprocess, mock_deps):
        """Runs playwright-cli install then install-deps when Chromium not cached."""
        from installer.steps.dependencies import install_playwright_cli

        mock_ready.side_effect = [False, False]
        mock_run.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.run.return_value = mock_result
        mock_deps.return_value = True
        assert install_playwright_cli() is True
        mock_subprocess.run.assert_called_once_with(
            ["playwright-cli", "install"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        mock_deps.assert_called_once()

    @patch("installer.steps.dependencies.time.sleep")
    @patch("installer.steps.dependencies._install_playwright_system_deps")
    @patch("installer.steps.dependencies.subprocess")
    @patch("installer.steps.dependencies._is_playwright_cli_ready")
    @patch("installer.steps.dependencies._run_bash_with_retry")
    def test_returns_false_when_browser_install_fails(
        self, mock_run, mock_ready, mock_subprocess, mock_deps, _mock_sleep
    ):
        """Returns False when playwright-cli install fails."""
        from installer.steps.dependencies import install_playwright_cli

        mock_ready.side_effect = [False, False]
        mock_run.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.run.return_value = mock_result
        assert install_playwright_cli() is False
        mock_deps.assert_not_called()
