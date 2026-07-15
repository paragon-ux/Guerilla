# Phase 14 Completion Report -- Snapshots and Resume Context

**Phase Result:** PASS -- Phase 14 complete
**Branch:** `feature/gate-c-continuity-mvp`
**Draft PR:** https://github.com/paragon-ux/Guerilla/pull/2

## Delivered Artifacts

### Repository Controls

- Updated `AGENTS.md`, `README.md`, `README_DEV.md`,
  `docs/CODEX_BUILD_PLAN.md`, `docs/TEST_MATRIX.md`,
  `docs/PROJECTION_SPEC.md`, `docs/phase_prompts/README.md`, and
  `docs/architecture/CURRENT_STATUS_MATRIX.md` for Phase 14 status.
- Updated `docs/architecture/README.md` with the refreshed status-matrix
  digest.
- Added `docs/phase_prompts/PHASE_14_SNAPSHOT_RESUME.md`.

### Snapshot and Resume Runtime

- Added `src/guerilla/projections/snapshots.py` with authoritative snapshot
  record creation, `captured_by` source edges, derived materialized summaries,
  snapshot verification, and bounded resume-context generation.
- Updated `src/guerilla/projections/__init__.py` exports.

### Tests

- Added `tests/integration/test_phase14_snapshot_resume.py`.
- Updated `tests/repository/test_repository_contract.py` to mark Phase 14
  projection/snapshot modules as allowed while continuing to block Phase 15+
  runtime modules.

## Validation Evidence

The one-command local wrapper was not run as a single command because this task
required stopping commands after one minute. The same validation sequence was
run in split steps with `UV_CACHE_DIR=.uv-cache` and workspace-local temp/cache
directories.

| Command | Exit code | Result | Evidence |
|---|---:|---|---|
| `uv lock --check` | 0 | Passed | Local terminal output |
| `uv sync --frozen --extra dev` | 0 | Passed | Local terminal output |
| `uv run --frozen --extra dev ruff format --check .` | 0 | Passed | Local terminal output |
| `uv run --frozen --extra dev ruff check .` | 0 | Passed | Local terminal output |
| `uv run --frozen --extra dev mypy src tests` | 0 | Passed | Local terminal output |
| Split implemented test suites | 0 | Passed, 158 tests including Phase 14 snapshot/resume tests | Local terminal output |
| `uv build` | 0 | Built sdist and wheel | `dist/guerilla-0.0.0.tar.gz`, `dist/guerilla-0.0.0-py3-none-any.whl` |
| Archive cache inspection | 0 | No `.uv-cache`, `.tmp`, or `pip-cache` entries in sdist or wheel | Local terminal output |
| Isolated wheel smoke | 0 | `pip --no-deps` install, import, `--version`, `--help`, and `version --json` passed from temp venv | `.tmp/guerilla-wheel-smoke-*` |
| PR #2 hosted CI | 0 | Python 3.11 and 3.12 validation passed | https://github.com/paragon-ux/Guerilla/pull/2/checks |

## Exit-Criteria Matrix

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| Snapshot records cite verified committed boundaries | PASS | `tests/integration/test_phase14_snapshot_resume.py` | Snapshot metadata pins source revision, source commit, source nodes, source query, policy, transformation version, summary hash, actor, and authority. |
| Summaries remain derived | PASS | `src/guerilla/projections/snapshots.py` | Materialized summaries live under `.guerilla/snapshots/` and are regenerated from authoritative replay. |
| Missing/corrupt summaries do not destroy authoritative continuity | PASS | `tests/integration/test_phase14_snapshot_resume.py` | Verification returns warnings but still validates authoritative snapshot records from replay. |
| Resume distinguishes authoritative, derived, stale, and unknown data | PASS | `tests/integration/test_phase14_snapshot_resume.py` | Resume context separates facts, derived summaries, stale observations, unknown outcomes, conflicts, operations, refreshes, and omitted information. |
| Pending reconciliation and refresh requirements are explicit | PASS | `tests/integration/test_phase14_snapshot_resume.py` | Pending action attempts, outcome-unknown results, and stale observations are surfaced. |
| Verification works without adapters/external systems | PASS | `tests/integration/test_phase14_snapshot_resume.py` | Tests inspect source for adapter invocation and use hand-built graph records. |
| Regeneration is deterministic | PASS | `tests/integration/test_phase14_snapshot_resume.py` | Old-revision resume remains stable after later commits and deleted indexes/projections. |
| Full validation and hosted CI pass | PASS | Split local validation; PR #2 hosted CI | Phase 15 may begin from this passed baseline. |

## Invariant Audit

- Snapshot nodes are authoritative evidence; materialized summaries and resume
  contexts are derived.
- `captured_by` edges use included source to snapshot direction.
- Summary hashes are canonical and deterministic for the same source revision,
  snapshot node, created time, transformation version, policy, and source data.
- Missing or corrupt materialized summaries do not replace or damage
  authoritative graph continuity.
- Resume contexts report stale observations and pending/unknown actions without
  performing refresh, reconciliation, retry, or next-operation execution.
- Snapshot/resume verification does not invoke adapters.

## Scope Audit

No prohibited runtime behavior was introduced. Phase 14 did not implement CLI
workflows, transports, subprocess isolation, real integrations, Gate D behavior,
performance benchmarking, archive/backup, or payload execution. Gate A
canonical bytes, identifiers, hashes, schemas, registries, relationship
directions, and authorization rules were not changed.

## Blockers and Contradictions

None.

## Git Summary

- Phase 14 snapshot/resume implementation and evidence are committed on
  `feature/gate-c-continuity-mvp`.
- `docs/reviews/` remains untracked and outside Phase 14 scope.

## Phase Handoff

Baseline: Phase 14 snapshot/resume generation, tests, local validation,
package build, isolated wheel smoke, and hosted CI are complete on draft PR #2.
Phase 15 may begin from this baseline. Phase 15 must add internal CLI, E2E,
and smoke workflows without adding transport bindings, subprocess isolation,
real integrations, or Gate D behavior.
