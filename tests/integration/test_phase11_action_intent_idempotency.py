from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import pytest

from guerilla.adapters import (
    AdapterHost,
    AsyncUnknownOutcomeAdapter,
    ReconstructedFilesystemAdapter,
    TransactionalRevisionedServiceAdapter,
    VirtualClock,
)
from guerilla.adapters.synthetic import deterministic_identifier
from guerilla.authority import AuthorityError, BoundaryError
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.index import SQLiteGraphIndex
from guerilla.orchestration import ActionExecutionError, ActionExecutionRequest, ActionOrchestrator
from guerilla.orchestration.actions import PHASE11_METADATA_KEY
from guerilla.storage import GraphStore, initialize_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase11-local-user", "actor_kind": "human"}


def _authority(principal_id: str = "local-user") -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": principal_id, "profile": "local-owner-v1"}


def _store(tmp_path: Path, contracts: ContractBundle) -> GraphStore:
    workspace_id = deterministic_identifier("workspace", 1100)
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts)


def _request(
    adapter: Any,
    action: str,
    arguments: dict[str, Any],
    *,
    idempotency_key: str,
    principal_id: str = "local-user",
    expected_graph_revision: int | None = None,
    expected_external_revision: str | None = None,
    root: str | None = None,
    namespace: str | None = None,
    after_state_selector: dict[str, Any] | None = None,
    fail_at: str | None = None,
) -> ActionExecutionRequest:
    return ActionExecutionRequest(
        adapter_id=adapter.adapter_id,
        state_boundary_id=adapter.boundary_id,
        action=action,
        arguments=arguments,
        idempotency_key=idempotency_key,
        principal_id=principal_id,
        actor=_actor(),
        authority=_authority(principal_id),
        requested_at=TS,
        intent_committed_at=TS,
        invocation_started_at=TS,
        result_committed_at=TS,
        expected_graph_revision=expected_graph_revision,
        expected_external_revision=expected_external_revision,
        root=root,
        namespace=namespace,
        correlation_id=f"corr-{idempotency_key}",
        causation_id=f"cause-{idempotency_key}",
        after_state_selector=after_state_selector,
        after_state_observed_at=TS,
        fail_at=fail_at,
    )


