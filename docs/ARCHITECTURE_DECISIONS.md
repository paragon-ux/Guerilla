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

Profile rules:

- JSON text is encoded as UTF-8 with no byte-order mark.
- Stored JSON Lines records use exactly one JSON object per line with LF line terminators.
- Hash input is the JSON object bytes without the trailing JSONL line terminator.
- Object keys are sorted lexicographically by Unicode code point.
- No insignificant whitespace is emitted in hash input.
- Array order is preserved and is semantically meaningful.
- Strings are emitted using JSON escaping only as required by the JSON grammar.
- Unicode strings are not normalized implicitly.
- Timestamps are RFC 3339 UTC strings with `Z`; offset forms are normalized before hashing.
- Numbers are restricted to integers within the JSON-safe integer range unless a later schema explicitly represents a decimal as a string.
- Floating-point `NaN`, infinity, negative zero, and implementation-dependent numeric spellings are prohibited.

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

Required prefixes:

| Object | Prefix |
|---|---|
| Workspace | `grw_` |
| Logical entity | `gri_` |
| Node revision | `grn_` |
| Edge | `gre_` |
| Transaction | `grt_` |
| Commit | `grm_` |
| Snapshot | `grs_` |
| Adapter | `gra_` |
| Projection | `grp_` |
| Protocol message | `gmsg_` |
| State boundary | `gsb_` |
| External system | `gxs_` |
| Extension namespace | `gxe_` |

Identifiers are opaque. Sorting by identifier is permitted only as a deterministic tie-breaker, not as proof of causation or graph order.

**Rationale:** UUIDv7 is standards-track, time-sortable for operations, and widely implementable without requiring Crockford-base32 parsing. Prefixes preserve object-family readability without transferring authority to the identifier text.

**Alternatives considered:** ULID was rejected as the default because UUIDv7 aligns better with common UUID tooling and binary storage. Unprefixed UUIDv7 was rejected because Phase 3 schemas and diagnostics benefit from object-family prefixes.

**Impact:** Phase 3 schemas must validate prefix and UUIDv7 shape. Phase 5 must provide deterministic validation and generation, but tests must not infer causation from UUID timestamps.

---

## AD-003 -- Hash Inputs and Domain Separation

**Decision:** Guerilla uses SHA-256 with explicit domain-separated byte inputs.

Required hash forms:

| Hash | Input |
|---|---|
| `record_hash` | `b"guerilla.record.v1\n"` + canonical JSON bytes of the record excluding `record_hash` |
| `payload_hash` | exact retained payload bytes after any required redaction |
| `transaction_hash` | `b"guerilla.transaction.v1\n"` + LF-joined canonical member `record_hash` values in transaction order + final LF |
| `commit_hash` | `b"guerilla.commit.v1\n"` + previous commit hash + LF + decimal graph revision + LF + transaction hash + LF |
| `segment_hash` | `b"guerilla.segment.v1\n"` + LF-joined commit hashes in segment order + final LF |

The genesis previous-commit value is exactly 64 zero characters.

**Rationale:** Domain separation prevents accidental cross-use of hashes. The selected inputs preserve the implementation specification's required record, payload, transaction, commit, and segment integrity chain without adding unstated authority.

**Alternatives considered:** Hashing raw stored JSONL lines was rejected because line endings and trailing newlines would become platform-sensitive. Including wall-clock commit time in `commit_hash` was rejected because graph revision and transaction hash already identify the committed state boundary.

**Impact:** Phase 4 fixtures must publish byte strings and expected SHA-256 values for every hash class before Phase 5 implementation starts.

---

## AD-004 -- Transaction and Record Ordering

**Decision:** A transaction has a canonical member-record order for hash construction and replay validation.

Ordering rules:

1. Graph header records are not transaction members.
2. Transaction begin and commit envelopes frame the transaction but are not member records.
3. Member records are ordered by record family rank: node before edge.
4. Within a family, records are ordered by identifier lexicographically.
5. `transaction_hash` uses member `record_hash` values in that canonical order.
6. Semantic causation is determined only by edges and identifiers, not by line position or timestamp order.

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
- A transaction is staged under `.guerilla/tmp/`, validated fully, appended to the active graph segment, flushed, fsynced, and then committed by a final commit record.
- Replay ignores incomplete transactions and reports them as recovery diagnostics.

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

- The effective principal is the local OS principal unless a transport profile later supplies an authenticated principal.
- Actor fields are lineage attribution only and do not grant authority.
- Policy decisions cover graph reads, graph appends, adapter observations, external actions, conflict decisions, snapshot access, payload access, and administrative configuration.
- Default bootstrap policy grants local workspace administrator privileges only to the workspace owner profile created at initialization.
- A model actor cannot receive broader authority than the effective principal and policy allow.

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

## Phase 3 Handoff

Phase 3 may begin from these frozen decisions. It must publish schemas, registries, and examples that make these decisions machine-checkable before Phase 5 runtime implementation starts.

No open Phase 2 decision remains that can change record identity, transaction validity, authority, replay semantics, canonicalization, identifier format, or hash construction.
