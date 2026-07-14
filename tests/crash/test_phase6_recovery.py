from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.identity import IdentifierGenerator
from guerilla.storage import GraphStore, StorageError, initialize_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase6-local-user", "actor_kind": "human"}


def _node(workspace_id: str, random_b: int) -> dict[str, Any]:
    ids = IdentifierGenerator()
    return {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "node_id": str(ids.generate("node", now_ms=1_721_000_000_010, random_b=random_b)),
        "entity_id": str(ids.generate("entity", now_ms=1_721_000_000_011, random_b=random_b)),
        "node_type": "event",
        "created_at": TS,
        "actor": _actor(),
        "authority": {
            "authority_type": "guerilla",
            "principal_id": "local-user",
            "profile": "local-owner-v1",
        },
        "status": "observed",
        "provenance": {"source": "phase6-crash-test", "source_record_ids": []},
        "payload_ref": {"retention_class": "none"},
        "metadata": {},
        "extensions": {},
    }


def _initialized_store(tmp_path: Path, contracts: ContractBundle) -> tuple[GraphStore, str]:
    ids = IdentifierGenerator()
    workspace_id = str(ids.generate("workspace", now_ms=1_721_000_000_000, random_b=99))
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts), workspace_id


def test_staged_transaction_without_active_append_is_ignored(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)

    with pytest.raises(StorageError) as excinfo:
        store.append_transaction(
            [_node(workspace_id, 70)],
            actor=_actor(),
            created_at=TS,
            committed_at=TS,
            fail_at="after_stage",
        )

    assert excinfo.value.code == "injected_failure"
    replay = store.replay()
    assert replay.graph_revision == 0
    assert replay.nodes == {}
    assert replay.warnings == []
    assert any((tmp_path / ".guerilla" / "tmp").glob("*.jsonl"))


def test_interrupted_append_after_member_fsync_replays_last_commit(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)

    with pytest.raises(StorageError) as excinfo:
        store.append_transaction(
            [_node(workspace_id, 80)],
            actor=_actor(),
            created_at=TS,
            committed_at=TS,
            fail_at="after_members_fsync",
        )

    assert excinfo.value.code == "injected_failure"
    replay = store.replay()
    assert replay.graph_revision == 0
    assert replay.nodes == {}
    assert "transaction_incomplete" in replay.warnings


def test_truncated_tail_is_ignored_after_last_durable_commit(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    committed = _node(workspace_id, 90)
    store.append_transaction([committed], actor=_actor(), created_at=TS, committed_at=TS)
    active = tmp_path / ".guerilla" / "graph" / "active.jsonl"
    active.write_bytes(active.read_bytes() + b'{"record_type":"transaction_begin"')

    replay = store.replay()

    assert replay.graph_revision == 1
    assert set(replay.nodes) == {committed["node_id"]}
    assert replay.warnings == ["incomplete_tail"]
