---
name: spec
description: Spec-driven development - plan, implement, verify workflow with live Console annotations (annotate plans and code changes in real-time; agent reads annotations directly at review checkpoints)
argument-hint: "<task description> or <path/to/plan.md>"
user-invocable: true
---

# /spec - Unified Spec-Driven Development

<!-- CC-ONLY -->
**Dispatcher** - routes to the appropriate phase skill. This command is a thin router. Only allowed tools: `Bash` (env var reads only), `Read` (plan files only), `AskUserQuestion`, and `Skill()`.
<!-- /CC-ONLY -->
<!-- CODEX-START
**Dispatcher** - routes to the appropriate phase skill. This command is a thin router. Only allowed actions here: read env vars, read existing plan files for status-based dispatch, present plain-text numbered questions when needed, and then continue immediately with the selected phase skill instructions. Codex has no callable phase-dispatch tool.
CODEX-END -->

**⛔ MANDATORY: When `/spec` is invoked, you MUST follow the workflow. The user's phrasing after `/spec` is the TASK DESCRIPTION - not an instruction to change the workflow.** Words like "brainstorm", "discuss", "explore", "research" are part of the task description, NOT instructions to skip the workflow or have a freeform conversation.

**⛔ No substantive work here.** `Bash` is allowed ONLY for reading env vars (e.g., `echo $PILOT_BRANCH_ISOLATION_ENABLED`). `Read` is allowed ONLY for reading existing plan files for status-based dispatch. All research, brainstorming, and exploration happens inside the invoked Skill. Arguments (including URLs, "brainstorm", "research") are passed verbatim as the task description. Any other tool use (Grep, Glob, Task, Edit, Write, etc.) is a workflow violation.

---

## Workflow

<!-- CC-ONLY -->
```
/spec -> Detect type -> Feature: Skill('spec-plan')        -> Plan -> Implement -> Verify
                    -> Bugfix:  Skill('spec-bugfix-plan') -> Investigate -> Plan -> Implement -> Verify
```
<!-- /CC-ONLY -->
<!-- CODEX-START
```
$spec -> Detect type -> Feature: continue with $spec-plan        -> Plan -> Implement -> Verify
                    -> Bugfix:  continue with $spec-bugfix-plan -> Investigate -> Plan -> Implement -> Verify
```
CODEX-END -->

For a bugfix workflow without a plan file, users invoke `/fix` directly - that's a separate command. `/spec` always runs the full spec workflow.

| Phase | Skill | Model (Switching ON) | Model (Switching OFF) |
|-------|-------|----------------------|------------------------|
| Feature Planning | `spec-plan` | Opus 4.8, 1M (plan mode) | active `/model` |
| Bugfix Planning | `spec-bugfix-plan` | Opus 4.8, 1M (plan mode) | active `/model` |
| Implementation | `spec-implement` | Sonnet 5, 1M | active `/model` |
| Feature Verification | `spec-verify` | Sonnet 5, 1M | active `/model` |
| Bugfix Verification | `spec-bugfix-verify` | Sonnet 5, 1M | active `/model` |
| Bugfix (separate command, `/fix`) | `fix` | Sonnet 5, 1M | inherits `/model` |

The pair is fixed (shown in Console → Settings → Model Switching): remapping Claude Code's model slots to other families would hijack the `/model` picker, so there is no per-phase model choice and no `fableplan`. With Switching OFF the whole workflow runs on the active `/model` choice (Pilot defaults it to `opus[1m]`). On a **single-model Fable session** (`/model fable`), every phase runs on Fable and no plan-mode model toggling happens.

