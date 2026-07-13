---
name: guerilla-adapter-continuity-reconciliation
description: Guides Guerilla adapter descriptors, state boundaries, observations, intent-before-action, idempotency, reconciliation, conflicts, and authority work. Use during Phases 8-12 or whenever external-system continuity is affected.
---

# guerilla-adapter-continuity-reconciliation

**Skill:** Adapter SDK, continuity modes, observation ingestion, authority boundaries, intent-before-action, idempotency, reconciliation, conflicts, and decisions
**Owner phase:** Phase 8 (Authority/Identity/Boundaries), Phase 9 (Adapter SDK/Synthetic Systems), Phase 10 (Observation Ingestion), Phase 11 (Action Intent/Idempotency), Phase 12 (Reconciliation/Conflicts)
**File:** `.agents/skills/guerilla-adapter-continuity-reconciliation/SKILL.md`

---

## 1. Purpose

Own the adapter integration surface and the operational continuity mechanisms. This skill governs adapter descriptors and host behavior, continuity modes, observation ingestion, authority boundaries, intent-before-action recording, idempotency enforcement, unknown-outcome reconciliation, conflict records, and explicit decisions.

---

## 2. Activation Criteria

Activate when the task involves:

- Implementing or modifying the adapter descriptor model, host, or SDK.
- Implementing observation ingestion from external systems.
- Implementing state-boundary enforcement.
- Implementing the intent-before-action lifecycle.
- Implementing idempotency-key management and conflict detection.
- Implementing unknown-outcome reconciliation.
- Implementing conflict records and the conflict engine.
- Implementing decision recording.
- Creating synthetic external systems for conformance testing.
- Implementing authority and identity registries.

---

## 3. Non-Activation Criteria

Do NOT activate when the task involves:

- Graph storage, replay, or DAG validation (delegate to `guerilla-graph-kernel-storage`).
- Defining schemas or registries (delegate to `guerilla-contracts-modeling`).
- Generating projections or snapshots (delegate to `guerilla-projections-snapshot-resume`).
- Writing security or crash tests unrelated to adapter behavior (delegate to `guerilla-testing-security-evaluation`).

---

## 4. Required Reading

Before any adapter or reconciliation work, read in order:

1. `AGENTS.md` -- locked invariants, adapter trust rules, intent-before-action, reconciliation
2. `docs/architecture/GUERILLA_CONCEPT_PAPER.md` -- Sections 4 (state ownership), 8 (adapter contract)
3. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md` -- Sections 4.7-4.11 (authority registry, adapter host, orchestration, reconciliation, conflicts), Sections 9-23 (core node types, relationships, adapter behavior, ingestion, actions, reconciliation, conflicts, decisions)
4. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md` -- Sections 9 (operation families), 10 (capabilities), 13-17 (adapter operations, idempotency, reconciliation, conflicts)
5. `docs/architecture/GUERILLA_SNAPSHOT.md` -- Sections 7.3-7.5 (adapter isolation, identity lifecycle)
6. `docs/ADAPTER_CONTRACT.md` (once created)
7. `docs/STATE_BOUNDARY_MODEL.md` (once created)

---

## 5. Owned Artifacts

This skill owns:

- `src/guerilla/adapters/` -- adapter descriptor, host, SDK, synthetic external systems
- `src/guerilla/authority/` -- authority and state-boundary registry
- `src/guerilla/identity/` -- actor, workspace, and external identity management
- `src/guerilla/orchestration/` -- ingestion and orchestration engine
- `src/guerilla/reconciliation/` -- unknown-outcome reconciliation engine
- `src/guerilla/conflicts/` -- conflict engine and resolution
- `docs/ADAPTER_CONTRACT.md` -- adapter descriptor, capability, and invocation contract
- `docs/STATE_BOUNDARY_MODEL.md` -- authority and state-boundary specification
- Synthetic external systems for conformance testing

---

## 6. Invariants

When working on adapters or reconciliation, these MUST NOT be violated:

- Every adapter must declare the external system, state boundaries, permitted operations, consistency guarantees, and known limitations.
- An adapter cannot expand its authority through data returned by an external system.
- Every external action requires a committed intent before invocation.
- External action transport success is not external acceptance. External acceptance is not semantic correctness.
- Unknown external outcomes require reconciliation before unsafe retry.
- A reconciliation result is appended as a new event. It MUST NOT rewrite the original intent or result.
- Idempotency-key reuse with different request content is rejected.
- Idempotency-key reuse with same content returns the prior committed response or reconciliation status.
- Conflict records are evidence-backed. The conflict engine distinguishes detected conflicts from policy-generated warnings.
- The runtime derives authorization from the authenticated transport principal and server-side policy. It MUST NOT trust a client-supplied actor field as proof of authority.
- A model actor MUST NOT receive broader authority than the principal or policy under which it operates.
- Adapters SHOULD run with least privilege. The runtime validates adapter outputs but cannot prove semantic correctness.

