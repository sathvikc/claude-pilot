---
sidebar_position: 1
title: Customize & Share
description: Create your own rules, commands, and skills — then share them across machines, projects, and organizations
---

# Customize & Share

Create your own rules, commands, and skills — then share them across machines, projects, and organizations.

## Create Your Own Assets

All assets are plain markdown files in your project's `.claude/` directory. Your project-level assets load alongside Pilot's built-in defaults and take precedence when they overlap.

| Asset | Location | When it loads | Best for |
|-------|----------|---------------|----------|
| **Rules** | `.claude/rules/` | Every session, or conditionally by file type | Guidelines Claude should always follow |
| **Commands** | `.claude/commands/` | On demand via `/command-name` | Specific workflows or multi-step tasks |
| **Skills** | `.claude/skills/` | Automatically when relevant | Reusable knowledge from past sessions |
| **Agents** | `.claude/agents/` | Spawned as sub-agents for specialized tasks | Code review, security audits, domain experts |

### How to create assets

- **Rules** — Create `.claude/rules/my-rule.md`. Add `paths: ["*.py"]` frontmatter to activate only for specific file types. Rules without `paths` load every session.
- **Commands** — Create `.claude/commands/my-command.md`. Invoke with `/my-command` in any session.
- **Skills** — Create `.claude/skills/my-skill.md` with a `description` frontmatter. Claude loads skills automatically when their description matches the current task.

### Auto-generation

- `/setup-rules` explores your codebase and generates project-specific rules based on your tech stack, conventions, and patterns. Also creates `AGENTS.md` for cross-tool compatibility.
- `/create-skill` builds reusable skills from any topic — explores the codebase and creates well-structured skills interactively.

### Monorepo support

Organize rules in nested subdirectories by product and team (e.g. `.claude/rules/my-product/team-x/`). Team-level rules must use `paths` frontmatter to scope to the right files. `/setup-rules` validates the structure, enforces path-scoping, and generates a `README.md` to document the organization.

### MCP servers

Add custom MCP servers in `.mcp.json`, then run `/setup-rules` to generate documentation so Claude knows how to use them.

## Share Across Boundaries

