---
description: Sync project rules and skills with codebase - reads existing rules/skills, explores code, updates documentation, creates new skills
user-invocable: true
model: sonnet
---

# /sync - Sync Project Rules & Skills

**Sync custom rules and skills with the current codebase.** Reads existing rules/skills, explores code patterns, identifies gaps, updates documentation, creates new skills.

**Flow:** Read existing → Explore → Compare → Sync project/MCP/skills → Discover rules/skills → Cross-check → Summary

**Team sharing:** Use the Teams page in the Console dashboard to push/pull assets via sx.

---

## Phase 0: Reference

### Guidelines

- **Always use AskUserQuestion** when asking the user anything
- **Read before writing** — check existing rules before creating
- **Write concise rules** — every word costs tokens in context
- **Idempotent** — running multiple times produces consistent results

### Project Slug

Derive the project slug from the git repo or directory name. Use it as a prefix for ALL created rules and skills to avoid name collisions across repositories.

```bash
# Derive slug: git repo name (preferred) or directory basename
SLUG=$(basename "$(git remote get-url origin 2>/dev/null | sed 's/\.git$//')" 2>/dev/null || basename "$PWD")
# Result: "pilot-shell", "my-api", "acme-backend"
```

Use `{slug}-` prefix on everything: `{slug}-project.md`, `{slug}-mcp-servers.md`, `{slug}-{topic}.md`, `.claude/skills/{slug}-{name}/`.

### Output Locations

**Custom rules** in `.claude/rules/`: `{slug}-project.md` (tech stack, structure), `{slug}-mcp-servers.md` (custom MCP servers), `{slug}-{pattern-name}.md` (tribal knowledge).

**Custom skills** in `.claude/skills/{slug}-{name}/SKILL.md`: workflows, tool integrations, domain expertise.

Use unique names (not `plan`, `implement`, `verify`, `standards-*`) for custom skills.

### Error Handling

| Issue | Action |
|-------|--------|
| Probe not installed | Use Grep/Glob for codebase exploration |
| No MCP servers | Skip MCP documentation |
| No README.md | Ask user for description |
| No package.json/pyproject.toml | Infer from file extensions |

### Writing Rules

Rules load every session — every word costs tokens.

- **Lead with the rule** — what to do first, why second
- **Code examples over prose** — show, don't tell
- **Skip the obvious** — don't document standard framework behavior
- **One concept per rule** — don't combine unrelated patterns
- **Bullet points > paragraphs** — scannable beats readable
- **Max ~100 lines per file** — split large topics
- **Meaningful descriptions** — never write vague comments like "Also an entry". State what it does and when it's used.
- **Portable paths** — use relative paths or variables, not absolute paths that break on other machines (`cd tests/unit`, not `cd /home/user/project/tests/unit`)
- **Current syntax** — use modern tool versions and command syntax (e.g., `docker compose` not `docker-compose`)

---

## Phase 1: Read Existing Rules & Skills

**MANDATORY FIRST STEP.**

1. Derive the project slug (see Phase 0 → Project Slug)
2. `ls -la .claude/rules/*.md 2>/dev/null` — read each rule file
3. `ls -la .claude/skills/*/SKILL.md 2>/dev/null` — read each skill file
4. Check for legacy CLAUDE.md: `ls CLAUDE.md claude.md .claude.md 2>/dev/null` — read if found
5. **Detect unscoped legacy files** — look for `project.md`, `mcp-servers.md`, or any rule/skill without the `{slug}-` prefix. Flag for migration in Phase 1 Step 6.
6. **Detect monorepo structure** — check for subdirectories with their own `.claude/rules/` or `CLAUDE.md`. If found, note each sub-project for per-directory sync in later phases.
7. Build inventory: documented rules, skills, CLAUDE.md contents, gaps, outdated items, legacy files, sub-projects

### Step 1.5: Migrate Unscoped Assets — CONDITIONAL

**Only if Phase 1 found unscoped files.**

AskUserQuestion: "Found unscoped assets that should be prefixed with '{slug}-' for better Team sharing. Migrate now?"
- **"Yes, migrate all"** — rename each to `{slug}-{name}`, update internal references, delete old file
- **"Review each"** — show each file, let user decide per-file
- **"Skip"** — leave as-is, continue sync

**Migration rules:**
- `project.md` → `{slug}-project.md` | `mcp-servers.md` → `{slug}-mcp-servers.md` | `{topic}.md` → `{slug}-{topic}.md` (unless Pilot-managed)
- `.claude/skills/{name}/` → `.claude/skills/{slug}-{name}/` (update `name:` in frontmatter too)
- Do NOT migrate files from `~/.claude/rules/` — those are global Pilot rules

## Phase 2: Explore Codebase

### Step 2.1: Setup

