# Phase 13 Completion Report -- Projections, Manifest, and Diff

**Phase Result:** PASS -- Phase 13 complete
**Branch:** `feature/gate-c-continuity-mvp`
**Draft PR:** https://github.com/paragon-ux/Guerilla/pull/2

## Delivered Artifacts

### Repository Controls

- Updated `AGENTS.md`, `README.md`, `README_DEV.md`,
  `docs/CODEX_BUILD_PLAN.md`, `docs/TEST_MATRIX.md`,
  `docs/PROJECTION_SPEC.md`, `docs/phase_prompts/README.md`, and
  `docs/architecture/CURRENT_STATUS_MATRIX.md` for Phase 13 status.
- Updated `docs/architecture/README.md` with the refreshed status-matrix
  digest.
- Added `docs/phase_prompts/PHASE_13_PROJECTIONS_MANIFEST_DIFF.md`.

### Projection Runtime

- Added `src/guerilla/projections/views.py` with deterministic derived views
  for lineage, dependency, conflict, manifest, diff, progress, and
  traceability.
- Updated `src/guerilla/projections/__init__.py` exports.
- Added disposable persisted projection cache output under
  `.guerilla/projections/<revision>/<view>/`.

### Tests

- Added `tests/integration/test_phase13_projections_manifest_diff.py`.
- Updated `tests/repository/test_repository_contract.py` to permit Phase 13
  projection modules while continuing to block Phase 14+ runtime modules.

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
| Split implemented test suites | 0 | Passed, 154 tests including Phase 13 projection tests | Local terminal output |
| `uv build` | 0 | Built sdist and wheel | `dist/guerilla-0.0.0.tar.gz`, `dist/guerilla-0.0.0-py3-none-any.whl` |
| Archive cache inspection | 0 | No `.uv-cache`, `.tmp`, or `pip-cache` entries in sdist or wheel | Local terminal output |
| Isolated wheel smoke | 0 | `pip --no-deps` install, import, `--version`, `--help`, and `version --json` passed from temp venv | `.tmp/guerilla-wheel-smoke-*` |
| PR #2 hosted CI | 0 | Python 3.11 and 3.12 validation passed | https://github.com/paragon-ux/Guerilla/pull/2/checks |

## Exit-Criteria Matrix

| Criterion | Status | Evidence | Notes |
|---|---|---|---|
| All Phase 13 projection views exist | PASS | `src/guerilla/projections/views.py` | Lineage, dependency, conflict, manifest, diff, progress, and traceability are implemented. |
| Every view is source-bound and derived | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` | Tests assert source revision, source query, source nodes, freshness, information loss, transformation version, policy version, result hash, and derived authority. |
| Manifest preserves authority, ambiguity, and stale-observation facts | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` | Latest non-superseded artifact revisions retain authority and external identity; stale observations are reported. |
| Diff reports immutable graph changes without modified-record claims | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` | Diff reports added records, supersession, resolved conflicts, and refreshed observations. |
| Persisted projections are disposable and regenerable | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` | Deleting `.guerilla/projections/` and regenerating preserves the result hash. |
| Replay and rebuilt index projection results agree | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` | Deleted SQLite index rebuilds from authoritative replay before indexed projection generation. |
| Projection generation invokes no adapters | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` | Projection engine source is checked for adapter host/invocation references. |
| Full validation and hosted CI pass | PASS | Split local validation; PR #2 hosted CI | Phase 14 may begin from this passed baseline. |

## Invariant Audit

- Projection results are marked `derived_non_authoritative`.
- Every projection cites source graph revision, commit hash, query, source
  nodes, transformation version, policy version, freshness, information loss,
  and result hash.
- Persisted projection files are cache artifacts and can be deleted without
  losing authoritative lineage.
- Replay-backed and rebuilt-index-backed manifest generation produce identical
  result hashes.
- Old-revision projection hashes remain stable after later commits.
- Conflict view derives effective resolved status from `resolved_by` lineage
  without mutating conflict records.
- Projection code does not invoke adapters or external actions.

## Scope Audit

No prohibited runtime behavior was introduced. Phase 13 did not implement
snapshots, resume contexts, CLI workflows, transports, subprocess isolation,
real integrations, Gate D behavior, or payload execution. Gate A canonical
bytes, identifiers, hashes, schemas, registries, relationship directions, and
authorization rules were not changed.

## Blockers and Contradictions

None.

## Git Summary

- Phase 13 projection/manifest/diff implementation and evidence are committed
  on `feature/gate-c-continuity-mvp`.
- `docs/reviews/` remains untracked and outside Phase 13 scope.

## Phase Handoff

Baseline: Phase 13 projection generation, tests, local validation, package
build, isolated wheel smoke, and hosted CI are complete on draft PR #2.
Phase 14 may begin from this baseline. Phase 14 must add snapshots,
snapshot verification, and resume contexts without changing Gate A/B contracts,
making projections authoritative, invoking adapters during replay/projection
generation, or starting Gate D work.
