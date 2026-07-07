---
sidebar_position: 4
title: /ask-codex
description: Run headless Codex as an orchestration sub-agent from Claude Code — one-shot second opinions, bounded code tasks, and mid-flight-steerable sessions.
---

# /ask-codex

Run headless Codex as an orchestration sub-agent from Claude Code.

Offload heavy analysis, get an independent second opinion from a different reasoning model, or delegate a bounded code task — including **watching the run live and steering it mid-flight** without a restart.

```bash
# Claude Code only
claude
> /ask-codex "Review the auth flow in this repo for race conditions"
> /ask-codex "Refactor src/parser.ts to remove the legacy tokenizer path"
```

## Requirements

- **OpenAI Codex CLI** installed and authenticated (`codex login`).
- **No Codex? No problem.** The skill auto-detects Codex at runtime — without it you get a friendly install pointer instead of an error, and installing Codex later needs no reinstall.

## Three Lanes

| Lane | Use For |
|------|---------|
| **Second opinion** (read-only) | Analysis, reviews, "what am I missing here?" |
| **Bounded code task** | A scoped implementation task; changes land as ordinary working-tree edits for review |
| **Steerable session** | Long jobs you want to watch live — `steer:` a correction into the running turn, `interrupt` it, or queue the next one |

The steerable session is the standout: no other lane lets you correct a run mid-flight instead of restarting it.

Hangs, silent failures, and auth hiccups are handled for you — runs fail loudly with clear guidance instead of stalling.

## Relationship to the Codex Companion Plugin

`/spec`, `/fix`, and `codex:rescue` keep using the companion plugin for workflow reviews; `/ask-codex` covers ad-hoc orchestration outside those workflows.

:::info Attribution
Vendored from [FabianWesner/claude-code-codex-skill](https://github.com/FabianWesner/claude-code-codex-skill) (MIT License) with Pilot additions: runtime auto-detection and safety hardening of the bundled clients.
:::
