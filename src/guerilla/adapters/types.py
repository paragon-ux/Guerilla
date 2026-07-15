"""Typed adapter SDK contracts for trusted in-process Phase 9 adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol, TypeAlias

AdapterCapability: TypeAlias = Literal["describe", "observe", "act", "evaluate", "reconcile"]
RetryClassification: TypeAlias = Literal[
    "never",
    "after_reconcile",
    "after_refresh",
    "after_backoff",
    "idempotent_replay",
    "not_applicable",
]
OperationClassification: TypeAlias = Literal[
    "described",
    "observed",
    "accepted",
    "rejected",
    "failed",
    "pending",
    "outcome_unknown",
    "evaluated",
    "confirmed_accepted",
    "confirmed_rejected",
    "confirmed_failed",
    "still_pending",
    "duplicated",
    "externally_completed_missing_lineage",
    "unknown",
]
SafeJson: TypeAlias = None | bool | int | str | list["SafeJson"] | dict[str, "SafeJson"]


@dataclass(frozen=True, slots=True)
class IdempotencyContext:
    """Adapter-native or future graph-backed idempotency context."""

    key: str
    request_hash: str
    retention_policy: str = "phase9-synthetic"
    native_supported: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AdapterOperationRequest:
    """Typed host-to-adapter request for one operation."""

    workspace_id: str
    adapter_id: str
    adapter_version: str
    system_id: str
    state_boundary_id: str
    operation_id: str
    principal_id: str
    actor: dict[str, Any]
    authority: dict[str, Any]
    contract_version: str
    requested_at: str
    capability: AdapterCapability
    data: dict[str, Any]
    deadline_ms: int | None = None
    timeout_ms: int = 1_000
    correlation_id: str | None = None
    causation_id: str | None = None
    idempotency: IdempotencyContext | None = None
    root: str | None = None
    endpoint: str | None = None
    namespace: str | None = None
    extensions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        if self.idempotency is None:
            value.pop("idempotency")
        return value


@dataclass(frozen=True, slots=True)
class AdapterOperationResult:
    """Typed adapter-to-host result. It is data, not a graph commit."""

    adapter_id: str
    adapter_version: str
    system_id: str
    state_boundary_id: str
    capability: AdapterCapability
    classification: OperationClassification
    occurred_at: str
    evidence: dict[str, Any]
    retry: RetryClassification
    data: dict[str, Any] = field(default_factory=dict)
    external_revision: str | None = None
    external_identity: dict[str, Any] | None = None
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    payload_ref: dict[str, Any] | None = None
    extensions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Adapter(Protocol):
    """Trusted in-process adapter interface."""

    @property
    def descriptor(self) -> dict[str, Any]:
        """Return the adapter descriptor used for host registration."""

    def describe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        """Return descriptor and capability metadata without mutating external state."""

    def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        """Read bounded external state."""

    def act(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        """Request an external mutation through a declared boundary."""

    def evaluate(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        """Evaluate a subject or external revision."""

    def reconcile(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        """Classify a previous uncertain action."""
