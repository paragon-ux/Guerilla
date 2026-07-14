"""Canonical encoding and hashing primitives."""

from guerilla.codec.canonical import (
    CanonicalJsonError,
    canonical_bytes,
    canonical_jsonl,
    canonicalize,
    normalize_timestamp,
    parse_raw_json,
)
from guerilla.codec.hashes import (
    ZERO_SHA256,
    archive_seal_hash,
    commit_hash,
    payload_hash,
    record_hash,
    segment_hash,
    segment_hash_envelope,
    sha256_hex,
    transaction_hash,
    transaction_hash_envelope,
)

__all__ = [
    "CanonicalJsonError",
    "ZERO_SHA256",
    "archive_seal_hash",
    "canonical_bytes",
    "canonical_jsonl",
    "canonicalize",
    "commit_hash",
    "normalize_timestamp",
    "parse_raw_json",
    "payload_hash",
    "record_hash",
    "segment_hash",
    "segment_hash_envelope",
    "sha256_hex",
    "transaction_hash",
    "transaction_hash_envelope",
]