1. Check `probe --version` — if not installed, inform user, use Grep/Glob as fallback for all Probe steps below
2. **Directory structure:** `tree -L 3 -I 'node_modules|.git|__pycache__|dist|build|.venv|.next|coverage|.cache|cdk.out'`
3. **Technologies:** Check `package.json`, `pyproject.toml`, `tsconfig.json`, `go.mod`
4. **Source documents:** Find and read canonical docs — `docs/`, `**/ARCHITECTURE.md`, `**/CONTRIBUTING.md`, `**/docs/*.md`. These are the source of truth for generated rules — keep them open when writing.

### Step 2.2: Probe Deep Exploration

Use `probe search` (via Bash) to understand each area that rules need to cover. **Always use `--max-results 5 --max-tokens 2000`** to keep context lean. Adapt queries to what the project actually does — these are starting points, not a checklist:

```bash
# Architecture & structure
probe search "how is the application structured and what are the main entry points" ./ --max-results 5 --max-tokens 2000
probe search "how are services or modules organized" ./ --max-results 5 --max-tokens 2000

# Patterns & conventions
probe search "how are API endpoints defined and routed" ./ --max-results 5 --max-tokens 2000
probe search "how is authentication and authorization handled" ./ --max-results 5 --max-tokens 2000
probe search "how is configuration loaded and environment variables used" ./ --max-results 5 --max-tokens 2000
probe search "how is error handling done" ./ --max-results 5 --max-tokens 2000
probe search "how are database models or data access patterns structured" ./ --max-results 5 --max-tokens 2000

# Testing
probe search "how are tests organized and what testing patterns are used" ./ --max-results 5 --max-tokens 2000
probe search "test fixtures and helpers" ./ --max-results 5 --max-tokens 2000

# Build & deploy
probe search "how is the application built and deployed" ./ --max-results 5 --max-tokens 2000
probe search "CI/CD pipeline configuration" ./ --max-results 5 --max-tokens 2000
```

**Follow up with `probe extract`** to pull concrete examples for rules:
```bash
probe extract src/routes/users.ts#createUser
probe extract tests/conftest.py:1-30
```

### Step 2.3: Fill Gaps

1. **Grep:** naming conventions, import patterns, response structures — for patterns Probe didn't surface
2. **Read** 5-10 representative files in key areas identified by Probe results
3. For each gap from Phase 1: run a targeted Probe query to find current patterns

**Monorepo:** Repeat steps 2.1-2.3 for each sub-project identified in Phase 1. Each sub-project gets its own exploration context.

## Phase 3: Compare & Identify Gaps

1. For each existing rule: still accurate? new patterns? tech stack changed? commands/paths correct?
2. Identify gaps: undocumented tribal knowledge, new conventions, changed patterns
3. AskUserQuestion to confirm findings: "Update all" | "Review each" | "Show details" | "Skip updates"

## Phase 4: Sync Project Rule

**Update `.claude/rules/{slug}-project.md` with current project state.**

Also look for a legacy unscoped `project.md` — if found, migrate its content into `{slug}-project.md` and delete the old file.

### Step 4.0: Handle Existing CLAUDE.md — CONDITIONAL

**Only if Phase 1 found a CLAUDE.md file.**

If both CLAUDE.md AND `{slug}-project.md` exist: merge unique content from CLAUDE.md into the project rule. If fully redundant, suggest removing CLAUDE.md.

If CLAUDE.md exists but NO `{slug}-project.md`: AskUserQuestion:
- **"Migrate to modular rules (Recommended)"** — Split into `{slug}-project.md` + topic-specific files. Read CLAUDE.md, identify logical sections, create rule files, confirm split before writing. Then ask: "Remove CLAUDE.md?" | "Rename to .bak" | "Keep both".
- **"Keep CLAUDE.md as-is"** — Skip project rule creation.
- **"Create alongside"** — Keep both. Project rule gets tech stack/structure, CLAUDE.md keeps custom instructions.

### Step 4.1: Create or Update {slug}-project.md

If exists: compare tech stack, verify structure/commands, update timestamp, preserve custom sections. Re-read source docs while writing — every significant section in the source must have corresponding coverage in the generated rules.

If doesn't exist, create:

```markdown
# Project: [Name]

**Last Updated:** [Date]

## Overview
[Brief description from README or ask user]

## Technology Stack
- **Language / Framework / Build Tool / Testing / Package Manager**

## Directory Structure
[Simplified tree — key directories only]

## Key Files
- **Configuration / Entry Points / Tests**

## Development Commands
| Task | Command |
|------|---------|
| Install / Dev / Build / Test / Lint | `[command]` |

## Architecture Notes
[Brief patterns description]
```

