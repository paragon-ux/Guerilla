---
name: guerilla-contracts-modeling
description: Defines and reviews Guerilla architecture decisions, schemas, registries, canonicalization fixtures, and compatibility contracts. Use during Phases 2-4 or whenever record identity, transaction validity, authority, or replay semantics are affected.
---

# guerilla-contracts-modeling

**Skill:** Contracts, schemas, registries, and fixture modeling
**Owner phase:** Phase 2 (Architecture Decisions), Phase 3 (Machine Contracts), Phase 4 (Conformance Fixtures)
**File:** `.agents/skills/guerilla-contracts-modeling/SKILL.md`

---

## 1. Purpose

Own the machine-readable contract surface of Guerilla. This skill governs architecture decisions affecting contracts, JSON Schemas, registries, canonicalization fixtures, data-model consistency, authority envelopes, protocol envelopes, errors, and compatibility review.

---

## 2. Activation Criteria

Activate when the task involves:

- Creating, modifying, or reviewing any file under `schemas/` or `registries/`.
- Freezing architecture decisions that affect record identity, transaction validity, authority, or replay semantics.
- Defining or changing node types, relationship types, error codes, or capability values.
- Creating valid/invalid conformance fixtures for canonicalization, hashing, or record validation.
- Resolving terminology conflicts across specifications.
- Reviewing extension namespace governance.

---

## 3. Non-Activation Criteria

Do NOT activate when the task involves:

- Implementing storage, replay, or the graph kernel (delegate to `guerilla-graph-kernel-storage`).
- Implementing adapter behavior, observation ingestion, or reconciliation (delegate to `guerilla-adapter-continuity-reconciliation`).
- Generating projections, manifests, or snapshots (delegate to `guerilla-projections-snapshot-resume`).
- Writing tests unrelated to schema or registry conformance (delegate to `guerilla-testing-security-evaluation`).
- Phase 1 repository scaffolding that does not involve contract decisions.

---

## 4. Required Reading

Before any contract work, read in order:

1. `AGENTS.md` -- locked invariants and source-of-truth order
2. `docs/architecture/GUERILLA_CONCEPT_PAPER.md` -- state ownership, graph thesis, eight core node types, nine core relationship types
3. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md` -- Sections 6-8 (canonical encoding, hashing, identifiers, record model), Sections 33-37 (MVP requirements, acceptance criteria)
4. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md` -- Sections 5-8 (envelope, actor, correlation, request/response), Section 25 (error model)
5. `docs/architecture/GUERILLA_SNAPSHOT.md` -- Sections 3 (accepted decisions), 7 (unresolved questions)
6. `docs/ARCHITECTURE_DECISIONS.md` (once created in Phase 2)

---

## 5. Owned Artifacts

This skill owns:

- `docs/ARCHITECTURE_DECISIONS.md` -- architecture decisions that affect contracts
- `docs/GLOSSARY.md` -- canonical terminology
- `docs/MVP_SCOPE.md` -- MVP boundary and acceptance criteria
- `docs/DATA_MODEL.md` -- node, edge, and record model specification
- `docs/GRAPH_RECORD_FORMAT.md` -- byte-level record layout and hash construction
- `docs/GLCP_CORE_SPEC.md` -- transport-independent protocol contract
- `docs/ADAPTER_CONTRACT.md` -- adapter descriptor, capability, and invocation contract
- `docs/STATE_BOUNDARY_MODEL.md` -- authority and state-boundary specification
- `docs/ERROR_REGISTRY.md` -- machine-readable error codes and classifications
- `schemas/*.schema.json` -- all versioned JSON Schemas (Phase 3+)
- `registries/*.json` -- all enum, capability, error, and extension registries (Phase 3+)
- `tests/fixtures/contracts/` -- valid, invalid, compatibility, and canonicalization fixtures (Phase 4)

---

## 6. Invariants

When working on contracts, these MUST NOT be violated:

