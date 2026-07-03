## Phase A — Finalize the Code

## Step 1: Early Background Review Launch

### 1a: Clean Up Stale Review Findings (always run, before any launch)

**Always run this first** — regardless of whether changes-review is enabled. Spec-review findings are stale artifacts from the planning phase that were already addressed during implementation; changes-review findings files are the previous run's output (agent mode writes a fresh one below — a stale file left behind would be read as if it reviewed THIS iteration's diff). The cleanup runs strictly BEFORE any launch in this step:

```bash
SESS_DIR="$HOME/.pilot/sessions/${PILOT_SESSION_ID:-default}"
FIND_BIN="/usr/bin/find"
[ -x "$FIND_BIN" ] || FIND_BIN="$(command -v find)"
test -d "$SESS_DIR" && "$FIND_BIN" "$SESS_DIR" -maxdepth 1 -name 'findings-spec-review-*.json' -delete
test -d "$SESS_DIR" && "$FIND_BIN" "$SESS_DIR" -maxdepth 1 -name 'findings-changes-review-*.json' -delete
```

Use the absolute `FIND_BIN` form above. In Pilot Shell sessions the shell hook may rewrite plain `find` to RTK, and RTK rejects the `-delete` predicate shape this cleanup needs.

### 1b: Stage the change's files (always run, before ANY reviewer launches)

The implementation phase does not commit, so the work sits in the WORKING TREE — modified files plus brand-new untracked ones (new modules, pages, tests). A review of that unstaged tree misfires both ways: a reviewer that reads `git status --untracked-files=all` reports a spurious `critical` ("deliverable depends on untracked files"), while a reviewer that reads only `git diff HEAD` silently OMITS the new files, so they go unreviewed. Fix both at once by staging the change's own files with a **real `git add`** before any reviewer launches below:

```bash
# Stage ONLY the plan's files (the paths from each task's `Files:` block) plus any
# documented deviations — NOT unrelated dirty or untracked files.
git add <path/from/plan/Files-block-1> <path/from/plan/Files-block-2> ...
# Sanity check: anything still untracked must NOT be part of this change.
git status --short --untracked-files=all | grep '^??' || true
```

A bare `git add -N` (intent-to-add) is NOT enough — `git status` still treats the path as untracked and a later `git commit` can record empty content. Use a real `git add`. **Staging is not committing** — the commit still waits for the review, doc-sync, and (Phase B) the worktree sync; `git add` is pre-authorized, the push is not. All reviewers below scope to `git diff HEAD` (which now includes the staged additions); never narrow to a committed ref-range, which is empty pre-commit.

**Reviewable file preflight:** the `Files:` block must contain at least one non-ignored repository artifact for implementation plans. `docs/plans/...` is workflow state and may be gitignored in Pilot Shell itself, so it cannot be the sole review target. Do NOT use `git add -f` to force ignored plan files into review. If every planned file is ignored, outside the repo, or only the plan file itself, set `Status: PENDING`, add a fix task for a reviewable non-production artifact (for smoke/no-production specs), and return to implementation before launching any reviewer.

---

<!-- CC-ONLY -->
**Resolve the changes-review mode** (fail-closed to `agent` — never pass the raw env var through):

```bash
SPEC_MODE="${PILOT_SPEC_CODE_REVIEW_MODE:-agent}"
case "$SPEC_MODE" in medium|high|xhigh) ;; *) SPEC_MODE=agent ;; esac
echo "$SPEC_MODE"
```

#### Agent mode (`SPEC_MODE=agent`) — launch the changes-review sub-agent NOW, in the background

**Only when `PILOT_CHANGES_REVIEW_ENABLED` is not `"false"`.** The single `changes-review` sub-agent is the low-token review mechanism; it works in the background while you run the Step 2 automated checks, and Step 3 collects its findings file.

**Derive plan slug** from the plan filename (strip `YYYY-MM-DD-` prefix and `.md`). Output path: `$SESS_DIR/findings-changes-review-<plan-slug>.json` (the 1a cleanup already removed any stale file).

