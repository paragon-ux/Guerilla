---
name: guerilla-graph-kernel-storage
description: Guides Guerilla graph kernel, append-only storage, transaction, replay, DAG integrity, payload, lock, and rebuildable index work. Use during Phases 5-7 or whenever authoritative graph storage behavior is affected.
---

# guerilla-graph-kernel-storage

**Skill:** Graph kernel, append-only storage, transactions, DAG integrity, replay, and indexing
**Owner phase:** Phase 5 (Codec/Config/Identifiers), Phase 6 (Append Store/Transactions/Replay), Phase 7 (DAG Integrity/Index/Query)
**File:** `.agents/skills/guerilla-graph-kernel-storage/SKILL.md`

---

## 1. Purpose

Own the authoritative graph storage core. This skill governs codec integration, append-only persistence, transaction management, commit-chain integrity, DAG validation, deterministic replay, graph verification, writer locking, payload references, and the rebuildable SQLite query index.

---

## 2. Activation Criteria

Activate when the task involves:

- Implementing or modifying canonical JSON encoding, record hashing, or commit-hash chain construction.
- Implementing the append-only JSON Lines graph store (`active.jsonl`, archive segments).
- Implementing transaction begin/commit, atomic append, and incomplete-transaction recovery.
- Implementing DAG validation: cycle detection, endpoint existence, relationship-type compatibility, self-loop rejection.
- Implementing graph replay, verification, and graph-head calculation.
- Implementing the writer lock.
- Implementing payload hashing and the content-addressed payload store.
- Implementing the rebuildable SQLite index.
- Workspace initialization and graph-header management.

---

## 3. Non-Activation Criteria

Do NOT activate when the task involves:

- Defining schemas or registries (delegate to `guerilla-contracts-modeling`).
- Implementing adapter observation, action, or reconciliation (delegate to `guerilla-adapter-continuity-reconciliation`).
- Generating projections, manifests, or snapshots (delegate to `guerilla-projections-snapshot-resume`).
- Writing security, crash, or performance tests (delegate to `guerilla-testing-security-evaluation`).

---

## 4. Required Reading

Before any kernel work, read in order:

