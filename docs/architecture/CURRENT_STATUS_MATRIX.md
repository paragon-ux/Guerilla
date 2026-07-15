# Current Status Matrix

**Status:** Gate C in progress -- Phase 14 complete
**Last updated:** 2026-07-14
**Current baseline:** draft Gate C branch `feature/gate-c-continuity-mvp`
**Evidence:** [Gate B completion report](../GATE_B_COMPLETION_REPORT.md), [Phase 9 completion report](../PHASE_09_COMPLETION_REPORT.md), [Phase 12 completion report](../PHASE_12_COMPLETION_REPORT.md), [Phase 13 completion report](../PHASE_13_COMPLETION_REPORT.md), [Phase 14 completion report](../PHASE_14_COMPLETION_REPORT.md), Phase 10 local evidence in `tests/integration/test_phase10_observation_ingestion.py`, Phase 11 local evidence in `tests/integration/test_phase11_action_intent_idempotency.py`, Phase 12 local evidence in `tests/integration/test_phase12_reconciliation_conflicts.py`, Phase 13 local evidence in `tests/integration/test_phase13_projections_manifest_diff.py`, Phase 14 local evidence in `tests/integration/test_phase14_snapshot_resume.py`, [PR #2](https://github.com/paragon-ux/Guerilla/pull/2)

**Hosted CI evidence:** [Gate A closure](https://github.com/paragon-ux/Guerilla/actions/runs/29302019930), [Phase 5](https://github.com/paragon-ux/Guerilla/actions/runs/29302731597), [Phase 6](https://github.com/paragon-ux/Guerilla/actions/runs/29303454247), [Phase 7](https://github.com/paragon-ux/Guerilla/actions/runs/29304114169), [Phase 8](https://github.com/paragon-ux/Guerilla/actions/runs/29304560354), [final Gate B PR validation](https://github.com/paragon-ux/Guerilla/actions/runs/29363456584), [Phase 9 PR validation](https://github.com/paragon-ux/Guerilla/actions/runs/29378512503), [Phase 10 PR validation](https://github.com/paragon-ux/Guerilla/actions/runs/29379475653), [PR #2 checks](https://github.com/paragon-ux/Guerilla/pull/2/checks)

---

## Current Maturity

Guerilla has moved beyond the pre-prototype stage. Gate A and Gate B are
complete, and Gate C is in progress: the architecture decisions, schemas,
registries, fixtures, canonical codec primitives, local append-only graph
kernel, replay path, DAG/index/query surface, local authority/boundary
enforcement, trusted synthetic adapter SDK, observe-only graph ingestion,
graph-backed action intent/idempotency orchestration,
uncertain-outcome reconciliation/conflict lineage, and deterministic derived
projections/manifests/diffs, and verified snapshot/resume contexts are
implemented and tested locally.

The project is now at the **continuity-MVP in progress stage**. Phase 10 is
complete, Phase 11 is complete, Phase 12 is complete, and Phase 13 is
complete, and Phase 14 is complete. CLI workflows, transport bindings, pilots,
and empirical evaluation are not implemented.

| Area | Estimated maturity | Assessment |
|---|---:|---|
| Problem definition and motivation | 95% | Clear standalone thesis: authority-preserving continuity over heterogeneous systems |
| Architectural boundaries | 95% | External systems retain application-state authority; Guerilla owns lineage authority |
| Frozen contracts and schemas | 90% | Gate A complete; schemas, registries, fixtures, and decision vectors are frozen for current protocol `0.2.0` |
| Protocol design | 75% | GLCP core contracts exist; runtime transport bindings and parity tests remain future work |
| Implementation design | 80% | Gate plan, storage/recovery model, state-boundary model, and test matrix are current through Gate B |
| Reference implementation | 75-80% | Local graph kernel, synthetic adapter SDK, observe-only ingestion, action intent/idempotency, reconciliation/conflict lineage, projection/manifest/diff layers, and snapshot/resume layers are implemented; CLI workflows remain pending |
| Adapter SDK and integrations | 45% | Phase 9 synthetic adapter SDK is implemented; Phase 10 observations, Phase 11 actions, and Phase 12 reconciliation use it; real adapters remain prohibited |
| Conformance and kernel testing | 80-85% | Gate A conformance, Gate B kernel/security/crash tests, Phase 9 adapter tests, Phase 10 observation tests, Phase 11 action/idempotency tests, Phase 12 reconciliation/conflict tests, Phase 13 projection tests, and Phase 14 snapshot/resume tests pass locally; transport interoperability and performance suites remain planned |
| Empirical evaluation | 0% | No pilots, benchmarks, or comparative evaluation have been run |
| Production readiness | 5% | Local kernel durability and authority checks exist; operational hardening, isolation, archive, backup/restore, and threat-model completion remain future phases |

---

## Gate Status

| Gate | Phases | Meaning | Status | Evidence |
|---|---|---|---|---|
| A -- Contract Ready | 1-4 | Architecture decisions, machine contracts, registries, and conformance fixtures are frozen | COMPLETE | `docs/ARCHITECTURE_DECISIONS.md`, `schemas/`, `registries/`, `tests/conformance/` |
| B -- Kernel Ready | 5-8 | Authoritative storage, replay, DAG integrity, rebuildable index, authority, and identity | COMPLETE | `docs/GATE_B_COMPLETION_REPORT.md`, `tests/integration/test_gate_b_kernel_checklist.py` |
| C -- Continuity MVP | 9-15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI | IN PROGRESS | Phase 14 complete |
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

### Gate C Phase 9-14 Continuity Baseline

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
- graph-backed action intent records committed before external mutation;
- invocation-start records committed before adapter `act`;
- explicit action-result records preserving external classification, revision,
  evidence, retry, warnings, and limitations;
- idempotency replay and conflict behavior reconstructed from authoritative
  graph replay;
- restart protection for prior invocation without committed result;
- optional after-state observation through the Phase 10 ingestion path.
- reconciliation events appended as new graph records without rewriting intent,
  invocation, or result records;
- missing-lineage recovery that preserves original intent and appends recovered
  result evidence;
- explicit conflicts for unknown outcomes, unsupported reconciliation,
  duplicate attempts, stale external revisions, and incomplete lineage;
- append-only decision and `resolved_by` resolution lineage with optional
  continuation operations.
- deterministic derived lineage, dependency, conflict, manifest, diff,
  progress, and traceability views;
- projection metadata that cites source graph revision, source query, source
  nodes, transformation version, policy version, freshness, information loss,
  and derived authority;
- disposable persisted projection cache files that regenerate from
  authoritative replay;
- rebuilt-index and replay projection agreement without adapter invocation.
- authoritative snapshot records that cite source graph revision, source
  commit, source query, source nodes, transformation version, policy version,
  summary hash, freshness requirements, information loss, actor, and authority;
- `captured_by` lineage from included source records to snapshot records;
- derived materialized snapshot summaries that can be deleted or corrupted
  without losing authoritative continuity;
- bounded resume contexts that separate authoritative facts, derived summaries,
  stale observations, unknown outcomes, pending reconciliation, refresh
  requirements, unresolved conflicts, relevant artifact revisions, and omitted
  information without executing actions.

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
- local Phase 11 validation through focused action intent/idempotency tests,
  formatting, linting, type checking, package build, and isolated wheel smoke.
- local Phase 12 validation through focused reconciliation/conflict tests,
  formatting, linting, and type checking.
- local Phase 13 validation through focused projection/manifest/diff tests,
  formatting, linting, and type checking.
- local Phase 14 validation through focused snapshot/resume tests, formatting,
  linting, and type checking.

---

## What Remains Incomplete

### Phase 15: Continuity MVP

The next gate must implement the continuity behavior that makes Guerilla useful
above the snapshot/resume baseline:

- CLI workflows.

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

The central remaining technical contribution is no longer basic graph storage
or uncertain-action recovery. It is demonstrating that CLI workflows can drive
the implemented continuity primitives without becoming a second
application-state owner.

---

## Practical Status Statement

A defensible project-status statement is:

> Guerilla has completed Gate B and is in Gate C. Its frozen contracts and local
> kernel can initialize a workspace, append and replay authoritative graph
> transactions, enforce DAG and authority constraints, verify hashes, recover
> incomplete tails, and rebuild non-authoritative indexes. Gate C now includes a
> trusted synthetic adapter SDK, observe-only ingestion that records bounded
> external facts while preserving external authority and revisions,
> graph-backed action intent/idempotency that prevents unsafe duplicate
> mutations, reconciliation/conflict lineage that makes uncertain outcomes
> explicit without rewriting history, and deterministic derived projections,
> manifests, and diffs that cite their source graph revisions without becoming
> authoritative, plus verified snapshots and resume contexts that regenerate
> from authoritative lineage. The next milestone is Phase 15: internal CLI,
> end-to-end, and smoke workflows without adding real integrations or changing
> Gate A/B contracts.