def _phase11_nodes(replay: Any, kind: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for node in replay.nodes.values():
        metadata = node["metadata"].get(PHASE11_METADATA_KEY)
        if isinstance(metadata, dict) and metadata.get("kind") == kind:
            nodes.append(node)
    return nodes


def test_all_synthetic_systems_use_one_intent_before_action_path(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    transactional = TransactionalRevisionedServiceAdapter()
    filesystem = ReconstructedFilesystemAdapter(tmp_path / "fs")
    clock = VirtualClock()
    async_adapter = AsyncUnknownOutcomeAdapter(clock=clock)
    host = AdapterHost(
        contracts=contracts,
        adapters=[transactional, filesystem, async_adapter],
        clock_ms=clock.now_ms,
    )
    orchestrator = ActionOrchestrator(store=store, host=host)

    accepted = orchestrator.execute(
        _request(
            transactional,
            "set_value",
            {"subject": "ticket-1", "value": "open"},
            idempotency_key="phase11-key-001",
            namespace="transactional",
            expected_graph_revision=0,
        )
    )
    written = orchestrator.execute(
        _request(
            filesystem,
            "write_file",
            {"path": "README.md", "content": "phase 11"},
            idempotency_key="phase11-key-002",
            root=str(filesystem.root / "README.md"),
            namespace="filesystem",
            expected_graph_revision=accepted.graph_revision,
        )
    )
    pending = orchestrator.execute(
        _request(
            async_adapter,
            "submit_job",
            {"subject": "job-1", "completion_delay_ms": 50},
            idempotency_key="phase11-key-003",
            namespace="async",
            expected_graph_revision=written.graph_revision,
        )
    )

    assert accepted.action_classification == "accepted"
    assert written.action_classification == "accepted"
    assert pending.action_classification == "pending"
    assert transactional.calls["act"] == filesystem.calls["act"] == async_adapter.calls["act"] == 1
    replay = store.replay()
    assert len(_phase11_nodes(replay, "action_request_event")) == 3
    assert len(_phase11_nodes(replay, "invocation_started_event")) == 3
    assert len(_phase11_nodes(replay, "action_result_event")) == 3
    for result in (accepted, written, pending):
        assert result.invocation_node_id is not None
        assert result.result_node_id is not None
        intent_revision = replay.record_revisions[result.intent_node_id]
        invocation_revision = replay.record_revisions[result.invocation_node_id]
        result_revision = replay.record_revisions[result.result_node_id]
        assert intent_revision < invocation_revision < result_revision

    source = inspect.getsource(ActionOrchestrator.execute).lower()
    assert "transactional" not in source
    assert "filesystem" not in source
    assert "async" not in source


def test_invalid_intent_inputs_do_not_commit_or_call(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    transactional = TransactionalRevisionedServiceAdapter()
    host = AdapterHost(contracts=contracts, adapters=[transactional])
    orchestrator = ActionOrchestrator(store=store, host=host)

    with pytest.raises(AuthorityError):
        orchestrator.execute(
            _request(
                transactional,
                "set_value",
                {"subject": "ticket-1", "value": "open"},
                idempotency_key="phase11-key-101",
                principal_id="intruder",
                namespace="transactional",
            )
        )
    assert transactional.calls["act"] == 0
    assert store.replay().graph_revision == 0

    filesystem = ReconstructedFilesystemAdapter(tmp_path / "fs")
    boundary_host = AdapterHost(contracts=contracts, adapters=[filesystem])
    with pytest.raises(BoundaryError):
        ActionOrchestrator(store=store, host=boundary_host).execute(
            _request(
                filesystem,
                "write_file",
                {"path": "x.txt", "content": "blocked"},
                idempotency_key="phase11-key-102",
                root=str(tmp_path / "outside" / "x.txt"),
                namespace="filesystem",
            )
        )
    assert filesystem.calls["act"] == 0
    assert store.replay().graph_revision == 0

    with pytest.raises(ActionExecutionError) as stale:
        orchestrator.execute(
            _request(
                transactional,
                "set_value",
                {"subject": "ticket-1", "value": "open"},
                idempotency_key="phase11-key-103",
                namespace="transactional",
                expected_graph_revision=99,
            )
        )
    assert stale.value.code == "stale_graph_revision"
    assert transactional.calls["act"] == 0
    assert store.replay().graph_revision == 0


def test_idempotency_replays_same_content_and_survives_index_loss(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    adapter = TransactionalRevisionedServiceAdapter()
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    orchestrator = ActionOrchestrator(store=store, host=host)
    request = _request(
        adapter,
        "set_value",
        {"subject": "ticket-1", "value": "open"},
        idempotency_key="phase11-key-201",
        namespace="transactional",
    )

    first = orchestrator.execute(request)
    same = orchestrator.execute(request)
    assert same.idempotency_status == "replayed_result"
    assert same.result_node_id == first.result_node_id
    assert adapter.calls["act"] == 1

    index = SQLiteGraphIndex(tmp_path)
    if index.path.exists():
        index.path.unlink()
    replayed_store = GraphStore(tmp_path, contracts=contracts)
    replayed = ActionOrchestrator(store=replayed_store, host=host).execute(request)
    assert replayed.idempotency_status == "replayed_result"
    assert adapter.calls["act"] == 1

    with pytest.raises(ActionExecutionError) as conflict:
        orchestrator.execute(
            _request(
                adapter,
                "set_value",
                {"subject": "ticket-1", "value": "closed"},
                idempotency_key="phase11-key-201",
                namespace="transactional",
            )
        )
    assert conflict.value.code == "idempotency_conflict"
    assert adapter.calls["act"] == 1


def test_idempotency_scope_prevents_cross_adapter_replay(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    first_adapter = TransactionalRevisionedServiceAdapter(seed=100)
    second_adapter = TransactionalRevisionedServiceAdapter(seed=140)
    host = AdapterHost(contracts=contracts, adapters=[first_adapter, second_adapter])
    orchestrator = ActionOrchestrator(store=store, host=host)

    first = orchestrator.execute(
        _request(
            first_adapter,
            "set_value",
            {"subject": "ticket-shared", "value": "open"},
            idempotency_key="phase11-shared-key",
            namespace="transactional",
        )
    )
    second = orchestrator.execute(
        _request(
            second_adapter,
            "set_value",
            {"subject": "ticket-shared", "value": "open"},
            idempotency_key="phase11-shared-key",
            namespace="transactional",
        )
    )

    assert first.idempotency_status == "new_intent"
    assert second.idempotency_status == "new_intent"
    assert first.result_node_id != second.result_node_id
    assert first_adapter.calls["act"] == 1
    assert second_adapter.calls["act"] == 1
    assert first_adapter.records["ticket-shared"]["revision"] == "rev-1"
    assert second_adapter.records["ticket-shared"]["revision"] == "rev-1"


def test_restart_points_resume_or_block_without_blind_retry(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    adapter = TransactionalRevisionedServiceAdapter()
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    orchestrator = ActionOrchestrator(store=store, host=host)

    with pytest.raises(ActionExecutionError):
        orchestrator.execute(
            _request(
                adapter,
                "set_value",
                {"subject": "ticket-1", "value": "open"},
                idempotency_key="phase11-key-301",
                namespace="transactional",
                fail_at="after_intent_commit_before_invocation",
            )
        )
    assert adapter.calls["act"] == 0
    assert store.replay().graph_revision == 1

    resumed = orchestrator.execute(
        _request(
            adapter,
            "set_value",
            {"subject": "ticket-1", "value": "open"},
            idempotency_key="phase11-key-301",
            namespace="transactional",
        )
    )
    assert resumed.idempotency_status == "resumed_after_intent"
    assert resumed.action_classification == "accepted"
    assert adapter.calls["act"] == 1

    with pytest.raises(ActionExecutionError):
        orchestrator.execute(
            _request(
                adapter,
                "set_value",
                {"subject": "ticket-2", "value": "unknown"},
                idempotency_key="phase11-key-302",
                namespace="transactional",
                fail_at="after_adapter_return_before_result_commit",
            )
        )
    assert adapter.calls["act"] == 2
    unknown = orchestrator.execute(
        _request(
            adapter,
            "set_value",
            {"subject": "ticket-2", "value": "unknown"},
            idempotency_key="phase11-key-302",
            namespace="transactional",
        )
    )
    assert unknown.idempotency_status == "prior_outcome_unknown"
    assert unknown.action_classification == "outcome_unknown"
    assert adapter.calls["act"] == 2


def test_result_classifications_after_state_and_replay_are_safe(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    filesystem = ReconstructedFilesystemAdapter(tmp_path / "fs")
    fs_host = AdapterHost(contracts=contracts, adapters=[filesystem])
    fs_orchestrator = ActionOrchestrator(store=store, host=fs_host)

    partial = fs_orchestrator.execute(
        _request(
            filesystem,
            "multi_write",
            {
                "writes": [
                    {"path": "a.txt", "content": "a"},
                    {"path": "b.txt", "content": "b"},
                ],
                "fail_after": 1,
            },
            idempotency_key="phase11-key-401",
            root=str(filesystem.root / "a.txt"),
            namespace="filesystem",
            after_state_selector={"path": "a.txt"},
        )
    )
    assert partial.action_classification == "failed"
    assert partial.after_state_observation is not None
    assert filesystem.calls["act"] == 1
    assert filesystem.calls["observe"] == 1
    replay_calls = dict(filesystem.calls)
    GraphStore(tmp_path, contracts=contracts).replay()
    SQLiteGraphIndex(tmp_path).rebuild(store.replay())
    assert filesystem.calls == replay_calls

    clock = VirtualClock()
    async_adapter = AsyncUnknownOutcomeAdapter(clock=clock)
    async_host = AdapterHost(contracts=contracts, adapters=[async_adapter], clock_ms=clock.now_ms)
    async_orchestrator = ActionOrchestrator(store=store, host=async_host)
    unknown_request = _request(
        async_adapter,
        "submit_job",
        {"subject": "job-unknown", "completion_delay_ms": 1, "force_unknown": True},
        idempotency_key="phase11-key-402",
        namespace="async",
    )
    unknown = async_orchestrator.execute(unknown_request)
    replayed = async_orchestrator.execute(unknown_request)
    assert unknown.action_classification == "outcome_unknown"
    assert replayed.idempotency_status == "replayed_result"
    assert async_adapter.calls["act"] == 1
