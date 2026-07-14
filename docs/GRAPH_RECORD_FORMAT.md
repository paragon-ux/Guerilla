# Graph Record Format

**Status:** FROZEN -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
**Contract version:** `0.2.0`
**Canonicalization:** `guerilla-cjson-v1`
**Hash algorithm:** `sha256`

## Canonical Bytes

Graph records are stored as JSON Lines. Each stored record is one canonical JSON
object followed by exactly one LF byte. Hash inputs use the canonical JSON bytes
without the trailing JSONL LF terminator.

Canonicalization follows `ARCHITECTURE_DECISIONS.md` AD-001:

- UTF-8 without BOM;
- sorted object members by Unicode scalar value sequence;
- no insignificant whitespace;
- array order preserved;
- exact string escaping rules;
- Unicode scalar values only;
- canonical UTC timestamps with `Z`;
- integers only within the JSON-safe range.

## Hash Fields

All SHA-256 digest fields are exactly 64 lowercase hexadecimal characters.

| Hash | Domain prefix | Covered bytes |
|---|---|---|
| `record_hash` | `guerilla.record.v1\n` | Canonical record JSON with `record_hash` removed |
| `payload_hash` | none | Exact retained post-redaction payload bytes |
| `transaction_hash` | `guerilla.transaction.v1\n` | Canonical transaction-hash envelope |
| `commit_hash` | `guerilla.commit.v1\n` | Canonical final commit record with `commit_hash` removed |
| `segment_hash` | `guerilla.segment.v1\n` | Canonical segment-hash envelope |
| `archive_seal_hash` | `guerilla.archive-seal.v1\n` | Canonical archive seal with `archive_seal_hash` removed |

The genesis previous-commit and previous-segment values are exactly 64 zero
characters.

## Transaction Ordering

Member records are ordered for `transaction_hash` as follows:

1. Core node records.
2. Core edge records.
3. Registered extension record families, ordered by family name.
4. Within a family, the primary Guerilla identifier in lexicographic order.

Transaction begin and final commit records frame the transaction but are not
member records. Duplicate member identifiers are rejected before hashing.

## Storage Boundary

The final commit record is the durable graph-revision boundary. Replay ignores
incomplete tails and never re-executes external actions. The durability sequence
and interruption classifications are frozen in AD-005 and vectorized in
`docs/decision_vectors/durability.json`.

## Published Vectors

Phase 2 decision vectors are under `docs/decision_vectors/`. Phase 4
conformance fixtures under `tests/fixtures/contracts/` contain the executable
fixture corpus for canonical bytes and hash preimages.

## Phase Boundary

This document defines byte contracts only. It does not implement a codec,
append store, archive writer, replay engine, or recovery tool.
