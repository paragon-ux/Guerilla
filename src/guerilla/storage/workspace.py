"""Workspace initialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from guerilla.codec import canonical_jsonl, parse_raw_json
from guerilla.contracts import ContractBundle
from guerilla.storage.errors import StorageError
from guerilla.storage.fsync import fsync_directory, fsync_file

WORKSPACE_DIRS = (
    ".guerilla/graph/archives",
    ".guerilla/payloads/sha256",
    ".guerilla/projections",
    ".guerilla/snapshots",
    ".guerilla/indexes",
    ".guerilla/locks",
    ".guerilla/logs",
    ".guerilla/tmp",
)


def graph_header(*, workspace_id: str, created_at: str) -> dict[str, object]:
    return {
        "record_type": "graph_header",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "graph_format_version": "guerilla-graph-jsonl-v1",
        "canonicalization_id": "guerilla-cjson-v1",
        "hash_algorithm": "sha256",
        "created_at": created_at,
        "authority_class": "authoritative_graph",
        "extensions": {},
    }


def initialize_workspace(
    root: Path,
    *,
    workspace_id: str,
    created_at: str,
    contracts: ContractBundle,
) -> dict[str, Any]:
    guerilla_dir = root / ".guerilla"
    graph_dir = guerilla_dir / "graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    for rel_path in WORKSPACE_DIRS:
        (root / rel_path).mkdir(parents=True, exist_ok=True)
    header = graph_header(workspace_id=workspace_id, created_at=created_at)
    contracts.assert_valid("graph_header.schema.json", header)
    active = graph_dir / "active.jsonl"
    if active.exists():
        if active.stat().st_size == 0:
            raise StorageError("partial_graph_file", "active graph exists but is empty")
        first_line = active.read_bytes().split(b"\n", maxsplit=1)[0]
        existing_header = parse_raw_json(first_line)
        if not isinstance(existing_header, dict):
            raise StorageError("invalid_graph_header", "active graph header must be an object")
        contracts.assert_valid("graph_header.schema.json", existing_header)
        if existing_header["workspace_id"] != workspace_id:
            raise StorageError("workspace_mismatch", "active graph belongs to another workspace")
        return existing_header
    with active.open("xb") as file_obj:
        file_obj.write(canonical_jsonl(header))
        fsync_file(file_obj)
    fsync_directory(graph_dir)
    return header
