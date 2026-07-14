"""Small fsync helpers for the local storage profile."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol


class Fsyncable(Protocol):
    def flush(self) -> object: ...

    def fileno(self) -> int: ...


def fsync_file(file_obj: Fsyncable) -> None:
    file_obj.flush()
    os.fsync(file_obj.fileno())


def fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
