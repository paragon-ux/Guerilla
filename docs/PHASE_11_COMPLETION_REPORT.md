# Phase 11 Completion Report -- Action Intent and Idempotency

**Phase Result:** PASS -- Phase 11 complete
**Branch:** `feature/gate-c-continuity-mvp`
**Draft PR:** https://github.com/paragon-ux/Guerilla/pull/2

## Delivered Artifacts

### Repository Controls

- Updated `AGENTS.md`, `README.md`, `README_DEV.md`,
  `docs/CODEX_BUILD_PLAN.md`, `docs/TEST_MATRIX.md`,
  `docs/ADAPTER_CONTRACT.md`, `docs/phase_prompts/README.md`, and
  `docs/architecture/CURRENT_STATUS_MATRIX.md` for Phase 11 status.
- Updated `docs/architecture/README.md` with the refreshed status-matrix
  digest.
- Added `docs/phase_prompts/PHASE_11_ACTION_INTENT_IDEMPOTENCY.md`.

### Action Runtime

- Added `src/guerilla/orchestration/actions.py` with typed action execution
  requests/results, durable action intent, invocation-start records,
  graph-backed idempotency lookup, explicit action-result recording, restart
  protection, and optional after-state observation through the Phase 10
  ingestor.
- Updated `src/guerilla/adapters/host.py` with request preflight validation
  that performs host checks without invoking adapter code.
- Updated `src/guerilla/orchestration/__init__.py` exports.

### Tests

- Added `tests/integration/test_phase11_action_intent_idempotency.py`.
- Updated `tests/repository/test_repository_contract.py` to permit Phase 11
  orchestration modules while continuing to block Phase 12+ runtime modules.

## Validation Evidence

The one-command local wrapper was not run as a single command because this task
required stopping commands after one minute. The same validation sequence was
run in split steps with `UV_CACHE_DIR=.uv-cache` and workspace-local temp/cache
directories.

| Command | Exit code | Result | Evidence |
|---|---:|---|---|
| `uv lock --check` | 0 | Passed | Local terminal output |
| `uv sync --frozen --extra dev` | 0 | Passed | Local terminal output |
| `uv run --frozen --extra dev ruff format --check .` | 0 | Passed, 66 files formatted | Local terminal output |
| `uv run --frozen --extra dev ruff check .` | 0 | Passed | Local terminal output |
| `uv run --frozen --extra dev mypy src tests` | 0 | Passed, 66 source files | Local terminal output |
| Split implemented test suites | 0 | Passed, 147 tests | Local terminal output |
| `uv build` | 0 | Built sdist and wheel | `dist/guerilla-0.0.0.tar.gz`, `dist/guerilla-0.0.0-py3-none-any.whl` |
| Archive cache inspection | 0 | No `.uv-cache`, `.tmp`, or `pip-cache` entries in sdist or wheel | Local terminal output |
| Isolated wheel smoke | 0 | `pip --no-deps` install, import, `--version`, `--help`, and `version --json` passed from temp venv | `.tmp/guerilla-wheel-smoke-*` |
| PR #2 hosted CI | 0 | Python 3.11 and 3.12 validation passed | https://github.com/paragon-ux/Guerilla/pull/2/checks |

## Exit-Criteria Matrix

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| No external action occurs without durable intent | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Operation and action-request event records commit before adapter `act`. |
| Invocation start is committed before adapter call | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Invocation-start event is durable before external mutation. |
| Idempotency survives restart and index loss | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Lookup is reconstructed from authoritative graph replay. |
| Same-key same-content returns prior result | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Replay does not call the adapter again. |
| Same-key different-content is rejected | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Rejected as `idempotency_conflict`. |
| Unknown outcomes are not retried blindly | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Prior invocation without committed result returns `outcome_unknown`. |
| Result classifications remain distinct | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Accepted, rejected, failed, pending, duplicate, and unknown classifications remain explicit. |
| Replay performs no adapter calls | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Replay and index rebuild do not invoke adapters. |
| All systems use one action path | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` | Transactional, filesystem, and asynchronous systems use `ActionOrchestrator`. |
| Full validation and hosted CI pass | PASS | Split local validation; PR #2 hosted CI | Phase 12 may begin from this passed baseline. |

## Invariant Audit

- Every external action path commits durable intent before invoking adapter
  `act`.
- Adapter action requests are schema-validated and host-validated before intent
  commitment.
- Invocation-start records commit before adapter invocation.
- Idempotency truth is reconstructed from authoritative graph replay, not from
  SQLite or adapter-native state.
- Replay and index rebuild do not invoke adapters or external actions.
- External systems remain application-state authorities.

## External-State Audit

| Synthetic system | Action evidence | Authority behavior |
|---|---|---|
| Transactional revisioned service | Compare-and-set actions preserve expected revision and native idempotency behavior | Guerilla records intent/result lineage and does not own the service transaction model. |
| Reconstructed filesystem | Structured filesystem actions preserve external identity, revision, and after-state observation | Guerilla records bounded action facts and observed after-state without owning filesystem semantics. |
| Asynchronous unknown-outcome service | Pending, duplicate, completed, and unknown classifications remain explicit | Guerilla records uncertain outcomes and does not infer success or retry unsafely. |

## Failure and Recovery Evidence

- Invalid principal, stale graph revision, malformed action request, and
  boundary escape fail before adapter invocation and before graph commitment.
- Injected failure before or during intent commitment leaves no action call.
- A committed intent without invocation can resume safely.
- A prior invocation-start without committed result returns `outcome_unknown`
  and does not call the adapter again.
- A committed result can be replayed across restart and SQLite index loss.
- Optional after-state observation uses the Phase 10 observe-only ingestion
  path.

## Scope Audit

No prohibited runtime behavior was introduced. Phase 11 did not implement a
reconciliation engine, conflict decisions, projections, snapshots, CLI
workflows, transports, subprocess isolation, real integrations, Gate D behavior,
or payload execution.

## Blockers and Contradictions

None.

## Git Summary

- Phase 10 evidence and local cache hardening are committed in `fe5a244`.
- Phase 11 action intent/idempotency implementation and evidence are committed
  on `feature/gate-c-continuity-mvp`.
- `docs/reviews/` remains untracked and outside Phase 11 scope.

## Phase Handoff

Baseline: Phase 11 action intent/idempotency, tests, local validation, package
build, isolated wheel smoke, and hosted CI are complete on draft PR #2. Phase
12 may begin from this baseline. Phase 12 must add uncertain-outcome
reconciliation, conflict lifecycle, and decisions without changing Gate A
canonical bytes, identifiers, hash preimages, relationship directions,
authorization rules, Gate B kernel semantics, or Phase 10/11 adapter
boundaries.
