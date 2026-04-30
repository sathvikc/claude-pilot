## Step 8: Implementation Planning

### 8.0: File Structure (when 4+ tasks expected, otherwise inline per task)

When the plan will have 4+ tasks, write a `## File Structure` section before tasks listing every file with one-line responsibility — decomposition decisions get locked in here. For 1–3 task plans skip this; the per-task `Files:` block already gives the same view.

```markdown
## File Structure

- `src/foo/bar.ts` (create) — pure function: `parseFoo(input) → Foo`. No I/O.
- `src/foo/loader.ts` (create) — fetches and caches Foo from API. Wraps `parseFoo`.
- `tests/foo/bar.test.ts` (create) — unit tests for `parseFoo`.
```

One responsibility per file. Files that change together live together. In existing codebases, follow established patterns — don't restructure unrelated code.

### 8.1: Task Granularity

**Task Granularity:** Each task: independently testable, focused (2-4 files max), verifiable. Split if multiple unrelated DoD criteria; merge if one can't be tested without the other. Don't create tasks for setup/boilerplate with no standalone value — fold into the first task that uses them.

**Task Structure:**

```markdown
### Task N: [Component Name]

**Objective:** [1-2 sentences]
**Dependencies:** [None | Task X, Task Y]
**Mapped Scenarios:** [None | TS-001, TS-002]

**Files:**

- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py`
- Test: `tests/exact/path/to/test.py`

**Key Decisions / Notes:**

- [Technical approach, pattern to follow with file:line ref]

**Definition of Done:**

- [ ] All tests pass
- [ ] No diagnostics errors
- [ ] [Verifiable criterion — e.g., "API returns 404 for nonexistent resources"]

**Verify:**

- `uv run pytest tests/path/to/test.py -q`
```

**DoD must be verifiable.** ✅ "GET /api/users?role=admin returns only admin users" ❌ "Feature works correctly"

**Performance considerations:** When a task processes data on a hot path (render loops, request handlers, polling callbacks), note it in Key Decisions. Flag: expensive computations that should be cached/memoized, heavy dependencies that have lighter alternatives, and repeated work that can be avoided when input hasn't changed.

**Zero-context assumption:** Assume implementer knows nothing. Provide exact file paths, explain domain concepts, reference similar patterns.

**Assumptions:** After creating tasks, write the `## Assumptions` section — one bullet per assumption: what you assume, which finding supports it, which task numbers depend on it. When implementation hits a surprise, this list tells the implementer which tasks are affected.

#### Step 8.2: Goal Verification Criteria

After creating tasks, derive for the `## Goal Verification` section:

1. State the goal
2. Derive 3-7 observable truths (falsifiable, user-perspective)
3. For each truth, identify supporting artifacts (files with real implementation, not stubs)
