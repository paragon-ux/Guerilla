# Codex Build Plan

**Status:** Gate C in progress -- Phase 10 Observation Ingestion local validation complete
**Owner phase:** Cross-phase; updated by each phase
**Controlling source documents:** `GUERILLA_WORKFLOW_CURRENT.md`, `Guerilla-Kickoff-Prompt.md`
**Regeneration trigger:** Any phase completion or gate status change

> **WARNING:** Gate B local kernel behavior, Phase 9 trusted in-process
> synthetic adapter SDK behavior, and Phase 10 observe-only ingestion are
> implemented. Do not treat graph-backed actions, reconciliation, projections,
> snapshots, transports, or real integrations as implemented.

---

## Purpose

Track the complete build sequence from repository bootstrap through research release. Define gates, phases, and the critical path.

---

## Gates

| Gate | Phases | Meaning | Status |
|---|---|---|---|
| A -- Contract Ready | 1-4 | Architecture decisions, schemas, registries, and fixtures are frozen | COMPLETE |
| B -- Kernel Ready | 5-8 | Authoritative storage, replay, DAG integrity, index, authority, identity | COMPLETE |
| C -- Continuity MVP | 9-15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI | IN PROGRESS |
| D -- External Compatible | 16-19 | Reference transport, isolated adapters, parity, security, durability, archive | BLOCKED |
| E -- Research Validated | 20-22 | Real heterogeneous pilots, benchmark evidence, reproducible release | BLOCKED |

---

## Complete Phase Inventory

| Phase | Name | Gate | Status |
|---|---|---|---|
| 1 | Repository and Agent-Control Bootstrap | A | PASS |
| 2 | Architecture Decisions | A | PASS |
| 3 | Machine Contracts | A | PASS |
| 4 | Conformance Fixtures | A | PASS |
| 5 | Codec, Config, Identifiers | B | PASS |
| 6 | Append Store, Transactions, Replay | B | PASS |
| 7 | DAG Integrity, Index, Query | B | PASS |
| 8 | Authority, Identity, Boundaries | B | PASS |
| 9 | Adapter SDK, Synthetic Systems | C | PASS |
| 10 | Observation Ingestion | C | LOCAL PASS / CI PENDING |
| 11 | Action Intent, Idempotency | C | PENDING |
| 12 | Reconciliation, Conflicts | C | PENDING |
| 13 | Projections, Manifest, Diff | C | PENDING |
| 14 | Snapshot, Resume | C | PENDING |
| 15 | Internal CLI, E2E, Smoke | C | PENDING |
| FINAL | Internal MVP Checklist | C | PENDING |
| 16 | GLCP Reference Client/Server | D | PENDING |
| 17 | Subprocess Adapter Host | D | PENDING |
| 18 | Transport Parity, Robustness | D | PENDING |
| 19 | Security, Durability, Archive | D | PENDING |
| FINAL | External Compatibility Checklist | D | PENDING |
| 20 | Heterogeneous Pilots | E | PENDING |
| 21 | Benchmark, Evaluation | E | PENDING |
| 22 | Release, Research Package | E | PENDING |
| FINAL | Release Checklist | E | PENDING |

---

## Critical Path

architecture decisions → machine contracts → codec and hashes → append/replay kernel → DAG and authority enforcement → synthetic adapters → intent/idempotency/reconciliation → snapshots and resume → external bindings → heterogeneous pilots → evaluation

---

## Unresolved Items

Gate A and Gate B are complete. Phase 9 is complete. Phase 10 is complete
locally and awaits hosted CI; Phase 11 has not started.
Frozen inputs for later kernel work are `docs/ARCHITECTURE_DECISIONS.md`,
`docs/contract_inventory.json`, `schemas/`, `registries/`, and
`tests/fixtures/contracts/`. Phase 5 added deterministic codec, config,
contract-loader, protocol-validation, payload-hash, and identifier primitives.
Phase 6 added local workspace initialization, content-addressed payload
persistence, writer locking, append transactions, replay, hash-chain
verification, and incomplete-tail recovery only; it did not add DAG validation,
indexing, authority registry, adapters, projections, or transports. Phase 7
added endpoint validation, cycle rejection, graph-head and exact-revision query
helpers, and a rebuildable non-authoritative SQLite index; it did not add
authority registry, adapters, projections, or transports. Phase 8 added fixed
local authorization, state-boundary enforcement helpers, adapter identity
registration without invocation, and scoped external identity lifecycle handling;
it did not add adapter invocation, projections, transports, or Phase 9 behavior.
Phase 9 added trusted configured in-process adapter SDK modules, one validating
host path, descriptor completeness checks, and three synthetic systems:
transactional revisioned service, reconstructed filesystem, and asynchronous
unknown-outcome service. Phase 9 did not add observation ingestion into graph
records, committed action orchestration, graph-backed idempotency,
reconciliation engine, projections, snapshots, transports, subprocess
isolation, real integrations, or Gate D behavior. Phase 10 added observe-only
ingestion that invokes adapter `observe`, preserves external facts in graph
records, classifies duplicate/stale/conflicting observations from authoritative
replay, and appends through one Gate B graph transaction. Phase 10 did not add
action intent, idempotency orchestration, reconciliation, projections,
snapshots, transports, subprocess isolation, real integrations, or Gate D
behavior. The Gate B checklist verifies clean reopen/replay, invalid-mutation
rollback, index loss rebuild, authority rejection, and replay/index query
equivalence. Phase 9 adapter tests verify the SDK and synthetic-system boundary
only. Phase 10 tests verify observation ingestion only.
