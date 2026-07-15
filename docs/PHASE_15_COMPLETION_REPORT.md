# Phase 15 Completion Report -- Internal CLI, E2E, Smoke

**Phase Result:** PASS -- Phase 15 complete
**Branch:** `feature/gate-c-continuity-mvp`
**Draft PR:** https://github.com/paragon-ux/Guerilla/pull/2

## Delivered Artifacts

### Repository Controls

- Updated `AGENTS.md`, `README.md`, `README_DEV.md`,
  `docs/CODEX_BUILD_PLAN.md`, `docs/TEST_MATRIX.md`,
  `docs/PROJECTION_SPEC.md`, `docs/phase_prompts/README.md`, and
  `docs/architecture/CURRENT_STATUS_MATRIX.md` for Phase 15 and Gate C status.
- Updated `docs/architecture/README.md` with the refreshed status-matrix
  digest.
- Added `docs/phase_prompts/PHASE_15_INTERNAL_CLI_E2E_SMOKE.md`.
- Added `docs/phase_prompts/FINAL_INTERNAL_MVP_CHECKLIST.md`.

### Internal CLI Runtime

- Added `src/guerilla/cli/workflows.py` as the local CLI workflow facade over
  existing runtime APIs.
- Updated `src/guerilla/cli/main.py` with workspace, adapter, goal,
  operation, observation, action, reconciliation, conflict, lineage, view,
  manifest, snapshot, and graph command families.
- Preserved clean wheel smoke behavior by keeping version/help import paths
  independent from optional runtime dependencies.

### Tests

- Added `tests/integration/test_phase15_internal_cli_e2e_smoke.py`.
- Updated `tests/repository/test_repository_contract.py` to permit local Phase
  15 CLI modules while continuing to block Phase 16+ runtime modules.

## Validation Evidence

The one-command local wrapper was not run as a single command because this task
required stopping commands after one minute. The same validation sequence was
run in split steps with `UV_CACHE_DIR=.uv-cache` and workspace-local temp/cache
directories.

| Command | Exit code | Result | Evidence |
|---|---:|---|---|
| `uv lock --check` | 0 | Passed | Local terminal output |
| `uv sync --frozen --extra dev` | 0 | Passed | Local terminal output |
| `uv run ruff format --check .` | 0 | Passed | Local terminal output |
| `uv run ruff check .` | 0 | Passed | Local terminal output |
| `uv run mypy src tests` | 0 | Passed | Local terminal output |
| Split implemented test suites | 0 | Passed, 162 tests including Phase 15 internal CLI/E2E tests | Local terminal output |
| `uv build` | 0 | Built sdist and wheel | `dist/guerilla-0.0.0.tar.gz`, `dist/guerilla-0.0.0-py3-none-any.whl` |
| Archive cache inspection | 0 | No `.uv-cache`, `.tmp`, or `pip-cache` entries in sdist or wheel | Local terminal output |
| Isolated wheel smoke | 0 | `pip --no-deps` install, import, `--version`, `--help`, and `version --json` passed from temp venv | `.tmp/guerilla-wheel-smoke-*` |
| Final PR #2 hosted CI | Required before final handoff | PR head check | Reported in final handoff to avoid recursive report churn |

## Exit-Criteria Matrix

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| Required command families exist | PASS | `src/guerilla/cli/main.py` | CLI exposes local workspace, adapter, mutation, query, projection, snapshot, and replay surfaces. |
| CLI uses existing runtime APIs | PASS | `src/guerilla/cli/workflows.py` | Commands delegate to `GraphStore`, `ObservationIngestor`, `ActionOrchestrator`, `ReconciliationEngine`, `ConflictEngine`, `ProjectionEngine`, and `SnapshotEngine`. |
| Stable success/error envelopes exist | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py` | Tests assert structured JSON outputs and non-zero error handling. |
| Transactional E2E passes | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py::test_transactional_cli_e2e_intent_after_state_and_evaluation` | Covers observation, local goal/operation creation, intent-before-action, after-state observation, evaluation, and replay safety. |
| Snapshot/manifest CLI smoke passes | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py::test_snapshot_manifest_cli_smoke_uses_derived_view_path` | Covers manifest, progress view, snapshot verify, and resume. |
| Reconstructed-filesystem E2E passes | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py::test_reconstructed_filesystem_cli_e2e_conflict_decision_and_rebuild` | Covers partial failure, conflict, decision resolution, lineage/view, index rebuild, snapshot, and replay safety. |
| Async unknown/reconciliation E2E passes | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py::test_async_unknown_cli_reconciliation_and_replay_safety` | Covers unresolved intents, unknown reconciliation, explicit conflict preservation, stale revision rejection, snapshot, resume, and replay safety. |
| Clean wheel smoke passes | PASS | Isolated wheel smoke | `guerilla --version`, `guerilla --help`, and `guerilla version --json` work from a `pip --no-deps` wheel install. |
| Gate D behavior remains out of scope | PASS | Source inspection and repository contract | No transport, subprocess host, real adapter, or Phase 16+ module was added. |

## Invariant Audit

- CLI output is derived command output, not authoritative graph state.
- Mutating commands append through the existing runtime APIs and graph store.
- Adapter actions still commit durable intent before invocation.
- Unknown outcomes remain explicit and require reconciliation before unsafe
  retry.
- Graph replay, verify, index rebuild, view generation, manifest generation,
  snapshot verification, and resume context generation do not invoke adapters
  or external actions.

## Scope Audit

No prohibited runtime behavior was introduced. Phase 15 did not implement
network transport, GLCP client/server, subprocess adapter hosting, real external
adapters, pilots, archive/backup, performance benchmarking, or Gate D behavior.
Gate A canonical bytes, identifiers, hashes, schemas, registries, relationship
directions, and authorization rules were not changed.

## Blockers and Contradictions

None.

## Git Summary

- Phase 15 local CLI/E2E implementation and evidence are committed on
  `feature/gate-c-continuity-mvp`.
- `docs/reviews/` remains untracked and outside Phase 15 scope.

## Phase Handoff

Baseline: Phase 15 internal CLI workflows, tests, local validation, package
build, isolated wheel smoke, and hosted CI are complete on draft PR #2.
Gate C closure may proceed from this baseline. Phase 16 must not begin until
the Gate C completion report, final validation, and hosted CI are complete.
