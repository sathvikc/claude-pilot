"""Worktree-mode review diffs must resolve against the FORK POINT, and the
documented ``base_branch`` source must be a command that actually returns it.

Three failure modes, one root defect - the review diff is resolved against the
wrong ref, and the reviewer scores the corrupted result at face value (#168):

1. ``git diff <base_branch>..HEAD`` (two dots) diffs against the base branch's
   LIVE TIP, not the point the worktree forked from. Once the base branch takes
   any commit after the fork - a sibling merge, an unrelated push, a parallel
   worktree landing - every one of those base-branch commits is rendered into
   the review diff INVERTED: a line the base branch added shows up as a line
   the branch under review deleted. The reviewer then scores that corrupted
   diff at face value and (verified in the issue) passes it. The three-dot form
   ``git diff <base_branch>...HEAD`` diffs from the merge base and shows only
   the branch's own work - it is what ``launcher/worktree.py``'s own
   ``list_worktree_changes`` already uses.

   ``HEAD...HEAD`` (the non-worktree substitution) is still an empty diff, so
   the templates' "if empty, fall back to ``git diff HEAD``" path is unaffected.

2. ``pilot worktree status`` takes no positional slug - argparse hard-errors on
   one, so an agent following the old instruction literally cannot resolve the
   base ref from the cited command. It is also session-scoped rather than
   slug-scoped: it reports the worktree registered for the current session (or
   ``{"active": false}``), not the one for the plan being verified.
   ``pilot worktree detect --json <slug>`` is the slug-scoped subcommand.

3. A reviewer contract that hardcodes a branch name instead of using the
   ``base_ref`` the orchestrator resolved is the same defect one level up: a
   worktree forked from ``dev`` but reviewed against ``main`` pulls in every
   commit ``dev`` carries beyond ``main``. Pilot Shell develops on ``dev``, so
   this is the normal case here rather than an edge case.
"""

from __future__ import annotations

import re
from pathlib import Path

PILOT_DIR = Path(__file__).resolve().parents[3] / "pilot"

# `..HEAD` not preceded by a third dot - i.e. a two-dot range against a ref's
# live tip. `...HEAD` (fork point) is the correct form and does not match.
_TIP_RANGE = re.compile(r"(?<!\.)\.\.HEAD")

# `worktree status` cited as the source of `base_branch` - it returns neither.
_STATUS_FOR_BASE_BRANCH = (re.compile(r"worktree status"), re.compile(r"base_branch"))

# `status --json <slug>` - `worktree status` accepts no positional slug.
_STATUS_WITH_SLUG = re.compile(r"status\s+--json\s+<slug>")

# The left side of a `...HEAD` range in a reviewer contract. A placeholder
# (`<base_ref>`, `{{BASE_REF}}`) is correct; a bare literal branch name is not.
_FORK_RANGE_LHS = re.compile(r"(\S+)\.\.\.HEAD")


def _scan(predicate, root: Path = PILOT_DIR) -> list[str]:
    offenders: list[str] = []
    for md in sorted(root.rglob("*.md")):
        for lineno, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if predicate(line):
                offenders.append(f"{md.relative_to(PILOT_DIR)}:{lineno}: {line.strip()[:160]}")
    return offenders


def test_review_diffs_use_fork_point_not_base_branch_tip() -> None:
    offenders = _scan(lambda line: bool(_TIP_RANGE.search(line)))
    assert not offenders, (
        "Review diffs must use the three-dot fork-point range "
        "`git diff <base_ref>...HEAD`, never the two-dot `<base_ref>..HEAD`, "
        "which diffs against the base branch's live tip and renders any "
        "post-fork base-branch commit into the review diff inverted - a "
        "base-branch addition appears as a deletion the branch never made "
        "(issue #168). Offenders:\n" + "\n".join(offenders)
    )


def test_base_branch_is_resolved_via_worktree_detect() -> None:
    name_rx, field_rx = _STATUS_FOR_BASE_BRANCH
    offenders = _scan(
        lambda line: (
            (bool(name_rx.search(line)) and bool(field_rx.search(line))) or bool(_STATUS_WITH_SLUG.search(line))
        )
    )
    assert not offenders, (
        "`pilot worktree status` takes no positional slug and returns no "
        "`base_branch` - `pilot worktree detect --json <slug>` is the "
        "subcommand that does. Cite `detect` wherever the base branch is "
        "resolved (issue #168). Offenders:\n" + "\n".join(offenders)
    )


def test_skills_invoke_review_scope_through_the_json_parse_guard() -> None:
    """`pilot review-scope` in a skill must go through `--json` so it fails CLOSED.

    A `pilot` binary predating this subcommand does not error on it - it prints
    the "Pilot Shell now runs directly inside Claude Code" transition banner and
    exits 0. So the obvious-looking guard

        DIFF=$(pilot review-scope --slug x 2>/dev/null || echo HEAD)

    never fires its fallback, and `DIFF` silently becomes the banner text, which
    then gets spliced into `git diff $DIFF`. Piping `--json` through a
    `json.load` parse fails on the banner, so the fallback actually runs.

    Verified live against the installed older binary: the plain form captured
    the full banner; the `--json` + parse form correctly yielded `HEAD`.
    """
    # `bin/pilot review-scope` is the invocation form skills use; a bare
    # `pilot review-scope` in backticked prose is a reference, not a call.
    offenders = [
        o
        for o in _scan(lambda line: "bin/pilot review-scope" in line and "--json" not in line)
        if o.startswith("skills/")
    ]
    assert not offenders, (
        "Skills must invoke `pilot review-scope` with `--json` and parse the "
        "result, so an older `pilot` binary (which prints a banner and exits 0) "
        "falls back instead of splicing banner text into `git diff`. Offenders:\n" + "\n".join(offenders)
    )


def _hardcoded_base_branch(line: str) -> bool:
    """A reviewer contract diffing against a literal branch instead of `base_ref`."""
    return any("<" not in lhs and "{" not in lhs for lhs in _FORK_RANGE_LHS.findall(line))


def test_reviewer_contracts_take_the_base_ref_from_the_orchestrator() -> None:
    """Reviewer prompt templates must diff against the SUPPLIED base ref.

    A hardcoded branch name is the same defect as a two-dot range, one level up:
    a worktree forked from ``dev`` but reviewed against ``main`` pulls in every
    commit ``dev`` carries beyond ``main``, so the reviewer scores a corrupted
    superset of the change. Pilot Shell itself develops on ``dev``, so this is
    the normal case here, not an edge case.

    Scoped to ``pilot/agents/`` - these are the contracts that actually run the
    diff. Skills and rules legitimately mention ``main...HEAD`` in prose that
    tells the agent NOT to use a ref-range.
    """
    offenders = _scan(_hardcoded_base_branch, root=PILOT_DIR / "agents")
    assert not offenders, (
        "Reviewer contracts must diff against the `base_ref` the orchestrator "
        "supplies (a `<placeholder>`), never a hardcoded branch name - a "
        "worktree forked from a non-`main` base would otherwise be reviewed "
        "against the wrong ref (issue #168). Offenders:\n" + "\n".join(offenders)
    )
