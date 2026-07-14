"""Domain-separated SHA-256 hash construction."""

from __future__ import annotations

import hashlib
from typing import Any

from guerilla.codec.canonical import canonical_bytes

ZERO_SHA256 = "0" * 64

RECORD_DOMAIN = b"guerilla.record.v1\n"
TRANSACTION_DOMAIN = b"guerilla.transaction.v1\n"
COMMIT_DOMAIN = b"guerilla.commit.v1\n"
SEGMENT_DOMAIN = b"guerilla.segment.v1\n"
ARCHIVE_SEAL_DOMAIN = b"guerilla.archive-seal.v1\n"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _without_field(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def payload_hash(payload: bytes) -> str:
    return sha256_hex(payload)


def record_hash(record: dict[str, Any]) -> str:
    return sha256_hex(RECORD_DOMAIN + canonical_bytes(_without_field(record, "record_hash")))


def transaction_hash(envelope: dict[str, Any]) -> str:
    return sha256_hex(TRANSACTION_DOMAIN + canonical_bytes(envelope))


def transaction_hash_envelope(
    *,
    actor: dict[str, Any],
    created_at: str,
    expected_graph_revision: int,
    expected_previous_commit_hash: str,
    member_record_hashes: list[str],
    transaction_id: str,
    workspace_id: str,
) -> dict[str, Any]:
    return {
        "actor": actor,
        "created_at": created_at,
        "expected_graph_revision": expected_graph_revision,
        "expected_previous_commit_hash": expected_previous_commit_hash,
        "member_record_hashes": member_record_hashes,
        "transaction_id": transaction_id,
        "workspace_id": workspace_id,
    }


def commit_hash(commit: dict[str, Any]) -> str:
    return sha256_hex(COMMIT_DOMAIN + canonical_bytes(_without_field(commit, "commit_hash")))


def segment_hash(envelope: dict[str, Any]) -> str:
    return sha256_hex(SEGMENT_DOMAIN + canonical_bytes(envelope))


def segment_hash_envelope(
    *,
    commit_hashes: list[str],
    first_graph_revision: int,
    last_graph_revision: int,
    previous_segment_hash: str,
    segment_id: str,
    workspace_id: str,
) -> dict[str, Any]:
    return {
        "commit_hashes": commit_hashes,
        "first_graph_revision": first_graph_revision,
        "last_graph_revision": last_graph_revision,
        "previous_segment_hash": previous_segment_hash,
        "segment_id": segment_id,
        "workspace_id": workspace_id,
    }


def archive_seal_hash(seal: dict[str, Any]) -> str:
    return sha256_hex(
        ARCHIVE_SEAL_DOMAIN + canonical_bytes(_without_field(seal, "archive_seal_hash"))
    )