1. `AGENTS.md` -- locked invariants, mutation and validation ordering, authoritative vs derived storage
2. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md` -- Sections 4-6 (components, workspace layout, canonical encoding), Sections 24-28 (validation pipeline, transactions, replay, indexing, archiving)
3. `docs/architecture/GUERILLA_CONCEPT_PAPER.md` -- Section 5 (single-DAG model, branching, convergence, acyclicity)
4. `docs/architecture/GUERILLA_SNAPSHOT.md` -- Sections 5-6 (implementation status, MVP boundary)
5. `docs/DATA_MODEL.md` (once created) -- node and edge record layouts
6. `docs/GRAPH_RECORD_FORMAT.md` (once created) -- byte-level record and hash construction
7. `docs/STORAGE_AND_RECOVERY.md` (once created) -- persistence, durability, crash recovery

---

## 5. Owned Artifacts

This skill owns:

- `src/guerilla/codec/` -- canonical encoding, hashing, record parsing/serialization
- `src/guerilla/storage/` -- append-only graph store, archive segments, writer lock
- `src/guerilla/graph/` -- node/edge model, DAG validation, graph heads, replay, verification
- `src/guerilla/payloads/` -- content-addressed payload store
- `src/guerilla/index/` -- rebuildable SQLite query index
- `src/guerilla/config/` -- workspace configuration and policy loader
- `docs/STORAGE_AND_RECOVERY.md` -- storage, durability, and recovery specification

---

## 6. Invariants

When working on the kernel, these MUST NOT be violated:

- Committed graph records are append-only and immutable.
- Every committed transaction produces a monotonically increasing graph revision with a unique commit hash.
- Direct authoritative edges form a DAG. Cycle detection must reject any edge that would create a directed cycle.
- Self-loops are rejected.
- Incomplete or invalid transactions are ignored during replay and reported as recovery warnings.
- Replay reconstructs graph state without repeating external actions.
- The SQLite index is rebuildable from authoritative graph records and payload references.
- An index mismatch causes the affected index to be discarded or marked invalid. The runtime MUST NOT repair authoritative records from index contents.
- The writer lock serializes all graph mutations. Concurrent append attempts must be rejected.
- Payload hashes are verified on read. Hash mismatch fails verification.
- Temporary and uncommitted files are never treated as graph state.

---

## 7. Ordered Procedure

### Phase 5 -- Codec, Config, Identifiers

1. Implement the canonical JSON codec: UTF-8, LF, lexicographically sorted keys for hash input, no insignificant whitespace in hash input, array order preserved, RFC 3339 UTC timestamps.
2. Implement SHA-256 record, payload, transaction, commit, and segment hash calculation.
3. Implement identifier generation (UUIDv7 or ULID with stable prefixes per the architecture decision).
4. Implement the workspace configuration loader reading from `.guerilla/config.toml`.
5. Write `docs/STORAGE_AND_RECOVERY.md`.

### Phase 6 -- Append Store, Transactions, Replay

1. Implement workspace initialization (graph header, directory structure, writer lock).
2. Implement the append-only JSON Lines graph store: active segment and archive segments.
3. Implement transaction begin and commit records with hash-chain integrity.
4. Implement atomic append with flush and fsync.
5. Implement the writer lock.
6. Implement replay: validate segment and commit chains, parse transactions, ignore incomplete transactions, verify hashes, rebuild node/edge maps, validate endpoints and acyclicity.
7. Implement graph verification.

### Phase 7 -- DAG Integrity, Index, Query

1. Implement node and edge validation: uniqueness, endpoint existence, relationship-type compatibility.
2. Implement cycle detection (reject any edge that would create a directed cycle).
3. Implement self-loop rejection.
4. Implement graph-head calculation.
5. Implement the rebuildable SQLite index.
6. Implement index rebuild from authoritative records.
7. Implement basic graph queries (node by id, nodes by type, edges by source/destination/type, lineage traversal).

---

## 8. Tests

Graph kernel tests must verify:

- Atomic commit: all-or-nothing transaction append.
- Incomplete transaction exclusion on replay.
- Previous-commit mismatch rejection.
- Transaction-hash mismatch rejection.
- Monotonic graph revision enforcement.
- Concurrent append rejection under writer lock.
- Direct cycle rejection.
- Self-loop rejection.
- Missing endpoint rejection.
- Linear ancestry, branching, multi-parent convergence, supersession.
- Deterministic replay producing identical graph state.
- Index deletion and lossless rebuild.
- Payload hash verification on read.
- Workspace initialization and verification.

Test commands: `uv run pytest tests/unit/ tests/integration/ -k "storage or graph or codec or index"`.

---

## 9. Failure Cases

Design the kernel to handle:

- Crash during transaction append -- incomplete transaction ignored on replay.
- Corrupt graph segment -- verification fails with explicit error.
- Disk full during append -- transaction rejected, graph unchanged.
- Lock file stale -- lock acquisition fails with diagnostic.
- Payload hash mismatch on read -- verification failure, operation rejected.
- Index corruption -- index discarded and rebuilt.
- Missing archive segment -- replay fails explicitly.

---

## 10. Stop Conditions

Stop kernel work and report the blocker if:

- Canonicalization produces different hashes for semantically identical records.
- Replay is not deterministic.
- A proposed edge creates a cycle that the detector does not catch.
- Index rebuild loses information present in the authoritative graph.
- The writer lock fails to prevent concurrent mutation.
- A hash-chain break cannot be distinguished from a missing segment.
- An architecture decision changes record identity or hash construction after code is written.

---

## 11. Completion Evidence

Kernel completion requires:

- Workspace initialization and verification passing.
- Atomic valid transaction commit passing.
- Incomplete transaction exclusion on replay passing.
- Cycle rejection passing.
- Graph replay deterministic and passing.
- Index deletion and lossless rebuild passing.
- All kernel unit and integration tests passing.

---

## 12. Handoff

After completing kernel work, hand off to:

- `guerilla-adapter-continuity-reconciliation` -- for adapter SDK, observation ingestion, and safe external actions.
- `guerilla-projections-snapshot-resume` -- for projections built on the verified graph.
- `guerilla-testing-security-evaluation` -- for crash simulation and performance measurement.
