# Phase 13 -- Projections, Manifest, and Diff

**Status:** PASS -- Phase 13 complete
**Owner phase:** Phase 13 (Projections, Manifest, and Diff)
**Gate:** C -- Continuity MVP
**Execution date:** 2026-07-14

## Objective

Implement deterministic, source-bound, non-authoritative projections over the
authoritative graph: lineage view, dependency view, conflict view,
latest-revision manifest, graph diff, progress view, and
requirement-traceability-style view.

Phase 13 proves this flow:

```text
load authoritative replay
-> optionally rebuild non-authoritative index
-> evaluate source-bound projection query
-> cite graph revision, source nodes, freshness, information loss, and policy
-> hash canonical stable projection bytes
-> optionally persist disposable projection cache
```

## Permitted Scope

- `src/guerilla/projections/`
- `docs/PROJECTION_SPEC.md`
- Narrow repository-contract allowance for Phase 13 modules.
- Integration tests for projection determinism, manifest, diff, persistence,
  index regeneration, source citation, and adapter non-invocation.
- Status and evidence documentation for Phase 13.

## Prohibited Scope

- Snapshots, resume contexts, CLI workflows, transports, subprocess/container
  isolation, real integrations, archive, backup, production hardening, or Gate
  D behavior.
- Treating projections, manifests, diffs, SQLite indexes, or persisted caches as
  authoritative graph truth.
- Invoking adapters or external actions while generating projections.
- Changing Gate A canonical bytes, identifiers, hashes, relationship
  directions, schemas, registries, or authorization rules.

## Required Sources

1. `AGENTS.md`
2. `docs/ARCHITECTURE_DECISIONS.md`
3. `docs/PROJECTION_SPEC.md`
4. `docs/STATE_BOUNDARY_MODEL.md`
5. `docs/STORAGE_AND_RECOVERY.md`
6. `docs/TEST_MATRIX.md`
7. `docs/CODEX_BUILD_PLAN.md`
8. `docs/PHASE_12_COMPLETION_REPORT.md`
9. `docs/architecture/GUERILLA_CONCEPT_PAPER.md`
10. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md`
11. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md`
12. `docs/architecture/GUERILLA_SNAPSHOT.md`

## Files Expected To Change

- `src/guerilla/projections/`
- `tests/integration/test_phase13_projections_manifest_diff.py`
- `tests/repository/test_repository_contract.py`
- `docs/PROJECTION_SPEC.md`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- `docs/phase_prompts/README.md`
- This prompt

## Invariants

- Projections are always derived and non-authoritative.
- Persisted projections are disposable and regenerable.
- Projection source graph revision and transformation version are mandatory.
- A cache entry from one graph revision cannot satisfy a request for another
  revision.
- Deleting persisted projections and the SQLite index loses no authoritative
  lineage.
- External observations are reported as potentially stale and requiring refresh
  before mutation.
- Projection generation never invokes adapters or external actions.

## Ordered Tasks

1. Implement a projection engine that reads authoritative replay or a rebuilt
   non-authoritative SQLite index.
2. Implement lineage and dependency views with bounded traversal, direction,
   truncation, and source-node citation.
3. Implement conflict view with effective resolution status from `resolved_by`
   lineage.
4. Implement latest eligible artifact manifest with authority, external
   identity, ambiguity, and stale-observation reports.
5. Implement graph diff between revisions without marking immutable records as
   modified.
6. Implement progress and traceability views.
7. Implement disposable persisted projection cache files keyed by source graph
   revision and view type.
8. Add semantic integration tests and repository-contract boundary tests.
9. Regenerate Phase 13 status documentation and completion evidence.

## Required Tests

- Every generated view cites source graph revision, source query, source nodes,
  transformation version, policy version, freshness, information loss, result
  hash, and derived authority.
- Same revision and query regenerate the same hash.
- Later commits do not change explicitly requested old-revision projections.
- Manifest excludes superseded artifact revisions and reports stale external
  observations.
- Resolved conflicts do not appear as effectively open blockers.
- Diff reports added nodes, supersession, resolved conflicts, and refreshed
  observations.
- Deleting persisted projection files and regenerating produces the same hash.
- Deleting the SQLite index causes rebuild from authoritative replay and
  produces the same projection hash.
- Projection code does not import or invoke adapter host paths.

## Failure and Crash Cases

- Missing source node for lineage root.
- Requested revision ahead of replay.
- Left diff revision greater than right diff revision.
- Deleted persisted projection cache.
- Deleted SQLite index.
- Later commits after an old revision projection has been generated.

## Documentation Regeneration

Update Phase 13 status and evidence only. Do not rewrite architecture papers or
change Gate A canonical bytes, identifiers, hashes, relationship directions, or
authorization rules.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| All Phase 13 projection views exist | PASS | `src/guerilla/projections/views.py` |
| Every view is source-bound and derived | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` |
| Manifest preserves authority, ambiguity, and stale-observation facts | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` |
| Diff reports immutable graph changes without modified-record claims | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` |
| Persisted projections are disposable and regenerable | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` |
| Replay and rebuilt index projection results agree | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` |
| Projection generation invokes no adapters | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` |
| Full validation and hosted CI pass | PASS | Split local validation sequence and PR #2 hosted CI |

## Completion Report Format

The Phase 13 completion report must include:

- Phase Result
- Delivered Artifacts
- Validation Evidence: `Command | Exit code | Result | Evidence`
- Exit-Criteria Matrix
- Invariant Audit
- Scope Audit
- Blockers and Contradictions
- Git Summary
- Handoff

## Stop Conditions

Stop before Phase 14 if:

- a projection becomes authoritative;
- projection output is non-deterministic for the same source revision and
  query;
- source graph revision or transformation version is omitted;
- a stale external observation is treated as current;
- projection generation invokes adapters;
- deleting projection cache or index changes lineage truth;
- Phase 13 requires snapshots, resume contexts, CLI workflows, transports, real
  integrations, or Gate D behavior.
