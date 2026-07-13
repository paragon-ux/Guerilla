# MVP Scope

**Status:** FROZEN -- Phase 2 complete
**Owner phase:** Phase 2 (Architecture Decisions)
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Sections 2, 33-37; `GUERILLA_SNAPSHOT.md` Section 6; `ARCHITECTURE_DECISIONS.md`
**Regeneration trigger:** Any MVP boundary or acceptance-criteria change

---

## Purpose

Define the mandatory MVP capabilities, explicitly excluded capabilities, acceptance criteria, and phase-to-capability traceability.

The MVP is local, single-workspace, and single-writer. It must prove authority-preserving lineage, deterministic replay, bounded external observations, intent-before-action, unknown-outcome reconciliation, and source-bound derived views before external transports or real integrations are introduced.

---

## Mandatory MVP Capabilities

| Capability | Owning phase |
|---|---|
| Local workspace initialization and verification | Phase 6 |
| One local writer lock | Phase 6 |
| Graph header and append transactions | Phase 6 |
| `guerilla-cjson-v1` canonical JSON and SHA-256 hashing | Phase 5 |
| UUIDv7 Guerilla identifiers with frozen prefixes | Phase 5 |
| Graph revisions and commit hash chain | Phase 6 |
| Eight core node types | Phase 3 |
| Nine core relationship types | Phase 3 |
| Endpoint validation and direct cycle rejection | Phase 7 |
| External authority envelopes | Phase 3, Phase 8 |
| State-boundary registry | Phase 8 |
| Trusted in-process adapter interface for MVP synthetic systems | Phase 9 |
| Adapter `describe`, `observe`, `act`, `evaluate`, and `reconcile` | Phase 9 |
| Observation ingestion preserving external authority and revision metadata | Phase 10 |
| Intent-before-action recording | Phase 11 |
| Idempotency for retryable mutations and external actions | Phase 11 |
| Unknown-outcome reconciliation | Phase 12 |
| Conflict records and resolution lineage | Phase 12 |
| Graph verification and deterministic replay | Phase 6 |
| SQLite or equivalent rebuildable non-authoritative index | Phase 7 |
| Lineage, manifest, snapshot, diff, conflict, progress, and resume projections | Phase 13, Phase 14 |
| Payload hashing, retention classes, and redaction metadata | Phase 5, Phase 19 |
| Protocol and graph conformance tests | Phase 4, Phase 15 |

---

## Explicitly Excluded From MVP

These capabilities are deferred and must not be required for MVP acceptance:

- remote graph service;
- multiple concurrent writers;
- distributed locking or consensus;
- event-stream subscriptions;
- adapter process sandboxing;
- signed commits and payload attestations;
- cross-workspace federation;
- selective lineage disclosure;
- portable snapshot bundles;
- incremental streaming projections;
- policy engines;
- scheduling and reservations;
- cost-aware planning;
- domain-specific semantic merge;
- global external-identity resolution;
- production UI;
- real external adapters before synthetic adapter conformance passes.

Deferred capabilities must preserve append-only graph history, direct-edge acyclicity, external-state authority, explicit state boundaries, source-bound projections, and payload non-execution.

---

## MVP Acceptance Criteria

The MVP is accepted only when all criteria are demonstrated by automated tests or reproducible evidence:

| # | Criterion | Evidence owner |
|---|---|---|
| 1 | A workspace can be initialized and verified. | Phase 6 |
| 2 | Valid transactions commit atomically. | Phase 6 |
| 3 | Incomplete transactions are ignored on replay. | Phase 6 |
| 4 | A proposed lineage cycle is rejected. | Phase 7 |
| 5 | External observations preserve authority and revision metadata. | Phase 10 |
| 6 | An external action is preceded by committed intent. | Phase 11 |
| 7 | An interrupted external action can be reconciled without duplicate mutation. | Phase 12 |
| 8 | Reused idempotency keys return the original result or a conflict. | Phase 11 |
| 9 | A stale external revision creates an explicit conflict. | Phase 12 |
| 10 | A projection can be regenerated from its graph revision. | Phase 13 |
| 11 | A snapshot identifies graph heads and freshness requirements. | Phase 14 |
| 12 | The index can be deleted and rebuilt without lineage loss. | Phase 7 |
| 13 | Replay does not invoke external actions. | Phase 6, Phase 12 |
| 14 | Payload content is never executed. | Phase 19 |
| 15 | No executable runtime component claims implementation completion without passing the conformance suite. | Phase 15 |

---

## MVP Conformance Test Mapping

| Test family | Required evidence |
|---|---|
| Record tests | valid/invalid node and edge records, duplicate identifiers, hash mismatches, unsupported versions, authority envelopes |
| Transaction tests | atomic commit, incomplete transaction recovery, previous-commit mismatch, transaction-hash mismatch, monotonic revisions, concurrent append rejection |
| DAG tests | linear ancestry, branching, convergence, supersession, cycle rejection, self-loop rejection, missing endpoints, reified symmetric relationships |
| Adapter tests | descriptor validity, state-boundary enforcement, read-only observation, structured action arguments, rejection preservation, unsupported capability, reconciliation, identity collision, consistency guarantees |
| Action-recovery tests | interruption before intent, after intent, after external completion, after result, and during reconciliation |
| Projection tests | deterministic output, source revision, source-node citation, information loss, stale observations, regeneration after index deletion, manifest ambiguity, snapshot verification, diff correctness |
| Security tests | path and endpoint escape, unauthorized access/action, redaction, payload non-execution, unsafe serialization rejection, capability escalation, idempotency-key abuse |
| Performance tests | append throughput, cycle-check cost, replay time, index rebuild time, traversal latency, projection latency, snapshot size, payload deduplication, archive performance |

---

## Phase-To-Capability Traceability

| Phase | Capability boundary |
|---|---|
| 2 | Freeze architecture decisions, glossary, and MVP boundary. |
| 3 | Publish schemas and registries that encode the frozen decisions. |
| 4 | Publish conformance fixtures and canonical hash vectors. |
| 5 | Implement canonical codec, identifiers, hashes, config, and payload primitives. |
| 6 | Implement append store, transactions, writer lock, replay, verification, and recovery. |
| 7 | Implement DAG validation, graph heads, rebuildable index, and query primitives. |
| 8 | Implement authority, identity, state boundaries, and local authorization policy. |
| 9 | Implement adapter descriptor/interface and synthetic systems. |
| 10 | Implement observation ingestion. |
| 11 | Implement intent-before-action and idempotency. |
| 12 | Implement reconciliation, conflicts, and decisions. |
| 13 | Implement deterministic projections, manifests, diffs, and progress views. |
| 14 | Implement snapshots and resume context. |
| 15 | Demonstrate internal CLI and end-to-end MVP acceptance. |

---

## Phase 3 Handoff

Phase 3 must encode this scope in machine-readable schemas and registries. It must not expand the MVP or implement runtime behavior.
