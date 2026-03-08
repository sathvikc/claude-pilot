## CLI Tools

### Pilot CLI

The `pilot` binary is at `~/.pilot/bin/pilot`. Do NOT call commands not listed here.

**Session & Context:**

| Command | Purpose |
|---------|---------|
| `pilot check-context --json` | Get context usage % (informational only) |
| `pilot register-plan <path> <status>` | Associate plan with session |

**Worktree:** `pilot worktree detect|create|diff|sync|cleanup|status --json <slug>`

Slug = plan filename without date prefix and `.md`. `create` auto-stashes uncommitted changes.

**License:** `pilot activate <key>`, `pilot deactivate`, `pilot status`, `pilot verify`, `pilot trial --check|--start`

**Other:** `pilot greet`, `pilot statusline`

**Do NOT exist:** ~~`pilot pipe`~~, ~~`pilot init`~~, ~~`pilot update`~~

---

### Probe — Code Search (CLI)

**⛔ Primary codebase search tool.** Instant results (<0.3s), runs via Bash. Always use Probe first for codebase search. Fallback: Grep/Glob for exact patterns.

Probe is installed globally via npm: `npm install -g @probelabs/probe`

**⛔ Always use `--max-results 5 --max-tokens 2000`** to keep context lean. This returns ~5 relevant code snippets within ~300 tokens — enough to understand patterns without bloating the 200k context window.

#### `probe search` — Semantic Code Search

```bash
# ⛔ Default: always limit results to protect context
probe search "authentication AND login" ./src --max-results 5 --max-tokens 2000

# Boolean operators (Elasticsearch syntax)
probe search "error AND handling" ./ --max-results 5 --max-tokens 2000
probe search "database NOT sqlite" ./ --max-results 5 --max-tokens 2000
probe search "(error OR exception) AND handle" ./ --max-results 5 --max-tokens 2000

# Wildcards
probe search "auth* connect*" ./ --max-results 5 --max-tokens 2000

# Language filter
probe search "interface" ./ --language typescript --max-results 5 --max-tokens 2000

# File filters (inside query string)
probe search "function AND ext:rs" ./           # By extension
probe search "class AND file:src/**/*.py" ./    # By file path
probe search "error AND dir:tests" ./           # By directory

# Include test files (excluded by default)
probe search "mock" ./ --allow-tests --max-results 5 --max-tokens 2000
```

**Key options:** `--max-tokens <n>` (always use), `--max-results <n>` (always use), `--allow-tests`, `--format color|markdown|json`, `--language <lang>`, `--session <id>` (dedup across related searches)

#### `probe extract` — AST-Aware Code Extraction

```bash
# Extract by line (finds enclosing function/class)
probe extract src/auth.ts:42

# Extract by symbol name
probe extract src/auth.ts#authenticate

# Extract line range
probe extract src/auth.ts:10-50

# Multiple files at once
probe extract src/auth.ts:42 src/user.ts#User src/api.ts:10-50

# From git diff (extract changed code blocks)
git diff | probe extract --diff
git diff --cached | probe extract --diff

# Output formats
probe extract src/auth.ts:42 --format json
probe extract src/auth.ts:42 --format markdown

# Add context lines
probe extract src/auth.ts:42 --context 5
```

**Formats:** `"file.ts:42"` (block at line), `"file.ts:10-50"` (range), `"file.ts#symbolName"` (by symbol), `"file.ts"` (whole file).

#### `probe query` — AST Pattern Matching

```bash
# Find all async functions
probe query "async function $NAME($$$)" --language typescript

# Find Python classes
probe query "class $CLASS: def __init__($$$)" --language python

# Find React hooks
probe query "useState($INITIAL)" ./src --language javascript

# Find Go structs
probe query "type $NAME struct { $$$FIELDS }" ./src --language go
```

**Metavariables:** `$NAME` (single node), `$$$BODY` (multiple nodes), `$_` (any single node).

`probe --version` to verify installation.

