"""Deterministic derived projections for Phase 13."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias

from guerilla.codec import canonical_bytes, payload_hash
from guerilla.conflicts import PHASE12_CONFLICT_METADATA_KEY
from guerilla.graph import GraphQuery
from guerilla.index import SQLiteGraphIndex
from guerilla.observability.ingestion import PHASE10_METADATA_KEY
from guerilla.storage import GraphStore

TRANSFORMATION_VERSION = "phase13-projections-v1"
DEFAULT_POLICY_VERSION = "phase13-default-policy-v1"
DEFAULT_GENERATED_AT = "1970-01-01T00:00:00Z"
DERIVED_AUTHORITY = "derived_non_authoritative"

ProjectionView: TypeAlias = Literal[
    "lineage",
    "dependency",
    "conflict",
    "manifest",
    "diff",
    "progress",
    "traceability",
]
LineageDirection: TypeAlias = Literal[
    "ancestors",
    "descendants",
    "both",
    "immediate_predecessors",
    "immediate_successors",
]


class ProjectionError(ValueError):
    """Raised when a projection cannot be generated deterministically."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ProjectionResult:
    """A derived, non-authoritative projection result."""

    projection_id: str
    view_type: ProjectionView
    workspace_id: str
    graph_revision: int
    commit_hash: str
    generated_at: str
    transformation_version: str
    policy_version: str
    source_query: dict[str, Any]
    source_node_ids: tuple[str, ...]
    freshness: dict[str, Any]
    information_loss: tuple[str, ...]
    persistence_mode: str
    authoritative_status: str
    payload: dict[str, Any]
    result_hash: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_node_ids"] = list(self.source_node_ids)
        value["information_loss"] = list(self.information_loss)
        return value


@dataclass(frozen=True, slots=True)
class PersistedProjection:
    """Location and digest for a persisted derived view."""

    path: Path
    result_hash: str
    graph_revision: int
    view_type: ProjectionView