```
Task(
  subagent_type="changes-review",
  run_in_background=true,
  prompt="""
  **Plan file:** <plan-path>
  **Changed files:** <paths from the plan's Files: blocks + documented deviations>
  **Runtime environment:** <plan's Runtime Environment section, if present>
  **Output path:** <absolute findings path above>

  Review the diff (git diff HEAD -- <changed files>) against the plan: compliance, quality, goal achievement.
  Write findings JSON to output_path using the Write tool.
  IMPORTANT: Include the plan file path in your output JSON as the "plan_file" field.
  """
)
```

**⛔ NEVER use `TaskOutput`** to retrieve results — Step 3 polls the findings file.

#### Skill mode (`SPEC_MODE` = `medium`/`high`/`xhigh`) — no reviewer launch here

The code review runs INLINE in Step 3 via the built-in `/code-review` skill at effort `$SPEC_MODE` — there is no subagent to launch early and no findings file to derive. The only launch in this step is the optional Codex companion below.

#### Codex Adversarial Review (Optional — launch NOW, in the background)

**If `PILOT_CODEX_CHANGES_REVIEW_ENABLED` is `"true"` (from Step 0):**

Launch Codex review NOW — it works in the background while you run the Step 2 automated checks and the Step 3 inline review.

**Derive plan slug** from the plan filename: strip the date prefix (`YYYY-MM-DD-`) and `.md` extension. Example: `2026-03-02-sku-builder-modal-cleanup.md` → `sku-builder-modal-cleanup`.

**Codex-once rule.** Codex runs at most once per `/spec` invocation. Before launching, check the sentinel file. If it exists, the review already ran in this session — skip the launch and the collection sub-step in Step 3. Verify-phase iterations (re-verify after fixing findings, code-review-gate annotation fixes) do NOT trigger another Codex run.

```bash
SESS_ID="${PILOT_SESSION_ID:-default}"
CODEX_FLAG="$HOME/.pilot/sessions/$SESS_ID/codex-changes-review-ran-<plan-slug>.flag"
if [ -f "$CODEX_FLAG" ]; then
  echo "Codex already reviewed this plan in this session — skipping (codex-once)."
  # Skip the launch below and the Codex collection sub-step in Step 3.
fi
```

1. Detect companion path and ensure project root:
```bash
CODEX_COMPANION=$(ls ~/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs 2>/dev/null | sort -V | tail -1)
PROJECT_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
```

