"""Adapter SDK and host errors for Phase 9."""

from __future__ import annotations


class AdapterError(ValueError):
    """Base adapter error with a stable Guerilla error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class AdapterValidationError(AdapterError):
    """Raised when an adapter descriptor, request, or result is invalid."""


class AdapterHostError(AdapterError):
    """Raised when the in-process adapter host rejects or normalizes an operation."""


class AdapterOperationError(AdapterError):
    """Raised by trusted adapters when a structured operation cannot complete."""
