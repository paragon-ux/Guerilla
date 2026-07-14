from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from guerilla.authority import AuthorityError
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.graph import GraphIntegrityError, GraphQuery
from guerilla.identity import IdentifierGenerator
from guerilla.index import SQLiteGraphIndex
from guerilla.storage import GraphStore, StorageError, initialize_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "gate-b-local-user", "actor_kind": "human"}


def _authority() -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": "local-user", "profile": "local-owner-v1"}


def _node(ids: IdentifierGenerator, workspace_id: str, random_b: int) -> dict[str, Any]:
    return {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "node_id": str(ids.generate("node", now_ms=1_721_000_300_000, random_b=random_b)),
        "entity_id": str(ids.generate("entity", now_ms=1_721_000_300_001, random_b=random_b)),
        "node_type": "artifact",
        "created_at": TS,
        "actor": _actor(),
        "authority": _authority(),
        "status": "open",
        "provenance": {"source": "gate-b-checklist", "source_record_ids": []},
        "payload_ref": {"retention_class": "none"},
        "metadata": {},
        "extensions": {},
    }


def _edge(
    ids: IdentifierGenerator,
    workspace_id: str,
    from_node_id: str,
    to_node_id: str,
    random_b: int,
) -> dict[str, Any]:
    return {
        "record_type": "edge",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "edge_id": str(ids.generate("edge", now_ms=1_721_000_300_002, random_b=random_b)),
        "relationship_type": "depends_on",
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "created_at": TS,
        "actor": _actor(),
        "provenance": {"source": "gate-b-checklist", "source_record_ids": []},
        "metadata": {},
        "extensions": {},
    }


def _store(tmp_path: Path, contracts: ContractBundle) -> tuple[GraphStore, str]:
    ids = IdentifierGenerator()
    workspace_id = str(ids.generate("workspace", now_ms=1_721_000_300_010, random_b=1))
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts), workspace_id


def _append(
    store: GraphStore, members: list[dict[str, Any]], principal_id: str = "local-user"
) -> None:
    store.append_transaction(
        members,
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
        principal_id=principal_id,
    )


def test_gate_b_clean_workspace_reopen_replay_heads_and_queries(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    ids = IdentifierGenerator()
    first = _node(ids, workspace_id, 10)
    second = _node(ids, workspace_id, 11)
    edge = _edge(ids, workspace_id, first["node_id"], second["node_id"], 12)

    _append(store, [second, edge, first])
    reopened = GraphStore(tmp_path, contracts=contracts)
    replay = reopened.replay()
    replay_query = GraphQuery(replay)
    index_query = SQLiteGraphIndex(tmp_path).query()

    assert replay.graph_revision == 1
    assert replay_query.heads().items == [second["node_id"]]
    assert index_query.heads().items == replay_query.heads().items
    assert index_query.commit(1).items == replay_query.commit(1).items


def test_gate_b_invalid_mutations_leave_reopened_graph_unchanged(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    ids = IdentifierGenerator()
    first = _node(ids, workspace_id, 20)
    second = _node(ids, workspace_id, 21)
    _append(
        store, [first, second, _edge(ids, workspace_id, first["node_id"], second["node_id"], 22)]
    )
    head = store.replay()

    with pytest.raises(StorageError):
        _append(store, [first])
    missing = str(ids.generate("node", now_ms=1_721_000_300_099, random_b=99))
    with pytest.raises(GraphIntegrityError):
        _append(store, [_edge(ids, workspace_id, second["node_id"], missing, 23)])
    with pytest.raises(GraphIntegrityError):
        _append(store, [_edge(ids, workspace_id, second["node_id"], first["node_id"], 24)])
    with pytest.raises(AuthorityError):
        _append(store, [_node(ids, workspace_id, 25)], principal_id="intruder")

    reopened = GraphStore(tmp_path, contracts=contracts).replay()
    assert reopened.graph_revision == head.graph_revision
    assert reopened.last_commit_hash == head.last_commit_hash
    assert set(reopened.nodes) == set(head.nodes)
    assert set(reopened.edges) == set(head.edges)


def test_gate_b_index_loss_rebuilds_without_lineage_loss(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    ids = IdentifierGenerator()
    first = _node(ids, workspace_id, 30)
    second = _node(ids, workspace_id, 31)
    _append(
        store, [first, second, _edge(ids, workspace_id, first["node_id"], second["node_id"], 32)]
    )
    replay = store.replay()
    index = SQLiteGraphIndex(tmp_path)
    before = index.query().heads().items

    index.path.unlink()
    assert index.status(replay).status == "missing"
    index.rebuild(replay)

    assert index.status(replay).status == "current"
    assert index.query().heads().items == before
    assert GraphQuery(replay).heads().items == before
