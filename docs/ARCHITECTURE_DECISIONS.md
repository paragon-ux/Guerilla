# Architecture Decisions

**Status:** FROZEN -- Phase 2 complete
**Owner phase:** Phase 2 (Architecture Decisions)
**Decision set version:** `0.2.0-phase2`
**Decision date:** 2026-07-13
**Controlling source documents:** `AGENTS.md`, `GUERILLA_CONCEPT_PAPER.md`, `GUERILLA_IMPLEMENTATION_SPEC.md`, `GUERILLA_PROTOCOL_SPEC.md`, `GUERILLA_SNAPSHOT.md`, `Note-on-Architecture.md`
**Regeneration trigger:** Any architecture decision change or compatibility-breaking contract change

---

## Purpose

This document freezes the architecture choices that affect record identity, transaction validity, authority, replay semantics, and downstream machine-readable contracts.

The decisions below are normative for Phases 3-5. They do not create schemas, registries, runtime code, adapters, transports, projections, or graph records.

---

## Core Relationship Directions

Every direct authoritative relationship has one permitted direction:

| Relationship | Direction |
|---|---|
| `depends_on` | prerequisite -> dependent |
| `produces` | producer -> product |
| `derives` | source -> derived |
| `causes` | cause -> effect |
| `evidences` | evidence -> supported record |
| `evaluated_by` | subject -> evaluation |
| `superseded_by` | earlier -> later |
| `resolved_by` | unresolved item -> resolution |
| `captured_by` | included source -> snapshot |

Relationship schemas, registries, fixtures, and runtime validators must preserve
these directions exactly. Any symmetric, cyclic, non-causal, or otherwise
non-DAG assertion is represented through a reified event or conflict node rather
than by reversing or weakening these direct edge directions.

---

## Decision Summary

| ID | Decision | Status | Downstream owner |
|---|---|---|---|
| AD-001 | Canonical JSON profile | Frozen | Phase 3, Phase 5 |
| AD-002 | Identifier scheme and prefixes | Frozen | Phase 3, Phase 5 |
| AD-003 | Hash inputs and domain separation | Frozen | Phase 3, Phase 5 |
| AD-004 | Transaction and record ordering | Frozen | Phase 3, Phase 6 |
| AD-005 | Writer lock and atomic append policy | Frozen | Phase 5, Phase 6 |
| AD-006 | Filesystem support boundary | Frozen | Phase 5, Phase 6 |
| AD-007 | Payload retention and redaction defaults | Frozen | Phase 3, Phase 5, Phase 19 |
| AD-008 | MVP adapter execution model | Frozen | Phase 8, Phase 9 |
| AD-009 | Local authorization profile | Frozen | Phase 8, Phase 19 |
| AD-010 | External identity lifecycle | Frozen | Phase 8, Phase 10 |
| AD-011 | Projection policy representation | Frozen | Phase 13, Phase 14 |
| AD-012 | Archive thresholds and sealed segments | Frozen | Phase 6, Phase 19 |
| AD-013 | Performance thresholds for MVP evidence | Frozen | Phase 15, Phase 21 |
| AD-014 | Extension namespace governance | Frozen | Phase 3, Phase 4 |

---

## AD-001 -- Canonical JSON Profile

**Decision:** Guerilla uses `guerilla-cjson-v1`, a deterministic UTF-8 JSON profile for hash input and stored graph records.

Canonical byte rules:

- Canonical JSON is a single JSON value encoded as UTF-8 with no byte-order mark.
- Stored graph records are JSON Lines: exactly one canonical JSON object followed by exactly one LF byte (`0x0a`).
- Hash input is the canonical JSON object bytes without the stored JSONL LF terminator.
- Object members are sorted lexicographically by Unicode scalar value sequence before escaping.
- Duplicate object member names are invalid before canonicalization.
- No insignificant whitespace is emitted.
- Array order is preserved and is semantically meaningful.
- Canonical bytes are independent of locale, process, platform newline settings, and filesystem encoding.

String and Unicode rules:

