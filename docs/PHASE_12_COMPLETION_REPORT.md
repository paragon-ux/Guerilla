# Phase 12 Completion Report -- Reconciliation, Conflicts, and Decisions

**Phase Result:** PASS -- Phase 12 complete
**Branch:** `feature/gate-c-continuity-mvp`
**Draft PR:** https://github.com/paragon-ux/Guerilla/pull/2

## Delivered Artifacts

### Repository Controls

- Updated `AGENTS.md`, `README.md`, `README_DEV.md`,
  `docs/CODEX_BUILD_PLAN.md`, `docs/TEST_MATRIX.md`,
  `docs/ADAPTER_CONTRACT.md`, `docs/phase_prompts/README.md`, and
  `docs/architecture/CURRENT_STATUS_MATRIX.md` for Phase 12 status.
- Updated `docs/architecture/README.md` with the refreshed status-matrix
  digest.
- Added `docs/phase_prompts/PHASE_12_RECONCILIATION_CONFLICTS.md`.

### Reconciliation and Conflict Runtime

- Added `src/guerilla/reconciliation/engine.py` with typed reconciliation
  requests/results, authoritative Phase 11 evidence loading, adapter
  `reconcile` invocation through the Phase 9 host, reconciliation event
  commits, missing-lineage recovery, unknown/unsupported outcome conflicts,
  duplicate-attempt detection, and optional after-state observation.
- Added `src/guerilla/conflicts/engine.py` with evidence-backed conflict
  records, append-only decisions, `resolved_by` lineage, and optional
  continuation operation records.
- Updated `src/guerilla/reconciliation/__init__.py` and
  `src/guerilla/conflicts/__init__.py` exports.

### Tests

- Added `tests/integration/test_phase12_reconciliation_conflicts.py`.
- Updated `tests/repository/test_repository_contract.py` to permit Phase 12
  reconciliation/conflict modules while continuing to block Phase 13+ runtime
  modules.

## Validation Evidence

The one-command local wrapper was not run as a single command because this task
required stopping commands after one minute. The same validation sequence was
run in split steps with `UV_CACHE_DIR=.uv-cache` and workspace-local temp/cache
directories.

| Command | Exit code | Result | Evidence |
|---|---:|---|---|
| `uv lock --check` | 0 | Passed | Local terminal output |
| `uv sync --frozen --extra dev` | 0 | Passed | Local terminal output |
| `uv run --frozen --extra dev ruff format --check .` | 0 | Passed, 69 files formatted | Local terminal output |
| `uv run --frozen --extra dev ruff check .` | 0 | Passed | Local terminal output |
| `uv run --frozen --extra dev mypy src tests` | 0 | Passed, 69 source files | Local terminal output |
| Split implemented test suites | 0 | Passed, 151 tests | Local terminal output |
| `uv build` | 0 | Built sdist and wheel | `dist/guerilla-0.0.0.tar.gz`, `dist/guerilla-0.0.0-py3-none-any.whl` |
| Archive cache inspection | 0 | No `.uv-cache`, `.tmp`, or `pip-cache` entries in sdist or wheel | Local terminal output |
| Stale wheel-smoke process cleanup | 0 | Stopped only processes whose executable path matched `guerilla-wheel-smoke-*`; none unrelated touched | Local terminal output |
| Isolated wheel smoke | 0 | `pip --no-deps` install, import, `--version`, `--help`, and `version --json` passed from temp venv | `.tmp/guerilla-wheel-smoke-*` |
| PR #2 hosted CI | 0 | Python 3.11 and 3.12 validation passed | https://github.com/paragon-ux/Guerilla/pull/2/checks |

Note: fresh stdlib venv creation exceeded the one-minute command cap and was
stopped by the harness, but the environment completed on disk and the isolated
wheel install/import/CLI smoke checks passed in separate capped commands.

## Exit-Criteria Matrix

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| Every interrupted action is classified or remains explicitly unknown | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` | Unknown and unsupported histories produce explicit conflicts. |
| Retry cannot silently duplicate mutation | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` | Recovered results become graph-backed idempotency truth. |
| Missing lineage is repaired without history rewrite | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` | Original intent/invocation records remain immutable; recovered result is appended. |
| Conflicts are evidence backed | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` | Conflict metadata includes type, subject, evidence, authority, severity, status, detection time, policy, required resolution, limitations, and details. |
| Decisions/resolutions are append-only | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` | Decisions append `resolved_by` lineage; original conflicts remain unchanged. |
| Outcome layers remain distinct | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` | Reconciliation event, recovered result, after-state observation, conflict, decision, and continuation operation are separate records. |
| All systems share one reconciliation engine | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` | Transactional, filesystem, and asynchronous synthetic systems use `ReconciliationEngine`. |
| Full validation and hosted CI pass | PASS | Split local validation; PR #2 hosted CI | Phase 13 may begin from this passed baseline. |

## Invariant Audit

- Reconciliation results append new event records and never rewrite original
  intent, invocation, result, conflict, or decision records.
- Missing-lineage recovery preserves original intent and invocation records and
  records recovered action-result evidence separately.
- Recovered result records do not fabricate the original result timestamp.
- Unknown outcomes remain explicit when evidence is insufficient.
- Conflict types remain registry-compatible; Phase 12-specific reasons are
  stored in metadata.
- Decisions and resolution lineage are append-only.
- Replay and index rebuild do not invoke adapters or external actions.

## External-State Audit

| Synthetic system | Reconciliation evidence | Authority behavior |
|---|---|---|
| Transactional revisioned service | Missing accepted result is recovered; stale external revision becomes an explicit conflict | Guerilla records reconciliation lineage and does not own the service transaction model. |
| Reconstructed filesystem | Missing filesystem action result is recovered without rewriting intent or invocation records | Guerilla records bounded reconciliation facts and does not own filesystem semantics. |
| Asynchronous unknown-outcome service | Completed async operation can be confirmed; unknowable history remains explicit `external_outcome_unknown` conflict | Guerilla does not assume success or retry unsafe unknown outcomes. |

## Failure and Recovery Evidence

- Interruption after adapter completion but before result commit is reconciled
  without duplicate mutation.
- Unsupported reconciliation capability creates an explicit incomplete-lineage
  conflict and does not call adapter `reconcile`.
- Unknown adapter history creates an explicit external-outcome conflict.
- Same request under different idempotency keys creates an explicit
  idempotency conflict.
- Stale external revision creates an explicit stale-revision conflict.
- Decisions resolve conflicts through append-only `resolved_by` lineage and can
  create continuation operation records.

## Scope Audit

No prohibited runtime behavior was introduced. Phase 12 did not implement
projections, manifests, diffs, snapshots, CLI workflows, transports,
subprocess isolation, real integrations, Gate D behavior, or payload execution.

## Blockers and Contradictions

None.

## Git Summary

- Phase 11 action intent/idempotency implementation and evidence are committed
  in `682561b`.
- Phase 12 reconciliation/conflict implementation and evidence are committed on
  `feature/gate-c-continuity-mvp`.
- `docs/reviews/` remains untracked and outside Phase 12 scope.

## Phase Handoff

Baseline: Phase 12 reconciliation/conflict records, tests, local validation,
package build, isolated wheel smoke, and hosted CI are complete on draft PR #2.
Phase 13 may begin from this baseline. Phase 13 must add projections,
manifests, and diffs without changing Gate A canonical bytes, identifiers, hash
preimages, relationship directions, authorization rules, Gate B kernel
semantics, or Phase 9-12 adapter/reconciliation boundaries.
