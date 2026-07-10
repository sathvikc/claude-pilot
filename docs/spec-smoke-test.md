# Spec Workflow Model-Switching Smoke Test

Dry-run of `/spec` (plan → implement → verify) with no real product work, to observe
automated model switching between the planning and execution legs.

## Observed models per phase

| Phase | Model | Context window | How switched |
|-------|-------|-----------------|---------------|
| Planning (`spec-plan`) | Opus 4.8 (`claude-opus-4-8[1m]`; plan mode) | 1M | `EnterPlanMode` called at start of planning (opusplan → Opus via the same-family `ANTHROPIC_DEFAULT_OPUS_MODEL` pin) |
| Implementation (`spec-implement`) | Sonnet 5 (`claude-sonnet-5`) | ~967k tokens (native 1M) | `ExitPlanMode` called after plan approval (opusplan → Sonnet) |
| Verification (`spec-verify`) | Sonnet 5 (`claude-sonnet-5`) | ~967k tokens (native 1M) | Same session as implementation — no further switch needed |

The implementation-leg reading above was confirmed directly via `/context` mid-run:
`Sonnet 5 · claude-sonnet-5 · 126.5k/967k tokens (13%)`.

## Why the switch happens

With `PILOT_MODEL_SWITCH_ENABLED=true` (default), Claude Code runs on the `opusplan`
model alias: plan mode resolves to Opus and non-plan-mode to Sonnet. Pilot additionally
pins the opus slot to `claude-opus-4-8[1m]` (same family — cross-family pins would hijack
the /model picker), which lifts the planning leg from 200K to 1M; the Sonnet 5 execution
leg is natively 1M. `/spec` calls `EnterPlanMode` before planning and `ExitPlanMode`
right after plan approval, so the model flip is automatic — no manual `/model` command
needed mid-workflow.

## Contrast: Model Switching OFF

If `PILOT_MODEL_SWITCH_ENABLED=false`, the whole `/spec` workflow (plan, implement,
verify) stays on a single model — `opus[1m]` (Opus 4.8 at its 1M context alias) — with
no `EnterPlanMode`/`ExitPlanMode` calls at all.
