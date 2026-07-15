# Phase 15 -- Internal CLI, E2E, Smoke

**Status:** PASS -- Phase 15 complete
**Owner phase:** Phase 15 (Internal CLI, E2E, Smoke)
**Gate:** C -- Continuity MVP
**Execution date:** 2026-07-15

## Objective

Expose the local continuity MVP through an internal CLI that uses the same
library APIs as the tests and runtime modules. Phase 15 proves local workspace,
adapter, observation, action, reconciliation, conflict, projection, manifest,
snapshot, and graph-replay workflows without adding transport bindings,
subprocess isolation, real adapters, or Gate D behavior.

## Permitted Scope

- `src/guerilla/cli/`
- Integration tests for local CLI E2E smoke scenarios.
- Repository-contract updates recognizing Phase 15 CLI modules.
- Status, test-matrix, and completion-report documentation.

## Prohibited Scope

- Network services, GLCP client/server transport, subprocess adapter hosting,
  real external adapters, pilots, archive/backup, or Phase 16+ behavior.
- CLI-specific mutation paths that bypass `GraphStore`, `ObservationIngestor`,
  `ActionOrchestrator`, `ReconciliationEngine`, `ConflictEngine`,
  `ProjectionEngine`, or `SnapshotEngine`.
- Treating projections, manifests, materialized summaries, indexes, or CLI
  output as authoritative graph state.
- Replaying adapters or external actions during graph replay, graph verify,
  index rebuild, projection generation, snapshot verification, or resume.

## Required Sources

1. `AGENTS.md`
2. `docs/ARCHITECTURE_DECISIONS.md`
3. `docs/ADAPTER_CONTRACT.md`
4. `docs/STATE_BOUNDARY_MODEL.md`
5. `docs/PROJECTION_SPEC.md`
6. `docs/STORAGE_AND_RECOVERY.md`
7. `docs/TEST_MATRIX.md`
8. `docs/CODEX_BUILD_PLAN.md`
9. `docs/PHASE_14_COMPLETION_REPORT.md`
10. `docs/phase_prompts/PHASE_14_SNAPSHOT_RESUME.md`
11. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md`
12. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md`
13. `docs/architecture/GUERILLA_SNAPSHOT.md`

## Files Expected To Change

- `src/guerilla/cli/main.py`
- `src/guerilla/cli/workflows.py`
- `tests/integration/test_phase15_internal_cli_e2e_smoke.py`
- `tests/repository/test_repository_contract.py`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- `docs/architecture/CURRENT_STATUS_MATRIX.md`
- `docs/phase_prompts/README.md`
- This prompt

## Invariants

- CLI mutations delegate to the same library APIs as integration tests.
- Mutating commands support workspace selection, structured JSON input,
  expected graph revision guards, principal context, deterministic JSON output,
  and stable non-zero error envelopes.
- Adapter actions still commit durable intent before adapter invocation.
- Unknown external outcomes require reconciliation and remain explicit when
  unresolved.
- Graph replay, verify, heads, index rebuild, view generation, manifest
  generation, snapshot verification, and resume context generation do not invoke
  adapters or external actions.
- All local CLI outputs are derived responses; authoritative truth remains the
  append-only graph.

## Required Tests

- Transactional service CLI E2E: initialize workspace, observe external state,
  create goal and operation records, commit intent, invoke action, record
  after-state observation, evaluate, and verify replay safety.
- Snapshot/manifest CLI smoke: generate a manifest, generate a progress view,
  create/verify a snapshot, and generate a bounded resume context through
  derived-output commands.
- Reconstructed filesystem CLI E2E: observe file state, commit partial-failure
  action, record conflict, append decision resolution, generate lineage/view,
  delete/rebuild index, snapshot, and replay without adapter calls.
- Async unknown-outcome CLI E2E: commit unknown action, list unresolved intent,
  reconcile unknown result, preserve conflict, reject stale graph revision,
  snapshot, resume, and verify replay safety.
- Stable JSON success and error envelopes.
- Adapter `list`, `describe`, and `validate` commands.
- Clean source-tree help/version behavior and clean wheel smoke.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Required command families exist | PASS | `src/guerilla/cli/main.py` |
| CLI delegates to runtime APIs, not a separate mutation path | PASS | `src/guerilla/cli/workflows.py`, `tests/integration/test_phase15_internal_cli_e2e_smoke.py` |
| Transactional E2E passes | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py::test_transactional_cli_e2e_intent_after_state_and_evaluation` |
| Snapshot/manifest CLI smoke passes | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py::test_snapshot_manifest_cli_smoke_uses_derived_view_path` |
| Reconstructed-filesystem E2E passes | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py::test_reconstructed_filesystem_cli_e2e_conflict_decision_and_rebuild` |
| Async unknown/reconciliation E2E passes | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py::test_async_unknown_cli_reconciliation_and_replay_safety` |
| Replay safety is evidenced | PASS | Phase 15 E2E replay-safety assertions |
| Gate D behavior remains out of scope | PASS | No transport, subprocess, or real-adapter modules added |

## Stop Conditions

Stop before Gate C closure if:

- any CLI command mutates graph records without the existing library APIs;
- graph replay or derived views invoke adapters or external actions;
- unknown outcomes are retried blindly instead of reconciled;
- CLI output becomes an authoritative source of lineage truth;
- transport, subprocess, real adapter, or Gate D behavior is required.
