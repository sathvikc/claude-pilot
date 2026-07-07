---
name: ask-codex
description: "Run headless Codex as an orchestration sub-agent — one-shot second opinions, bounded code tasks, and mid-flight-steerable app-server sessions. Auto-detects Codex and guides users who don't have it installed."
argument-hint: "<question or task for Codex>"
user-invocable: true
---

# /ask-codex — Codex as an Orchestration Sub-Agent

Run headless Codex (`codex exec` / `codex app-server`) to offload heavy analysis, get an independent second opinion, or delegate a bounded code task to a separate reasoning agent — including watching a run live and correcting it mid-flight without a restart.

The user's arguments are the question or task for Codex. Pick the lane after detection:

- **Question / analysis / review** → Step 2 recipe (a) — read-only one-shot
- **Bounded code-writing task** → Step 2 recipe (b) — workspace-write one-shot
- **Long job (>20 min expected) or one you may need to correct mid-flight** → Step 3 session daemon

## Scope Rules

- **Build-time developer tool ONLY** — analysis, code, reviews, and second opinions launched by the supervising agent or operator. Codex-produced code lands as ordinary working-tree changes for review; sub-agents do NOT commit.
- **Complementary to the Codex companion plugin** — `/spec`, `/fix`, and `codex:rescue` keep using the `codex@openai-codex` broker for workflow reviews and rescue handoffs. This skill covers ad-hoc orchestration outside those workflows.

## Iron Rules (verified operational knowledge)

1. **ALWAYS append `</dev/null` to every `codex exec` launch.** Root cause of ALL observed silent startup hangs (up to 5h46m dead, 0 CPU, no session log): when stdin is an open pipe, `codex exec` blocks forever on "Reading additional input from stdin..." BEFORE creating a session. With `</dev/null` the same command returns in seconds.
2. **Always pass `-C <abs repo>` and an ABSOLUTE `-o` path** (scratchpad, not `/tmp`) — some agent runtimes reset cwd.
3. **Concurrency:** Codex's 5-hour rolling limit is the real constraint (weekly ≈ unlimited). Default max 2 concurrent instances (1 long + 1 short); queue the rest serially. Burst higher only when the user states the window has headroom.
4. **Liveness:** no output/scratch activity for 30 min ⇒ presume hung, kill, relaunch with a SIMPLIFIED brief. There is no native timeout flag: run in the background and poll, or wrap with `gtimeout <secs>`.

## Workflow

Detection first, always — then the lane picked above. See `steps/01-detect.md` through `steps/03-steerable.md`.
