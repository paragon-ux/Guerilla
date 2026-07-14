# Storage and Recovery

**Status:** Gate B complete -- local kernel storage/replay/index verified
**Owner phase:** Phase 5 (Codec/Config), Phase 6 (Append Store/Transactions), Phase 19 (Security/Durability)
**Controlling source documents:** `docs/ARCHITECTURE_DECISIONS.md`, `docs/decision_vectors/durability.json`, `GUERILLA_IMPLEMENTATION_SPEC.md` Sections 5-6 and 24-28
**Regeneration trigger:** Any storage/recovery change, Phase 7 graph-integrity change, or Phase 19 durability/archive change

---

## Purpose

Define the implemented local workspace layout, append-only active graph format,
transaction durability sequence, replay verification, DAG integrity, payload
persistence, crash recovery behavior, and the rebuildable query index through
Gate B.

---

## Implemented Local Workspace Layout

| Path | Authority | Gate B behavior |
|---|---|---|
| `.guerilla/graph/active.jsonl` | Authoritative lineage | One graph header followed by append-only transaction records |
| `.guerilla/graph/archives/` | Authoritative archive target | Directory created; archive rotation remains Phase 19 |
| `.guerilla/payloads/sha256/` | Referenced data | Content-addressed retained payload bytes |
| `.guerilla/locks/writer.lock` | Runtime coordination | Exclusive local single-writer lock metadata |
| `.guerilla/tmp/` | Temporary staging | Transaction stage files are non-authoritative and ignored by replay |
| `.guerilla/indexes/graph.sqlite` | Non-authoritative derived storage | Rebuildable SQLite index sourced from authoritative replay |
| `.guerilla/projections/`, `.guerilla/snapshots/` | Non-authoritative derived storage | Directories only; no Phase 7 runtime behavior |

---

## Transaction Durability Sequence

Gate B appends through one local JSONL path:

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

## DAG Integrity, Authority, and Query Index

Phase 7 validates direct edge transactions before staging. Validation checks
duplicate node/edge identifiers, same-transaction node endpoints, missing
endpoints, self-loops, relationship endpoint-type compatibility from
`registries/relationship_types.json`, and direct cycle creation. A failed graph
integrity check rejects the full transaction before any graph revision advances.

Phase 8 adds the fixed local `local-owner-v1` authorization profile to graph
reads and appends. Actor fields, authority envelopes, adapter descriptors,
extensions, and payload content do not grant effective permissions.

Graph queries are available from authoritative replay and from the SQLite index.
Both serving paths declare workspace id, graph revision, commit hash, query name,
limit, truncation, and result items. Supported query surfaces are node lookup,
edge lookup, commit lookup, entity revisions, graph heads, ancestors, and
descendants.

The SQLite index stores rebuildable metadata, commits, nodes, edges, record
revision, adjacency source fields, and canonical record JSON. It never generates
authoritative identifiers, repairs graph records, or advances beyond the durable
graph. Missing, corrupt, stale, or ahead index state is detected; rebuild uses
authoritative replay as the source.

---

## Payload Persistence

Retained payloads are written under `.guerilla/payloads/sha256/<digest>` where
`digest` is the lowercase SHA-256 payload hash. Reads distinguish invalid
digests, missing payloads, and hash mismatches. Payload bytes remain data and
are never executed by storage or replay.

---

## Deferred Items

Gate B does not implement adapter invocation, observations, external actions,
reconciliation, projections, transport bindings, archive rotation,
backup/restore, network-filesystem support, or stale-lock breaking. Those remain
owned by later phases.
