# Current Status Matrix

**Status:** Gate B complete -- Kernel Ready
**Last updated:** 2026-07-14
**Current baseline:** `05183d61fecc668362e145624385832f50851f31`
**Evidence:** `docs/GATE_B_COMPLETION_REPORT.md`, PR #1 merged to `main`

---

## Current Maturity

Guerilla has moved beyond the pre-prototype stage. Gate A and Gate B are
complete: the architecture decisions, schemas, registries, fixtures, canonical
codec primitives, local append-only graph kernel, replay path, DAG/index/query
surface, and local authority/boundary enforcement are implemented and tested.

The project is now at the **kernel-ready / pre-continuity-MVP stage**. Phase 9
has not started, and no adapter runtime, observations, external actions,
reconciliation engine, projections, snapshots, transport bindings, pilots, or
empirical evaluation are implemented.

| Area | Estimated maturity | Assessment |
|---|---:|---|
| Problem definition and motivation | 95% | Clear standalone thesis: authority-preserving continuity over heterogeneous systems |
| Architectural boundaries | 95% | External systems retain application-state authority; Guerilla owns lineage authority |
| Frozen contracts and schemas | 90% | Gate A complete; schemas, registries, fixtures, and decision vectors are frozen for current protocol `0.2.0` |
| Protocol design | 75% | GLCP core contracts exist; runtime transport bindings and parity tests remain future work |
| Implementation design | 80% | Gate plan, storage/recovery model, state-boundary model, and test matrix are current through Gate B |
| Reference implementation | 40% | Local graph kernel is implemented; continuity MVP behavior remains pending |
| Adapter SDK and integrations | 0% | Phase 9 synthetic adapter SDK has not started; real adapters remain prohibited |
| Conformance and kernel testing | 60% | Gate A conformance and Gate B kernel/security/crash tests pass; adapter/projection/security/performance suites remain planned |
| Empirical evaluation | 0% | No pilots, benchmarks, or comparative evaluation have been run |
| Production readiness | 5% | Local kernel durability and authority checks exist; operational hardening, isolation, archive, backup/restore, and threat-model completion remain future phases |

---

## Gate Status

| Gate | Phases | Meaning | Status | Evidence |
|---|---|---|---|---|
| A -- Contract Ready | 1-4 | Architecture decisions, machine contracts, registries, and conformance fixtures are frozen | COMPLETE | `docs/ARCHITECTURE_DECISIONS.md`, `schemas/`, `registries/`, `tests/conformance/` |
| B -- Kernel Ready | 5-8 | Authoritative storage, replay, DAG integrity, rebuildable index, authority, and identity | COMPLETE | `docs/GATE_B_COMPLETION_REPORT.md`, `tests/integration/test_gate_b_kernel_checklist.py` |
| C -- Continuity MVP | 9-15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI | PENDING | Phase 9 not started |
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

### Current Evidence Base

The Gate B report records passing local validation for:

- lockfile and dependency sync checks;
- formatting, linting, and type checking;
- full repository tests;
- package build and isolated wheel smoke;
- focused Gate B checklist tests;
- hosted CI for the merged Gate B PR.

---

## What Remains Incomplete

### Phase 9-15: Continuity MVP

The next gate must implement the continuity behavior that makes Guerilla useful
above the kernel:

- synthetic adapter SDK;
- adapter `describe`, `observe`, `act`, `evaluate`, and `reconcile` surfaces;
- bounded observation ingestion;
- committed intent-before-action;
- idempotency enforcement;
- uncertain-outcome reconciliation;
- conflict lifecycle;
- projections, manifests, diffs, snapshots, resume contexts, and CLI workflows.

No real adapter should be added before synthetic adapter conformance passes.

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

> Guerilla has completed Gate B. Its frozen contracts and local kernel can
> initialize a workspace, append and replay authoritative graph transactions,
> enforce DAG and authority constraints, verify hashes, recover incomplete
> tails, and rebuild non-authoritative indexes. The next milestone is Phase 9:
> a synthetic adapter SDK and testbed that exercises bounded observations,
> intent-before-action, idempotency, and reconciliation without adding real
> integrations or changing the Gate B kernel contract.
