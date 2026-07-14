from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from guerilla.codec import canonical_bytes, parse_raw_json, record_hash
from guerilla.contracts import ContractBundle, ContractError, load_contract_bundle
from guerilla.identity import IdentifierGenerator
from guerilla.storage import (
    GraphStore,
    LockHeldError,
    ReplayError,
    StorageError,
    WriterLock,
    initialize_workspace,
    read_payload,
    write_payload,
)
from guerilla.storage.payload_store import payload_path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _ids() -> IdentifierGenerator:
    return IdentifierGenerator()


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase6-local-user", "actor_kind": "human"}


def _authority() -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": "local-user", "profile": "local-owner-v1"}


def _workspace_id(ids: IdentifierGenerator) -> str:
    return str(ids.generate("workspace", now_ms=1_721_000_000_000, random_b=1))


def _node(
    ids: IdentifierGenerator,
    workspace_id: str,
    *,
    node_type: str = "goal",
    status: str = "open",
    random_b: int,
) -> dict[str, Any]:
    return {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "node_id": str(ids.generate("node", now_ms=1_721_000_000_001, random_b=random_b)),
        "entity_id": str(ids.generate("entity", now_ms=1_721_000_000_002, random_b=random_b)),
        "node_type": node_type,
        "created_at": TS,
        "actor": _actor(),
        "authority": _authority(),
        "status": status,
        "provenance": {"source": "phase6-test", "source_record_ids": []},
        "payload_ref": {"retention_class": "none"},
        "metadata": {},
        "extensions": {},
    }


def _initialized_store(tmp_path: Path, contracts: ContractBundle) -> tuple[GraphStore, str]:
    ids = _ids()
    workspace_id = _workspace_id(ids)
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts), workspace_id


def test_workspace_initialization_is_idempotent(contracts: ContractBundle, tmp_path: Path) -> None:
    ids = _ids()
    workspace_id = _workspace_id(ids)

    header = initialize_workspace(
        tmp_path,
        workspace_id=workspace_id,
        created_at=TS,
        contracts=contracts,
    )
    second_header = initialize_workspace(
        tmp_path,
        workspace_id=workspace_id,
        created_at=TS,
        contracts=contracts,
    )

    active = tmp_path / ".guerilla" / "graph" / "active.jsonl"
    assert active.read_bytes().count(b"\n") == 1
    assert header == second_header
    replay = GraphStore(tmp_path, contracts=contracts).replay()
    assert replay.workspace_id == workspace_id
    assert replay.graph_revision == 0
    assert replay.last_commit_hash == "0" * 64


