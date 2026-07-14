"""Authority and boundary error types."""

from __future__ import annotations


class AuthorityError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class BoundaryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class IdentityConflictError(ValueError):
    def __init__(
        self, code: str, message: str, *, evidence: dict[str, object] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.evidence = evidence or {}