class ProjectionEngine:
    """Generate source-bound projections from replay or rebuilt index data."""

    def __init__(self, *, store: GraphStore, use_index: bool = False) -> None:
        self.store = store
        self.use_index = use_index

    def lineage(
        self,
        node_id: str,
        *,
        direction: LineageDirection = "ancestors",
        revision: int | None = None,
        max_depth: int = 1_000,
        limit: int = 10_000,
        generated_at: str = DEFAULT_GENERATED_AT,
        policy_version: str = DEFAULT_POLICY_VERSION,
    ) -> ProjectionResult:
        query = self._query()
        target = query._revision(revision)
        nodes = _visible_nodes(query, target)
        if node_id not in nodes:
            raise ProjectionError("missing_endpoint", "lineage root node is not visible")
        if direction == "ancestors":
            related = query.ancestors(
                node_id,
                revision=target,
                max_depth=max_depth,
                limit=limit,
            )
            related_items = [str(item) for item in related.items]
            truncated = related.truncated
        elif direction == "descendants":
            related = query.descendants(
                node_id,
                revision=target,
                max_depth=max_depth,
                limit=limit,
            )
            related_items = [str(item) for item in related.items]
            truncated = related.truncated
        elif direction == "both":
            ancestors = query.ancestors(node_id, revision=target, max_depth=max_depth, limit=limit)
            descendants = query.descendants(
                node_id,
                revision=target,
                max_depth=max_depth,
                limit=limit,
            )
            related_items = sorted({*ancestors.items, *descendants.items})
            truncated = ancestors.truncated or descendants.truncated
        elif direction == "immediate_predecessors":
            related_ids = sorted(
                edge["from_node_id"]
                for edge in _visible_edges(query, target).values()
                if edge["to_node_id"] == node_id
            )
            related_items = related_ids[:limit]
            truncated = len(related_ids) > limit
        else:
            related_ids = sorted(
                edge["to_node_id"]
                for edge in _visible_edges(query, target).values()
                if edge["from_node_id"] == node_id
            )
            related_items = related_ids[:limit]
            truncated = len(related_ids) > limit
        source_node_ids = sorted({node_id, *related_items})
        edges = _edges_within(query, target, source_node_ids)
        payload = {
            "root_node_id": node_id,
            "direction": direction,
            "nodes": _node_summaries(nodes, source_node_ids, query, target),
            "edges": _edge_summaries(edges, query, target),
            "truncated": truncated,
        }
        return self._result(
            view_type="lineage",
            query=query,
            revision=target,
            generated_at=generated_at,
            policy_version=policy_version,
            source_query={
                "view": "lineage",
                "node_id": node_id,
                "direction": direction,
                "max_depth": max_depth,
                "limit": limit,
            },
            source_node_ids=tuple(source_node_ids),
            information_loss=(
                "payload contains node and edge summaries, not complete record bodies",
            ),
            payload=payload,
        )

    def dependency(
        self,
        *,
        revision: int | None = None,
        generated_at: str = DEFAULT_GENERATED_AT,
        policy_version: str = DEFAULT_POLICY_VERSION,
        limit: int = 10_000,
    ) -> ProjectionResult:
        query = self._query()
        target = query._revision(revision)
        edges = [
            edge
            for edge in _visible_edges(query, target).values()
            if edge["relationship_type"] == "depends_on"
        ]
        edges.sort(key=lambda edge: (edge["from_node_id"], edge["to_node_id"], edge["edge_id"]))
        truncated = len(edges) > limit
        selected = edges[:limit]
        source_nodes = sorted(
            {str(edge["from_node_id"]) for edge in selected}
            | {str(edge["to_node_id"]) for edge in selected}
        )
        payload = {
            "edges": _edge_summaries(selected, query, target),
            "truncated": truncated,
        }
        return self._result(
            view_type="dependency",
            query=query,
            revision=target,
            generated_at=generated_at,
            policy_version=policy_version,
            source_query={"view": "dependency", "relationship_type": "depends_on", "limit": limit},
            source_node_ids=tuple(source_nodes),
            information_loss=("only direct depends_on edges are included",),
            payload=payload,
        )

    def conflict(
        self,
        *,
        revision: int | None = None,
        status: str | None = "open",
        generated_at: str = DEFAULT_GENERATED_AT,
        policy_version: str = DEFAULT_POLICY_VERSION,
    ) -> ProjectionResult:
        query = self._query()
        target = query._revision(revision)
        nodes = _visible_nodes(query, target)
        conflicts = [node for node in nodes.values() if node["node_type"] == "conflict"]
        conflicts.sort(key=lambda node: (node["status"], node["created_at"], node["node_id"]))
        decisions_by_conflict = _decisions_by_conflict(query, target)
        payload = {
            "status_filter": status,
            "conflicts": [
                {
                    "node_id": node["node_id"],
                    "record_status": node["status"],
                    "effective_status": _conflict_effective_status(
                        node,
                        decisions_by_conflict,
                    ),
                    "conflict_type": node["metadata"].get("conflict_type"),
                    "metadata": node["metadata"].get(PHASE12_CONFLICT_METADATA_KEY),
                    "resolved_by": decisions_by_conflict.get(str(node["node_id"]), []),
                    "authority": node.get("authority"),
                    "state_boundary_id": node.get("state_boundary_id"),
                }
                for node in conflicts
                if status is None
                or _conflict_effective_status(node, decisions_by_conflict) == status
            ],
        }
        return self._result(
            view_type="conflict",
            query=query,
            revision=target,
            generated_at=generated_at,
            policy_version=policy_version,
            source_query={"view": "conflict", "status": status},
            source_node_ids=tuple(str(node["node_id"]) for node in conflicts),
            information_loss=("conflict view omits non-conflict historical context",),
            payload=payload,
        )

    def manifest(
        self,
        *,
        revision: int | None = None,
        node_types: tuple[str, ...] = ("artifact",),
        generated_at: str = DEFAULT_GENERATED_AT,
        policy_version: str = DEFAULT_POLICY_VERSION,
    ) -> ProjectionResult:
        query = self._query()
        target = query._revision(revision)
        nodes = _visible_nodes(query, target)
        eligible = [
            node
            for node in nodes.values()
            if node["node_type"] in node_types
            and not _is_superseded(query, target, str(node["node_id"]))
        ]
        eligible.sort(key=lambda node: (node["node_type"], node["entity_id"], node["node_id"]))
        entries = []
        for node in eligible:
            observation = _phase10_metadata(node)
            entries.append(
                {
                    "node_id": node["node_id"],
                    "entity_id": node["entity_id"],
                    "node_type": node["node_type"],
                    "status": node["status"],
                    "state_boundary_id": node.get("state_boundary_id"),
                    "graph_revision": query.replay.record_revisions[node["node_id"]],
                    "external_identity": None
                    if observation is None
                    else observation.get("external_identity"),
                    "external_revision": None
                    if observation is None
                    else observation.get("external_revision"),
                    "content_hash": None
                    if observation is None
                    else observation.get("content_hash"),
                    "authority": node["authority"],
                }
            )
        ambiguity_reports = _manifest_ambiguity_reports(entries)
        stale_reports = _manifest_stale_reports(entries)
        payload = {
            "entries": entries,
            "ambiguity_reports": ambiguity_reports,
            "stale_observation_reports": stale_reports,
        }
        return self._result(
            view_type="manifest",
            query=query,
            revision=target,
            generated_at=generated_at,
            policy_version=policy_version,
            source_query={"view": "manifest", "node_types": list(node_types)},
            source_node_ids=tuple(str(entry["node_id"]) for entry in entries),
            information_loss=(
                "manifest selects latest non-superseded eligible nodes "
                "and omits full event history",
            ),
            payload=payload,
        )

    def diff(
        self,
        *,
        left_revision: int,
        right_revision: int | None = None,
        generated_at: str = DEFAULT_GENERATED_AT,
        policy_version: str = DEFAULT_POLICY_VERSION,
    ) -> ProjectionResult:
        query = self._query()
        right = query._revision(right_revision)
        left = query._revision(left_revision)
        if left > right:
            raise ProjectionError(
                "invalid_revision", "left revision must not exceed right revision"
            )
        left_nodes = _visible_nodes(query, left)
        right_nodes = _visible_nodes(query, right)
        left_edges = _visible_edges(query, left)
        right_edges = _visible_edges(query, right)
        added_nodes = sorted(set(right_nodes) - set(left_nodes))
        added_edges = sorted(set(right_edges) - set(left_edges))
        payload = {
            "left": {"graph_revision": left, "commit_hash": query._commit_hash(left)},
            "right": {"graph_revision": right, "commit_hash": query._commit_hash(right)},
            "added_nodes": _node_summaries(right_nodes, added_nodes, query, right),
            "added_edges": _edge_summaries(
                [right_edges[edge_id] for edge_id in added_edges], query, right
            ),
            "superseded_nodes": _superseded_between(query, left, right),
            "opened_conflicts": _conflict_ids_between(query, left, right, status="open"),
            "resolved_conflicts": _resolved_conflicts_between(query, left, right),
            "policy_only_status_changes": [],
            "refreshed_observations": _refreshed_observations_between(query, left, right),
            "omitted_unchanged_history": True,
        }
        return self._result(
            view_type="diff",
            query=query,
            revision=right,
            generated_at=generated_at,
            policy_version=policy_version,
            source_query={"view": "diff", "left_revision": left, "right_revision": right},
            source_node_ids=tuple(sorted(set(added_nodes) | set(left_nodes))),
            information_loss=("unchanged record bodies are omitted",),
            payload=payload,
        )

    def progress(
        self,
        *,
        revision: int | None = None,
        generated_at: str = DEFAULT_GENERATED_AT,
        policy_version: str = DEFAULT_POLICY_VERSION,
    ) -> ProjectionResult:
        query = self._query()
        target = query._revision(revision)
        heads = query.heads(revision=target).items
        open_conflicts = self.conflict(
            revision=target,
            status="open",
            generated_at=generated_at,
            policy_version=policy_version,
        ).payload["conflicts"]
        nodes = _visible_nodes(query, target)
        operations = [
            node
            for node in nodes.values()
            if node["node_type"] == "operation"
            and node["status"] not in {"completed", "resolved", "closed"}
        ]
        operations.sort(key=lambda node: (node["status"], node["created_at"], node["node_id"]))
        open_conflict_node_ids = [str(item["node_id"]) for item in open_conflicts]
        payload = {
            "structural_heads": heads,
            "open_conflict_node_ids": open_conflict_node_ids,
            "blocked": bool(open_conflicts),
            "eligible_next_operations": [
                {"node_id": node["node_id"], "status": node["status"]} for node in operations
            ],
            "stale_observations": _manifest_stale_reports(
                self.manifest(revision=target).payload["entries"]
            ),
        }
        return self._result(
            view_type="progress",
            query=query,
            revision=target,
            generated_at=generated_at,
            policy_version=policy_version,
            source_query={"view": "progress"},
            source_node_ids=tuple(sorted(set(heads) | set(open_conflict_node_ids))),
            information_loss=("progress view omits non-blocking historical records",),
            payload=payload,
        )

    def traceability(
        self,
        *,
        revision: int | None = None,
        generated_at: str = DEFAULT_GENERATED_AT,
        policy_version: str = DEFAULT_POLICY_VERSION,
    ) -> ProjectionResult:
        query = self._query()
        target = query._revision(revision)
        nodes = _visible_nodes(query, target)
        edges = _visible_edges(query, target)
        selected_edges = [
            edge
            for edge in edges.values()
            if edge["relationship_type"]
            in {"depends_on", "produces", "derives", "evidences", "evaluated_by", "resolved_by"}
        ]
        selected_edges.sort(
            key=lambda edge: (edge["relationship_type"], edge["from_node_id"], edge["to_node_id"])
        )
        decisions_by_conflict = _decisions_by_conflict(query, target)
        source_nodes = sorted(
            {str(edge["from_node_id"]) for edge in selected_edges}
            | {str(edge["to_node_id"]) for edge in selected_edges}
        )
        payload = {
            "nodes": _node_summaries(nodes, source_nodes, query, target),
            "edges": _edge_summaries(selected_edges, query, target),
            "blocking_conflicts": [
                node["node_id"]
                for node in nodes.values()
                if node["node_type"] == "conflict"
                and _conflict_effective_status(node, decisions_by_conflict) == "open"
            ],
        }
        return self._result(
            view_type="traceability",
            query=query,
            revision=target,
            generated_at=generated_at,
            policy_version=policy_version,
            source_query={"view": "traceability"},
            source_node_ids=tuple(source_nodes),
            information_loss=("traceability view compresses detailed branch and event history",),
            payload=payload,
        )

    def persist(self, result: ProjectionResult) -> PersistedProjection:
        target = (
            self.store.root
            / ".guerilla"
            / "projections"
            / str(result.graph_revision)
            / result.view_type
            / f"{result.projection_id}.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(canonical_bytes(result.to_dict()) + b"\n")
        return PersistedProjection(
            path=target,
            result_hash=result.result_hash,
            graph_revision=result.graph_revision,
            view_type=result.view_type,
        )

    def _query(self) -> GraphQuery:
        replay = self.store.replay()
        if not self.use_index:
            return GraphQuery(replay)
        index = SQLiteGraphIndex(self.store.root)
        if index.status(replay).status != "current":
            index.rebuild(replay)
        return index.query()

    def _result(
        self,
        *,
        view_type: ProjectionView,
        query: GraphQuery,
        revision: int,
        generated_at: str,
        policy_version: str,
        source_query: dict[str, Any],
        source_node_ids: tuple[str, ...],
        information_loss: tuple[str, ...],
        payload: dict[str, Any],
    ) -> ProjectionResult:
        freshness = {
            "source_graph_revision": revision,
            "external_observations_may_be_stale": True,
            "refresh_required_before_external_mutation": True,
        }
        hash_input = {
            "view_type": view_type,
            "workspace_id": query.replay.workspace_id,
            "graph_revision": revision,
            "commit_hash": query._commit_hash(revision),
            "transformation_version": TRANSFORMATION_VERSION,
            "policy_version": policy_version,
            "source_query": source_query,
            "source_node_ids": list(source_node_ids),
            "freshness": freshness,
            "information_loss": list(information_loss),
            "authoritative_status": DERIVED_AUTHORITY,
            "payload": payload,
        }
        result_hash = payload_hash(canonical_bytes(hash_input))
        return ProjectionResult(
            projection_id=f"prj_{result_hash[:32]}",
            view_type=view_type,
            workspace_id=query.replay.workspace_id,
            graph_revision=revision,
            commit_hash=query._commit_hash(revision),
            generated_at=generated_at,
            transformation_version=TRANSFORMATION_VERSION,
            policy_version=policy_version,
            source_query=source_query,
            source_node_ids=source_node_ids,
            freshness=freshness,
            information_loss=information_loss,
            persistence_mode="generated",
            authoritative_status=DERIVED_AUTHORITY,
            payload=payload,
            result_hash=result_hash,
        )


def _visible_nodes(query: GraphQuery, revision: int) -> dict[str, dict[str, Any]]:
    return query._visible_nodes(revision)


def _visible_edges(query: GraphQuery, revision: int) -> dict[str, dict[str, Any]]:
    return query._visible_edges(revision)


def _node_summaries(
    nodes: dict[str, dict[str, Any]],
    node_ids: list[str] | tuple[str, ...],
    query: GraphQuery,
    revision: int,
) -> list[dict[str, Any]]:
    summaries = []
    for node_id in sorted(dict.fromkeys(node_ids)):
        node = nodes[node_id]
        summaries.append(
            {
                "node_id": node_id,
                "entity_id": node["entity_id"],
                "node_type": node["node_type"],
                "status": node["status"],
                "graph_revision": query.replay.record_revisions[node_id],
                "visible_at_revision": revision,
            }
        )
    return summaries


def _edge_summaries(
    edges: list[dict[str, Any]],
    query: GraphQuery,
    revision: int,
) -> list[dict[str, Any]]:
    return [
        {
            "edge_id": edge["edge_id"],
            "relationship_type": edge["relationship_type"],
            "from_node_id": edge["from_node_id"],
            "to_node_id": edge["to_node_id"],
            "graph_revision": query.replay.record_revisions[edge["edge_id"]],
            "visible_at_revision": revision,
        }
        for edge in sorted(
            edges,
            key=lambda edge: (
                edge["relationship_type"],
                edge["from_node_id"],
                edge["to_node_id"],
                edge["edge_id"],
            ),
        )
    ]


def _edges_within(
    query: GraphQuery,
    revision: int,
    node_ids: set[str] | list[str],
) -> list[dict[str, Any]]:
    selected = set(node_ids)
    return [
        edge
        for edge in _visible_edges(query, revision).values()
        if edge["from_node_id"] in selected and edge["to_node_id"] in selected
    ]


def _is_superseded(query: GraphQuery, revision: int, node_id: str) -> bool:
    return any(
        edge["relationship_type"] == "superseded_by" and edge["from_node_id"] == node_id
        for edge in _visible_edges(query, revision).values()
    )


def _phase10_metadata(node: dict[str, Any]) -> dict[str, Any] | None:
    metadata = node.get("metadata", {}).get(PHASE10_METADATA_KEY)
    return metadata if isinstance(metadata, dict) else None


def _manifest_ambiguity_reports(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_identity: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        identity = entry.get("external_identity")
        if not isinstance(identity, dict):
            continue
        key = "|".join(
            str(identity.get(field, ""))
            for field in (
                "system_id",
                "state_boundary_id",
                "external_kind",
                "external_id",
                "namespace",
            )
        )
        by_identity.setdefault(key, []).append(entry)
    reports = []
    for key, grouped in sorted(by_identity.items()):
        revisions = {str(item.get("external_revision")) for item in grouped}
        if len(grouped) > 1 and len(revisions) > 1:
            reports.append(
                {
                    "identity_key": key,
                    "node_ids": [item["node_id"] for item in grouped],
                    "reason": "incomparable_external_revisions",
                }
            )
    return reports


def _manifest_stale_reports(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reports = []
    for entry in entries:
        if entry.get("external_identity") is not None:
            reports.append(
                {
                    "node_id": entry["node_id"],
                    "reason": "external_observation_requires_refresh_before_mutation",
                }
            )
    return reports


def _decisions_by_conflict(query: GraphQuery, revision: int) -> dict[str, list[str]]:
    decisions: dict[str, list[str]] = {}
    for edge in _visible_edges(query, revision).values():
        if edge["relationship_type"] == "resolved_by":
            decisions.setdefault(str(edge["from_node_id"]), []).append(str(edge["to_node_id"]))
    return {key: sorted(value) for key, value in sorted(decisions.items())}


def _conflict_effective_status(
    node: dict[str, Any],
    decisions_by_conflict: dict[str, list[str]],
) -> str:
    node_id = str(node["node_id"])
    if decisions_by_conflict.get(node_id):
        return "resolved"
    return str(node.get("status", "open"))


def _superseded_between(query: GraphQuery, left: int, right: int) -> list[dict[str, Any]]:
    left_edges = _visible_edges(query, left)
    results = []
    for edge_id, edge in _visible_edges(query, right).items():
        if edge_id in left_edges or edge["relationship_type"] != "superseded_by":
            continue
        results.append(
            {
                "earlier_node_id": edge["from_node_id"],
                "later_node_id": edge["to_node_id"],
                "edge_id": edge_id,
            }
        )
    return sorted(results, key=lambda item: (item["earlier_node_id"], item["later_node_id"]))


def _conflict_ids_between(query: GraphQuery, left: int, right: int, *, status: str) -> list[str]:
    left_nodes = _visible_nodes(query, left)
    decisions_by_conflict = _decisions_by_conflict(query, right)
    return sorted(
        node_id
        for node_id, node in _visible_nodes(query, right).items()
        if node_id not in left_nodes
        and node["node_type"] == "conflict"
        and _conflict_effective_status(node, decisions_by_conflict) == status
    )


def _resolved_conflicts_between(query: GraphQuery, left: int, right: int) -> list[str]:
    left_edges = _visible_edges(query, left)
    return sorted(
        str(edge["from_node_id"])
        for edge_id, edge in _visible_edges(query, right).items()
        if edge_id not in left_edges and edge["relationship_type"] == "resolved_by"
    )


def _refreshed_observations_between(query: GraphQuery, left: int, right: int) -> list[str]:
    left_nodes = _visible_nodes(query, left)
    return sorted(
        node_id
        for node_id, node in _visible_nodes(query, right).items()
        if node_id not in left_nodes and _phase10_metadata(node) is not None
    )