Share all four asset types across machines, projects, and organizations using [Skillshare](https://github.com/runkids/skillshare). Skillshare is installed automatically by the Pilot installer and works with **50+ AI coding tools** — Claude Code, Cursor, Codex, Windsurf, Copilot, and more. One central source of truth for all your AI assets.

Use the `skillshare` CLI for operations and the Console Share page for browsing, editing, and managing assets.

### Getting Started

```bash
# Global mode — available in all projects
skillshare init --targets claude

# Project mode — skills committed to this repo
skillshare init -p --targets claude

# Cross-machine sync — add a git remote
skillshare init --remote git@github.com:you/my-skills.git
```

### Project Mode — team sharing via git

Commit `.skillshare/skills/` to your repo. Team members get all assets on `git clone` — no extra setup.

```bash
skillshare init -p --targets claude     # Initialize project mode
skillshare install <url> -p             # Install a skill to the project
skillshare install -p                   # Install all from registry.yaml
skillshare sync -p                      # Sync to Claude's directory
skillshare status -p                    # Check project status
```

New team members onboard with:

```bash
git clone <repo> && cd <repo> && skillshare install -p && skillshare sync -p
```

[Project Setup Guide →](https://skillshare.runkids.cc/docs/how-to/sharing/project-setup)

### Global Mode — personal cross-machine sync

Skills in `~/.config/skillshare/skills/` sync to `~/.claude/skills/` on every machine. Add a git remote to push/pull between devices.

```bash
skillshare init --remote git@github.com:you/my-skills.git   # First machine
skillshare push -m "Add skill"                               # Push changes
# On another machine:
skillshare init --remote git@github.com:you/my-skills.git   # Auto-pulls
skillshare pull                                              # Sync updates
```

```bash
skillshare status -g            # Global status
skillshare list -g              # List global skills
skillshare install <url> -g     # Install to global
skillshare sync -g --all        # Sync skills + extras → Claude
skillshare collect -g           # Import local-only skills to source
skillshare diff -g              # Show pending changes
```

[Cross-Machine Sync Guide →](https://skillshare.runkids.cc/docs/how-to/sharing/cross-machine-sync)

### Extras — rules, commands, agents

Extras manage non-skill assets (rules, commands, agents) as first-class resources with their own CLI commands (Skillshare 0.17+). Extras support both global and project mode, multiple targets per extra, and three sync modes.

```bash
# Create a new extra
skillshare extras init rules --target ~/.claude/rules          # Global
skillshare extras init rules -p --target .claude/rules         # Project

# List extras with sync status
skillshare extras list                                          # Interactive TUI
skillshare extras list --json -g                                # JSON output

# Collect files from a target back into source
skillshare extras collect rules --from ~/.claude/rules

# Change sync mode
skillshare extras mode rules --mode copy                        # copy | merge | symlink

# Remove an extra (source files preserved)
skillshare extras remove rules
```

Source directories live under `~/.config/skillshare/extras/<name>/` (global) or `.skillshare/extras/<name>/` (project). Extras sync alongside skills when you push/pull. The Pilot installer configures extras automatically.

| Sync Mode | Behavior |
|-----------|----------|
| `merge` (default) | Per-file symlinks from target to source |
| `copy` | Per-file copies |
| `symlink` | Entire directory symlink |

### Organization Mode — org-wide distribution

Track shared repos to distribute curated assets across your organization.

```bash
skillshare install github.com/org/skills --track   # Install tracked repo
skillshare update --all && skillshare sync -g       # Update all tracked repos
```

[Organization Sharing Guide →](https://skillshare.runkids.cc/docs/how-to/sharing/organization-sharing)

### .skillignore — hide skills from discovery

Place a `.skillignore` at the source root or inside a tracked repo to hide skills from all commands. Uses full gitignore syntax:

```
draft-*          # hide all draft skills
_archived/       # hide entire directory
!test-important  # negation — keep this one
**/temp          # ignore temp at any depth
```

### Health checks

Run `skillshare doctor` to validate your setup. Use `--json` for CI pipelines:

```bash
skillshare doctor                                    # Human-readable
skillshare doctor --json                             # Structured JSON
skillshare doctor --json | jq -e '.summary.errors == 0'  # CI gate
```

### Console Share Page

The Share page in the Pilot Console provides a full management interface:

- **Source & Sync** — asset counts (skills, rules, commands, agents) for both project and global scopes
- **Team Remote** — connected git remotes with **Push** and **Pull** buttons for one-click sync
- **Assets Grid** — all assets with type and scope badges, filterable by scope (Project / Global / All) and type (Skill / Rule / Command / Agent), plus text search
- **Asset Detail** — click any asset to:
  - **Preview** rendered markdown or view raw source
  - **Edit** markdown in-place with a Save button
  - **Rename** the asset file
  - **Delete** with confirmation prompt
  - View metadata (source, version, install date, repository URL) and file list

### CLI Quick Reference

| Command | Description |
|---------|-------------|
| `skillshare init --targets claude` | Initialize global mode |
| `skillshare init -p --targets claude` | Initialize project mode |
| `skillshare init --remote <url>` | Set up git remote |
| `skillshare status -g` / `-p` | Check status |
| `skillshare list -g` / `-p` | List skills |
| `skillshare install <url> -g` / `-p` | Install a skill |
| `skillshare sync -g --all` | Sync skills + extras |
| `skillshare sync -p` | Sync project skills |
| `skillshare collect -g` | Import local-only skills |
| `skillshare update --all` | Update tracked repos |
| `skillshare push -m "msg"` | Push to remote |
| `skillshare pull` | Pull from remote |
| `skillshare diff -g` / `-p` | Show pending changes |
| `skillshare audit --json -g` | Security audit |
| `skillshare extras init <name> --target <path>` | Create an extra |
| `skillshare extras list [--json]` | List extras with sync status |
| `skillshare extras collect <name> --from <path>` | Collect files into source |
| `skillshare extras mode <name> --mode <mode>` | Change sync mode |
| `skillshare extras remove <name>` | Remove an extra |
| `skillshare doctor [--json]` | Health check |

### Documentation

- [Quick Start](https://skillshare.runkids.cc/docs/learn/with-claude-code) — Get started with Skillshare
- [Commands Reference](https://skillshare.runkids.cc/docs/reference/commands) — All CLI commands
- [Extras Reference](https://skillshare.runkids.cc/docs/reference/commands/extras) — Extras CLI commands
- [Cross-Machine Sync](https://skillshare.runkids.cc/docs/how-to/sharing/cross-machine-sync) — Sync via git push/pull
- [Project Setup](https://skillshare.runkids.cc/docs/how-to/sharing/project-setup) — Commit skills to your repo
- [Organization Sharing](https://skillshare.runkids.cc/docs/how-to/sharing/organization-sharing) — Tracked repos for teams
