## Testing

### TDD — Mandatory

**⛔ STOP: Do you have a failing test? If not, write one FIRST.**

#### Red-Green-Refactor

1. **RED** — One minimal test for the desired behavior. Behavior, not implementation. Mocks for external deps only. Naming: Python `test_<function>_<scenario>_<expected>` | TS `it("should <behavior> when <condition>")`.
2. **VERIFY RED** — Run it; confirm it fails because the feature doesn't exist (not syntax). If it passes → rewrite.
3. **GREEN** — Simplest code that passes. No extras, no refactor. Hardcoding is fine.
4. **VERIFY GREEN** — Full suite passes. Check diagnostics.
5. **REFACTOR** — Improve quality; tests stay green; no new behavior.

**TDD applies to:** new functions, API endpoints, business logic, bug fixes (reproduce first), behavior changes. **Skip:** docs, config, dep versions, formatting-only.

**Recovery (code before test):** don't revert — write the test now, verify it catches regressions. Goal is coverage, not ritual.

---

### Test Strategy & Coverage

**Unit for logic, integration for interactions, E2E for workflows. Minimum 80% coverage.**

| Type | When | Requirements |
|------|------|--------------|
| **Unit** | Pure functions, business logic, validation | <1 ms each, mock ALL external deps, `@pytest.mark.unit` |
| **Integration** | DB, external APIs, file I/O, auth flows | Real test deps, fixtures, cleanup, `@pytest.mark.integration` |
| **E2E** | Complete user workflows, API chains | Test entire flow |

External deps? No → unit. Yes → integration. Complete user workflow? Yes → E2E.

### Property-Based Testing (PBT)

Use when behavior depends on data shape, ranges, or combinations — not single known input.

| Lang | Tool | Example |
|------|------|---------|
| Python | `hypothesis` | `@given(st.lists(st.integers()))` |
| TypeScript | `fast-check` | `fc.assert(fc.property(fc.array(fc.integer()), ...))` |
| Go | `go test -fuzz` | `func FuzzFoo(f *testing.F) { f.Fuzz(...) }` |

**Use:** parsers, serializers, invariants, encode/decode roundtrips, bug-fix preservation. **Don't:** simple CRUD, UI, fixed-input validation, config. Supplements example-based tests, doesn't replace. Keep strategies simple. CI runs: `max_examples`/`numRuns` 100–200.

### Running Tests

```bash
uv run pytest -q                              # Python (quiet)
uv run pytest --cov=src --cov-fail-under=80  # Coverage
bun test                                      # Bun
npm test -- --silent                          # Jest/Vitest
```

### Mandatory Mocking in Unit Tests

| Call | MUST mock | Example |
|------|-----------|---------|
| HTTP/network | `httpx`, `requests` | `@patch("module.httpx.Client")` |
| Subprocess | `subprocess.run` | `@patch("module.subprocess.run")` |
| File I/O | `open`, `Path.read_text` | `@patch("builtins.open")` or `tmp_path` |
| Database | SQLite, PostgreSQL | Test fixtures |
| External APIs | Any third-party | Mock the client |

Mock at module level (where imported, not where defined). Test > 1 s = likely unmocked I/O.

### ⛔ E2E: Frontend/UI (MANDATORY for web apps)

Any change that affects what the user sees MUST be verified with browser automation — both `/spec` and quick mode. Unit tests don't catch layout bugs, stale bundles, or wiring issues. Tier priority and procedure: see `browser-automation.md` and `verification.md`.

### ⛔ Mock Audit on Dependency Changes

When a function gains a new dependency (subprocess, helper, I/O), update ALL existing tests for that function. Tests passing locally with real binaries fail in CI without them — the #1 cause of CI-only failures.

**Checklist:** (1) `Grep` the function name in `tests/`; (2) verify subprocess/I/O calls are mocked in each test; (3) run with `--tb=short` to surface unmocked calls fast.

### Anti-Patterns

- **Dependent tests** — each must work independently.
- **Testing implementation, not behavior** — assert outputs/state, not which mocks were called. `assert result == expected`, not `mock.assert_called_with(...)`. Behavior unchanged → tests still pass after refactor.
- **Incomplete mocks hiding structural assumptions** — mocks must mirror the complete real API, not just the fields you think you need. Partial mocks hide coupling and break against real data.
- **Unmocked environment dependencies** — locally-installed tools (probe, node) pass locally, fail CI. Mock every subprocess, PATH lookup, FS check for external tools.
- **Unnecessary mocks** — only for external deps.
- **Test-only methods in production** — never add methods/properties/flags purely for test access. Refactor so behavior is observable through public interfaces.
- **Mocking without understanding** — a mock that doesn't reflect real behavior is a lie. Tests pass against the lie, fail against reality.

### ⛔ Zero Tolerance for Failing Tests

Every test failure MUST be fixed before work is done. Run the FULL suite, not just files you touched. "Pre-existing failure" is not an excuse — if you see it, you fix it.

### Completion Checklist

- [ ] All new functions have tests
- [ ] Tests follow naming convention
- [ ] Unit tests mock external dependencies
- [ ] Full test suite passes (0 failures) — not just your files
- [ ] Coverage ≥ 80% verified
- [ ] Actual program executed and verified

### Assertion-Correctness Warning

Industry research (HumanEval across four LLMs) found > **62% of LLM-generated test assertions were incorrect** — passing tests asserting on the wrong field. False confidence is worse than no test.

Four mental checks before committing any assertion:

1. **One-character bug check** — would a one-char bug in the implementation still pass? `assert result` (truthy) ≠ `assert result == 42` (exact). If a tiny mistake survives, the assertion is too weak.
2. **Right field check** — `response.status` vs `response.body.error` is a common confusion. Confirm the assertion targets the field that carries meaning.
3. **Computed value check** — for hand-derived expected values, verify via a second path (different code, manual calculation, reference). Don't trust your own arithmetic.
4. **Spec-named behavior check** — assert the behavior the spec/contract names, not what you imagined. "User can perform X within rate limit" is named; "calls `_internal_fn` with `'QUEUED'`" is mechanics.

If you can't write a precise assertion because the spec is ambiguous, **STOP and ask** — don't pattern-match a plausible expected value.
