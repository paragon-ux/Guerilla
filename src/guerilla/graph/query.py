"""Replay-backed graph query helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from guerilla.authority import LocalAuthorizationProfile
from guerilla.codec import ZERO_SHA256
from guerilla.graph.errors import GraphQueryError

DEFAULT_QUERY_LIMIT = 10_000
DEFAULT_MAX_DEPTH = 1_000
ServingPath = Literal["replay", "index"]


@dataclass(frozen=True, slots=True)
class QueryEnvelope:
    workspace_id: str
    graph_revision: int
    commit_hash: str
    serving_path: ServingPath
    query: str
    limit: int
    truncated: bool
    items: list[Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GraphQuery:
    def __init__(
        self,
        replay: Any,
        *,
        serving_path: ServingPath = "replay",
        principal_id: str = "local-user",
        owner_principal_id: str = "local-user",
    ) -> None:
        LocalAuthorizationProfile(owner_principal_id=owner_principal_id).require(
            principal_id,
            "graph.read",
        )
        self.replay = replay
        self.serving_path = serving_path

    def _revision(self, revision: int | None) -> int:
        target = self.replay.graph_revision if revision is None else revision
        if target < 0:
            raise GraphQueryError("invalid_revision", "revision must be non-negative")
        if target > self.replay.graph_revision:
            raise GraphQueryError("revision_ahead", "revision is ahead of replayed graph")
        return int(target)

    def _commit_hash(self, revision: int) -> str:
        if revision == 0:
            return ZERO_SHA256
        for commit in self.replay.commits:
            if commit.graph_revision == revision:
                return str(commit.commit_hash)
        raise GraphQueryError("missing_commit", "revision has no committed hash")

    def _visible_nodes(self, revision: int) -> dict[str, dict[str, Any]]:
        return {
            node_id: node
            for node_id, node in self.replay.nodes.items()
            if self.replay.record_revisions[node_id] <= revision
        }

    def _visible_edges(self, revision: int) -> dict[str, dict[str, Any]]:
        return {
            edge_id: edge
            for edge_id, edge in self.replay.edges.items()
            if self.replay.record_revisions[edge_id] <= revision
        }

    def _envelope(
        self,
        *,
        query: str,
        revision: int,
        items: list[Any],
        limit: int,
        truncated: bool,
    ) -> QueryEnvelope:
        return QueryEnvelope(
            workspace_id=self.replay.workspace_id,
            graph_revision=revision,
            commit_hash=self._commit_hash(revision),
            serving_path=self.serving_path,
            query=query,
            limit=limit,
            truncated=truncated,
            items=items,
        )

    def node(self, node_id: str, *, revision: int | None = None) -> QueryEnvelope:
        target = self._revision(revision)
        nodes = self._visible_nodes(target)
        items = [nodes[node_id]] if node_id in nodes else []
        return self._envelope(query="node", revision=target, items=items, limit=1, truncated=False)

    def edge(self, edge_id: str, *, revision: int | None = None) -> QueryEnvelope:
        target = self._revision(revision)
        edges = self._visible_edges(target)
        items = [edges[edge_id]] if edge_id in edges else []
        return self._envelope(query="edge", revision=target, items=items, limit=1, truncated=False)

    def commit(self, graph_revision: int) -> QueryEnvelope:
        target = self._revision(graph_revision)
        if target == 0:
            items: list[Any] = []
        else:
            items = [
                asdict(commit)
                for commit in self.replay.commits
                if commit.graph_revision == graph_revision
            ]
        return self._envelope(
            query="commit",
            revision=target,
            items=items,
            limit=1,
            truncated=False,
        )

    def entity_revisions(
        self,
        entity_id: str,
        *,
        revision: int | None = None,
        limit: int = DEFAULT_QUERY_LIMIT,
    ) -> QueryEnvelope:
        target = self._revision(revision)
        items = [
            node_id
            for node_id, node in self._visible_nodes(target).items()
            if node["entity_id"] == entity_id
        ]
        items.sort(key=lambda item: (self.replay.record_revisions[item], item))
        truncated = len(items) > limit
        return self._envelope(
            query="entity_revisions",
            revision=target,
            items=items[:limit],
            limit=limit,
            truncated=truncated,
        )

    def heads(
        self,
        *,
        revision: int | None = None,
        limit: int = DEFAULT_QUERY_LIMIT,
    ) -> QueryEnvelope:
        target = self._revision(revision)
        nodes = self._visible_nodes(target)
        outgoing = {edge["from_node_id"] for edge in self._visible_edges(target).values()}
        items = sorted(node_id for node_id in nodes if node_id not in outgoing)
        truncated = len(items) > limit
        return self._envelope(
            query="heads",
            revision=target,
            items=items[:limit],
            limit=limit,
            truncated=truncated,
        )

    def ancestors(
        self,
        node_id: str,
        *,
        revision: int | None = None,
        max_depth: int = DEFAULT_MAX_DEPTH,
        limit: int = DEFAULT_QUERY_LIMIT,
    ) -> QueryEnvelope:
        target = self._revision(revision)
        incoming: dict[str, set[str]] = {}
        for edge in self._visible_edges(target).values():
            incoming.setdefault(str(edge["to_node_id"]), set()).add(str(edge["from_node_id"]))
        items, truncated = self._bounded_walk(incoming, node_id, max_depth=max_depth, limit=limit)
        return self._envelope(
            query="ancestors",
            revision=target,
            items=items,
            limit=limit,
            truncated=truncated,
        )

    def descendants(
        self,
        node_id: str,
        *,
        revision: int | None = None,
        max_depth: int = DEFAULT_MAX_DEPTH,
        limit: int = DEFAULT_QUERY_LIMIT,
    ) -> QueryEnvelope:
        target = self._revision(revision)
        outgoing: dict[str, set[str]] = {}
        for edge in self._visible_edges(target).values():
            outgoing.setdefault(str(edge["from_node_id"]), set()).add(str(edge["to_node_id"]))
        items, truncated = self._bounded_walk(outgoing, node_id, max_depth=max_depth, limit=limit)
        return self._envelope(
            query="descendants",
            revision=target,
            items=items,
            limit=limit,
            truncated=truncated,
        )

    @staticmethod
    def _bounded_walk(
        adjacency: dict[str, set[str]],
        start: str,
        *,
        max_depth: int,
        limit: int,
    ) -> tuple[list[str], bool]:
        results: list[str] = []
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(start, 0)]
        truncated = False
        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                if adjacency.get(current):
                    truncated = True
                continue
            for next_id in sorted(adjacency.get(current, ())):
                if next_id in visited:
                    continue
                visited.add(next_id)
                if len(results) >= limit:
                    truncated = True
                    return results, truncated
                results.append(next_id)
                queue.append((next_id, depth + 1))
        return results, truncated