2. Build the review prompt file by rendering the **template at `$HOME/.claude/agents/changes-review-codex.md`**. The template is the single source of truth for code-review semantics — do NOT re-state the prompt inline in this skill. Substitute four placeholders:
   - `{{PLAN_PATH}}` — absolute path to the plan file
   - `{{PLAN_GOAL}}` — the 1–2 sentence Goal sentence from the plan's `## Summary`
   - `{{BASE_REF}}` — `main` (or the worktree base branch detected via `pilot worktree status --json`)
   - `{{CHANGED_FILES}}` — newline-separated paths to the files the plan said it would touch (extracted from each task's `Files:` block)

```bash
PROMPT_TEMPLATE="$HOME/.claude/agents/changes-review-codex.md"
PROMPT_FILE="/tmp/codex-changes-review-${PILOT_SESSION_ID:-default}-<plan-slug>.md"

PLAN_PATH="/absolute/path/to/docs/plans/YYYY-MM-DD-<slug>.md"
PLAN_GOAL="<one or two sentences from the plan Summary>"
BASE_REF="main"
CHANGED_FILES=$(printf -- '- %s\n' \
  path/to/changed/file-1 \
  path/to/changed/file-2)

PLAN_PATH="$PLAN_PATH" PLAN_GOAL="$PLAN_GOAL" BASE_REF="$BASE_REF" CHANGED_FILES="$CHANGED_FILES" \
PROMPT_TEMPLATE="$PROMPT_TEMPLATE" PROMPT_FILE="$PROMPT_FILE" \
uv run --no-project --python python3 python -c '
import os, pathlib
text = pathlib.Path(os.environ["PROMPT_TEMPLATE"]).read_text()
for key in ("PLAN_PATH", "PLAN_GOAL", "BASE_REF", "CHANGED_FILES"):
    text = text.replace("{{" + key + "}}", os.environ[key])
pathlib.Path(os.environ["PROMPT_FILE"]).write_text(text)
'
```

3. Launch the task in background. **For `task`, the companion's `--background` flag IS supported** (unlike `review`/`adversarial-review`). Use the companion's own background mode — the launch command returns the job ID immediately on stdout. Capture the job ID for collection in Step 3.

   ⛔ **Launch the companion via Bash from the MAIN conversation — NEVER through a subagent** (`codex:codex-rescue` included): a subagent-launched job's ID is unreachable afterwards (no findings file, no `TaskOutput`, no `SendMessage`).

   ```
   Bash(
     command="cd $PROJECT_ROOT && node $CODEX_COMPANION task --background --prompt-file \"$PROMPT_FILE\"",
     run_in_background=false,
     timeout=60000
   )
   ```

   The stdout looks like: `Codex Task started in the background as task-<id>. Check /codex:status task-<id> for progress.` Extract the `task-…` token and store as `JOB_ID`.

   **Verify registration before letting Step 3 poll** — fail-fast guard against synthetic-ID launches:

   ```bash
   node "$CODEX_COMPANION" status "$JOB_ID" --json 2>/dev/null | grep -q '"status":' \
     || { echo "Codex launch did not register with broker — JOB_ID is synthetic. Skipping Codex this run."; JOB_ID=""; }
   ```

   If `$JOB_ID` is empty after this check, skip Step 3's Codex collection and rely on the Step 3 changes review alone (agent findings or inline `/code-review`, per the resolved mode). If Changes Review is disabled too, no automated review runs this iteration — record that gap explicitly in the verification report.

**Do NOT wait** — proceed to Step 2 immediately. You'll be notified when the polling bash (Step 3) completes.
<!-- /CC-ONLY -->
<!-- CODEX-START
**If `PILOT_CHANGES_REVIEW_ENABLED` is `"false"` (from Step 0),** skip the rest of this step and proceed directly to Step 2 (Automated Checks).

**When enabled:** launch the managed Codex custom agent immediately. It runs while automated checks execute in Step 2.

Gather context first:

```bash
git status --short
```

Collect: changed files list, runtime environment info, test framework constraints, and plan risks section. Derive the plan slug from the plan filename by stripping the date prefix and `.md`.

Persist the returned agent id so Step 3 can survive long checks or compaction. Use a deterministic session file:

```bash
SESS_DIR="$HOME/.pilot/sessions/${PILOT_SESSION_ID:-default}"
AGENT_ID_FILE="$SESS_DIR/changes-review-agent-id-<plan-slug>.txt"
mkdir -p "$SESS_DIR"
```

```python
review = multi_agent_v1.spawn_agent(
    agent_type="changes-review",
    message="""
    Plan file: <plan-path>
    User request: <original task description that invoked $spec>
    Changed files: [file list]
    Runtime environment: [how to start, port, deploy path]
    Test framework constraints: [what it can/cannot test]

    Review implementation: compliance, quality, and goal achievement.
    Return ONLY valid JSON matching the changes-review schema.
    Include the plan file path in the `plan_file` field.
    """,
)
CHANGES_REVIEW_AGENT_ID = review.agent_id
```

After spawning, write `CHANGES_REVIEW_AGENT_ID` to `$AGENT_ID_FILE`.

Do NOT wait here. Proceed directly to Step 2.

Self-review the implementation diff before proceeding: `git diff --stat` to verify scope matches the plan, and spot-check changed files for obvious issues (security, missing error handling, dead code).
CODEX-END -->
