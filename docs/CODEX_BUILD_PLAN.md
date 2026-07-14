# Codex Build Plan

**Status:** Gate B in progress -- Phase 8 PASS
**Owner phase:** Cross-phase; updated by each phase
**Controlling source documents:** `GUERILLA_WORKFLOW_CURRENT.md`, `Guerilla-Kickoff-Prompt.md`
**Regeneration trigger:** Any phase completion or gate status change

> **WARNING:** Phase 8 local authority and boundary registries are implemented.
> Do not treat adapters, projections, transports, or Phase 9+ behavior as
> implemented.

---

## Purpose

Track the complete build sequence from repository bootstrap through research release. Define gates, phases, and the critical path.

---

## Gates

| Gate | Phases | Meaning | Status |
|---|---|---|---|
| A -- Contract Ready | 1-4 | Architecture decisions, schemas, registries, and fixtures are frozen | COMPLETE |
| B -- Kernel Ready | 5-8 | Authoritative storage, replay, DAG integrity, index, authority, identity | Phase 8 PASS; Gate B checklist next |
| C -- Continuity MVP | 9-15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI | BLOCKED |
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
| 9 | Adapter SDK, Synthetic Systems | C | PENDING |
| 10 | Observation Ingestion | C | PENDING |
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

Gate A is complete and Phase 8 has passed local validation. The Gate B checklist
is next.
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
it did not add adapters, projections, transports, or Phase 9 behavior.
