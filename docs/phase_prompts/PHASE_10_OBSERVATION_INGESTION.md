# Phase 10 -- Observation Ingestion

**Status:** LOCAL PASS -- Phase 10 implementation and local validation complete; hosted CI pending
**Owner phase:** Phase 10 (Observation Ingestion)
**Gate:** C -- Continuity MVP
**Execution date:** 2026-07-14

## Objective

Implement observation-first ingestion that records bounded external facts from
trusted synthetic adapters into the authoritative Guerilla graph without
transferring application-state authority to Guerilla.

Phase 10 proves that all three Phase 9 synthetic systems can use one validated
observe-only flow:

```text
validated observation request
-> authorization check
-> state-boundary check
-> adapter observe
-> result validation
-> normalization into graph records
-> one authoritative graph transaction
-> derived response
```

The adapter never commits directly to the graph.

## Permitted Scope

- `src/guerilla/observability/`
- Narrow exports from `src/guerilla/adapters/` or `src/guerilla/graph/` only if
  needed by the observation ingestion API.
- `tests/integration/` and `tests/adapters/` coverage for observation ingestion.
- `tests/fixtures/adapters/` additions for observation scenarios.
- Documentation/status updates for Phase 10 evidence.

## Prohibited Scope

- External action orchestration or committed intent-before-action.
- Adapter `act`, `reconcile`, or retry orchestration from the observation path.
- Graph-backed idempotency, reconciliation engine, conflict decision engine,
  projections, snapshots, CLI workflows, transports, subprocess isolation, real
  integrations, pilots, archive, backup, or production hardening.
- Product-specific graph-core branches keyed by synthetic adapter type.
- Treating adapter result data, projections, index rows, or derived response
  objects as authoritative graph state.

## Required Sources

1. `AGENTS.md`
2. `docs/PHASE_09_COMPLETION_REPORT.md`
3. `docs/ARCHITECTURE_DECISIONS.md`
4. `docs/MVP_SCOPE.md`
5. `docs/DATA_MODEL.md`
6. `docs/GRAPH_RECORD_FORMAT.md`
7. `docs/GLCP_CORE_SPEC.md`
8. `docs/ADAPTER_CONTRACT.md`
9. `docs/STATE_BOUNDARY_MODEL.md`
10. `docs/STORAGE_AND_RECOVERY.md`
11. `docs/SECURITY_MODEL.md`
12. `docs/ERROR_REGISTRY.md`
13. `docs/TEST_MATRIX.md`
14. `docs/CODEX_BUILD_PLAN.md`
15. `docs/phase_prompts/PHASE_09_ADAPTER_SDK_SYNTHETIC_SYSTEMS.md`
16. `schemas/node.schema.json`
17. `schemas/edge.schema.json`
18. `schemas/adapter_observe.schema.json`
19. `schemas/external_identity.schema.json`
20. `schemas/payload_ref.schema.json`
21. `registries/node_types.json`
22. `registries/relationship_types.json`

## Files Expected To Change

- New Phase 10 ingestion modules under `src/guerilla/observability/`
- `src/guerilla/observability/__init__.py`
- New or updated tests under `tests/integration/` and `tests/adapters/`
- Optional fixture additions under `tests/fixtures/adapters/`
- `docs/ADAPTER_CONTRACT.md`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- `docs/phase_prompts/README.md`
- This prompt

## Invariants

- One logically authoritative Guerilla graph exists per workspace.
- Every graph mutation uses the Gate B append transaction path.
- External systems retain application-state authority.
- Observation records preserve external identity, external revision, provenance,
  payload retention/redaction metadata, freshness, consistency limitations,
  correlation, causation, local receipt time, effective time, and graph commit
  time.
- Observation ingestion invokes only `observe`.
- Replay never invokes adapters or external actions.
- Stale, conflicting, out-of-order, unknown, absent revision, rename, deletion,
  identity reuse, and incomplete lineage cases remain explicit.
- All synthetic systems share one ingestion implementation.

## Ordered Tasks

1. Define typed observation ingestion requests, responses, duplicate/conflict
   classifications, and normalized observation metadata.
