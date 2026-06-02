"""Tests for installer UI abstraction layer."""

from __future__ import annotations


class TestConsole:
    """Test Console wrapper class."""

    def test_console_status_outputs_blue_text(self):
        """Console.status should output styled message."""
        from installer.ui import Console

        console = Console()
        # Should not raise
        console.status("Installing...")

    def test_console_success_outputs_green_checkmark(self):
        """Console.success should output green checkmark message."""
        from installer.ui import Console

        console = Console()
        console.success("Installed successfully")

    def test_console_warning_outputs_yellow_warning(self):
        """Console.warning should output yellow warning message."""
        from installer.ui import Console

        console = Console()
        console.warning("This might cause issues")

    def test_console_error_outputs_red_error(self):
        """Console.error should output red error message."""
        from installer.ui import Console

        console = Console()
        console.error("Installation failed")

    def test_console_progress_context_manager(self):
        """Console.progress should return a context manager."""
        from installer.ui import Console

        console = Console()
        with console.progress(total=10, description="Downloading") as progress:
            progress.advance(5)
            progress.advance(5)


class TestConsoleNonInteractive:
    """Test Console in non-interactive mode."""

    def test_input_returns_default_in_non_interactive(self):
        """In non-interactive mode, input returns default."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        result = console.input("Enter value:", default="default_value")
        assert result == "default_value"


class TestConsoleInteractiveInput:
    """Console.input() reading from the controlling terminal (non-TTY stdin)."""

    def test_input_submits_when_enter_is_bare_carriage_return(self, monkeypatch):
        """Enter delivered as a lone CR (no LF) must submit the line.

        Regression (6283848b): the readline()-based prompt held a trailing CR
        pending (universal-newline CR/CRLF disambiguation), so under the VSCode/
        debugpy launcher Enter ('\\r') never returned -- the user saw '^M' and
        input hung. Keeping the write end open simulates a real terminal that
        does not send EOF; the read must still complete on the bare CR.
        """
        import os
        import sys
        import threading

        from installer.ui import Console

        class _FakeStdin:
            def isatty(self) -> bool:
                return False

        monkeypatch.setattr(sys, "stdin", _FakeStdin())

        read_fd, write_fd = os.pipe()
        os.write(write_fd, b"LICENSE-KEY-XYZ\r")

        console = Console()
        monkeypatch.setattr(console, "_get_input_stream", lambda: os.fdopen(read_fd, "r"))

        result: dict[str, str] = {}

        def _read() -> None:
            result["value"] = console.input("Enter your license key")

        worker = threading.Thread(target=_read, daemon=True)
        worker.start()
        worker.join(timeout=5.0)

        try:
            assert not worker.is_alive(), "input() hung waiting for a newline after a bare CR"
            assert result["value"] == "LICENSE-KEY-XYZ"
        finally:
            os.close(write_fd)  # unblock any hung reader so the daemon thread can exit