- Every core record (node, edge, transaction, commit, snapshot) must have a versioned JSON Schema.
- Every enum value (node types, relationship types, error codes, capabilities) must be registered.
- Canonicalization and hash construction must be published with test vectors.
- Two independent validation paths must return the same result for every fixture.
- No unresolved architecture choice may change record identity, transaction validity, authority, or replay semantics.
- Schemas and registries are versioned; changing a published schema requires a new version.
- Unknown critical fields must cause rejection; unknown optional fields may be tolerated only when permitted by compatibility rules.
- Extension namespaces must be registered with owner, version, compatibility range, schemas, invariants, downgrade behavior, and security implications.
- An extension MUST NOT redefine the meaning of a core field or relationship type.

---

## 7. Ordered Procedure

### Phase 2 -- Architecture Decisions

1. Read the four core architecture papers and the rationale note.
2. Identify every unresolved decision listed in `GUERILLA_SNAPSHOT.md` Section 7.
3. For each decision, propose a concrete resolution with rationale, alternatives considered, and impact on downstream contracts.
4. Write `docs/ARCHITECTURE_DECISIONS.md` with version, date, status, and rationale for each decision.
5. Write `docs/GLOSSARY.md` with every defined term and locked distinction.
6. Write `docs/MVP_SCOPE.md` with mandatory and excluded capabilities.
7. Verify that all four architecture papers use consistent terminology for all 20 defined terms.

### Phase 3 -- Machine Contracts

1. Finalize the canonical JSON profile selection and identifier scheme (UUIDv7 or ULID).
2. Write all 20 JSON Schemas under `schemas/`.
3. Write all 6 registries under `registries/`.
4. Write `docs/DATA_MODEL.md`, `docs/GRAPH_RECORD_FORMAT.md`, `docs/GLCP_CORE_SPEC.md`.
5. Write `docs/ADAPTER_CONTRACT.md`, `docs/STATE_BOUNDARY_MODEL.md`, `docs/ERROR_REGISTRY.md`.
6. Update `docs/TEST_MATRIX.md` with contract-conformance test entries.

### Phase 4 -- Conformance Fixtures

1. Create valid fixtures for every record type and message envelope.
2. Create invalid fixtures for every required validation rule.
3. Create compatibility fixtures for version negotiation and unknown fields.
4. Create canonicalization fixtures with published hash vectors.
5. Verify that two independent validation implementations produce identical results.

---

## 8. Tests

Contract-conformance tests must verify:

- Every schema validates its intended valid instances and rejects its intended invalid instances.
- Every registry entry is referenced by at least one schema.
- Canonicalization fixtures produce identical hashes across implementations.
- Error codes are stable and machine-readable.
- Extension schemas do not redefine core fields.
- Version negotiation and compatibility rules are enforced.

Test commands follow the project standard: `uv run pytest tests/conformance/`.

---

## 9. Failure Cases

Design contracts to handle:

- Missing required fields -- reject with `schema_violation`.
- Unknown critical fields -- reject with `schema_violation`.
- Unsupported protocol version -- reject with `unsupported_version`.
- Invalid identifier format -- reject with `invalid_message`.
- Duplicate identifiers -- reject with `duplicate_id`.
- Extension namespace collision -- reject with `identity_collision`.
- Hash mismatch -- reject with `record_hash_mismatch` or `payload_hash_mismatch`.

---

## 10. Stop Conditions

Stop work on the affected contract and report the blocker if:

- An architecture decision contradicts a locked invariant.
- Two architecture papers use materially different definitions for the same term.
- A schema change would alter record identity, hashing, or replay semantics.
- An extension proposes to redefine a core field.
- A fixture produces different results across independent validators.
- A required decision is blocked by an unresolved upstream decision.

---

## 11. Completion Evidence

Completion of contract work requires:

- Versioned, committed schemas and registries.
- A frozen `ARCHITECTURE_DECISIONS.md` with no open decisions affecting record identity or replay.
- A cross-document terminology matrix showing consistency.
- Passing conformance fixtures with published hash vectors.
- Two independent validation paths returning identical results for every fixture.

---

## 12. Handoff

After completing contract work, hand off to:

- `guerilla-graph-kernel-storage` -- for codec implementation, storage, and replay.
- `guerilla-adapter-continuity-reconciliation` -- for adapter descriptor and invocation contracts.
- `guerilla-projections-snapshot-resume` -- for projection metadata and snapshot schemas.
- `guerilla-testing-security-evaluation` -- for conformance fixture validation.
