## Step 2: One-Shot Recipes (`codex exec`)

`-s`/`--sandbox`: `read-only` (default) | `workspace-write` (edits the tree) | `danger-full-access`.
Final message goes to stdout and to `-o <file>`; streaming logs go to stderr; `--json` = JSONL events.
Model flags: `-m gpt-5.5 -c model_reasoning_effort="xhigh"` are the verified defaults — drop both to inherit the user's own Codex config.

**(a) Read-only second opinion / analysis:**

```bash
"$CODEX_BIN" exec -C <abs-repo> -m gpt-5.5 -c model_reasoning_effort="xhigh" -s read-only \
  -o <abs-out>.txt "<question>" </dev/null
```

**(b) Bounded code-writing task (edits the working tree):**

```bash
"$CODEX_BIN" exec -C <abs-repo> -m gpt-5.5 -c model_reasoning_effort="xhigh" -s workspace-write \
  -o <abs-out>.txt "<imperative task>" </dev/null
```

**(c) Follow-up that keeps Codex's session context** (the run header prints `session id:`):

```bash
cd <abs-repo> && "$CODEX_BIN" exec resume --last -o <abs-out>.txt "<next step>" </dev/null
# or target a specific session: "$CODEX_BIN" exec resume <SESSION_ID> -o <abs-out>.txt "<next step>" </dev/null
```

`resume` accepts `-m`/`-o`/`--json` but NOT `-s`/`--sandbox` or `-C`. Sandbox is inherited from the resumed session; workdir is the CURRENT cwd (not the original session's dir), so `cd` into the target repo first — verified: a resume from the wrong cwd wrote its output file there instead of the intended dir.

**Launch pattern:** prefer launching in the background (`run_in_background=true`) so xhigh reasoning does not block, then read the `-o` file when done. Smoke-tested baseline: a read-only repo summary runs in ~15 seconds.

**Context caveat (observed):** `codex exec` loads the target repo's `AGENTS.md` — your prompt COMPETES with repo instructions, and repo workflows can override short prompts entirely. For repo-independent questions, point `-C` at a neutral directory instead (it must be a git repo, or pass `--skip-git-repo-check`).