2. Implement one observation ingestor that validates request data, invokes the
   Phase 9 host through `observe`, validates adapter results, normalizes records,
   and appends exactly one graph transaction.
3. Create graph records for bounded observation operation nodes, observation
   event nodes, artifact/external-state revision nodes, and evidence/causal
   edges using existing node and relationship types.
4. Preserve exact external revision tokens, external identity tuples, adapter
   version, boundary, provenance, payload retention/redaction metadata,
   correlation/causation IDs, effective time, receipt time, commit time,
   freshness, and consistency limitations in graph metadata.
5. Implement deterministic duplicate and ordering classification from replayed
   authoritative graph state, not from derived indexes.
6. Add tests that run transactional, reconstructed filesystem, and asynchronous
   synthetic systems through the same ingestion implementation.
7. Add failure tests for unauthorized observation, boundary escape, adapter
   exception, malformed result, missing provenance, missing revision, retained
   payload, metadata-only payload, redaction, replay safety, and index rebuild.
8. Regenerate Phase 10 status documentation and completion evidence.

## Required Tests

- First observation creates one graph transaction with operation, event,
  artifact/external revision, and edges.
- Repeated identical observation is deterministic and does not create a
  conflicting artifact revision.
- Duplicate event correlation is deterministic.
- Same external revision with changed content is explicit.
- Stale, out-of-order, unknown ordering, and absent revision cases are explicit.
- Rename, deletion, and identity reuse are represented without changing external
  authority.
- Missing provenance is rejected.
- Unauthorized observation and state-boundary escape happen before adapter
  invocation.
- Adapter exception and malformed result do not append a graph transaction.
- Retained payload, metadata-only payload, and redaction metadata are preserved.
- Replay performs no adapter calls.
- Index loss and rebuild preserve observation truth.
- All three synthetic systems use the same ingestion implementation.

## Failure and Crash Cases

- Authorization denied.
- Boundary escape.
- Adapter raises an exception.
- Adapter result is malformed or lacks required observation provenance.
- Append transaction fails before commit.
- Duplicate or conflicting external observation appears after restart.
- Index is deleted and rebuilt from authoritative graph records.

## Documentation Regeneration

Update documentation only for Phase 10 status and evidence. Do not rewrite the
imported architecture papers. Corrections to frozen architecture decisions
require reopening the appropriate gate.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| All observations enter one validated flow | PASS | `tests/integration/test_phase10_observation_ingestion.py` |
| External authority and revisions are preserved | PASS | `tests/integration/test_phase10_observation_ingestion.py` |
| Duplicate behavior is deterministic | PASS | `tests/integration/test_phase10_observation_ingestion.py` |
| Stale/conflicting/out-of-order/unknown conditions remain explicit | PASS | `tests/integration/test_phase10_observation_ingestion.py` |
| Observation never mutates external state | PASS | `tests/integration/test_phase10_observation_ingestion.py` |
| Replay performs no adapter calls | PASS | `tests/integration/test_phase10_observation_ingestion.py` |
| All systems use the same ingestion implementation | PASS | `tests/integration/test_phase10_observation_ingestion.py` |
| Full validation and hosted CI pass | LOCAL PASS / CI PENDING | local validation sequence and PR checks |

## Completion Report Format

The Phase 10 completion report must include:

- Phase Result
- Delivered Artifacts
- Validation Evidence: `Command | Exit code | Result | Evidence`
- Exit-Criteria Matrix
- Invariant Audit
- External-State Audit for all three synthetic systems
- Failure and Recovery Evidence
- Scope Audit
- Blockers and Contradictions
- Git Summary
- Handoff

## Stop Conditions

Stop before Phase 11 if:

- observation ingestion transfers application-state authority to Guerilla;
- any observation path invokes `act`, creates action intent, retries, or infers
  external acceptance;
- adapter output bypasses validation;
- adapter code commits directly to the graph;
- duplicate/conflict truth depends only on SQLite or another derived index;
- replay invokes adapters or external actions;
- a real integration, transport, subprocess host, projection, snapshot, or
  reconciliation engine is needed;
- all three synthetic systems cannot share one ingestion implementation.
