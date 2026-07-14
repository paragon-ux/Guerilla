"""DAG and endpoint validation for authoritative graph transactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from guerilla.graph.errors import GraphIntegrityError

DEFAULT_TRAVERSAL_LIMIT = 10_000
DEFAULT_MAX_DEPTH = 1_000


@dataclass(frozen=True, slots=True)
class RelationshipRule:
    value: str
    from_node_types: frozenset[str]
    to_node_types: frozenset[str]
    acyclic: bool


def relationship_rules(registries: dict[str, dict[str, Any]]) -> dict[str, RelationshipRule]:
    try:
        entries = registries["relationship_types.json"]["entries"]
    except KeyError as exc:
        raise GraphIntegrityError(
            "missing_relationship_registry",
            "relationship registry is unavailable",
        ) from exc
    rules: dict[str, RelationshipRule] = {}
    for entry in entries:
        value = str(entry["value"])
        from_types = entry.get("from_node_types")
        to_types = entry.get("to_node_types")
        if not isinstance(from_types, list) or not isinstance(to_types, list):
            raise GraphIntegrityError(
                "missing_endpoint_restriction",
                f"relationship {value} has no endpoint type restrictions",
            )
        rules[value] = RelationshipRule(
            value=value,
            from_node_types=frozenset(str(item) for item in from_types),
            to_node_types=frozenset(str(item) for item in to_types),
            acyclic=entry.get("direct_edge_must_remain_acyclic") is True,
        )
    return rules


def _member_id(record: dict[str, Any]) -> str:
    if record.get("record_type") == "node":
        return str(record["node_id"])
    if record.get("record_type") == "edge":
        return str(record["edge_id"])
    raise GraphIntegrityError("unsupported_record_type", "only node and edge records are supported")


def _adjacency_from_edges(edges: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for edge in edges.values():
        adjacency.setdefault(str(edge["from_node_id"]), set()).add(str(edge["to_node_id"]))
    return adjacency


def _find_path(
    adjacency: dict[str, set[str]],
    start: str,
    target: str,
    *,
    max_depth: int,
    traversal_limit: int,
) -> list[str] | None:
    stack: list[tuple[str, list[str]]] = [(start, [start])]
    visited: set[str] = set()
    steps = 0
    while stack:
        node_id, path = stack.pop()
        if node_id == target:
            return path
        if node_id in visited:
            continue
        visited.add(node_id)
        steps += 1
        if steps > traversal_limit:
            raise GraphIntegrityError(
                "traversal_limit_exceeded",
                "cycle validation exceeded traversal limit",
            )
        if len(path) > max_depth:
            raise GraphIntegrityError("max_depth_exceeded", "cycle validation exceeded max depth")
        for next_id in sorted(adjacency.get(node_id, ()), reverse=True):
            if next_id not in visited:
                stack.append((next_id, [*path, next_id]))
    return None


def validate_transaction_integrity(
    *,
    committed_nodes: dict[str, dict[str, Any]],
    committed_edges: dict[str, dict[str, Any]],
    members: list[dict[str, Any]],
    registries: dict[str, dict[str, Any]],
    max_depth: int = DEFAULT_MAX_DEPTH,
    traversal_limit: int = DEFAULT_TRAVERSAL_LIMIT,
) -> None:
    rules = relationship_rules(registries)
    adjacency = _adjacency_from_edges(committed_edges)
    node_types = {node_id: str(node["node_type"]) for node_id, node in committed_nodes.items()}
    seen_member_ids: set[str] = set()
    for member in members:
        identifier = _member_id(member)
        if identifier in seen_member_ids:
            raise GraphIntegrityError("duplicate_id", "transaction contains duplicate identifiers")
        seen_member_ids.add(identifier)
        if member.get("record_type") == "node":
            if identifier in committed_nodes or identifier in committed_edges:
                raise GraphIntegrityError("duplicate_id", "node identifier already exists")
            node_types[identifier] = str(member["node_type"])

    for member in members:
        if member.get("record_type") != "edge":
            continue
        edge_id = str(member["edge_id"])
        if edge_id in committed_edges or edge_id in committed_nodes:
            raise GraphIntegrityError("duplicate_id", "edge identifier already exists")
        relationship_type = str(member["relationship_type"])
        rule = rules.get(relationship_type)
        if rule is None:
            raise GraphIntegrityError(
                "unknown_relationship_type",
                f"relationship type is not registered: {relationship_type}",
            )
        if not rule.acyclic:
            raise GraphIntegrityError(
                "non_acyclic_direct_edge",
                f"relationship type cannot be stored as a direct edge: {relationship_type}",
            )
        from_node_id = str(member["from_node_id"])
        to_node_id = str(member["to_node_id"])
        if from_node_id == to_node_id:
            raise GraphIntegrityError("self_loop", "direct edges cannot point to the same node")
        from_type = node_types.get(from_node_id)
        to_type = node_types.get(to_node_id)
        if from_type is None or to_type is None:
            raise GraphIntegrityError("missing_endpoint", "edge endpoint does not exist")
        if from_type not in rule.from_node_types or to_type not in rule.to_node_types:
            raise GraphIntegrityError(
                "incompatible_endpoint_type",
                "edge endpoint node type is incompatible with the relationship type",
            )
        witness_path = _find_path(
            adjacency,
            to_node_id,
            from_node_id,
            max_depth=max_depth,
            traversal_limit=traversal_limit,
        )
        if witness_path is not None:
            raise GraphIntegrityError(
                "lineage_cycle",
                "direct edge would create a lineage cycle",
                witness_path=[from_node_id, to_node_id, *witness_path[1:]],
            )
        adjacency.setdefault(from_node_id, set()).add(to_node_id)
