from __future__ import annotations

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.graph import GraphIntegrityError, GraphQuery
from guerilla.identity import IdentifierGenerator
from guerilla.index import SQLiteGraphIndex
from guerilla.storage import GraphStore, initialize_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase7-local-user", "actor_kind": "human"}


def _authority() -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": "local-user", "profile": "local-owner-v1"}


def _node(
    ids: IdentifierGenerator, workspace_id: str, node_type: str, random_b: int
) -> dict[str, Any]:
    return {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "node_id": str(ids.generate("node", now_ms=1_721_000_100_000, random_b=random_b)),
        "entity_id": str(ids.generate("entity", now_ms=1_721_000_100_001, random_b=random_b)),
        "node_type": node_type,
        "created_at": TS,
        "actor": _actor(),
        "authority": _authority(),
        "status": "open",
        "provenance": {"source": "phase7-test", "source_record_ids": []},
        "payload_ref": {"retention_class": "none"},
        "metadata": {},
        "extensions": {},
    }


def _edge(
    ids: IdentifierGenerator,
    workspace_id: str,
    relationship_type: str,
    from_node_id: str,
    to_node_id: str,
    random_b: int,
) -> dict[str, Any]:
    return {
        "record_type": "edge",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "edge_id": str(ids.generate("edge", now_ms=1_721_000_100_002, random_b=random_b)),
        "relationship_type": relationship_type,
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "created_at": TS,
        "actor": _actor(),
        "provenance": {"source": "phase7-test", "source_record_ids": []},
        "metadata": {},
        "extensions": {},
    }


def _initialized_store(tmp_path: Path, contracts: ContractBundle) -> tuple[GraphStore, str]:
    ids = IdentifierGenerator()
    workspace_id = str(ids.generate("workspace", now_ms=1_721_000_100_010, random_b=1))
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts), workspace_id


def _append(
    store: GraphStore,
    members: list[dict[str, Any]],
) -> None:
    store.append_transaction(members, actor=_actor(), created_at=TS, committed_at=TS)


