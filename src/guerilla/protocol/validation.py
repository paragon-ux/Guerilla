"""GLCP schema validation helpers for Phase 5."""

from __future__ import annotations

from typing import Any

from guerilla.contracts import ContractBundle, ContractError


def _reject_unknown_critical_extensions(message: dict[str, Any], contracts: ContractBundle) -> None:
    known = {
        entry["namespace_id"]
        for entry in contracts.registries["extension_namespaces.json"]["entries"]
    }
    extensions = message.get("extensions", {})
    if not isinstance(extensions, dict):
        return
    for name, extension in extensions.items():
        if not isinstance(extension, dict):
            continue
        if extension.get("critical") is True and extension.get("namespace_id") not in known:
            raise ContractError(
                "unknown_critical_extension",
                f"unknown critical extension namespace for {name}",
            )


def validate_protocol_request(message: dict[str, Any], contracts: ContractBundle) -> None:
    contracts.assert_valid("protocol_request.schema.json", message)
    _reject_unknown_critical_extensions(message, contracts)


def validate_protocol_response(response: dict[str, Any], contracts: ContractBundle) -> None:
    contracts.assert_valid("protocol_response.schema.json", response)


def validate_protocol_error(error: dict[str, Any], contracts: ContractBundle) -> None:
    contracts.assert_valid("protocol_error.schema.json", error)
