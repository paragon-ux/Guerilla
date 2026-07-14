"""Exclusive local writer lock."""

from __future__ import annotations

import getpass
import json
import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from guerilla import __version__
from guerilla.codec import canonical_jsonl
from guerilla.storage.errors import LockHeldError
from guerilla.storage.fsync import fsync_directory, fsync_file


@dataclass(frozen=True, slots=True)
class LockMetadata:
    workspace_id: str
    pid: int
    host: str
    user: str
    acquired_at: str
    runtime_version: str

    def to_dict(self) -> dict[str, object]:
        return {
            "workspace_id": self.workspace_id,
            "pid": self.pid,
            "host": self.host,
            "user": self.user,
            "acquired_at": self.acquired_at,
            "runtime_version": self.runtime_version,
        }


class WriterLock:
    def __init__(self, lock_path: Path, metadata: LockMetadata) -> None:
        self.lock_path = lock_path
        self.metadata = metadata
        self._held = False

    @classmethod
    def acquire(cls, locks_dir: Path, *, workspace_id: str, acquired_at: str) -> WriterLock:
        locks_dir.mkdir(parents=True, exist_ok=True)
        metadata = LockMetadata(
            workspace_id=workspace_id,
            pid=os.getpid(),
            host=socket.gethostname(),
            user=getpass.getuser(),
            acquired_at=acquired_at,
            runtime_version=__version__,
        )
        lock_path = locks_dir / "writer.lock"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(lock_path, flags)
        except FileExistsError as exc:
            raise LockHeldError("writer_lock_held", "writer lock already exists") from exc
        with os.fdopen(fd, "wb") as file_obj:
            file_obj.write(canonical_jsonl(metadata.to_dict()))
            fsync_file(file_obj)
        fsync_directory(locks_dir)
        lock = cls(lock_path, metadata)
        lock._held = True
        return lock

    @staticmethod
    def inspect(locks_dir: Path) -> dict[str, object] | None:
        lock_path = locks_dir / "writer.lock"
        if not lock_path.exists():
            return None
        metadata = json.loads(lock_path.read_text(encoding="utf-8"))
        return cast(dict[str, object], metadata)

    def release(self) -> None:
        if not self._held:
            return
        try:
            self.lock_path.unlink()
            fsync_directory(self.lock_path.parent)
        finally:
            self._held = False

    def __enter__(self) -> WriterLock:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()
