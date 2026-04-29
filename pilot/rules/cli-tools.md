## CLI Tools

### Pilot CLI

`~/.pilot/bin/pilot`. Do NOT call commands not listed here.

| Group | Commands |
|-------|----------|
| Session | `pilot check-context --json`, `pilot register-plan <path> <status>` |
| Worktree | `pilot worktree detect\|create\|diff\|sync\|cleanup\|status --json <slug>` (slug = plan filename without date prefix and `.md`; `create` auto-stashes) |
| License | `pilot activate <key>`, `pilot deactivate`, `pilot status`, `pilot verify`, `pilot trial --check\|--start` |
| Other | `pilot greet`, `pilot statusline` |

**Do NOT exist:** ~~`pilot pipe`~~, ~~`pilot init`~~, ~~`pilot update`~~.

---

### RTK — Rust Token Killer

Token-optimized CLI proxy (60–90% savings on dev operations).

```bash
rtk gain              # Token savings analytics
rtk gain --history    # Command usage history
rtk discover          # Find missed optimization opportunities
rtk proxy <cmd>       # Bypass filtering (debugging)
rtk --version         # Verify install
```

All other commands are auto-rewritten by the Claude Code hook (e.g., `git status` → `rtk git status`, transparent).

⚠️ **Name collision:** if `rtk gain` errors, you may have `reachingforthejack/rtk` (Rust Type Kit) on PATH instead.

---

### Probe — Code Search (CLI)

**Intent-based code search.** For symbol/structure queries, prefer CodeGraph (`mcp-servers.md`); for grep-style exact text, prefer Grep. Probe sits between them — fast (<0.3s), AST-aware, ranks by relevance.

Installed via `npm install -g @probelabs/probe`. Verify with `probe --version`.

#### `probe search` — Semantic Search

**⛔ Always pass `--max-results 5 --max-tokens 2000`** to `probe search` to keep context lean. These flags don't apply to `extract` or `query`.

```bash
probe search "auth AND login" ./src --max-results 5 --max-tokens 2000
```

**Query syntax:** Boolean (`AND`/`OR`/`NOT`), wildcards (`auth*`), filters inside the query (`ext:rs`, `file:src/**/*.py`, `dir:tests`). Use `--language <lang>` for language filter, `--allow-tests` to include tests, `--session <id>` to dedupe across related searches.

#### `probe extract` — AST-Aware Extraction

```bash
probe extract src/auth.ts:42                # block at line (finds enclosing fn/class)
probe extract src/auth.ts:10-50             # line range
probe extract src/auth.ts#authenticate      # by symbol
probe extract a.ts:42 b.ts#User c.ts:10-50  # multiple at once
git diff | probe extract --diff             # extract changed blocks
```

`--format json|markdown`, `--context <n>` for surrounding lines.

#### `probe query` — AST Pattern Matching

```bash
probe query "async function $NAME($$$)" --language typescript
probe query "class $CLASS: def __init__($$$)" --language python
probe query "useState($INITIAL)" ./src --language javascript
```

**Metavariables:** `$NAME` (single node), `$$$BODY` (multiple), `$_` (any single).