- Input JSON text MUST be valid UTF-8.
- Strings MUST contain only Unicode scalar values; isolated surrogate code points are invalid.
- Guerilla does not normalize Unicode. NFC, NFD, and other equivalent-looking forms remain distinct bytes when their scalar sequences differ.
- Canonical output emits non-control Unicode scalar values directly as UTF-8 except for quotation mark (`"`), reverse solidus (`\`), and JSON control characters.
- Quotation mark and reverse solidus are escaped as `\"` and `\\`.
- The solidus (`/`) is not escaped.
- Control characters use the shortest required JSON escape: `\b`, `\t`, `\n`, `\f`, and `\r` for those five characters; other U+0000 through U+001F values use lowercase six-byte `\u00xx`.
- Hex digits in escapes emitted by the canonicalizer are lowercase.

Timestamp rules:

- Stored timestamp fields use canonical UTC RFC 3339 form with `Z`.
- The canonical grammar is `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS.fractionZ`.
- Fractional seconds are allowed only when non-zero precision is needed.
- Fractional seconds are normalized by trimming trailing zeroes and retaining at most 9 digits.
- Offset input may be accepted by parsers only before storage; it is converted to UTC before hashing.
- Lowercase `t` or `z`, missing timezone, offset timestamps in stored records, and leap seconds (`:60`) are invalid.
- Valid timestamp years are `0001` through `9999`.

Number rules:

- JSON numbers are permitted only for integers.
- Integers MUST be in the inclusive JSON-safe range `-9007199254740991` through `9007199254740991`.
- Negative zero, leading plus signs, leading zeroes other than the single value `0`, decimal points, exponents, `NaN`, and infinity are invalid.
- Decimal, money, duration, or arbitrary-precision values MUST be represented by strings under a schema that defines their grammar.

**Rationale:** The architecture already requires UTF-8, LF, sorted keys, no insignificant whitespace, array-order preservation, RFC 3339 UTC timestamps, and no implicit Unicode normalization. This decision freezes those assumptions into one named profile while avoiding floating-point ambiguity.

**Alternatives considered:** Raw JSON writer output was rejected because it is not stable across implementations. Full RFC 8785 adoption without Guerilla-specific timestamp and number restrictions was rejected because downstream graph hashes require stricter record semantics.

**Impact:** Phase 3 schemas must prohibit unsupported numeric forms. Phase 4 canonicalization fixtures must include key order, string escaping, timestamp, Unicode, integer-boundary, and invalid-number cases.

---

## AD-002 -- Identifier Scheme and Prefixes

**Decision:** Guerilla default identifiers use UUIDv7 with stable lowercase prefixes.

Identifier format:

```text
<prefix><uuidv7-lowercase-rfc4122>
```

The UUID portion MUST match this grammar:

```text
[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}
```

Validation rules:

- The UUID version nibble MUST be `7`.
- The RFC 4122 variant bits MUST be `10`, represented by lowercase `8`, `9`, `a`, or `b` as the first hex digit of the fourth UUID group.
- UUID hex digits MUST be lowercase.
- Braces, uppercase UUID text, hyphenless UUID text, URNs, base32/base64 encodings, and raw UUIDv4/ULID identifiers are invalid as Guerilla core identifiers.
- Prefix and UUID family are validated together; a node field cannot carry an edge, transaction, message, or extension prefix.
- The UUIDv7 timestamp bits are not authority, causation, or graph order. Graph revision and committed edges are authoritative.

Required prefixes:

| Object | Prefix |
|---|---|
| Workspace | `grw_` |
| Logical entity | `gri_` |
| Node revision | `grn_` |
| Edge | `gre_` |
| Transaction | `grt_` |
| Commit | `grm_` |
| Graph segment | `gsg_` |
| Snapshot | `grs_` |
| Adapter | `gra_` |
| Projection | `grp_` |
| Protocol message | `gmsg_` |
| State boundary | `gsb_` |
| External system | `gxs_` |
| Extension namespace | `gxe_` |

Identifiers are opaque. Sorting by identifier is permitted only as a deterministic tie-breaker, not as proof of causation or graph order.

Collision and import rules:

- A generated collision in the target identifier scope MUST be regenerated before transaction validation.
- A submitted duplicate identifier within the transaction or already committed graph is rejected with `duplicate_id`.
- A reused UUID value with a different registered prefix is a distinct identifier family but MUST still satisfy that field's prefix rule.
- Legacy Guerilla identifiers from unsupported families MUST NOT be accepted as core record identifiers.
- Imported legacy identifiers MAY be preserved only as authority-scoped external identifiers or explicit migration metadata.
- Migrating legacy Guerilla records creates new UUIDv7-prefixed records and records a migration decision; committed records are not rewritten.
- External system identifiers are never coerced into Guerilla UUIDv7 identifiers.

**Rationale:** UUIDv7 is standards-track, time-sortable for operations, and widely implementable without requiring Crockford-base32 parsing. Prefixes preserve object-family readability without transferring authority to the identifier text.

**Alternatives considered:** ULID was rejected as the default because UUIDv7 aligns better with common UUID tooling and binary storage. Unprefixed UUIDv7 was rejected because Phase 3 schemas and diagnostics benefit from object-family prefixes.

**Impact:** Phase 3 schemas must validate prefix and UUIDv7 shape. Phase 5 must provide deterministic validation and generation, but tests must not infer causation from UUID timestamps.

---

## AD-003 -- Hash Inputs and Domain Separation

**Decision:** Guerilla uses SHA-256 with explicit domain-separated byte inputs.

Digest representation:

- All SHA-256 digest fields store exactly 64 lowercase hexadecimal characters.
- The hash algorithm is identified by an adjacent schema field or contract version, not by prefixing digest values with `sha256:`.
- The genesis previous-commit hash is exactly 64 zero characters.
- The genesis previous-segment hash is exactly 64 zero characters.
- A graph revision used in a hash preimage is encoded as unsigned decimal ASCII with no leading zeroes, except the genesis value `0`.

Required hash forms and preimages:

| Hash | Input |
|---|---|
| `record_hash` | ASCII bytes `guerilla.record.v1\n` followed by canonical JSON bytes of the record with `record_hash` removed |
| `payload_hash` | Exact retained payload bytes after required redaction, with no domain prefix |
| `transaction_hash` | ASCII bytes `guerilla.transaction.v1\n` followed by canonical JSON bytes of the transaction-hash envelope |
| `commit_hash` | ASCII bytes `guerilla.commit.v1\n` followed by canonical JSON bytes of the final commit record with `commit_hash` removed |
| `segment_hash` | ASCII bytes `guerilla.segment.v1\n` followed by canonical JSON bytes of the segment-hash envelope |
| `archive_seal_hash` | ASCII bytes `guerilla.archive-seal.v1\n` followed by canonical JSON bytes of the archive seal record with `archive_seal_hash` removed |

The transaction-hash envelope covers transaction metadata and ordered members exactly:

```json
{
  "actor": "<canonical actor object>",
  "created_at": "<canonical timestamp>",
  "expected_graph_revision": "<graph revision integer>",
  "expected_previous_commit_hash": "<64 hex>",
  "member_record_hashes": ["<64 hex in canonical transaction order>"],
  "transaction_id": "<grt_ UUIDv7 identifier>",
  "workspace_id": "<grw_ UUIDv7 identifier>"
}
```

The final commit record covers commit metadata exactly:

```json
{
  "canonicalization_id": "guerilla-cjson-v1",
  "commit_id": "<grm_ UUIDv7 identifier>",
  "committed_at": "<canonical timestamp>",
  "graph_revision": "<graph revision integer>",
  "hash_algorithm": "sha256",
  "previous_commit_hash": "<64 hex>",
  "transaction_hash": "<64 hex>",
  "transaction_id": "<grt_ UUIDv7 identifier>",
  "workspace_id": "<grw_ UUIDv7 identifier>"
}
```

The segment-hash envelope covers segment identity and ordered commits exactly:

```json
{
  "commit_hashes": ["<64 hex in graph-revision order>"],
  "first_graph_revision": "<graph revision integer>",
  "last_graph_revision": "<graph revision integer>",
  "previous_segment_hash": "<64 hex>",
  "segment_id": "<gsg_ UUIDv7 identifier>",
  "workspace_id": "<grw_ UUIDv7 identifier>"
}
```

Newline policy:

- Domain separators are ASCII strings ending in exactly one LF byte.
- Canonical JSON bytes following the domain separator are not followed by an additional newline for hash input.
- Stored JSONL records still include exactly one LF byte after the canonical JSON object; that storage terminator is never part of `record_hash`, `transaction_hash`, `commit_hash`, `segment_hash`, or `archive_seal_hash`.

**Rationale:** Domain separation prevents accidental cross-use of hashes. The selected inputs preserve the implementation specification's required record, payload, transaction, commit, and segment integrity chain without adding unstated authority.

**Alternatives considered:** Hashing raw stored JSONL lines was rejected because line endings and trailing newlines would become platform-sensitive. Including wall-clock commit time in `commit_hash` was rejected because graph revision and transaction hash already identify the committed state boundary.

**Impact:** Phase 4 fixtures must publish byte strings and expected SHA-256 values for every hash class before Phase 5 implementation starts.

---

## AD-004 -- Transaction and Record Ordering

**Decision:** A transaction has a canonical member-record order for hash construction and replay validation.

Ordering rules:

1. Graph header records are not transaction members.
2. Transaction begin and commit envelopes frame the transaction but are not member records.
3. Member records are ordered by record family rank.
4. Core family rank is `node` before `edge`.
5. Registered extension record families sort after core records by registered family name, then by identifier.
6. Within one family, records are ordered by their primary Guerilla identifier lexicographically as Unicode scalar values.
7. `transaction_hash` uses member `record_hash` values in canonical transaction order.
8. Semantic causation is determined only by edges and identifiers, not by line position, timestamp order, UUID timestamp bits, or input order.

Duplicate and endpoint rules:

- Duplicate member identifiers in one transaction are rejected before hashing with `duplicate_id`.
- A member identifier that already exists in the committed graph is rejected with `duplicate_id`.
- A namespaced extension family whose ordering, schema, or critical compatibility rule is unknown is rejected before hashing.
- Unknown optional extension fields that are permitted by compatibility rules remain part of the stored canonical bytes when retained; ignored optional fields cannot alter core semantics.
- Edge endpoints MUST be node identifiers, never edge, transaction, commit, message, adapter, projection, state-boundary, or extension identifiers.
- Edge endpoints are valid when each endpoint exists in a prior committed graph revision or as a node member of the same transaction.
- Same-transaction endpoints are validated against the full canonical node-member set, not against original input order.
- Self-loops are rejected.
- Direct authoritative edges that would create a cycle are rejected after endpoint existence and relationship-type compatibility are established.
- Relationship-specific endpoint restrictions are enforced from the relationship registry; missing restrictions block mutation rather than falling back to best effort.

**Rationale:** Nodes must be known before edges can pass endpoint validation. Lexicographic identifier ordering gives stable cross-process ordering without allowing timestamps or append order to create hidden causation.

**Alternatives considered:** Original input order was rejected because equivalent transactions could hash differently. Sorting only by record hash was rejected because diagnostics and endpoint validation are easier when family order is explicit.

**Impact:** Phase 3 schemas must distinguish transaction framing from member records. Phase 6 replay must reject transactions whose committed hash does not match canonical member order.

---

## AD-005 -- Writer Lock and Atomic Append Policy

**Decision:** The MVP uses a local single-writer workspace lock plus staged append and fsync.

Policy:

- A writer obtains an exclusive lock file under `.guerilla/locks/`.
- Lock metadata records process id, host, user, workspace id, acquisition time, and runtime version.
- Stale locks are not automatically broken; an explicit verify or recovery command must classify the lock before retry.
- A transaction is staged under `.guerilla/tmp/`, validated fully, appended to the active graph segment, flushed, fsynced, and committed only by a final commit record.
- The final commit record is the only durable graph-revision boundary.
- Replay ignores incomplete tails and reports them as recovery diagnostics without re-executing external actions.

Durability sequence:

1. Create the lock file with exclusive create semantics.
2. Flush and fsync the lock file.
3. Fsync the `.guerilla/locks/` directory.
4. Write the staged transaction bytes under `.guerilla/tmp/`.
5. Flush and fsync the staged transaction file.
6. Fsync the `.guerilla/tmp/` directory.
7. Append transaction-begin and canonical member records to the active graph segment.
8. Flush and fsync the active segment.
9. Append the final commit record containing `transaction_hash`, `graph_revision`, `previous_commit_hash`, and `commit_hash`.
10. Flush and fsync the active segment again after the final commit record.
11. Fsync the active segment directory.
12. Remove the staged transaction file.
13. Fsync `.guerilla/tmp/`.
14. Release the writer lock.
15. Fsync `.guerilla/locks/`.

Interruption classifications:

| Interruption point | Recovery classification | Replay behavior |
|---|---|---|
| Before durable lock file | no graph mutation | retry may acquire lock |
| After durable lock before staged transaction | stale lock, no staged mutation | verify lock owner before retry |
| During staged transaction write | incomplete staged transaction | ignore staged file after verification |
| After staged fsync before active append | staged but uncommitted | ignore staged file after verifying no active tail |
| During active begin/member append | incomplete active tail | ignore bytes after last valid committed graph revision |
| After begin/member fsync before final commit record | prepared without commit | ignore transaction members and report `transaction_incomplete` |
| During final commit-record write | torn commit record | ignore incomplete commit and report `transaction_incomplete` |
| After final commit record write before final segment fsync | commit uncertain | verify segment; accept only if complete commit hash chain validates |
| After final segment fsync before directory fsync | committed, directory uncertain | verify active segment path and parent directory state |
| After directory fsync before lock release | committed with leftover lock | verify graph, then classify lock as stale committed writer |
| During archive seal write | archive seal incomplete | active graph remains authoritative; archive seal is ignored until valid |

Incomplete-tail policy:

- Replay scans only complete LF-terminated JSONL records.
- Bytes after the last complete LF-terminated record are an incomplete tail.
- A complete but invalid JSON object after the last valid commit record is treated as an incomplete transaction tail unless it is part of a valid later committed transaction.
- Recovery tools MAY truncate or quarantine incomplete tails only after writing separate recovery evidence; replay itself does not rewrite authoritative files.

**Rationale:** This preserves the local single-writer MVP and avoids inventing distributed locking before Gate B.

**Alternatives considered:** Optimistic multi-writer append was rejected for the MVP. Silent stale-lock removal was rejected because it could mask an uncertain writer outcome.

**Impact:** Phase 6 must test writer contention, stale lock reporting, crash before commit, and crash after commit.

---

## AD-006 -- Filesystem Support Boundary

**Decision:** The reference write profile supports local filesystems with reliable exclusive locks, atomic rename, file flush, and directory flush.

Network, synchronized, virtualized, or eventually consistent filesystems are read-only or experimental unless a later conformance profile proves equivalent locking and durability behavior.

**Rationale:** The architecture requires deterministic replay and safe unknown-outcome handling. Network filesystem semantics vary too much to be part of the first mutation boundary.

**Alternatives considered:** Declaring broad filesystem support was rejected because it would settle durability behavior without evidence.

**Impact:** Phase 5 configuration must expose a filesystem profile. Phase 6 tests must fail fast when required local durability features are unavailable.

---

## AD-007 -- Payload Retention and Redaction Defaults

**Decision:** The MVP default is metadata-first payload handling.

Defaults:

- Raw payloads are not persisted unless policy explicitly permits retention.
- Retained payloads are stored only after redaction.
- `payload_hash` is computed over the retained post-redaction bytes.
- The graph records redaction occurrence, redaction policy version, retained payload hash, media type, size, and retention class.
- Removed secret bytes and pre-redaction hashes are not retained.
- Missing retained payloads and payload hash mismatches are distinct verification outcomes.

Default retention classes:

| Class | Default behavior |
|---|---|
| `none` | no payload persisted |
| `metadata` | metadata only |
| `content_addressed` | retained post-redaction payload |
| `external_reference` | authority-scoped external locator only |

**Rationale:** This preserves payload safety while allowing content-addressed evidence when explicitly configured.

**Alternatives considered:** Always retaining observed payloads was rejected for privacy and secret-risk reasons. Retaining pre-redaction hashes was rejected because it can preserve sensitive material indirectly.

**Impact:** Phase 3 schemas must model retention class and redaction metadata. Phase 19 must test secret redaction and payload non-execution.

---

## AD-008 -- MVP Adapter Execution Model

**Decision:** MVP adapters are trusted, configured, in-process Python components invoked only through typed adapter interfaces.

Rules:

- The runtime loads only configured adapters.
- Adapter descriptors are validated before operations.
- Adapter outputs are validated before graph commit.
- Adapter code is never loaded from graph payloads.
- Adapter subprocess, container, remote, or marketplace isolation is deferred beyond the internal MVP.

**Rationale:** The implementation specification treats adapters as trusted components and defers full isolation. In-process synthetic adapters let Phases 9-12 prove continuity semantics without adding a transport or sandbox boundary.

**Alternatives considered:** Subprocess adapters were rejected for the MVP because they belong to the later external-compatible stage. Remote adapters were rejected because transport must not create a second mutation path.

**Impact:** Phase 9 synthetic adapters must exercise the same typed interface intended for later isolated adapters.

---

## AD-009 -- Local Authorization Profile

**Decision:** The MVP uses a local policy profile with operation-scoped permissions.

Rules:

- The fixed profile id is `local-owner-v1`; it is mandatory for the local single-writer MVP.
- The effective principal is the local OS principal unless a transport profile later supplies an authenticated principal.
- Actor fields are lineage attribution only and do not grant authority.
- Policy decisions cover graph reads, graph appends, adapter observations, external actions, conflict decisions, snapshot access, payload access, and administrative configuration.
- Default bootstrap policy grants local workspace administrator privileges only to the workspace owner profile created at initialization.
- A model actor cannot receive broader authority than the effective principal and policy allow.
- A general programmable policy engine is deferred and MUST NOT be introduced before the fixed local profile is implemented and tested.
- Payload content, adapter descriptors, client actor fields, and extension metadata cannot grant authority.

**Rationale:** This freezes the distinction between actor attribution and authorization while staying inside the local single-writer MVP.

**Alternatives considered:** Trusting client-supplied actor fields was rejected by the protocol specification. Deferring authorization entirely was rejected because state-boundary and payload rules require policy from the first implementation.

**Impact:** Phase 8 must implement policy records and actor/principal separation before adapter mutation exists.

---

## AD-010 -- External Identity Lifecycle

**Decision:** External identity is represented as an authority-scoped tuple and never assumed globally unique.

Identity tuple:

```text
system_id, state_boundary_id, external_kind, external_id, optional namespace, optional external_revision
```

Lifecycle rules:

- Rename is a new observation linked to the prior identity when evidence exists.
- Deletion is an observed event, not removal of prior lineage.
- Identifier reuse with incompatible evidence creates an `identity_collision` conflict.
- Cross-system aliasing requires an explicit reified assertion node or decision; it is not inserted as a symmetric direct edge.
- External revision tokens are preserved exactly as reported and may be normalized only in derived indexes.

**Rationale:** This directly addresses rename, deletion, reuse, and aliasing without transferring application-state authority to Guerilla.

**Alternatives considered:** Global external identifiers were rejected because external systems define identity differently. Silent alias merge was rejected because it can create false lineage.

**Impact:** Phase 8 and Phase 10 must include identity-collision and external-revision preservation tests.

---

## AD-011 -- Projection Policy Representation

**Decision:** Projection policies are declarative, versioned data documents, not executable code.

Rules:

- A projection output cites source graph revision, source query or node set, transformation id, transformation version, policy version, generation time, freshness, information loss, and result hash.
- Policies may select, filter, sort, group, and limit graph records using registered declarative fields.
- Policies must not execute scripts, import code, mutate graph records, invoke adapters, or read external systems directly.
- Serving a persisted projection from an earlier graph revision requires an explicit request for that revision.

**Rationale:** Derived views must not become hidden state authorities or execution paths.

**Alternatives considered:** General-purpose projection scripts were rejected for the MVP because they would blur payload and execution safety boundaries.

**Impact:** Phase 13 must define a declarative policy schema and deterministic result hashing.

---

## AD-012 -- Archive Thresholds and Sealed Segments

**Decision:** The MVP seals active graph segments by size or commit count, whichever comes first.

Default thresholds:

- active segment size: 64 MiB;
- active segment commit count: 50,000 commits;
- retained active segment minimum: one current writable segment;
- archive seal includes first and last graph revision, previous segment hash, segment hash, record count, commit count, creation time, canonicalization id, and hash algorithm.
- archive seal includes `archive_seal_hash` computed by AD-003 after all other seal fields are finalized.
- archive seal verification must confirm the previous-segment hash, ordered commit hashes, segment hash, seal hash, graph-revision range, record count, commit count, canonicalization id, and hash algorithm.

Thresholds are configuration values, but changing them must not change record or commit hashes.

**Rationale:** Fixed defaults make archive tests reproducible while keeping archive cadence adjustable.

**Alternatives considered:** Time-based sealing alone was rejected because it is harder to test deterministically.

**Impact:** Phase 6 and Phase 19 must test archive seal verification and missing/corrupt archive failure.

---

## AD-013 -- Performance Thresholds for MVP Evidence

**Decision:** The MVP records performance targets as acceptance evidence thresholds, not as protocol semantics.

Initial evidence thresholds:

| Measurement | MVP target |
|---|---|
| Append p95 latency for a 10-record transaction | <= 250 ms on the reference local profile |
| Replay of 100,000 records | <= 30 seconds on the reference local profile |
| Index rebuild of 100,000 records | <= 45 seconds on the reference local profile |
| Default lineage traversal depth | 1,000 edges |
| Default query result limit | 10,000 records |
| Default retained payload size limit | 10 MiB |
| Projection regeneration determinism | identical result hash for same revision and policy |

Failures to meet these targets do not invalidate lineage; they block MVP acceptance until documented, tuned, or explicitly revised.

**Rationale:** The snapshot lists performance thresholds as unresolved. This freezes measurable targets without making performance an authority rule.

**Alternatives considered:** No thresholds was rejected because Phase 21 needs reproducible baselines. Hard protocol limits were rejected because deployments may differ.

**Impact:** Phase 21 benchmarks must report these measurements and any revised thresholds.

---

## AD-014 -- Extension Namespace Governance

**Decision:** Extensions are namespaced, registered, schema-bound, and cannot redefine core semantics.

Rules:

- Extension namespaces use lowercase DNS-style or reverse-DNS-style names and receive a Guerilla namespace id with prefix `gxe_`.
- Every extension declares owner, version, compatibility range, schemas, invariants, downgrade behavior, security implications, and affected capabilities.
- Unknown critical extension fields cause rejection.
- Unknown optional extension fields may be ignored only under negotiated compatibility rules.
- Extensions must not mutate committed records, bypass DAG validation, redefine core relationship direction, mark derived views authoritative, grant authority from payload content, or transfer external application-state ownership to Guerilla.

**Rationale:** Extension support is necessary, but it must not weaken the invariants that make one authoritative lineage graph coherent.

**Alternatives considered:** Free-form extension fields were rejected because they would make compatibility and security review impossible.

**Impact:** Phase 3 must create an extension namespace registry and schemas for extension metadata.

---

## Normative Decision Vectors

Phase 2 publishes machine-readable decision vectors under `docs/decision_vectors/`.
They are closure evidence for decisions that schemas and conformance fixtures must
preserve:

| Vector | Governing decision | Purpose |
|---|---|---|
| `canonical_json.json` | AD-001 | Canonical Unicode, escaping, timestamp, and integer-boundary behavior |
| `identifiers.json` | AD-002 | UUIDv7 grammar, prefix families, invalid families, and collision policy |
| `hashes.json` | AD-003 | Exact domain-separated preimages and expected SHA-256 digests |
| `transaction_ordering.json` | AD-004 | Canonical family ordering, duplicate handling, same-transaction endpoint policy |
| `durability.json` | AD-005 | Required fsync sequence, final commit-record boundary, recovery classifications |

These vectors are normative examples, not schemas, registries, runtime code, or
graph records. Phase 3 schemas and Phase 4 fixtures must remain compatible with
them.

---

## Phase 3 Handoff

Phase 3 may begin from these frozen decisions. It must publish schemas, registries, and examples that make these decisions machine-checkable before Phase 5 runtime implementation starts.

No open Phase 2 decision remains that can change record identity, transaction validity, authority, replay semantics, canonicalization, identifier format, or hash construction.