def test_valid_transaction_appends_in_canonical_order_and_replays(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = _ids()
    first = _node(ids, workspace_id, random_b=20)
    second = _node(ids, workspace_id, node_type="artifact", random_b=10)

    commit = store.append_transaction(
        [first, second],
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
    )
    replay = store.replay()

    committed_ids = sorted([first["node_id"], second["node_id"]])
    assert commit["committed_record_ids"] == committed_ids
    assert replay.graph_revision == 1
    assert replay.last_commit_hash == commit["commit_hash"]
    assert set(replay.nodes) == set(committed_ids)
    active_lines = (tmp_path / ".guerilla" / "graph" / "active.jsonl").read_bytes().splitlines()
    assert [parse_raw_json(line)["record_type"] for line in active_lines] == [
        "graph_header",
        "transaction_begin",
        "node",
        "node",
        "transaction_commit",
    ]


def test_invalid_duplicate_identifier_commits_nothing(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = _ids()
    node = _node(ids, workspace_id, random_b=30)

    store.append_transaction([node], actor=_actor(), created_at=TS, committed_at=TS)
    with pytest.raises(StorageError) as excinfo:
        store.append_transaction([node], actor=_actor(), created_at=TS, committed_at=TS)

    assert excinfo.value.code == "duplicate_id"
    replay = store.replay()
    assert replay.graph_revision == 1
    assert list(replay.nodes) == [node["node_id"]]


def test_writer_lock_rejects_concurrent_append(contracts: ContractBundle, tmp_path: Path) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    lock = WriterLock.acquire(
        tmp_path / ".guerilla" / "locks",
        workspace_id=workspace_id,
        acquired_at=TS,
    )
    try:
        with pytest.raises(LockHeldError) as excinfo:
            store.append_transaction(
                [_node(_ids(), workspace_id, random_b=40)],
                actor=_actor(),
                created_at=TS,
                committed_at=TS,
            )
        assert excinfo.value.code == "writer_lock_held"
    finally:
        lock.release()


def test_replay_detects_record_hash_corruption(contracts: ContractBundle, tmp_path: Path) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    node = _node(_ids(), workspace_id, random_b=50)
    store.append_transaction([node], actor=_actor(), created_at=TS, committed_at=TS)
    active = tmp_path / ".guerilla" / "graph" / "active.jsonl"
    lines = active.read_bytes().splitlines()
    stored_node = parse_raw_json(lines[2])
    stored_node["status"] = "closed"
    lines[2] = canonical_bytes(stored_node)
    active.write_bytes(b"\n".join(lines) + b"\n")

    with pytest.raises(ReplayError) as excinfo:
        store.replay()
    assert excinfo.value.code == "record_hash_mismatch"


def test_replay_detects_previous_commit_corruption(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    store.append_transaction(
        [_node(_ids(), workspace_id, random_b=55)],
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
    )
    active = tmp_path / ".guerilla" / "graph" / "active.jsonl"
    lines = active.read_bytes().splitlines()
    commit = parse_raw_json(lines[3])
    commit["previous_commit_hash"] = "f" * 64
    lines[3] = canonical_bytes(commit)
    active.write_bytes(b"\n".join(lines) + b"\n")

    with pytest.raises(ReplayError) as excinfo:
        store.replay()
    assert excinfo.value.code == "previous_commit_mismatch"


def test_replay_detects_transaction_hash_corruption(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    store.append_transaction(
        [_node(_ids(), workspace_id, random_b=57)],
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
    )
    active = tmp_path / ".guerilla" / "graph" / "active.jsonl"
    lines = active.read_bytes().splitlines()
    commit = parse_raw_json(lines[3])
    commit["transaction_hash"] = "f" * 64
    lines[3] = canonical_bytes(commit)
    active.write_bytes(b"\n".join(lines) + b"\n")

    with pytest.raises(ReplayError) as excinfo:
        store.replay()
    assert excinfo.value.code == "transaction_hash_mismatch"


def test_replay_detects_noncanonical_committed_line(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    node = _node(_ids(), workspace_id, random_b=60)
    store.append_transaction([node], actor=_actor(), created_at=TS, committed_at=TS)
    active = tmp_path / ".guerilla" / "graph" / "active.jsonl"
    lines = active.read_bytes().splitlines()
    stored_node = parse_raw_json(lines[2])
    assert record_hash(stored_node) == stored_node["record_hash"]
    lines[2] = (
        b'{"workspace_id":"'
        + stored_node["workspace_id"].encode("ascii")
        + b'","record_type":"node"}'
    )
    active.write_bytes(b"\n".join(lines) + b"\n")

    with pytest.raises(ReplayError) as excinfo:
        store.replay()
    assert excinfo.value.code == "noncanonical_jsonl_record"


def test_unknown_critical_graph_member_extension_rejected(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    node = _node(_ids(), workspace_id, random_b=65)
    node["extensions"] = {
        "example.unknown.critical": {
            "critical": True,
            "namespace_id": "gxe_018f1f8e-5d4b-7a10-8a20-0c9b0b23c901",
            "value": {},
        }
    }

    with pytest.raises(ContractError) as excinfo:
        store.append_transaction([node], actor=_actor(), created_at=TS, committed_at=TS)

    assert excinfo.value.code == "unknown_critical_extension"
    assert store.replay().graph_revision == 0


def test_replay_rejects_crlf_graph_records(contracts: ContractBundle, tmp_path: Path) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    store.append_transaction(
        [_node(_ids(), workspace_id, random_b=67)],
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
    )
    active = tmp_path / ".guerilla" / "graph" / "active.jsonl"
    active.write_bytes(active.read_bytes().replace(b"\n", b"\r\n"))

    with pytest.raises(ReplayError) as excinfo:
        store.replay()

    assert excinfo.value.code == "noncanonical_jsonl_record"


def test_payload_store_verifies_content_addressed_bytes(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    initialize_workspace(
        tmp_path,
        workspace_id=_workspace_id(_ids()),
        created_at=TS,
        contracts=contracts,
    )
    payload = b"phase6 payload bytes"
    digest = write_payload(tmp_path, payload)

    assert read_payload(tmp_path, digest) == payload
    payload_path(tmp_path, digest).write_bytes(b"tampered")
    with pytest.raises(StorageError) as write_excinfo:
        write_payload(tmp_path, payload)
    assert write_excinfo.value.code == "payload_hash_mismatch"
    with pytest.raises(StorageError) as excinfo:
        read_payload(tmp_path, digest)
    assert excinfo.value.code == "payload_hash_mismatch"
    payload_path(tmp_path, digest).unlink()
    with pytest.raises(StorageError) as missing:
        read_payload(tmp_path, digest)
    assert missing.value.code == "payload_missing"
