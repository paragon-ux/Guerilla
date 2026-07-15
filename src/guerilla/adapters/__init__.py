"""Adapter SDK, host, and synthetic external systems."""

from guerilla.adapters.errors import (
    AdapterError,
    AdapterHostError,
    AdapterOperationError,
    AdapterValidationError,
)
from guerilla.adapters.host import AdapterHost
from guerilla.adapters.synthetic import (
    AsyncUnknownOutcomeAdapter,
    ReconstructedFilesystemAdapter,
    TransactionalRevisionedServiceAdapter,
    VirtualClock,
    request_hash,
)
from guerilla.adapters.types import (
    Adapter,
    AdapterOperationRequest,
    AdapterOperationResult,
    IdempotencyContext,
)

__all__ = [
    "Adapter",
    "AdapterError",
    "AdapterHost",
    "AdapterHostError",
    "AdapterOperationError",
    "AdapterOperationRequest",
    "AdapterOperationResult",
    "AdapterValidationError",
    "AsyncUnknownOutcomeAdapter",
    "IdempotencyContext",
    "ReconstructedFilesystemAdapter",
    "TransactionalRevisionedServiceAdapter",
    "VirtualClock",
    "request_hash",
]
