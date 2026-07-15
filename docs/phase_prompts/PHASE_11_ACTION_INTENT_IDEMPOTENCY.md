# Phase 11 -- Action Intent and Idempotency

**Status:** PASS -- Phase 11 complete
**Owner phase:** Phase 11 (Action Intent and Idempotency)
**Gate:** C -- Continuity MVP
**Execution date:** 2026-07-14

## Objective

Implement safe external mutation initiation through committed graph intent,
structured adapter invocation, graph-backed idempotency, explicit result
recording, and optional after-state observation.

Phase 11 proves that all three Phase 9 synthetic systems use one action path:

```text
validate request
-> commit durable intent
-> verify durable intent
-> commit invocation-start event
-> invoke adapter act
-> commit action-result event
-> optionally observe after-state through Phase 10 ingestion
```

## Permitted Scope

- `src/guerilla/orchestration/`
- Narrow adapter-host preflight validation support.
- Integration tests for action intent, idempotency, restart behavior, and
  after-state observation.
- Status and evidence documentation for Phase 11.

## Prohibited Scope

- Reconciliation engine or conflict engine implementation.
- Blind retry after a prior invocation without a committed result.
- Real integrations, transports, subprocess/container isolation, projections,
  snapshots, CLI workflows, archive, backup, or Gate D behavior.
- Treating adapter-native idempotency, SQLite indexes, projections, or runtime
  responses as authoritative idempotency truth.
- Product-specific orchestration branches for synthetic system types.

## Required Sources

1. `AGENTS.md`
2. `docs/PHASE_10_COMPLETION_REPORT.md`
3. `docs/ARCHITECTURE_DECISIONS.md`
4. `docs/ADAPTER_CONTRACT.md`
5. `docs/STATE_BOUNDARY_MODEL.md`
6. `docs/STORAGE_AND_RECOVERY.md`
7. `docs/TEST_MATRIX.md`
8. `docs/CODEX_BUILD_PLAN.md`
9. `docs/phase_prompts/PHASE_09_ADAPTER_SDK_SYNTHETIC_SYSTEMS.md`
10. `docs/phase_prompts/PHASE_10_OBSERVATION_INGESTION.md`
11. `schemas/adapter_act.schema.json`
12. `schemas/node.schema.json`
13. `schemas/edge.schema.json`
14. `registries/relationship_types.json`

## Files Expected To Change

- `src/guerilla/orchestration/`
- `src/guerilla/adapters/host.py`
- `tests/integration/`
- `tests/repository/test_repository_contract.py`
- `docs/ADAPTER_CONTRACT.md`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- `docs/phase_prompts/README.md`
- This prompt

## Invariants

- Every external action requires a committed intent before adapter invocation.
- Adapter action requests are validated before intent commitment.
- Invocation start is committed before adapter `act` is called.
- Same idempotency key plus same request hash returns prior committed result or
  resumes only when no invocation has started.
- Same idempotency key plus different request hash is rejected.
- Prior invocation without a committed result is reported as unknown and is not
  retried blindly.
- Idempotency truth is reconstructed from authoritative graph replay and
  survives index loss.
- Replay and index rebuild never invoke adapters or external actions.
- External systems remain application-state authorities.

## Ordered Tasks

1. Add typed action execution request, result, error, and metadata contracts.
2. Add adapter-host request preflight validation that performs all host checks
   without invoking adapter code.
3. Implement graph-backed idempotency lookup from replayed Phase 11 intent,
   invocation, and result records.
4. Commit operation and action-request event records before invoking `act`.
5. Commit invocation-start event records before adapter invocation.
6. Invoke adapter `act` with structured arguments, expected external revision,
   idempotency context, correlation, boundary, and authorization context.
7. Commit action-result event records with external classification, revision,
   action identifiers, warnings, limitations, retry classification, and
   adapter evidence.
8. Optionally route after-state observation through the Phase 10 ingestor.
9. Add tests for all three synthetic systems, idempotency behavior, injected
   interruption points, replay safety, and index-loss behavior.
10. Regenerate Phase 11 status documentation and completion evidence.

## Required Tests

- Invalid principal, stale graph revision, unsupported or escaped boundary, and
  malformed action requests cause zero adapter calls and no graph commit.
- Intent is durably committed before adapter `act`.
- Invocation start is committed before adapter `act`.
- Adapter acceptance, rejection, failure, pending, duplicate, and unknown
  classifications are recorded distinctly.
- Same key plus same content returns the prior result.
- Same key plus different content returns `idempotency_conflict`.
- Idempotency survives restart and index loss.
- A committed intent without invocation can resume safely.
- A prior invocation without committed result returns `outcome_unknown` and does
  not call the adapter again.
- Native and adapter-emulated idempotency are exercised.
- Filesystem partial mutation can be followed by after-state observation.
- Asynchronous unknown outcome is not retried blindly.
- Replay and index rebuild do not call adapters.
- All three synthetic systems use the same action orchestrator.

## Failure and Crash Cases

- Before intent validation.
- Before intent commit.
- During intent commit.
- After intent commit before invocation.
- After invocation-start commit before adapter call.
- During adapter call or after external completion before result commit.
- During result commit.
- After result commit before after-state observation.
- During after-state observation.

## Documentation Regeneration

Update Phase 11 status and evidence only. Do not rewrite architecture papers or
change Gate A canonical bytes, identifiers, hashes, relationship directions, or
authorization rules.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| No external action occurs without durable intent | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| Idempotency survives restart and index loss | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| Same-key different-content is rejected | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| Unknown outcomes are not retried blindly | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| Result classifications remain distinct | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| Replay performs no adapter calls | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| All systems use one action path | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| Full validation and hosted CI pass | PASS | Split local validation sequence and PR #2 hosted CI |

## Completion Report Format

The Phase 11 completion report must include:

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

Stop before Phase 12 if:

- any adapter `act` can occur before committed intent;
- a prior invocation without committed result is retried blindly;
- idempotency truth depends only on SQLite or adapter-native state;
- same-key different-content is accepted silently;
- replay or index rebuild invokes an adapter;
- action orchestration needs product-specific branches;
- reconciliation, conflicts, projections, snapshots, transport, or real
  integrations are required to pass Phase 11.
