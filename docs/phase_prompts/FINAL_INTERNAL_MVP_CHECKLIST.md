# Final Internal MVP Checklist -- Gate C

**Status:** PASS -- Gate C checklist complete
**Owner phase:** Final Gate C checklist
**Gate:** C -- Continuity MVP
**Execution date:** 2026-07-15

## Objective

Verify that Phases 9-15 together form an internal continuity MVP: one
authoritative Guerilla graph preserves continuity across transactional,
reconstructed-filesystem, and asynchronous unknown-outcome synthetic systems
without owning their application state or starting Gate D.

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---:|---|---|---|
| 1 | One adapter SDK supports all three synthetic state models | PASS | `tests/adapters/test_phase9_adapter_sdk.py` |
| 2 | Synthetic adapters declare capabilities and limitations | PASS | `tests/adapters/test_phase9_adapter_sdk.py` |
| 3 | Observations preserve external authority/revisions | PASS | `tests/integration/test_phase10_observation_ingestion.py` |
| 4 | Actions always follow committed intent | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| 5 | Idempotency prevents unsafe duplicate mutation | PASS | `tests/integration/test_phase11_action_intent_idempotency.py` |
| 6 | Interrupted actions reconcile or remain explicitly unknown | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py`, `tests/integration/test_phase15_internal_cli_e2e_smoke.py` |
| 7 | Conflict/decision history is immutable and evidence backed | PASS | `tests/integration/test_phase12_reconciliation_conflicts.py` |
| 8 | Projections are deterministic and non-authoritative | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` |
| 9 | Manifests preserve ambiguity, freshness, and source links | PASS | `tests/integration/test_phase13_projections_manifest_diff.py`, `tests/integration/test_phase15_internal_cli_e2e_smoke.py` |
| 10 | Diffs compare revisions without implying in-place mutation | PASS | `tests/integration/test_phase13_projections_manifest_diff.py` |
| 11 | Snapshots cite verified boundaries | PASS | `tests/integration/test_phase14_snapshot_resume.py` |
| 12 | Resume distinguishes authoritative, derived, stale, and unknown data | PASS | `tests/integration/test_phase14_snapshot_resume.py`, `tests/integration/test_phase15_internal_cli_e2e_smoke.py` |
| 13 | Replay performs no external actions | PASS | `tests/integration/test_phase10_observation_ingestion.py`, `tests/integration/test_phase11_action_intent_idempotency.py`, `tests/integration/test_phase12_reconciliation_conflicts.py`, `tests/integration/test_phase15_internal_cli_e2e_smoke.py` |
| 14 | Index/projection loss removes no authority | PASS | `tests/integration/test_phase7_graph_index_query.py`, `tests/integration/test_phase13_projections_manifest_diff.py`, `tests/integration/test_phase15_internal_cli_e2e_smoke.py` |
| 15 | CLI/library use one mutation path | PASS | `src/guerilla/cli/workflows.py`, `tests/integration/test_phase15_internal_cli_e2e_smoke.py` |
| 16 | All three E2E scenarios pass | PASS | `tests/integration/test_phase15_internal_cli_e2e_smoke.py` |
| 17 | No real adapter exists | PASS | Repository contract and `src/guerilla/adapters/synthetic.py` |
| 18 | No network/subprocess transport exists | PASS | Repository contract and source inspection; no Phase 16/17 modules added |
| 19 | Supported Python versions pass hosted CI | PASS | PR #2 hosted checks at the final Phase 15 head; final handoff records the result |
| 20 | Every completion claim links to evidence | PASS | `docs/TEST_MATRIX.md`, phase completion reports, this checklist |

## Performance Evidence

Gate C records smoke-level timing only; production benchmarking remains Phase
21 scope.

| Reference workload | Local result |
|---|---|
| Transactional CLI E2E pytest command | 1 passed in 26.20s |
| Snapshot/manifest CLI smoke pytest command | 1 passed in 12.09s |
| Reconstructed filesystem CLI E2E pytest command | 1 passed in 33.48s |
| Async unknown-outcome CLI E2E pytest command | 1 passed in 20.96s |
| Repository contract command after Phase 15 docs | 41 passed in 2.42s |

These timings include Python startup, schema validation, filesystem sync, index
refresh, projection generation, and snapshot work. They are not throughput
targets and do not claim production readiness.

## Security and Safety Checks

| Check | Status | Evidence | Residual risk |
|---|---|---|---|
| Adapter capability escalation rejected | PASS | `tests/security/test_phase8_authority_boundaries.py`, `tests/adapters/test_phase9_adapter_sdk.py` | Full isolated-adapter sandbox remains Gate D/Phase 17 |
| Boundary/path/endpoint/namespace escape rejected | PASS | `tests/security/test_phase8_authority_boundaries.py`, `tests/adapters/test_phase9_adapter_sdk.py`, `tests/integration/test_phase10_observation_ingestion.py`, `tests/integration/test_phase11_action_intent_idempotency.py` | Real endpoint policy remains Gate D |
| Actor/payload authority claims cannot escalate | PASS | `tests/security/test_phase8_authority_boundaries.py` | Broader policy engine deferred |
| Unsafe numeric/JSON serialization rejected | PASS | `tests/conformance/test_conformance_fixtures.py`, `tests/adapters/test_phase9_adapter_sdk.py` | Additional hostile-format fuzzing deferred |
| Payloads are not executed | PASS | `tests/adapters/test_phase9_adapter_sdk.py` | Phase 19 will add broader payload-security tests |
| Malformed adapter results rejected | PASS | `tests/adapters/test_phase9_adapter_sdk.py` | Subprocess adapter result isolation deferred |
| Idempotency-key abuse rejected | PASS | `tests/integration/test_phase11_action_intent_idempotency.py`, `tests/integration/test_phase12_reconciliation_conflicts.py` | Retention-expiry policy remains future work |
| Replay-triggered action attempt absent | PASS | `tests/integration/test_phase11_action_intent_idempotency.py`, `tests/integration/test_phase15_internal_cli_e2e_smoke.py` | Real adapter replay audit remains Gate D |
| Projection and snapshot outputs remain derived | PASS | `tests/integration/test_phase13_projections_manifest_diff.py`, `tests/integration/test_phase14_snapshot_resume.py` | Projection-injection fuzzing remains Phase 19/21 |
| Snapshot tampering detected | PASS | `tests/integration/test_phase14_snapshot_resume.py` | Archive seal and portable bundle tamper checks remain Gate D |
| Pre-redaction secret retention avoided by current model | PARTIAL | `docs/ARCHITECTURE_DECISIONS.md`, `src/guerilla/observability/ingestion.py` | Comprehensive secret-redaction testing remains Phase 19 |
| Unauthorized conflict resolution rejected by local profile | PASS | `tests/security/test_phase8_authority_boundaries.py`, `tests/integration/test_phase12_reconciliation_conflicts.py` | Multi-principal policy remains future work |

## Scope Audit

No Gate D work was started. The repository still has no reference transport,
subprocess adapter host, real external adapter, production archive/backup,
pilot integration, or empirical benchmark suite. CLI commands are local and
delegate to the existing runtime APIs.

## Handoff

Gate C is complete once final local validation and hosted CI pass at the Phase
15 head. Phase 16 may begin only after this checklist, the Gate C completion
report, final validation, and hosted CI are complete.