def test_same_transaction_endpoints_heads_and_replay_index_queries(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = IdentifierGenerator()
    a = _node(ids, workspace_id, "artifact", 10)
    b = _node(ids, workspace_id, "artifact", 11)
    c = _node(ids, workspace_id, "artifact", 12)
    d = _node(ids, workspace_id, "artifact", 13)
    edges = [
        _edge(ids, workspace_id, "depends_on", a["node_id"], b["node_id"], 20),
        _edge(ids, workspace_id, "depends_on", a["node_id"], c["node_id"], 21),
        _edge(ids, workspace_id, "depends_on", b["node_id"], d["node_id"], 22),
        _edge(ids, workspace_id, "depends_on", c["node_id"], d["node_id"], 23),
    ]

    _append(store, [d, c, b, a, *reversed(edges)])
    replay = store.replay()
    replay_query = GraphQuery(replay)
    index = SQLiteGraphIndex(tmp_path)
    index_query = index.query()

    assert replay.graph_revision == 1
    assert index.status(replay).status == "current"
    assert replay_query.heads().items == [d["node_id"]]
    assert index_query.heads().items == replay_query.heads().items
    assert set(replay_query.ancestors(d["node_id"]).items) == {
        a["node_id"],
        b["node_id"],
        c["node_id"],
    }
    assert index_query.ancestors(d["node_id"]).items == replay_query.ancestors(d["node_id"]).items
    assert replay_query.node(a["node_id"], revision=0).items == []
    assert replay_query.node(a["node_id"], revision=1).items[0]["node_id"] == a["node_id"]
    assert index_query.commit(1).items == replay_query.commit(1).items


@pytest.mark.parametrize(
    ("case", "expected_code"),
    [
        ("self_loop", "self_loop"),
        ("missing_endpoint", "missing_endpoint"),
        ("incompatible_endpoint", "incompatible_endpoint_type"),
    ],
)
def test_invalid_edge_transactions_do_not_advance_revision(
    contracts: ContractBundle, tmp_path: Path, case: str, expected_code: str
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = IdentifierGenerator()
    artifact = _node(ids, workspace_id, "artifact", 30)
    snapshot = _node(ids, workspace_id, "snapshot", 31)
    if case == "self_loop":
        members = [
            artifact,
            _edge(ids, workspace_id, "depends_on", artifact["node_id"], artifact["node_id"], 32),
        ]
    elif case == "missing_endpoint":
        missing = str(ids.generate("node", now_ms=1_721_000_100_099, random_b=99))
        members = [
            artifact,
            _edge(ids, workspace_id, "depends_on", artifact["node_id"], missing, 33),
        ]
    else:
        members = [
            artifact,
            snapshot,
            _edge(ids, workspace_id, "captured_by", snapshot["node_id"], artifact["node_id"], 34),
        ]

    with pytest.raises(GraphIntegrityError) as excinfo:
        _append(store, members)

    assert excinfo.value.code == expected_code
    replay = store.replay()
    assert replay.graph_revision == 0
    assert replay.nodes == {}
    assert (tmp_path / ".guerilla" / "graph" / "active.jsonl").read_bytes().count(b"\n") == 1


def test_short_and_long_cycle_rejections_preserve_revision(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = IdentifierGenerator()
    a = _node(ids, workspace_id, "artifact", 40)
    b = _node(ids, workspace_id, "artifact", 41)
    c = _node(ids, workspace_id, "artifact", 42)
    _append(
        store,
        [
            a,
            b,
            c,
            _edge(ids, workspace_id, "depends_on", a["node_id"], b["node_id"], 43),
            _edge(ids, workspace_id, "depends_on", b["node_id"], c["node_id"], 44),
        ],
    )

    for edge in [
        _edge(ids, workspace_id, "depends_on", c["node_id"], a["node_id"], 45),
        _edge(ids, workspace_id, "depends_on", b["node_id"], a["node_id"], 46),
    ]:
        with pytest.raises(GraphIntegrityError) as excinfo:
            _append(store, [edge])
        assert excinfo.value.code == "lineage_cycle"
        assert excinfo.value.witness_path

    replay = store.replay()
    assert replay.graph_revision == 1
    assert len(replay.edges) == 2


def test_reified_symmetric_relation_avoids_direct_cycle(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = IdentifierGenerator()
    left = _node(ids, workspace_id, "artifact", 50)
    right = _node(ids, workspace_id, "artifact", 51)
    relation = _node(ids, workspace_id, "event", 52)

    _append(
        store,
        [
            left,
            right,
            relation,
            _edge(ids, workspace_id, "depends_on", left["node_id"], relation["node_id"], 53),
            _edge(ids, workspace_id, "depends_on", right["node_id"], relation["node_id"], 54),
        ],
    )

    replay = store.replay()
    assert replay.graph_revision == 1
    assert GraphQuery(replay).heads().items == [relation["node_id"]]


def test_index_delete_corrupt_rebuild_and_status(contracts: ContractBundle, tmp_path: Path) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = IdentifierGenerator()
    a = _node(ids, workspace_id, "artifact", 60)
    b = _node(ids, workspace_id, "artifact", 61)
    _append(
        store,
        [a, b, _edge(ids, workspace_id, "depends_on", a["node_id"], b["node_id"], 62)],
    )
    replay = store.replay()
    index = SQLiteGraphIndex(tmp_path)

    assert index.status(replay).status == "current"
    index.path.unlink()
    assert index.status(replay).status == "missing"
    index.rebuild(replay)
    assert index.query().heads().items == GraphQuery(replay).heads().items
    index.path.write_bytes(b"not sqlite")
    assert index.status(replay).status == "corrupt"
    index.rebuild(replay)
    with closing(sqlite3.connect(index.path)) as connection:
        connection.execute("update metadata set value = ? where key = 'source_revision'", ("99",))
        connection.commit()
    assert index.status(replay).status == "ahead"


def test_bounded_traversal_truncates_and_index_matches(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = IdentifierGenerator()
    nodes = [_node(ids, workspace_id, "artifact", 70 + index) for index in range(5)]
    edges = [
        _edge(
            ids,
            workspace_id,
            "depends_on",
            nodes[index]["node_id"],
            nodes[index + 1]["node_id"],
            80 + index,
        )
        for index in range(4)
    ]
    _append(store, [*nodes, *edges])
    replay = store.replay()
    replay_walk = GraphQuery(replay).descendants(nodes[0]["node_id"], max_depth=2)
    index_walk = SQLiteGraphIndex(tmp_path).query().descendants(nodes[0]["node_id"], max_depth=2)

    assert replay_walk.items == [nodes[1]["node_id"], nodes[2]["node_id"]]
    assert replay_walk.truncated is True
    assert index_walk.items == replay_walk.items
    assert index_walk.truncated is True


@given(data=st.data(), node_count=st.integers(min_value=2, max_value=6))
@settings(max_examples=20, deadline=None)
def test_property_generated_dag_rebuilds_and_rejects_reverse_cycle(
    data: Any, node_count: int, contracts: ContractBundle
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = Path(directory)
        store, workspace_id = _initialized_store(tmp_path, contracts)
        ids = IdentifierGenerator()
        nodes = [_node(ids, workspace_id, "artifact", 100 + index) for index in range(node_count)]
        possible_edges = [(i, j) for i in range(node_count) for j in range(i + 1, node_count)]
        edge_pairs = data.draw(
            st.lists(
                st.sampled_from(possible_edges),
                min_size=1,
                max_size=min(8, len(possible_edges)),
                unique=True,
            )
        )
        edges = [
            _edge(
                ids,
                workspace_id,
                "depends_on",
                nodes[start]["node_id"],
                nodes[end]["node_id"],
                200 + index,
            )
            for index, (start, end) in enumerate(edge_pairs)
        ]

        _append(store, [*nodes, *edges])
        replay = store.replay()
        assert SQLiteGraphIndex(tmp_path).query().heads().items == GraphQuery(replay).heads().items

        start, end = edge_pairs[0]
        with pytest.raises(GraphIntegrityError) as excinfo:
            _append(
                store,
                [
                    _edge(
                        ids,
                        workspace_id,
                        "depends_on",
                        nodes[end]["node_id"],
                        nodes[start]["node_id"],
                        300,
                    )
                ],
            )
        assert excinfo.value.code == "lineage_cycle"
        assert store.replay().graph_revision == 1
