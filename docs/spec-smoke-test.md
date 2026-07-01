# Spec Workflow Model-Switching Smoke Test

Dry-run of `/spec` (plan → implement → verify) with no real product work, to observe
automated model switching between the planning and execution legs.

## Observed models per phase

| Phase | Model | Context window | How switched |
|-------|-------|-----------------|---------------|
| Planning (`spec-plan`) | Opus 4.8 (plan mode) | 200K | `EnterPlanMode` called at start of planning (opusplan → Opus) |
| Implementation (`spec-implement`) | Sonnet 5 (`claude-sonnet-5`) | 967k tokens (native 1M) | `ExitPlanMode` called after plan approval (opusplan → Sonnet) |
| Verification (`spec-verify`) | Sonnet 5 (`claude-sonnet-5`) | 967k tokens (native 1M) | Same session as implementation — no further switch needed |

The implementation-leg reading above was confirmed directly via `/context` mid-run:
`Sonnet 5 · claude-sonnet-5 · 126.5k/967k tokens (13%)`.

## Why the switch happens

With `PILOT_MODEL_SWITCH_ENABLED=true` (default), Claude Code runs on the `opusplan`
model alias. Under this alias, plan mode resolves to Opus and non-plan-mode resolves
to Sonnet. `/spec` calls `EnterPlanMode` before planning and `ExitPlanMode` right after
plan approval, so the model flip is automatic — no manual `/model` command needed
mid-workflow. Claude Code has no `opusplan[1m]` alias, so under Model Switching ON the
planning leg is capped at 200K while the Sonnet execution leg gets Sonnet 5's native 1M.

## Contrast: Model Switching OFF

If `PILOT_MODEL_SWITCH_ENABLED=false`, the whole `/spec` workflow (plan, implement,
verify) stays on a single model — `opus[1m]` (Opus 4.8 at its 1M context alias) — with
no `EnterPlanMode`/`ExitPlanMode` calls at all.
