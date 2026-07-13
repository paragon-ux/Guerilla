# Codex Build Plan

**Status:** PLACEHOLDER -- cross-phase (all phases)
**Owner phase:** Cross-phase; updated by each phase
**Controlling source documents:** `GUERILLA_WORKFLOW_CURRENT.md`, `Guerilla-Kickoff-Prompt.md`
**Regeneration trigger:** Any phase completion or gate status change

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until each phase completes.

---

## Purpose

Track the complete build sequence from repository bootstrap through research release. Define gates, phases, and the critical path.

---

## Gates

| Gate | Phases | Meaning | Status |
|---|---|---|---|
| A -- Contract Ready | 1-4 | Architecture decisions, schemas, registries, and fixtures are frozen | Phase 1 in progress |
| B -- Kernel Ready | 5-8 | Authoritative storage, replay, DAG integrity, index, authority, identity | BLOCKED |
| C -- Continuity MVP | 9-15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI | BLOCKED |
| D -- External Compatible | 16-19 | Reference transport, isolated adapters, parity, security, durability, archive | BLOCKED |
| E -- Research Validated | 20-22 | Real heterogeneous pilots, benchmark evidence, reproducible release | BLOCKED |

---

## Complete Phase Inventory

| Phase | Name | Gate | Status |
|---|---|---|---|
| 1 | Repository and Agent-Control Bootstrap | A | IN PROGRESS |
| 2 | Architecture Decisions | A | PENDING |
| 3 | Machine Contracts | A | PENDING |
| 4 | Conformance Fixtures | A | PENDING |
| 5 | Codec, Config, Identifiers | B | PENDING |
| 6 | Append Store, Transactions, Replay | B | PENDING |
| 7 | DAG Integrity, Index, Query | B | PENDING |
| 8 | Authority, Identity, Boundaries | B | PENDING |
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

No phase beyond Phase 1 has been executed. All phase statuses are PENDING.
