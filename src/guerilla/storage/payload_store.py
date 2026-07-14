"""Content-addressed retained payload storage."""

from __future__ import annotations

import os
from pathlib import Path

from guerilla.codec import payload_hash
from guerilla.storage.errors import StorageError
from guerilla.storage.fsync import fsync_directory, fsync_file


def payload_path(root: Path, digest: str) -> Path:
    if not (len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)):
        raise StorageError("invalid_payload_hash", "payload digest must be 64 lowercase hex")
    return root / ".guerilla" / "payloads" / "sha256" / digest


def write_payload(root: Path, payload: bytes) -> str:
    digest = payload_hash(payload)
    path = payload_path(root, digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return digest
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags)
    with os.fdopen(fd, "wb") as file_obj:
        file_obj.write(payload)
        fsync_file(file_obj)
    fsync_directory(path.parent)
    return digest


def read_payload(root: Path, digest: str) -> bytes:
    path = payload_path(root, digest)
    if not path.exists():
        raise StorageError("payload_missing", "payload is missing")
    payload = path.read_bytes()
    if payload_hash(payload) != digest:
        raise StorageError("payload_hash_mismatch", "payload hash mismatch")
    return payload
