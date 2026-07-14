# Storage and Recovery

**Status:** Gate B in progress -- Phase 6 local append/replay implemented
**Owner phase:** Phase 5 (Codec/Config), Phase 6 (Append Store/Transactions), Phase 19 (Security/Durability)
**Controlling source documents:** `docs/ARCHITECTURE_DECISIONS.md`, `docs/decision_vectors/durability.json`, `GUERILLA_IMPLEMENTATION_SPEC.md` Sections 5-6 and 24-28
**Regeneration trigger:** Any storage/recovery change, Phase 7 graph-integrity change, or Phase 19 durability/archive change

---

## Purpose

Define the implemented local workspace layout, append-only active graph format,
transaction durability sequence, replay verification, payload persistence, and
crash recovery behavior for Phase 6.

---

## Implemented Local Workspace Layout

| Path | Authority | Phase 6 behavior |
|---|---|---|
| `.guerilla/graph/active.jsonl` | Authoritative lineage | One graph header followed by append-only transaction records |
| `.guerilla/graph/archives/` | Authoritative archive target | Directory created; archive rotation remains Phase 19 |
| `.guerilla/payloads/sha256/` | Referenced data | Content-addressed retained payload bytes |
| `.guerilla/locks/writer.lock` | Runtime coordination | Exclusive local single-writer lock metadata |
| `.guerilla/tmp/` | Temporary staging | Transaction stage files are non-authoritative and ignored by replay |
| `.guerilla/projections/`, `.guerilla/snapshots/`, `.guerilla/indexes/` | Non-authoritative derived storage | Directories only; no Phase 6 runtime behavior |

---

## Transaction Durability Sequence

Phase 6 appends through one local JSONL path:

1. Acquire `.guerilla/locks/writer.lock` with exclusive creation.
2. Replay the active graph to the last durable commit.
3. Validate transaction members against frozen schemas after computing record hashes.
4. Stage `transaction_begin`, sorted members, and `transaction_commit` in `.guerilla/tmp/`.
5. Flush and fsync the staged file, then fsync the temp directory when supported.
6. Append `transaction_begin` and all members to `active.jsonl`; flush and fsync.
7. Append the final `transaction_commit`; flush and fsync.
8. Fsync the graph directory when supported.
9. Delete the staged file and fsync the temp directory when supported.
10. Release the writer lock.

The commit record is the durable transaction boundary. A transaction advances
the graph revision only when its final commit record is present and verifies.

---

## Replay Verification

Replay is side-effect free and does not invoke adapters, projections, actions,
or transports. It verifies:

- graph header schema validity;
- canonical JSONL bytes for every complete stored record;
- transaction begin schema, expected graph revision, and previous commit hash;
- member schema validity, duplicate identifier rejection, workspace match, and
  record hash verification;
- transaction hash coverage over transaction metadata and ordered member hashes;
- commit workspace, transaction ID, committed record order, previous commit hash,
  monotonic graph revision, commit hash, and commit schema validity.

Replay ignores incomplete non-LF-terminated tails and unfinished transactions
after the last durable commit, returning diagnostics. Complete corrupt records
raise replay errors instead of being silently ignored.

---

## Payload Persistence

Retained payloads are written under `.guerilla/payloads/sha256/<digest>` where
`digest` is the lowercase SHA-256 payload hash. Reads distinguish invalid
digests, missing payloads, and hash mismatches. Payload bytes remain data and
are never executed by storage or replay.

---

## Deferred Items

Phase 6 does not implement DAG cycle validation, endpoint existence checks,
SQLite indexing, graph query services, authority registry enforcement, external
identity mapping, adapters, projections, transport bindings, archive rotation,
backup/restore, network-filesystem support, or stale-lock breaking. Those remain
owned by later phases.
