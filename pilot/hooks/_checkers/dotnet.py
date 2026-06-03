"""Dotnet file checker — single-file dotnet format check (no per-edit build)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from _lib.util import BLUE, NC, check_file_length

DOTNET_EXTENSIONS = {".cs", ".razor"}
DEBUG = os.environ.get("HOOK_DEBUG", "").lower() == "true"


def debug_log(message: str) -> None:
    """Print debug message if enabled."""
    if DEBUG:
        print(f"{BLUE}[DEBUG]{NC} {message}", file=sys.stderr)


def find_project_root(file_path: Path) -> Path | None:
    """Find nearest directory with a .csproj or .sln file."""
    current = file_path.parent
    depth = 0
    while current != current.parent:
        if list(current.glob("*.csproj")) or list(current.glob("*.sln")):
            return current
        current = current.parent
        depth += 1
        if depth > 20:
            break
    return None


def check_dotnet(file_path: Path) -> tuple[int, str]:
    """Check .NET file with a single-file `dotnet format`. Returns (0, reason)."""
    stem = file_path.stem
    if stem.endswith("Tests") or stem.endswith("Test"):
        return 0, ""
    # Skip files inside a .NET test project (dir convention: MyApp.Tests / MyApp.Test).
    # A path-segment match avoids over-skipping siblings like MyApp.TestData.
    if any(part.endswith((".Tests", ".Test")) for part in file_path.parts):
        return 0, ""

    length_warning = check_file_length(file_path)

    project_root = find_project_root(file_path)
    if not project_root:
        return 0, length_warning

    dotnet_bin = shutil.which("dotnet")
    if not dotnet_bin:
        return 0, length_warning

    has_issues, results = _run_dotnet_format(dotnet_bin, project_root, file_path)

    if has_issues:
        parts = []
        for tool_name, (count, _) in results.items():
            label = "issue" if count == 1 else "issues"
            parts.append(f"{count} {tool_name} {label}")
        reason = f"Dotnet: {', '.join(parts)} in {file_path.name}"
        details = _format_dotnet_issues(file_path, results)
        if details:
            reason = f"{reason}\n{details}"
        if length_warning:
            reason = f"{reason}\n{length_warning}"
        return 0, reason

    return 0, length_warning


def _run_dotnet_format(
    dotnet_bin: str,
    project_root: Path,
    file_path: Path,
) -> tuple[bool, dict[str, tuple]]:
    """Run `dotnet format whitespace --folder` scoped to the edited file and collect results."""
    has_issues = False
    results: dict[str, tuple] = {}
    try:
        # `whitespace --folder` skips the MSBuild project load, restore, and analyzer
        # compilation (the dominant per-edit cost) while still applying .editorconfig
        # whitespace rules. Style/analyzer feedback is deferred to the LSP and
        # `dotnet build` / `dotnet test`.
        cmd = [
            dotnet_bin, "format", "whitespace",
            str(project_root), "--folder",
            "--verify-no-changes", "--verbosity", "q",
        ]

        try:
            include_path = file_path.relative_to(project_root)
        except ValueError:
            include_path = file_path
        cmd.extend(["--include", str(include_path)])

        debug_log(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=project_root,
            timeout=60,
        )
        debug_log(f"Format exit code: {result.returncode}")

        if result.returncode != 0:
            output = result.stdout + result.stderr
            # Collect filenames that need formatting
            format_lines = [
                line.strip()
                for line in output.splitlines()
                if line.strip() and not line.strip().startswith("The dotnet format command")
            ]
            if format_lines:
                has_issues = True
                results["format"] = (len(format_lines), format_lines)
            else:
                # Non-zero exit but no specific lines — still report
                has_issues = True
                results["format"] = (1, ["Code formatting issues detected"])
    except subprocess.TimeoutExpired:
        debug_log("Format check timed out")
    except (OSError, subprocess.SubprocessError) as exc:
        debug_log(f"Format check failed to run: {exc}")
    return has_issues, results


def _format_dotnet_issues(file_path: Path, results: dict[str, tuple]) -> str:
    """Format .NET diagnostic issues as plain text."""
    lines: list[str] = []
    try:
        display_path = file_path.relative_to(Path.cwd())
    except ValueError:
        display_path = file_path
    lines.append(f".NET Issues found in: {display_path}")

    if "format" in results:
        count, format_lines = results["format"]
        plural = "issue" if count == 1 else "issues"
        lines.append(f"Format: {count} whitespace {plural} (run `dotnet format`)")
        for line in format_lines[:10]:
            lines.append(f"  {line}")
        if count > 10:
            lines.append(f"  ... and {count - 10} more")

    lines.append("Fix .NET issues above before continuing")
    return "\n".join(lines)
