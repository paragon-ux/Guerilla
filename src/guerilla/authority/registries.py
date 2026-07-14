"""Committed configuration registries for Phase 8 authority boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from guerilla.authority.errors import BoundaryError, IdentityConflictError
from guerilla.contracts import ContractBundle

REGISTRY_METADATA_KEY = "guerilla_registry"


@dataclass(frozen=True, slots=True)
class ExternalSystemRegistration:
    system_id: str
    name: str
    system_type: str
    owner_principal_id: str
    identity_semantics: str
    revision_semantics: str
    lifecycle_status: str = "active"


@dataclass(slots=True)
class BoundaryRegistry:
    contracts: ContractBundle
    boundaries: dict[str, dict[str, Any]] = field(default_factory=dict)

    def register(self, boundary: dict[str, Any]) -> None:
        self.contracts.assert_valid("state_boundary.schema.json", boundary)
        boundary_id = str(boundary["state_boundary_id"])
        self._reject_ambiguous_writer(boundary)
        self.boundaries[boundary_id] = boundary

    def require_operation(
        self,
        boundary_id: str,
        operation: str,
        *,
        root: str | None = None,
        endpoint: str | None = None,
        namespace: str | None = None,
    ) -> dict[str, Any]:
        boundary = self._boundary(boundary_id)
        if operation not in boundary["permitted_operations"]:
            raise BoundaryError("state_boundary_violation", "operation is not permitted")
        if root is not None:
            self._require_root(boundary, root)
        if endpoint is not None:
            self._require_member(boundary, "permitted_endpoints", endpoint)
        if namespace is not None:
            self._require_member(boundary, "resource_namespaces", namespace)
        return boundary

    def _boundary(self, boundary_id: str) -> dict[str, Any]:
        try:
            return self.boundaries[boundary_id]
        except KeyError as exc:
            raise BoundaryError("unknown_boundary", "state boundary is not registered") from exc

    def _reject_ambiguous_writer(self, candidate: dict[str, Any]) -> None:
        if "act" not in candidate["permitted_operations"]:
            return
        candidate_namespaces = set(candidate.get("resource_namespaces", []))
        candidate_roots = {_normalize_root(root) for root in candidate.get("permitted_roots", [])}
        for existing in self.boundaries.values():
            if existing["system_id"] != candidate["system_id"]:
                continue
            if "act" not in existing["permitted_operations"]:
                continue
            existing_namespaces = set(existing.get("resource_namespaces", []))
            existing_roots = {_normalize_root(root) for root in existing.get("permitted_roots", [])}
            if candidate_namespaces & existing_namespaces or candidate_roots & existing_roots:
                raise BoundaryError("ambiguous_authority", "overlapping primary write boundary")

    @staticmethod
    def _require_root(boundary: dict[str, Any], requested: str) -> None:
        roots = boundary.get("permitted_roots", [])
        if not roots:
            raise BoundaryError("state_boundary_violation", "boundary declares no permitted roots")
        requested_path = Path(requested).resolve(strict=False)
        for root in roots:
            root_path = Path(str(root)).resolve(strict=False)
            if requested_path == root_path or root_path in requested_path.parents:
                return
        raise BoundaryError("state_boundary_violation", "requested root escapes boundary")

    @staticmethod
    def _require_member(boundary: dict[str, Any], field: str, requested: str) -> None:
        allowed = {str(value) for value in boundary.get(field, [])}
        if requested not in allowed:
            raise BoundaryError("state_boundary_violation", f"{field} does not include request")

    @classmethod
    def from_replay(cls, replay: Any, contracts: ContractBundle) -> BoundaryRegistry:
        registry = cls(contracts=contracts)
        for payload in _registry_payloads(replay, "state_boundary"):
            registry.register(payload)
        return registry


@dataclass(slots=True)
class AdapterIdentityRegistry:
    contracts: ContractBundle
    boundary_registry: BoundaryRegistry
    adapters: dict[str, dict[str, Any]] = field(default_factory=dict)

    def register(self, descriptor: dict[str, Any]) -> None:
        self.contracts.assert_valid("adapter_descriptor.schema.json", descriptor)
        for boundary in descriptor["state_boundaries"]:
            if str(boundary["state_boundary_id"]) not in self.boundary_registry.boundaries:
                self.boundary_registry.register(boundary)
        known_boundaries = set(self.boundary_registry.boundaries)
        for capability in descriptor["capabilities"]:
            for boundary_id in capability["state_boundary_ids"]:
                if boundary_id not in known_boundaries:
                    raise BoundaryError(
                        "state_boundary_violation", "capability references unknown boundary"
                    )
        self.adapters[str(descriptor["adapter_id"])] = descriptor


@dataclass(slots=True)
class ExternalIdentityRegistry:
    contracts: ContractBundle
    identities: dict[tuple[str, str, str, str, str, str | None], dict[str, Any]] = field(
        default_factory=dict
    )

    def record_observed(self, identity: dict[str, Any]) -> None:
        self.contracts.assert_valid("external_identity.schema.json", identity)
        self.identities[_identity_key(identity)] = dict(identity)

    def record_renamed(self, previous: dict[str, Any], current: dict[str, Any]) -> None:
        previous_event = dict(previous)
        previous_event["lifecycle_state"] = "renamed"
        current_event = dict(current)
        current_event.setdefault("lifecycle_state", "observed")
        self.record_observed(previous_event)
        self.record_observed(current_event)

    def record_deleted(self, identity: dict[str, Any]) -> None:
        deleted = dict(identity)
        deleted["lifecycle_state"] = "deleted"
        self.record_observed(deleted)

    def record_reused(self, identity: dict[str, Any]) -> None:
        self.contracts.assert_valid("external_identity.schema.json", identity)
        raise IdentityConflictError(
            "identity_collision",
            "external identity reuse requires conflict evidence",
            evidence={"external_identity": dict(identity)},
        )

    def record_alias(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
        *,
        decision_node_id: str | None = None,
    ) -> None:
        if decision_node_id is None:
            raise IdentityConflictError(
                "alias_requires_reified_assertion",
                "cross-system aliasing requires a decision or reified assertion",
                evidence={"left": dict(left), "right": dict(right)},
            )
        left_alias = dict(left)
        right_alias = dict(right)
        left_alias["lifecycle_state"] = "aliased"
        right_alias["lifecycle_state"] = "aliased"
        left_alias.setdefault("metadata", {})["decision_node_id"] = decision_node_id
        right_alias.setdefault("metadata", {})["decision_node_id"] = decision_node_id
        self.record_observed(left_alias)
        self.record_observed(right_alias)


def _registry_payloads(replay: Any, kind: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for node in replay.nodes.values():
        metadata = node.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        payload = metadata.get(REGISTRY_METADATA_KEY)
        if isinstance(payload, dict) and payload.get("kind") == kind:
            value = payload.get("value")
            if isinstance(value, dict):
                payloads.append(value)
    return payloads


def _identity_key(identity: dict[str, Any]) -> tuple[str, str, str, str, str, str | None]:
    return (
        str(identity["system_id"]),
        str(identity["state_boundary_id"]),
        str(identity["external_kind"]),
        str(identity["external_id"]),
        str(identity.get("namespace", "")),
        str(identity.get("external_revision")) if "external_revision" in identity else None,
    )


def _normalize_root(root: str) -> str:
    return str(Path(root).resolve(strict=False))