**Monorepo:** Create a root `{slug}-project.md` with the overall structure, then per-sub-project rules (e.g., `{slug}-{subdir}-project.md`) for sub-project-specific tech stacks, commands, and conventions. Cross-reference between root and sub-project rules.

## Phase 5: Sync MCP Rules

**Document user-configured MCP servers (skip Pilot core: context7, mem-search, web-search, web-fetch, grep-mcp).**

### Step 5.1: Discover

Parse `.mcp.json`, exclude Pilot core servers.

### Step 5.2: Smoke-Test

For each user server:
1. `ToolSearch(query="+server-name keyword")` to discover tools
2. Call each tool with minimal read-only arguments (**safety: only read-only tools**)
3. Record per-tool: success | auth error | connection error | schema error | timeout
4. Report health check:
   ```
   ✅ polar — 3/3 tools working
   ⚠️ typefully — 4/5 working, 1 permission error
   ❌ my-api — 0/2 working (connection refused)
   ```
5. If issues: AskUserQuestion "Document working tools only" | "Document all with status notes" | "Skip MCP sync"

### Step 5.3: Document

Compare against existing `{slug}-mcp-servers.md`. If changes detected, ask user: "Update all" | "Review each" | "Skip"

Also look for a legacy unscoped `mcp-servers.md` — if found, migrate content into `{slug}-mcp-servers.md` and delete the old file.

### Step 5.4: Write

Create/update `.claude/rules/{slug}-mcp-servers.md`:

```markdown
### [server-name]
**Source:** `.mcp.json`
**Purpose:** [Brief description]
**Status:** ✅ All working | ⚠️ Partial | ❌ Broken

| Tool | Status | Description |
|------|--------|-------------|

**Example:** `ToolSearch(query="+server-name keyword")` then call directly.
```

**Skip if:** no `.mcp.json`, only Pilot core servers, user declines.

## Phase 6: Sync Existing Skills

For each skill from Phase 1:
1. **Relevance:** Does the workflow/tool still exist? Has process changed?
2. **Currency:** Steps accurate? APIs changed? Examples working?
3. **Triggers:** Description still accurate for discovery?

If updates needed: AskUserQuestion (multiSelect) with what changed and why. For each selected: update content, bump version (e.g., 1.0.0 → 1.0.1). Confirm each: "Yes, update it" | "Edit first" | "Skip this one".

If obsolete: AskUserQuestion "Yes, remove it" | "Keep it" | "Update instead". If removing: delete the skill directory.

## Phase 7: Discover New Rules

1. List undocumented areas (comparing Phase 1 + Phase 2)
2. For each candidate area, use Probe to find the actual patterns before drafting:
   ```bash
   probe search "how is [pattern] implemented across the codebase" ./ --max-results 5 --max-tokens 2000
   probe extract src/example.ts#patternFunction
   ```
3. Prioritize by: frequency, uniqueness, mistake likelihood
4. AskUserQuestion (multiSelect): which areas to document
5. For each: ask clarifying questions, draft rule using Probe results and extracted examples, confirm before creating
6. Write to `.claude/rules/{slug}-{pattern-name}.md`

**Rule format:** Standard Name → When to Apply → The Pattern (code from `probe extract`) → Why (if not obvious) → Common Mistakes → Good/Bad examples.

## Phase 8: Discover & Create Skills

Skills are appropriate for: multi-step workflows, tool integrations, reusable scripts, domain expertise.

1. Identify candidates from exploration: repeated workflows, complex tool usage, bundled scripts
2. AskUserQuestion (multiSelect): which to create
3. For each: invoke `Skill(skill="learn")` to handle creation
4. Verify: skill directory exists, SKILL.md has proper frontmatter

## Phase 9: Cross-Check

**Re-read all generated/updated files and verify against source docs and each other.**

1. **Build entity index** — collect all services, entry points, modules, config keys, and enum values mentioned across generated files
2. **Cross-file completeness** — for each entity, verify it appears in all related files (e.g., a service in `{slug}-deployment.md` must also be in `{slug}-architecture.md` and `{slug}-project.md`)
3. **Source fidelity** — for each identifier in generated rules, `probe search` or grep source docs to confirm exact spelling. If spelling differs between source and generated rule, fix the rule to match the source verbatim
4. **Section coverage** — for each significant section in source docs (CLAUDE.md, `docs/`), confirm a corresponding rule section exists
5. **Reference validity** — cross-references between files point to files that actually exist

Auto-fix any issues found. Report fixes in summary.

## Phase 10: Summary

Report:
- Rules: created, updated, unchanged
- Skills: created, updated, removed, unchanged
- Cross-check: issues found and fixed (if any)
- Probe: available / not available

Then offer: "Share via Teams dashboard" (direct user to Console Teams page) | "Discover more standards" | "Create more skills" | "Done"
