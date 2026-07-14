"""Payload hashing and verification primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from guerilla.codec import payload_hash


@dataclass(frozen=True, slots=True)
class PayloadVerification:
    ok: bool
    status: str
    expected_hash: str | None = None
    actual_hash: str | None = None


def verify_payload_reference(
    payload_ref: dict[str, Any], payload: bytes | None
) -> PayloadVerification:
    retention_class = payload_ref.get("retention_class")
    if retention_class in {"none", "metadata", "external_reference"}:
        if payload is None:
            return PayloadVerification(ok=True, status="not_retained")
        return PayloadVerification(ok=False, status="unexpected_payload")
    if retention_class != "content_addressed":
        return PayloadVerification(ok=False, status="unsupported_retention_class")
    expected = payload_ref.get("payload_hash")
    if not isinstance(expected, str):
        return PayloadVerification(ok=False, status="missing_payload_hash")
    if payload is None:
        return PayloadVerification(ok=False, status="missing_payload", expected_hash=expected)
    actual = payload_hash(payload)
    if actual != expected:
        return PayloadVerification(
            ok=False,
            status="payload_hash_mismatch",
            expected_hash=expected,
            actual_hash=actual,
        )
    return PayloadVerification(
        ok=True,
        status="verified",
        expected_hash=expected,
        actual_hash=actual,
    )
