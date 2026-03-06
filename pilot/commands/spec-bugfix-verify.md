---
description: "Bugfix verification phase - tests, quality checks, fix confirmation"
argument-hint: "<path/to/plan.md>"
user-invocable: false
model: sonnet
hooks:
  Stop:
    - command: uv run python "${CLAUDE_PLUGIN_ROOT}/hooks/spec_verify_validator.py"
---

# /spec-bugfix-verify - Bugfix Verification Phase

**Phase 3 (bugfix).** Lightweight verification: run tests, quality checks, confirm fix works.

**Input:** Bugfix plan with `Status: COMPLETE`
**Output:** Plan → VERIFIED (success) or loop back to implementation (failure)

**Why no sub-agents:** The regression test proves the fix works. The full test suite proves nothing else broke. Sub-agents would re-verify what tests already prove.

---

## Critical Constraints

- **NO review sub-agents** — tests prove correctness for bugfixes
- **NO stopping** — everything automatic. Never ask "Should I fix these?"
- **Fix ALL issues automatically** — no permission needed
- **Plan file is source of truth** — re-read after auto-compaction

---

## Step 3.1: Run Full Test Suite

Run all tests. Fix any failures immediately. Re-run until green.

## Step 3.2: Verify the Fix

1. **Read the plan's regression test** (from Task 1)
2. **Run it specifically:** `uv run pytest <test-path>::<test-name> -q`
3. Must PASS — if not, fix is incomplete, fix immediately
4. **Scope check:** Read changed files, confirm changes match plan scope. Flag unplanned changes.

## Step 3.3: Quality Checks

1. **Type checker** — zero new errors
2. **Linter** — errors are blockers, fix immediately
3. **Build** (if applicable) — must succeed

## Step 3.4: Plan Verify Commands

Run each task's `Verify:` commands. Defer server-dependent commands (containing `curl`, `localhost`, `http://`) to Step 3.5.

## Step 3.5: Runtime Verification (only if deferred commands exist)

If no server-dependent commands were deferred: skip to Final.

Otherwise: start service → run deferred commands → stop service → fix failures.

---

## Final

### Step 3.6: Worktree Sync (if worktree active)

1. Detect: `~/.pilot/bin/pilot worktree detect --json <plan_slug>`
2. If no worktree: skip to Step 3.8.
3. Pre-sync: verify clean working tree on base branch
4. Save plan to project root: `cp <worktree_plan> <project_root>/docs/plans/`
5. Show diff: `~/.pilot/bin/pilot worktree diff --json <plan_slug>`
6. Notify + AskUserQuestion: "Yes, squash merge" | "No, keep" | "Discard"
7. Handle:
   - **Squash:** `worktree sync` then `cleanup --force` + `cd` in SAME bash call
   - **Keep:** Report path
   - **Discard:** `cleanup --force` + `cd` in SAME bash call

   NEVER separate cleanup and cd into different Bash calls.

### Step 3.7: Post-Merge Verification (after squash merge only)

Full test suite + type checker + build. If any fails: fix on base branch, re-run.

### Step 3.8: Update Plan Status

**All passes:** Set `Status: VERIFIED`, register, report:
```
Bugfix verified — regression test passes, full suite green.
```

**Fails:** Add fix tasks, set `Status: PENDING`, increment `Iterations`, invoke `Skill(skill='spec-implement', args='<plan-path>')`.

ARGUMENTS: $ARGUMENTS
