"""Rebuildable non-authoritative SQLite graph index."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from guerilla.codec import ZERO_SHA256, canonical_bytes, parse_raw_json
from guerilla.graph.query import GraphQuery
from guerilla.storage.store import CommitInfo, ReplayResult

INDEX_SCHEMA_VERSION = "phase7-graph-index-v1"


@dataclass(frozen=True, slots=True)
class IndexStatus:
    status: str
    source_revision: int | None
    source_commit_hash: str | None
    reason: str | None = None


def mark_index_invalid(root: Path, reason: str) -> None:
    indexes = root / ".guerilla" / "indexes"
    indexes.mkdir(parents=True, exist_ok=True)
    (indexes / "graph.sqlite.invalid").write_text(reason, encoding="utf-8")


class SQLiteGraphIndex:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / ".guerilla" / "indexes" / "graph.sqlite"

    def rebuild(self, replay: ReplayResult) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".sqlite.tmp")
        if tmp_path.exists():
            tmp_path.unlink()
        with closing(sqlite3.connect(tmp_path)) as connection:
            self._create_schema(connection)
            metadata = {
                "schema_version": INDEX_SCHEMA_VERSION,
                "workspace_id": replay.workspace_id,
                "source_revision": str(replay.graph_revision),
                "source_commit_hash": replay.last_commit_hash,
                "status": "current",
            }
            connection.executemany(
                "insert into metadata(key, value) values(?, ?)",
                sorted(metadata.items()),
            )
            connection.executemany(
                "insert into commits(graph_revision, commit_hash, transaction_hash, transaction_id)"
                " values(?, ?, ?, ?)",
                [
                    (
                        commit.graph_revision,
                        commit.commit_hash,
                        commit.transaction_hash,
                        commit.transaction_id,
                    )
                    for commit in replay.commits
                ],
            )
            connection.executemany(
                "insert into nodes(node_id, entity_id, node_type, graph_revision, record_json)"
                " values(?, ?, ?, ?, ?)",
                [
                    (
                        node_id,
                        str(node["entity_id"]),
                        str(node["node_type"]),
                        replay.record_revisions[node_id],
                        canonical_bytes(node).decode("utf-8"),
                    )
                    for node_id, node in sorted(replay.nodes.items())
                ],
            )
            connection.executemany(
                "insert into edges("
                "edge_id, relationship_type, from_node_id, to_node_id, graph_revision, record_json"
                ") values(?, ?, ?, ?, ?, ?)",
                [
                    (
                        edge_id,
                        str(edge["relationship_type"]),
                        str(edge["from_node_id"]),
                        str(edge["to_node_id"]),
                        replay.record_revisions[edge_id],
                        canonical_bytes(edge).decode("utf-8"),
                    )
                    for edge_id, edge in sorted(replay.edges.items())
                ],
            )
            connection.commit()
        tmp_path.replace(self.path)
        invalid_marker = self.path.with_suffix(".sqlite.invalid")
        if invalid_marker.exists():
            invalid_marker.unlink()

    def status(self, replay: ReplayResult | None = None) -> IndexStatus:
        if not self.path.exists():
            return IndexStatus("missing", None, None, "index file is absent")
        try:
            metadata = self._metadata()
            source_revision = int(metadata["source_revision"])
            source_commit = metadata["source_commit_hash"]
        except (OSError, KeyError, ValueError, sqlite3.DatabaseError) as exc:
            return IndexStatus("corrupt", None, None, f"{type(exc).__name__}: {exc}")
        if metadata.get("schema_version") != INDEX_SCHEMA_VERSION:
            return IndexStatus("unsupported_schema", source_revision, source_commit)
        if replay is None:
            return IndexStatus(
                str(metadata.get("status", "unknown")),
                source_revision,
                source_commit,
            )
        if source_revision > replay.graph_revision:
            return IndexStatus("ahead", source_revision, source_commit)
        if source_revision < replay.graph_revision or source_commit != replay.last_commit_hash:
            return IndexStatus("stale", source_revision, source_commit)
        return IndexStatus("current", source_revision, source_commit)

    def query(self) -> GraphQuery:
        return GraphQuery(self.to_replay_result(), serving_path="index")

    def to_replay_result(self) -> ReplayResult:
        metadata = self._metadata()
        result = ReplayResult(
            workspace_id=metadata["workspace_id"],
            graph_revision=int(metadata["source_revision"]),
            last_commit_hash=metadata.get("source_commit_hash", ZERO_SHA256),
        )
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            for row in connection.execute(
                "select graph_revision, commit_hash, transaction_hash, transaction_id "
                "from commits order by graph_revision"
            ):
                result.commits.append(
                    CommitInfo(
                        graph_revision=int(row["graph_revision"]),
                        commit_hash=str(row["commit_hash"]),
                        transaction_hash=str(row["transaction_hash"]),
                        transaction_id=str(row["transaction_id"]),
                    )
                )
            for row in connection.execute("select node_id, graph_revision, record_json from nodes"):
                node = parse_raw_json(str(row["record_json"]).encode("utf-8"))
                node_id = str(row["node_id"])
                result.nodes[node_id] = _ensure_record(node)
                result.record_revisions[node_id] = int(row["graph_revision"])
            for row in connection.execute("select edge_id, graph_revision, record_json from edges"):
                edge = parse_raw_json(str(row["record_json"]).encode("utf-8"))
                edge_id = str(row["edge_id"])
                result.edges[edge_id] = _ensure_record(edge)
                result.record_revisions[edge_id] = int(row["graph_revision"])
        return result

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            create table metadata(
              key text primary key,
              value text not null
            );
            create table commits(
              graph_revision integer primary key,
              commit_hash text not null,
              transaction_hash text not null,
              transaction_id text not null
            );
            create table nodes(
              node_id text primary key,
              entity_id text not null,
              node_type text not null,
              graph_revision integer not null,
              record_json text not null
            );
            create table edges(
              edge_id text primary key,
              relationship_type text not null,
              from_node_id text not null,
              to_node_id text not null,
              graph_revision integer not null,
              record_json text not null
            );
            create index edges_from_idx on edges(from_node_id);
            create index edges_to_idx on edges(to_node_id);
            create index nodes_entity_idx on nodes(entity_id, graph_revision);
            """
        )

    def _metadata(self) -> dict[str, str]:
        with closing(sqlite3.connect(self.path)) as connection:
            rows = connection.execute("select key, value from metadata").fetchall()
        return {str(key): str(value) for key, value in rows}


def _ensure_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("indexed record is not an object")
    return value