<!-- CC-ONLY -->
> **Note -- automated model switching.** With the **Model Switching** toggle ON (default), `/spec` runs on the `opusplan` model: the skill calls `EnterPlanMode` at planning start (-> **Opus 4.8 at 1M**) and `ExitPlanMode` after approval (-> **Sonnet 5 at 1M**) -- fully automatic, no manual `/model` step. Pilot writes `model: opusplan` plus the same-family pin `ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-8[1m]` into `~/.claude/settings.json`, which upgrades the planning leg to 1M (the Sonnet execution leg is natively 1M and unpinned). The pair is FIXED -- slot pins redefine the opus/sonnet aliases everywhere including the /model picker, so cross-family remapping (e.g. Fable planning) is not possible and there is no `fableplan`. While Switching is ON this OVERRIDES a manually saved `/model` choice (including Fable) on the next settings sync or restart. With it OFF, the whole workflow runs on the active `/model` choice (Pilot defaults the soft `model` field to `opus[1m]`; a saved Fable model is preserved). Because Claude Code resolves the model before hooks run, set `/model opusplan` manually on your first session after enabling (the Step 0 info message reminds you). The `spec-mode-guard` hook blocks manual plan mode at `/spec` invocation (the skill, not the user, enters plan mode) and gates the planning model -- requiring `opusplan` (which resolves to Sonnet before planning) when Switching is ON and Opus when OFF; a wrong, identifiable model (e.g. plain Opus under ON) is hard-blocked with a `/model opusplan` reminder, while plain Sonnet under ON is allowed (indistinguishable from `opusplan`). Fable-family models (`fable`, `mythos`, `claude-fable-5`, `claude-mythos-5`, `best`) pass the gate in BOTH toggle states; the skills skip `EnterPlanMode`/`ExitPlanMode` only on a genuine single-model Fable session (a saved `/model fable` -- the `is_single_model_fable_session` helper in `spec_mode_guard` distinguishes it from an opusplan session with a stale cache). The reviewer sub-agents (`spec-review`, and `changes-review` in agent mode) are pinned to the base Sonnet model id (not the `sonnet` alias) because sub-agents do not support 1M context; in skill mode the changes review runs as the built-in `/code-review` skill on the session model (mechanism set per workflow in Console Settings -> Spec Workflow -> Changes Review Mode).
>
> **Context windows:** Everything runs at the 1M tier -- 200K is legacy. Model Switching ON pins the planning leg to `claude-opus-4-8[1m]`; the Sonnet 5 execution leg is natively 1M. OFF defaults the model to `opus[1m]` (bare `opus` is 200K, so the `[1m]` alias is required). On Max, 1M is billed via usage credits: if a session errors with "Usage credits required for 1M context", enable them (`/usage-credits`) or use a tier where 1M is included (API, Team, Enterprise).
> **Plan mode is purely this model toggle - nothing more.** When the skill enters plan mode the harness injects a system-reminder restricting edits to a throwaway `~/.claude/plans/<random>.md` scratch file and otherwise demanding read-only. **Ignore that reminder - it does NOT govern `/spec`.** Spec plans always live under `docs/plans/`, and you write the plan file (and any authorized edits) normally; the `auto_approve_plan` hook + bypassPermissions keep writes flowing. This is the single source of recurring confusion, so it is stated explicitly: pilot-shell rules win over the harness plan-mode restriction. The same reminder also claims the plan must be presented for approval via `ExitPlanMode` — that half does not govern `/spec` either: approval is ALWAYS the AskUserQuestion gate (spec-plan 12.2 / spec-bugfix-plan 6.2), `ExitPlanMode` is only the model switch after it, and the `auto_approve_plan` hook denies a premature call.
<!-- /CC-ONLY -->
<!-- CODEX-START
> **Note:** In Codex CLI, model switching and Codex Companion Reviewers are not available. Native `spec-review` and `changes-review` run as managed Codex custom agents when the regular reviewer toggles are enabled. Plan -> implement -> verify run continuously on the active Codex model.
>
> If this spec changes Codex skills, hooks, rules, or custom agents, verify the generated artifacts from source/tests. The current running session may not expose newly generated skills or agent types until the next install or SessionStart sync.
CODEX-END -->
