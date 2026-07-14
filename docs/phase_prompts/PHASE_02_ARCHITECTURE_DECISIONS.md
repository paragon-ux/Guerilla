# Phase 2 - Architecture Decisions

**Status:** PASS - Phase 2 complete
**Gate:** A - Contract Ready
**Owner phase:** Phase 2 (Architecture Decisions)
**Required predecessor:** Phase 1 PASS with reproducible lockfile, valid skills, source-integrity enforcement, isolated wheel smoke evidence, and updated status surfaces

> **Completion note:** Phase 2 froze architecture decisions, glossary terminology, MVP scope, and decision vectors. Phase 3 and Phase 4 have since completed Gate A. Runtime implementation remains out of scope for this prompt.

---

## 1. Phase Objective

Freeze the architecture decisions that can affect record identity, transaction validity, authority rules, replay behavior, compatibility, and downstream machine-readable contracts.

---

## 2. Permitted Scope

Phase 2 may update only architecture-decision and planning documents:

- `docs/ARCHITECTURE_DECISIONS.md`
- `docs/GLOSSARY.md`
- `docs/MVP_SCOPE.md`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- `docs/phase_prompts/PHASE_02_ARCHITECTURE_DECISIONS.md`

Phase 2 may add decision-oriented tests or executable vectors only when they do not implement runtime graph, storage, adapter, protocol, or projection behavior.

---

## 3. Prohibited Scope

Phase 2 must not implement:

- schemas or registries;
- canonical JSON codec behavior;
- identifier generation;
- record, payload, transaction, or commit hashing;
- graph storage, replay, DAG validation, or indexing;
- adapters, synthetic external systems, observations, actions, reconciliation, conflicts, projections, snapshots, transports, services, or UI.

---

## 4. Required Source Documents

Read in order:

1. `AGENTS.md`
2. `docs/architecture/GUERILLA_CONCEPT_PAPER.md`
3. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md`
4. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md`
5. `docs/architecture/GUERILLA_SNAPSHOT.md`
6. `docs/architecture/CURRENT_STATUS_MATRIX.md`
7. `docs/architecture/RELATED_WORK.md`
8. `docs/rationale/Note-on-Architecture.md`
9. `docs/GUERILLA_WORKFLOW_CURRENT.md`
10. `docs/phase_prompts/Guerilla-Kickoff-Prompt.md`

---

## 5. Invariants That Cannot Change

All locked invariants in `AGENTS.md` remain controlling. In particular:

- one logically authoritative Guerilla graph exists per workspace;
- committed graph history is append-only and immutable;
- direct authoritative edges form a DAG;
- external systems retain application-state authority;
- every external action requires committed intent before invocation;
- graph replay never re-executes external actions;
- projections, manifests, snapshots, diffs, indexes, and caches are derived and non-authoritative;
- missing or contradictory contracts block mutation rather than trigger guessing.

---

## 6. Implementation Tasks

1. Confirm Phase 1 closure evidence and stop if any blocker remains.
2. Inventory unresolved decisions from `GUERILLA_SNAPSHOT.md` and the implementation/protocol specifications.
3. Resolve canonical JSON profile selection.
4. Resolve UUIDv7 versus ULID and identifier prefix rules.
5. Resolve record hash, payload hash, transaction hash, and commit hash inputs.
6. Resolve transaction ordering and canonical record order.
7. Resolve writer-lock, atomic append, flush, fsync, and recovery policy.
8. Resolve local and network filesystem support boundaries.
9. Resolve payload retention and redaction defaults.
10. Resolve MVP adapter execution model and authorization profile.
11. Resolve projection policy representation.
12. Resolve archive thresholds and sealed-segment rules.
13. Resolve extension namespace governance.
14. Update `ARCHITECTURE_DECISIONS.md`, `GLOSSARY.md`, and `MVP_SCOPE.md`.
15. Update downstream placeholders only to reflect frozen decisions, without implementing Phase 3+ contracts.

---

## 7. Required Tests and Evidence

Phase 2 evidence must include:

- terminology consistency checks across the four architecture papers and Phase 2 documents;
- decision coverage checks proving every unresolved item is resolved or explicitly deferred without affecting identity, validity, authority, or replay;
- any canonicalization or identifier decision vectors needed to guide Phase 3, without implementing the runtime codec.

---

## 8. Failure and Crash Cases

Phase 2 must document how later phases will test:

- canonicalization mismatch;
- identifier collision;
- hash mismatch;
- incomplete transaction recovery;
- local writer contention;
- stale external revision;
- unknown external action outcome;
- projection staleness.

No Phase 2 test may fabricate graph records as accepted runtime behavior.

---

## 9. Documentation Regeneration

Regenerate or update:

- `docs/ARCHITECTURE_DECISIONS.md`
- `docs/GLOSSARY.md`
- `docs/MVP_SCOPE.md`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- this prompt, if its scope changes

Architecture papers are not rewritten in Phase 2. Corrections go through `ARCHITECTURE_DECISIONS.md`.

---

## 10. Exit Criteria

Phase 2 is complete only when:

1. every decision affecting record identity, transaction validity, authority, or replay is frozen;
2. no unresolved choice can change Phase 3 schemas or Phase 5 hash/codec behavior;
3. `ARCHITECTURE_DECISIONS.md`, `GLOSSARY.md`, and `MVP_SCOPE.md` are no longer placeholders;
4. terminology is consistent across controlled sources;
5. no schemas, registries, runtime modules, adapters, transports, or projection implementations were introduced;
6. validation evidence is linked for every completion claim.

---

## 11. Completion Report Format

Use the repository-standard phase completion format from `AGENTS.md`:

- Phase Result
- Delivered Artifacts
- Validation Evidence
- Exit-Criteria Matrix
- Scope Audit
- Blockers and Contradictions
- Phase Handoff

---

## 12. Stop Conditions

Stop and report the blocker if:

- Phase 1 closure is not accepted;
- an authorized source is missing or unreadable;
- two controlling sources conflict in a way that changes Phase 2 scope;
- a decision would violate a locked invariant;
- a decision would require a Phase 3 schema or Phase 5 runtime implementation to justify it;
- the work would modify imported architecture papers instead of recording decisions.
