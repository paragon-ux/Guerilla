"""Graph integrity error types."""

from __future__ import annotations


class GraphIntegrityError(ValueError):
    def __init__(self, code: str, message: str, *, witness_path: list[str] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.witness_path = witness_path or []


class GraphQueryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
