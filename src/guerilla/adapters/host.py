"""Trusted in-process adapter host for Phase 9."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import Any, cast

from guerilla.adapters.errors import AdapterHostError, AdapterValidationError
from guerilla.adapters.types import (
    Adapter,
    AdapterCapability,
    AdapterOperationRequest,
    AdapterOperationResult,
)
from guerilla.authority import (
    AdapterIdentityRegistry,
    BoundaryRegistry,
    LocalAuthorizationProfile,
    validate_authority_envelope,
)
from guerilla.authority.errors import BoundaryError
from guerilla.contracts import ContractBundle

CONTRACT_VERSION = "0.2.0"
DESCRIPTOR_TRUST_MODEL = "trusted_in_process_python"
ADAPTER_AUTH_OPERATION: dict[AdapterCapability, str] = {
    "describe": "adapter.observe",
    "observe": "adapter.observe",
    "act": "adapter.act",
    "evaluate": "adapter.observe",
    "reconcile": "adapter.observe",
}
REQUIRED_CAPABILITY_METADATA = frozenset(
    {
        "read_consistency",
        "write_behavior",
        "event_ordering",
        "concurrency",
        "conflict_handling",
        "replay_support",
        "snapshot_support",
        "identity_stability",
        "lineage_completeness",
        "idempotency",
        "schemas",
        "limitations",
    }
)
RESULT_CLASSIFICATIONS: dict[AdapterCapability, frozenset[str]] = {
    "describe": frozenset({"described"}),
    "observe": frozenset({"observed", "failed"}),
    "act": frozenset(
        {"accepted", "rejected", "failed", "pending", "outcome_unknown", "duplicated"}
    ),
    "evaluate": frozenset({"evaluated", "failed"}),
    "reconcile": frozenset(
        {
            "confirmed_accepted",
            "confirmed_rejected",
            "confirmed_failed",
            "still_pending",
            "duplicated",
            "externally_completed_missing_lineage",
            "unknown",
            "failed",
        }
    ),
}
JSON_SAFE_MIN = -9_007_199_254_740_991
JSON_SAFE_MAX = 9_007_199_254_740_991


class AdapterHost:
    """Register configured adapters and invoke exactly one validated operation."""

    def __init__(
        self,
        *,
        contracts: ContractBundle,
        adapters: Iterable[Adapter] = (),
        owner_principal_id: str = "local-user",
        clock_ms: Callable[[], int] | None = None,
    ) -> None:
        self.contracts = contracts
        self.boundaries = BoundaryRegistry(contracts=contracts)
        self.adapter_identities = AdapterIdentityRegistry(
            contracts=contracts,
            boundary_registry=self.boundaries,
        )
        self.authorization = LocalAuthorizationProfile(owner_principal_id=owner_principal_id)
        self._clock_ms = clock_ms or (lambda: int(time.monotonic_ns() // 1_000_000))
        self._adapters: dict[str, Adapter] = {}
        self._descriptors: dict[str, dict[str, Any]] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: Adapter) -> None:
        descriptor = adapter.descriptor
        self._validate_descriptor(descriptor)
        adapter_id = str(descriptor["adapter_id"])
        if adapter_id in self._adapters:
            raise AdapterHostError("duplicate_id", "adapter id is already registered")
        self.adapter_identities.register(descriptor)
        self._adapters[adapter_id] = adapter
        self._descriptors[adapter_id] = descriptor

    def descriptor(self, adapter_id: str) -> dict[str, Any]:
        try:
            return self._descriptors[adapter_id]
        except KeyError as exc:
            raise AdapterHostError("unknown_adapter", "adapter is not registered") from exc

    def invoke(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        start_ms = self._clock_ms()
        self._validate_request(request, now_ms=start_ms)
        adapter = self._adapters[request.adapter_id]
        operation = getattr(adapter, request.capability)
        try:
            result = cast(AdapterOperationResult, operation(request))
        except AdapterHostError:
            raise
        except Exception as exc:
            raise AdapterHostError("adapter_error", "adapter operation failed") from exc
        elapsed_ms = self._clock_ms() - start_ms
        if elapsed_ms > request.timeout_ms:
            raise AdapterHostError("adapter_unavailable", "adapter operation exceeded timeout")
        self._validate_result(request, result)
        return result

    def _validate_descriptor(self, descriptor: dict[str, Any]) -> None:
        self.contracts.assert_valid("adapter_descriptor.schema.json", descriptor)
        if descriptor["trust_model"] != DESCRIPTOR_TRUST_MODEL:
            raise AdapterValidationError("schema_violation", "unsupported adapter trust model")
        _assert_safe_json(descriptor)
        capabilities = descriptor.get("capabilities", [])
        if not isinstance(capabilities, list):
            raise AdapterValidationError("schema_violation", "capabilities must be a list")
        seen_capability_boundaries: set[tuple[str, str]] = set()
        for capability in capabilities:
            if not isinstance(capability, dict):
                raise AdapterValidationError("schema_violation", "capability must be an object")
            for boundary_id in capability["state_boundary_ids"]:
                key = (str(capability["capability"]), str(boundary_id))
                if key in seen_capability_boundaries:
                    raise AdapterValidationError(
                        "duplicate_id",
                        "duplicate capability declaration for boundary",
                    )
                seen_capability_boundaries.add(key)
            if capability.get("supported") is True:
                metadata = capability.get("metadata")
                if not isinstance(metadata, dict):
                    raise AdapterValidationError(
                        "schema_violation",
                        "supported capability requires metadata",
                    )
                missing = sorted(REQUIRED_CAPABILITY_METADATA - set(metadata))
                if missing:
                    raise AdapterValidationError(
                        "schema_violation",
                        f"capability metadata missing: {', '.join(missing)}",
                    )
                if capability["capability"] == "act" and not metadata.get("mutating_actions"):
                    raise AdapterValidationError(
                        "schema_violation",
                        "act capability must declare mutating_actions",
                    )

    def _validate_request(self, request: AdapterOperationRequest, *, now_ms: int) -> None:
        if request.contract_version != CONTRACT_VERSION:
            raise AdapterValidationError("unsupported_version", "unsupported contract version")
        descriptor = self.descriptor(request.adapter_id)
        if request.adapter_version != descriptor["version"]:
            raise AdapterValidationError("unsupported_version", "adapter version mismatch")
        if request.system_id != descriptor["system_id"]:
            raise AdapterValidationError("state_boundary_violation", "request system mismatch")
        if request.timeout_ms < 0:
            raise AdapterValidationError("invalid_message", "timeout must be non-negative")
        if request.deadline_ms is not None and now_ms > request.deadline_ms:
            raise AdapterHostError("adapter_unavailable", "adapter operation deadline expired")
        if request.capability == "act" and request.idempotency is None:
            raise AdapterValidationError(
                "idempotency_conflict",
                "act request requires idempotency context",
            )
        _assert_safe_json(request.data)
        _assert_safe_json(request.actor)
        _assert_safe_json(request.authority)
        _assert_safe_json(request.extensions)
        _assert_supported_extensions(self.contracts, request.extensions)
        validate_authority_envelope(
            request.authority,
            effective_principal_id=request.principal_id,
        )
        self.authorization.require(request.principal_id, ADAPTER_AUTH_OPERATION[request.capability])
        self._require_declared_capability(descriptor, request.capability, request.state_boundary_id)
        if request.capability == "describe":
            if request.state_boundary_id not in self.boundaries.boundaries:
                raise BoundaryError("state_boundary_violation", "unknown state boundary")
        else:
            self.boundaries.require_operation(
                request.state_boundary_id,
                request.capability,
                root=request.root,
                endpoint=request.endpoint,
                namespace=request.namespace,
            )

    def _require_declared_capability(
        self,
        descriptor: dict[str, Any],
        capability_name: AdapterCapability,
        boundary_id: str,
    ) -> None:
        for capability in descriptor["capabilities"]:
            if (
                capability["capability"] == capability_name
                and capability.get("supported") is True
                and boundary_id in capability["state_boundary_ids"]
            ):
                return
        raise AdapterHostError("unsupported_capability", "capability is not declared")

    def _validate_result(
        self,
        request: AdapterOperationRequest,
        result: AdapterOperationResult,
    ) -> None:
        if result.adapter_id != request.adapter_id:
            raise AdapterValidationError("schema_violation", "result adapter mismatch")
        if result.adapter_version != request.adapter_version:
            raise AdapterValidationError("schema_violation", "result adapter version mismatch")
        if result.system_id != request.system_id:
            raise AdapterValidationError("schema_violation", "result system mismatch")
        if result.state_boundary_id != request.state_boundary_id:
            raise AdapterValidationError("schema_violation", "result boundary mismatch")
        if result.capability != request.capability:
            raise AdapterValidationError("schema_violation", "result capability mismatch")
        if result.classification not in RESULT_CLASSIFICATIONS[request.capability]:
            raise AdapterValidationError(
                "schema_violation",
                "result classification is not valid for capability",
            )
        _assert_safe_json(result.data)
        _assert_safe_json(result.evidence)
        _assert_safe_json(result.extensions)
        _assert_supported_extensions(self.contracts, result.extensions)
        if result.payload_ref is not None:
            self.contracts.assert_valid("payload_ref.schema.json", result.payload_ref)
        if result.external_identity is not None:
            self.contracts.assert_valid("external_identity.schema.json", result.external_identity)
            if result.external_identity["system_id"] != request.system_id:
                raise AdapterValidationError(
                    "schema_violation",
                    "external identity system mismatch",
                )
            if result.external_identity["state_boundary_id"] != request.state_boundary_id:
                raise AdapterValidationError(
                    "schema_violation",
                    "external identity boundary mismatch",
                )


def _assert_supported_extensions(contracts: ContractBundle, extensions: dict[str, Any]) -> None:
    known_namespaces = {
        str(entry["namespace_id"])
        for entry in contracts.registries["extension_namespaces.json"]["entries"]
    }
    for name, extension in extensions.items():
        if not isinstance(extension, dict):
            raise AdapterValidationError("schema_violation", f"invalid extension {name}")
        if (
            extension.get("critical") is True
            and extension.get("namespace_id") not in known_namespaces
        ):
            raise AdapterValidationError(
                "unknown_critical_extension",
                f"unknown critical extension namespace for {name}",
            )


def _assert_safe_json(value: Any) -> None:
    if value is None or isinstance(value, str | bool):
        return
    if isinstance(value, int):
        if not JSON_SAFE_MIN <= value <= JSON_SAFE_MAX:
            raise AdapterValidationError("invalid_message", "integer exceeds JSON-safe range")
        return
    if isinstance(value, float):
        raise AdapterValidationError("invalid_message", "floating point JSON is not supported")
    if isinstance(value, list):
        for item in value:
            _assert_safe_json(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AdapterValidationError("invalid_message", "object keys must be strings")
            _assert_safe_json(item)
        return
    raise AdapterValidationError("invalid_message", "value is not safe JSON")
