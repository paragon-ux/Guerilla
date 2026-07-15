# Phase 14 -- Snapshots and Resume Context

**Status:** PASS -- Phase 14 complete
**Owner phase:** Phase 14 (Snapshots and Resume Context)
**Gate:** C -- Continuity MVP
**Execution date:** 2026-07-14

## Objective

Implement verified continuity boundaries that allow a later process or agent to
resume from authoritative lineage instead of from an ungrounded summary.

Phase 14 proves this flow:

```text
select verified graph revision
-> verify source commit
-> compute heads and continuity set
-> generate derived summary
-> hash summary
-> commit snapshot node and captured_by edges
-> persist optional derived payload
-> verify and regenerate resume context without adapters
```

## Permitted Scope

- `src/guerilla/projections/snapshots.py`
- `docs/PROJECTION_SPEC.md`
- Integration tests for snapshot creation, verification, materialized summary
  recovery, source commit mismatch, stale observations, pending/unknown actions,
  old-revision resume, deleted indexes/projections, and adapter non-invocation.
- Status and evidence documentation for Phase 14.

## Prohibited Scope

- CLI workflows, transports, subprocess/container isolation, real integrations,
  archive, backup, production hardening, performance benchmarking, or Gate D
  behavior.
- Treating materialized snapshot summaries or resume contexts as authoritative
  graph truth.
- Invoking adapters, reconciling actions, refreshing observations, or executing
  next operations while creating/verifying snapshots or resume contexts.
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
8. `docs/PHASE_13_COMPLETION_REPORT.md`
9. `docs/phase_prompts/PHASE_13_PROJECTIONS_MANIFEST_DIFF.md`
10. `docs/architecture/GUERILLA_CONCEPT_PAPER.md`
11. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md`
12. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md`
13. `docs/architecture/GUERILLA_SNAPSHOT.md`

## Files Expected To Change

- `src/guerilla/projections/snapshots.py`
- `src/guerilla/projections/__init__.py`
- `tests/integration/test_phase14_snapshot_resume.py`
- `docs/PROJECTION_SPEC.md`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- `docs/phase_prompts/README.md`
- This prompt

## Invariants

- Snapshot nodes are authoritative evidence that a graph boundary was captured.
- Materialized snapshot summaries and resume contexts are derived and
  non-authoritative.
- Snapshot records cite source graph revision, source commit, source query,
  source nodes, transformation version, policy version, summary hash,
  information loss, freshness requirements, created time, actor, and authority.
- `captured_by` edges follow the Gate A direction: included source to snapshot.
- Missing or corrupt materialized summaries do not destroy authoritative
  continuity; verification regenerates from graph replay.
- Resume contexts distinguish authoritative facts, derived summaries, stale
  observations, unknown outcomes, pending reconciliation, required refreshes,
  unresolved conflicts, and omitted information.
- Resume context generation never executes a next operation.

## Required Tests

- Clean snapshot creation commits one snapshot node and `captured_by` edges for
  included source nodes.
- Verification checks source revision, source commit, source nodes, summary
  hash, transformation/policy versions, and captured edges.
- Missing materialized summary verifies from authoritative graph replay with a
  warning.
- Corrupt materialized summary verifies from authoritative graph replay with a
  warning.
- Resume context separates authoritative facts, derived summaries, stale
  observations, unknown outcomes, open goals, eligible operations, blocked
  operations, unresolved conflicts, pending reconciliation, refresh
  requirements, artifact revisions, and omitted information.
- Old-revision snapshots remain stable after later commits.
- Deleted SQLite index and projection cache do not prevent verification or
  resume regeneration.
- Source commit mismatch is rejected.
- Snapshot/resume code invokes no adapters and executes no actions.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Snapshot records cite verified committed boundaries | PASS | `tests/integration/test_phase14_snapshot_resume.py` |
| Summaries remain derived | PASS | `src/guerilla/projections/snapshots.py` |
| Missing/corrupt summaries do not destroy authoritative continuity | PASS | `tests/integration/test_phase14_snapshot_resume.py` |
| Resume distinguishes authoritative, derived, stale, and unknown data | PASS | `tests/integration/test_phase14_snapshot_resume.py` |
| Pending reconciliation and refresh requirements are explicit | PASS | `tests/integration/test_phase14_snapshot_resume.py` |
| Verification works without adapters/external systems | PASS | `tests/integration/test_phase14_snapshot_resume.py` |
| Regeneration is deterministic | PASS | `tests/integration/test_phase14_snapshot_resume.py` |
| Full validation and hosted CI pass | PASS | Split local validation sequence and PR #2 hosted CI |

## Stop Conditions

Stop before Phase 15 if:

- a materialized summary or resume context becomes authoritative;
- snapshot verification requires adapters or external systems;
- resume context generation executes an operation, observation, reconciliation,
  or refresh;
- missing/corrupt materialized summaries prevent authoritative verification;
- source commit mismatch is accepted;
- Phase 14 requires CLI workflows, transports, real integrations, or Gate D
  behavior.
