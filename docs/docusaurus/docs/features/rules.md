---
sidebar_position: 4
title: Rules & Standards
description: Production-tested best practices loaded into every session
---

# Rules & Standards

Production-tested best practices loaded into every session.

Rules are loaded automatically at session start. They're not suggestions — they're enforced standards. Coding standards load conditionally based on the file type being edited, keeping context lean. Your project-level rules in `.claude/rules/` are loaded alongside Pilot's built-ins and take precedence when they overlap.

## Built-in Rule Categories

### Core Workflow (3 rules)

- `task-and-workflow.md` — Task management, /spec orchestration, deviation handling
- `testing.md` — TDD workflow, test strategy, coverage requirements (≥80%)
- `verification.md` — Execution verification, completion requirements

### Development Practices (3 rules)

- `development-practices.md` — Project policies, systematic debugging, git rules
- `context-management.md` — Auto-compaction and context preservation
- `pilot-memory.md` — Online learning triggers

### Tools (3 rules)

- `research-tools.md` — Search priority and tool selection guide
- `cli-tools.md` — Pilot CLI, Probe code search, RTK token optimization
- `playwright-cli.md` — Browser automation for E2E UI testing

### Collaboration (1 rule)

- `skill-sharing.md` — Skillshare CLI and three-tier sharing model

## Coding Standards — Activated by File Type

| Standard | Activates On | Coverage |
|----------|-------------|----------|
| Python | `*.py` | uv, pytest, ruff, basedpyright, type hints |
| TypeScript | `*.ts, *.tsx, *.js, *.jsx` | npm/pnpm, Jest, ESLint, Prettier, React patterns |
| Go | `*.go` | Modules, testing, formatting, error handling |
| Frontend | `*.tsx, *.jsx, *.html, *.vue, *.css` | Components, CSS, accessibility, responsive design |
| Backend | `**/models/**, **/routes/**, **/api/**` | API design, data models, query optimization, migrations |

:::tip Custom rules
Create `.claude/rules/my-rule.md` in your project. Add `paths: ["*.py"]` frontmatter to activate only for specific file types. Run `/sync` to auto-discover patterns and generate project-specific rules for you.
:::

:::info Monorepo support
Organize rules in nested subdirectories by product and team (e.g. `.claude/rules/my-product/team-x/`). Team-level rules must use `paths` frontmatter to scope to the right files. `/sync` generates a `README.md` in your rules directory to document the structure.
:::