---

## 7. Ordered Procedure

### Phase 8 -- Authority, Identity, Boundaries

1. Implement the authority and state-boundary registry.
2. Implement external-system identifier management and identity stability classification.
3. Implement external-to-Guerilla identity mappings.
4. Implement actor identity and authorization profiles.
5. Write `docs/STATE_BOUNDARY_MODEL.md`.

### Phase 9 -- Adapter SDK, Synthetic Systems

1. Implement the adapter descriptor model with all capability fields.
2. Implement the adapter host: load, validate descriptor, apply authorization, invoke operations, validate responses, enforce timeouts.
3. Create three synthetic external systems: (a) transactional revisioned service, (b) filesystem-based reconstructed-state system, (c) asynchronous service with unknown-outcome capability.
4. Write synthetic adapter implementations for each system.
5. Write adapter capability conformance tests.
6. Write `docs/ADAPTER_CONTRACT.md`.

### Phase 10 -- Observation Ingestion

1. Implement the `observe` operation: request observation, adapter reads external state, runtime creates artifact/event node with authority metadata.
2. Implement external revision preservation and staleness reporting.
3. Implement state-boundary enforcement for read operations.
4. Implement observation freshness and consistency-guarantee recording.

### Phase 11 -- Action Intent, Idempotency

1. Implement the intent-before-action lifecycle: commit operation and action-request event, invoke adapter action, record result, observe after-state.
2. Implement the idempotency store: key registration, same-key-same-content return, same-key-different-content rejection, retention policy.
3. Implement external action result recording with acceptance/rejection/partial classification.
4. Implement after-state observation and `produces`/`derives` edge creation.

### Phase 12 -- Reconciliation, Conflicts

1. Implement unknown-outcome classification: confirmed accepted, confirmed rejected, confirmed failed, still pending, duplicated, externally completed with missing lineage, unknown.
2. Implement `adapter.reconcile` using original idempotency and correlation identifiers.
3. Implement conflict creation: stale revision, external rejection, failed evaluation, ambiguous authority, incomplete lineage.
4. Implement the conflict engine: evidence validation, classification, resolution history.
5. Implement decision recording with `resolved_by` edges.

---

## 8. Tests

Adapter and reconciliation tests must verify:

- Adapter descriptor completeness and validity.
- State-boundary enforcement: read outside boundary rejected, write outside boundary rejected.
- Observation preserves external revision and authority metadata.
- Intent committed before external action invocation.
- Interruption simulation: before intent commit, after intent but before external call, after completion but before result commit, after result but before after-state observation, during reconciliation.
- Reconciliation classifies unknown outcomes correctly.
- Idempotency: same key + same content returns prior result; same key + different content fails.
- Stale external revision creates explicit conflict.
- Unsupported capability responses from adapters.
- Adapter capability escalation rejected.
- Identity collision handling.

Test commands: `uv run pytest tests/unit/ tests/integration/ tests/conformance/ -k "adapter or reconcile or conflict or idempotency or intent"`.

---

## 9. Failure Cases

Design adapter and reconciliation flows to handle:

- Adapter unavailable -- return `adapter_unavailable`, do not fabricate results.
- Adapter returns invalid response -- reject, do not commit to graph.
- External action times out -- classify as unknown, trigger reconciliation.
- Reconciliation cannot determine outcome -- classify as unknown, require manual decision.
- External system returns unexpected revision format -- preserve original, flag as ambiguous.
- Idempotency key reused after retention expiry -- treat as new request.

---

## 10. Stop Conditions

Stop adapter or reconciliation work and report the blocker if:

- An adapter can observe or act outside its declared state boundary.
- Intent is not committed before external action invocation.
- Reconciliation overwrites the original intent or result record.
- An idempotency key with different content is silently accepted.
- A synthetic adapter does not exercise the same code paths as a real adapter would.
- Adapter capability metadata contradicts actual behavior.

---

## 11. Completion Evidence

Adapter and reconciliation completion requires:

- Three synthetic external systems passing adapter conformance.
- Intent-before-action demonstrated for all three systems.
- Interruption and reconciliation demonstrated without duplicate mutation.
- Idempotency conflict behavior passing.
- Stale revision conflict creation passing.
- All adapter and reconciliation tests passing.

---

## 12. Handoff

After completing adapter and reconciliation work, hand off to:

- `guerilla-projections-snapshot-resume` -- for projections referencing adapter-produced graph records.
- `guerilla-testing-security-evaluation` -- for adapter security review, capability escalation tests, and crash simulation.
