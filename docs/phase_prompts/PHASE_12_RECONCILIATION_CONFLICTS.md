# Phase 12 -- Reconciliation, Conflicts, and Decisions

**Status:** PASS -- Phase 12 complete
**Owner phase:** Phase 12 (Reconciliation, Conflicts, and Decisions)
**Gate:** C -- Continuity MVP
**Execution date:** 2026-07-14

## Objective

Implement uncertain-outcome recovery, duplicate detection, explicit conflicts,
evidence-backed decisions, resolution lineage, and continuation operations.

Phase 12 proves this flow:

```text
load committed evidence
-> authorize reconciliation
-> validate adapter capability
-> invoke reconcile
-> validate result
-> classify outcome
-> commit reconciliation event
-> create result, conflict, or continuation records
```

## Permitted Scope

- `src/guerilla/reconciliation/`
- `src/guerilla/conflicts/`
- Narrow repository-contract allowance for Phase 12 modules.
- Integration tests for reconciliation, conflicts, decisions, replay, and
  idempotency recovery behavior.
- Status and evidence documentation for Phase 12.

## Prohibited Scope

- Projections, manifests, diffs, snapshots, resume contexts, CLI workflows,
  transports, subprocess/container isolation, real integrations, archive,
  backup, production hardening, or Gate D behavior.
- Rewriting or deleting original intent, invocation, result, conflict, or
  decision records.
- Retrying an unknown external action as a substitute for reconciliation.
- Treating adapter-native history, SQLite indexes, projections, or runtime
  memory as authoritative graph truth.

## Required Sources

1. `AGENTS.md`
2. `docs/PHASE_11_COMPLETION_REPORT.md`
3. `docs/ARCHITECTURE_DECISIONS.md`
4. `docs/ADAPTER_CONTRACT.md`
5. `docs/STATE_BOUNDARY_MODEL.md`
6. `docs/STORAGE_AND_RECOVERY.md`
7. `docs/TEST_MATRIX.md`
8. `docs/CODEX_BUILD_PLAN.md`
9. `docs/phase_prompts/PHASE_11_ACTION_INTENT_IDEMPOTENCY.md`
10. `schemas/adapter_reconcile.schema.json`
11. `schemas/conflict.schema.json`
12. `registries/conflict_types.json`
13. `registries/relationship_types.json`

## Files Expected To Change

- `src/guerilla/reconciliation/`
- `src/guerilla/conflicts/`
- `tests/integration/`
- `tests/repository/test_repository_contract.py`
- `docs/ADAPTER_CONTRACT.md`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- `docs/phase_prompts/README.md`
- This prompt

## Invariants

- A reconciliation result is always appended as a new event and never rewrites
  original intent or result records.
- Missing lineage recovery preserves the original intent and invocation records.
- Recovered result records do not fabricate the original result timestamp.
- Unknown outcomes remain explicit when evidence is insufficient.
- Retry cannot silently duplicate mutation.
- Conflict records include type, subject, evidence, authority, severity, status,
  detection time, policy version, required resolution class, and limitations.
- Decisions and resolution lineage are append-only.
- External result, after-state observation, evaluation, conflict, and
  goal-completion decision layers remain distinct.
- All three synthetic systems use one reconciliation engine.

## Ordered Tasks

1. Add typed reconciliation request, result, and error contracts.
2. Load Phase 11 action intent, invocation, and result evidence from
   authoritative graph replay.
3. Validate authorization, adapter capability, state boundary, and
   `adapter.reconcile` contract before committing reconciliation output.
4. Invoke adapter `reconcile` through the Phase 9 host.
5. Commit reconciliation events with classification, evidence, retry,
   limitations, warnings, external revision, and external identity metadata.
6. Recover missing action-result lineage without rewriting prior records.
7. Create evidence-backed conflicts for unknown, unsupported, stale, duplicate,
   and incomplete-lineage conditions.
8. Add append-only decision and `resolved_by` resolution flow with optional
   continuation operation.
9. Add tests for interrupted actions, unknown/unsupported reconciliation,
   duplicate attempts, stale revisions, conflict evidence, append-only
   decisions, replay, and index rebuild behavior.
10. Regenerate Phase 12 status documentation and completion evidence.

## Required Tests

- Interruption after adapter completion but before result commit is reconciled
  without duplicate mutation.
- Missing lineage is recovered without rewriting intent or invocation records.
- Recovered results become graph-backed idempotency truth for later retries.
- Unknown and unsupported reconciliation outcomes create explicit conflicts.
- Stale external revisions and same-request/different-key attempts create
  explicit conflicts.
- Conflict records carry complete evidence and resolution metadata.
- Decisions append `resolved_by` lineage and optional continuation operations.
- Replay and index rebuild preserve reconciliation/conflict truth without
  invoking adapters.
- Transactional, filesystem, and asynchronous synthetic systems share one
  reconciliation engine.

## Failure and Crash Cases

- Before reconciliation validation.
- During reconciliation.
- After adapter reconciliation before commit.
- During reconciliation commit.
- After reconciliation commit before after-state observation.
- During after-state observation.
- Unsupported reconciliation capability.
- Reconciliation timeout or unavailable history.

## Documentation Regeneration

Update Phase 12 status and evidence only. Do not rewrite architecture papers or
change Gate A canonical bytes, identifiers, hashes, relationship directions, or
authorization rules.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Every interrupted action is classified or remains explicitly unknown | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` |
| Retry cannot silently duplicate mutation | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` |
| Missing lineage is repaired without history rewrite | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` |
| Conflicts are evidence backed | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` |
| Decisions/resolutions are append-only | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` |
| Outcome layers remain distinct | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` |
| All systems share one reconciliation engine | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` |
| Full validation and hosted CI pass | PASS | Split local validation sequence and PR #2 hosted CI |

## Completion Report Format

The Phase 12 completion report must include:

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

Stop before Phase 13 if:

- reconciliation rewrites prior records;
- missing lineage recovery fabricates original result timestamps;
- unknown outcomes are retried blindly;
- conflict evidence is incomplete;
- decisions delete or overwrite conflicts;
- reconciliation requires projections, snapshots, transports, or real
  integrations;
- Gate A canonical bytes, identifiers, hashes, relationship directions, or
  authorization rules would need to change.
