# Current Status Matrix

**Status:** Gate C in progress -- Phase 10 complete locally
**Last updated:** 2026-07-14
**Current baseline:** draft Gate C branch `feature/gate-c-continuity-mvp`
**Evidence:** [Gate B completion report](../GATE_B_COMPLETION_REPORT.md), [Phase 9 completion report](../PHASE_09_COMPLETION_REPORT.md), Phase 10 local evidence in `tests/integration/test_phase10_observation_ingestion.py`, [PR #2](https://github.com/paragon-ux/Guerilla/pull/2)

**Hosted CI evidence:** [Gate A closure](https://github.com/paragon-ux/Guerilla/actions/runs/29302019930), [Phase 5](https://github.com/paragon-ux/Guerilla/actions/runs/29302731597), [Phase 6](https://github.com/paragon-ux/Guerilla/actions/runs/29303454247), [Phase 7](https://github.com/paragon-ux/Guerilla/actions/runs/29304114169), [Phase 8](https://github.com/paragon-ux/Guerilla/actions/runs/29304560354), [final Gate B PR validation](https://github.com/paragon-ux/Guerilla/actions/runs/29363456584), [Phase 9 PR validation](https://github.com/paragon-ux/Guerilla/actions/runs/29378512503). Phase 10 hosted CI is pending for the next PR head.

---

## Current Maturity

Guerilla has moved beyond the pre-prototype stage. Gate A and Gate B are
complete, and Gate C is in progress: the architecture decisions, schemas,
registries, fixtures, canonical codec primitives, local append-only graph
kernel, replay path, DAG/index/query surface, local authority/boundary
enforcement, trusted synthetic adapter SDK, and observe-only graph ingestion
are implemented and tested locally.

The project is now at the **continuity-MVP in progress stage**. Phase 10 is
complete locally. Action intent/idempotency, reconciliation engine, projections,
snapshots, transport bindings, pilots, and empirical evaluation are not
implemented.

| Area | Estimated maturity | Assessment |
|---|---:|---|
| Problem definition and motivation | 95% | Clear standalone thesis: authority-preserving continuity over heterogeneous systems |
| Architectural boundaries | 95% | External systems retain application-state authority; Guerilla owns lineage authority |
| Frozen contracts and schemas | 90% | Gate A complete; schemas, registries, fixtures, and decision vectors are frozen for current protocol `0.2.0` |
| Protocol design | 75% | GLCP core contracts exist; runtime transport bindings and parity tests remain future work |
| Implementation design | 80% | Gate plan, storage/recovery model, state-boundary model, and test matrix are current through Gate B |
| Reference implementation | 55-60% | Local graph kernel, synthetic adapter SDK, and observe-only ingestion are implemented; action/reconciliation/projection/snapshot layers remain pending |
| Adapter SDK and integrations | 35% | Phase 9 synthetic adapter SDK is implemented; Phase 10 observations use it; real adapters remain prohibited |
| Conformance and kernel testing | 60-65% | Gate A conformance, Gate B kernel/security/crash tests, Phase 9 adapter tests, and Phase 10 observation tests pass locally; projection, transport interoperability, and performance suites remain planned |
| Empirical evaluation | 0% | No pilots, benchmarks, or comparative evaluation have been run |
| Production readiness | 5% | Local kernel durability and authority checks exist; operational hardening, isolation, archive, backup/restore, and threat-model completion remain future phases |

---

## Gate Status

| Gate | Phases | Meaning | Status | Evidence |
|---|---|---|---|---|
| A -- Contract Ready | 1-4 | Architecture decisions, machine contracts, registries, and conformance fixtures are frozen | COMPLETE | `docs/ARCHITECTURE_DECISIONS.md`, `schemas/`, `registries/`, `tests/conformance/` |
| B -- Kernel Ready | 5-8 | Authoritative storage, replay, DAG integrity, rebuildable index, authority, and identity | COMPLETE | `docs/GATE_B_COMPLETION_REPORT.md`, `tests/integration/test_gate_b_kernel_checklist.py` |
| C -- Continuity MVP | 9-15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI | IN PROGRESS | Phase 10 complete locally; hosted CI pending |
| D -- External Compatible | 16-19 | Reference transport, isolated adapters, transport parity, security/durability/archive | BLOCKED | Requires Gate C |
| E -- Research Validated | 20-22 | Heterogeneous pilots, benchmarks, evaluation, reproducible release | BLOCKED | Requires Gate D |

---

## What Is Complete

### Gate A Contract Baseline

The project has frozen:

- architecture decisions that affect identity, transaction validity, authority,
  replay, compatibility, and canonical bytes;
- glossary and MVP scope;
- JSON Schemas for core records and protocol envelopes;
- registries for node types, relationship types, conflict types, capability
  values, error codes, and extension namespaces;
- conformance fixtures, compatibility cases, and canonical hash vectors.

### Gate B Kernel Baseline

The local kernel implements and tests:

- canonical JSON parsing and byte generation;
- UUIDv7-prefixed identifier validation and generation;
- record, payload, transaction, commit, segment, and archive-seal hash helpers;
- workspace initialization;
- content-addressed payload storage with corruption detection;
- append-only JSONL transaction begin/member/commit records;
- writer locking for the local single-writer MVP;
- durable append and replay with incomplete-tail recovery;
- duplicate ID, endpoint, self-loop, cycle, and relationship compatibility checks;
- graph heads, exact-revision reads, bounded lineage traversal, and replay/index
  query equivalence;
- rebuildable non-authoritative SQLite index;
- fixed local authorization profile;
- state-boundary enforcement helpers;
- adapter identity registration without invocation;
- scoped external identity lifecycle handling.

### Gate C Phase 9-10 Continuity Baseline

The local continuity MVP now includes:

- trusted configured in-process adapter SDK modules;
- one validating adapter host path for `describe`, `observe`, `act`,
  `evaluate`, and `reconcile`;
- transactional revisioned, reconstructed filesystem, and asynchronous
  unknown-outcome synthetic systems;
- observe-only ingestion through one validated path;
- authoritative graph records for bounded observation operations, observation
  events, external-state artifact revisions, and evidence/causal edges;
- preservation of external identity, external revision, adapter version,
  state-boundary ID, provenance, payload retention/redaction metadata,
  freshness, consistency limitations, receipt time, and graph commit time;
- deterministic duplicate, stale, conflicting, out-of-order, unknown-ordering,
  absent-revision, rename, deletion, and identity-reuse classifications;
- replay and index rebuild without adapter invocation.

### Current Evidence Base

The Gate B report records passing local validation for:

- lockfile and dependency sync checks;
- formatting, linting, and type checking;
- full repository tests;
- package build and isolated wheel smoke;
- focused Gate B checklist tests;
- hosted CI for the merged Gate B PR.
- hosted CI for Phase 9 on draft PR #2.
- local Phase 10 validation through focused observation ingestion tests,
  formatting, linting, type checking, and full test suite.

---

## What Remains Incomplete

### Phase 11-15: Continuity MVP

The next gate must implement the continuity behavior that makes Guerilla useful
above the observe-only baseline:

- committed intent-before-action;
- idempotency enforcement;
- uncertain-outcome reconciliation;
- conflict lifecycle;
- projections, manifests, diffs, snapshots, resume contexts, and CLI workflows.

No real adapter should be added before internal synthetic adapter conformance
and Gate C completion pass.

### Phase 16-19: External Compatibility

External compatibility remains future work:

- GLCP reference client/server;
- subprocess adapter host;
- transport parity;
- adapter isolation;
- archive rotation and sealed archive verification;
- backup/restore;
- security and durability hardening.

### Phase 20-22: Research Validation

The research claim still needs:

- heterogeneous pilots with materially different state models;
- reproducible benchmarks;
- resume-accuracy and lineage-completeness evaluation;
- comparison against summary-only continuity, conventional logs, workflow
  histories, and provenance-only recording;
- release evidence package.

---

## Current Critical Path

The credible route from the current baseline is:

> Gate B kernel baseline -> synthetic adapters -> observation ingestion -> committed intent and idempotency -> reconciliation and conflicts -> projections -> snapshots and resume -> CLI smoke -> transport and adapter isolation -> heterogeneous pilots -> evaluation.

The central remaining technical contribution is not basic graph storage. It is
demonstrating that one authoritative lineage graph can coordinate heterogeneous
external systems without becoming their application-state owner, especially when
external actions have uncertain outcomes.

---

## Practical Status Statement

A defensible project-status statement is:

> Guerilla has completed Gate B and is in Gate C. Its frozen contracts and local
> kernel can initialize a workspace, append and replay authoritative graph
> transactions, enforce DAG and authority constraints, verify hashes, recover
> incomplete tails, and rebuild non-authoritative indexes. Gate C now includes a
> trusted synthetic adapter SDK and observe-only ingestion that records bounded
> external facts while preserving external authority and revisions. The next
> milestone is Phase 11: committed intent-before-action and graph-backed
> idempotency without adding real integrations or changing Gate A/B contracts.
