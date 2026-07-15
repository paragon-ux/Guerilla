from __future__ import annotations

from copy import deepcopy
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
from guerilla.conflicts import (
    PHASE12_CONFLICT_METADATA_KEY,
    ConflictEngine,
    ConflictError,
    ConflictRecordRequest,
    ConflictResolutionRequest,
)
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.orchestration import ActionExecutionError, ActionExecutionRequest, ActionOrchestrator
from guerilla.orchestration.actions import PHASE11_METADATA_KEY
from guerilla.reconciliation import ReconciliationEngine, ReconciliationRequest
from guerilla.storage import GraphStore, initialize_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase12-local-user", "actor_kind": "human"}


def _authority(principal_id: str = "local-user") -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": principal_id, "profile": "local-owner-v1"}


def _store(tmp_path: Path, contracts: ContractBundle) -> GraphStore:
    workspace_id = deterministic_identifier("workspace", 1200)
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts)


def _action_request(
    adapter: Any,
    action: str,
    arguments: dict[str, Any],
    *,
    idempotency_key: str,
    expected_external_revision: str | None = None,
    root: str | None = None,
    namespace: str | None = None,
    fail_at: str | None = None,
) -> ActionExecutionRequest:
    return ActionExecutionRequest(
        adapter_id=adapter.adapter_id,
        state_boundary_id=adapter.boundary_id,
        action=action,
        arguments=arguments,
        idempotency_key=idempotency_key,
        principal_id="local-user",
        actor=_actor(),
        authority=_authority(),
        requested_at=TS,
        intent_committed_at=TS,
        invocation_started_at=TS,
        result_committed_at=TS,
        expected_external_revision=expected_external_revision,
        root=root,
        namespace=namespace,
        correlation_id=f"corr-{idempotency_key}",
        causation_id=f"cause-{idempotency_key}",
        fail_at=fail_at,
    )


def _reconcile_request(
    adapter: Any,
    intent_node_id: str,
    idempotency_key: str,
    *,
    namespace: str | None = None,
    after_state_selector: dict[str, Any] | None = None,
    fail_at: str | None = None,
) -> ReconciliationRequest:
    return ReconciliationRequest(
        adapter_id=adapter.adapter_id,
        state_boundary_id=adapter.boundary_id,
        intent_node_id=intent_node_id,
        idempotency_key=idempotency_key,
        principal_id="local-user",
        actor=_actor(),
        authority=_authority(),
        requested_at=TS,
        reconciled_at=TS,
        namespace=namespace,
        correlation_id=f"reconcile-{idempotency_key}",
        after_state_selector=after_state_selector,
        after_state_observed_at=TS,
        fail_at=fail_at,
    )


def _phase11_node(replay: Any, *, kind: str, idempotency_key: str) -> dict[str, Any]:
    matches = []
    for node in replay.nodes.values():
        metadata = node["metadata"].get(PHASE11_METADATA_KEY)
        if (
            isinstance(metadata, dict)
            and metadata.get("kind") == kind
            and metadata.get("idempotency_key") == idempotency_key
        ):
            assert isinstance(node, dict)
            matches.append(node)
    assert len(matches) == 1
    return matches[0]


def _phase12_conflicts(replay: Any) -> list[dict[str, Any]]:
    return [
        node
        for node in replay.nodes.values()
        if node["node_type"] == "conflict" and PHASE12_CONFLICT_METADATA_KEY in node["metadata"]
    ]


def test_missing_lineage_recovery_uses_one_engine_for_all_synthetic_systems(
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
    actions = ActionOrchestrator(store=store, host=host)
    reconciler = ReconciliationEngine(store=store, host=host)

    for adapter, action, arguments, key, namespace, root in (
        (
            transactional,
            "set_value",
            {"subject": "ticket-1", "value": "open"},
            "phase12-key-001",
            "transactional",
            None,
        ),
        (
            filesystem,
            "write_file",
            {"path": "note.txt", "content": "phase 12"},
            "phase12-key-002",
            "filesystem",
            str(filesystem.root / "note.txt"),
        ),
        (
            async_adapter,
            "submit_job",
            {"subject": "job-1", "completion_delay_ms": 10},
            "phase12-key-003",
            "async",
            None,
        ),
    ):
        with pytest.raises(ActionExecutionError):
            actions.execute(
                _action_request(
                    adapter,
                    action,
                    arguments,
                    idempotency_key=key,
                    namespace=namespace,
                    root=root,
                    fail_at="after_adapter_return_before_result_commit",
                )
            )

    clock.advance(20)
    results = []
    for adapter, key, namespace in (
        (transactional, "phase12-key-001", "transactional"),
        (filesystem, "phase12-key-002", "filesystem"),
        (async_adapter, "phase12-key-003", "async"),
    ):
        intent = _phase11_node(
            store.replay(),
            kind="action_request_event",
            idempotency_key=key,
        )
        results.append(
            reconciler.reconcile(
                _reconcile_request(
                    adapter,
                    str(intent["node_id"]),
                    key,
                    namespace=namespace,
                    after_state_selector=(
                        {"subject": "ticket-1"} if adapter is transactional else None
                    ),
                )
            )
        )

    assert [result.classification for result in results] == [
        "confirmed_accepted",
        "confirmed_accepted",
        "confirmed_accepted",
    ]
    assert all(result.recovered_result_node_id is not None for result in results)
    assert isinstance(results[0].after_state_observation, dict)
    assert transactional.calls["act"] == filesystem.calls["act"] == async_adapter.calls["act"] == 1
    assert transactional.calls["reconcile"] == filesystem.calls["reconcile"] == 1
    assert async_adapter.calls["reconcile"] == 1

    replay = store.replay()
    first_recovered_result_node_id = results[0].recovered_result_node_id
    assert first_recovered_result_node_id is not None
    recovered_node = replay.nodes[first_recovered_result_node_id]
    assert recovered_node["metadata"][PHASE11_METADATA_KEY]["kind"] == "action_result_event"
    assert recovered_node["provenance"]["metadata"]["original_result_timestamp_fabricated"] is False
    replayed = actions.execute(
        _action_request(
            transactional,
            "set_value",
            {"subject": "ticket-1", "value": "open"},
            idempotency_key="phase12-key-001",
            namespace="transactional",
        )
    )
    assert replayed.idempotency_status == "replayed_result"
    assert replayed.result_node_id == results[0].recovered_result_node_id
    assert transactional.calls["act"] == 1


def test_unknown_and_unsupported_reconciliation_create_explicit_conflicts(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    clock = VirtualClock()
    async_adapter = AsyncUnknownOutcomeAdapter(clock=clock)
    host = AdapterHost(contracts=contracts, adapters=[async_adapter], clock_ms=clock.now_ms)
    actions = ActionOrchestrator(store=store, host=host)
    reconciler = ReconciliationEngine(store=store, host=host)

    unknown = actions.execute(
        _action_request(
            async_adapter,
            "submit_job",
            {"subject": "job-unknown", "force_unknown": True},
            idempotency_key="phase12-key-101",
            namespace="async",
        )
    )
    assert unknown.action_classification == "outcome_unknown"
    result = reconciler.reconcile(
        _reconcile_request(
            async_adapter,
            unknown.intent_node_id,
            "phase12-key-101",
            namespace="async",
        )
    )
    assert result.classification == "unknown"
    assert len(result.conflict_node_ids) == 1
    conflict = store.replay().nodes[result.conflict_node_ids[0]]
    conflict_metadata = conflict["metadata"][PHASE12_CONFLICT_METADATA_KEY]
    assert conflict_metadata["conflict_type"] == "external_outcome_unknown"
    assert conflict_metadata["status"] == "open"
    assert async_adapter.calls["act"] == 1

    unsupported = TransactionalRevisionedServiceAdapter(seed=1300)
    unsupported.descriptor["capabilities"] = [
        deepcopy(capability)
        for capability in unsupported.descriptor["capabilities"]
        if capability["capability"] != "reconcile"
    ]
    unsupported_host = AdapterHost(contracts=contracts, adapters=[unsupported])
    unsupported_actions = ActionOrchestrator(store=store, host=unsupported_host)
    accepted = unsupported_actions.execute(
        _action_request(
            unsupported,
            "set_value",
            {"subject": "ticket-unsupported", "value": "open"},
            idempotency_key="phase12-key-102",
            namespace="transactional",
        )
    )
    unsupported_result = ReconciliationEngine(store=store, host=unsupported_host).reconcile(
        _reconcile_request(
            unsupported,
            accepted.intent_node_id,
            "phase12-key-102",
            namespace="transactional",
        )
    )
    assert unsupported_result.classification == "unknown"
    assert len(unsupported_result.conflict_node_ids) == 1
    unsupported_conflict = store.replay().nodes[unsupported_result.conflict_node_ids[0]]
    assert (
        unsupported_conflict["metadata"][PHASE12_CONFLICT_METADATA_KEY]["conflict_reason"]
        == "unsupported_reconciliation"
    )
    assert unsupported.calls["reconcile"] == 0


def test_reconciliation_detects_stale_revision_and_duplicate_attempt_conflicts(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    transactional = TransactionalRevisionedServiceAdapter()
    host = AdapterHost(contracts=contracts, adapters=[transactional])
    actions = ActionOrchestrator(store=store, host=host)
    reconciler = ReconciliationEngine(store=store, host=host)

    first = actions.execute(
        _action_request(
            transactional,
            "set_value",
            {"subject": "ticket-dup", "value": "open"},
            idempotency_key="phase12-key-201",
            namespace="transactional",
        )
    )
    duplicate = actions.execute(
        _action_request(
            transactional,
            "set_value",
            {"subject": "ticket-dup", "value": "open"},
            idempotency_key="phase12-key-202",
            namespace="transactional",
        )
    )
    duplicate_reconcile = reconciler.reconcile(
        _reconcile_request(
            transactional,
            duplicate.intent_node_id,
            "phase12-key-202",
            namespace="transactional",
        )
    )
    duplicate_conflicts = [
        store.replay().nodes[node_id]["metadata"][PHASE12_CONFLICT_METADATA_KEY]
        for node_id in duplicate_reconcile.conflict_node_ids
    ]
    assert any(
        conflict["conflict_reason"] == "same_request_different_local_attempts"
        for conflict in duplicate_conflicts
    )

    stale = actions.execute(
        _action_request(
            transactional,
            "set_value",
            {"subject": "ticket-dup", "value": "closed"},
            idempotency_key="phase12-key-203",
            namespace="transactional",
            expected_external_revision="rev-0",
        )
    )
    assert stale.action_classification == "rejected"
    stale_reconcile = reconciler.reconcile(
        _reconcile_request(
            transactional,
            stale.intent_node_id,
            "phase12-key-203",
            namespace="transactional",
        )
    )
    stale_conflicts = [
        store.replay().nodes[node_id]["metadata"][PHASE12_CONFLICT_METADATA_KEY]
        for node_id in stale_reconcile.conflict_node_ids
    ]
    assert any(
        conflict["conflict_type"] == "stale_external_revision" for conflict in stale_conflicts
    )
    assert first.result_node_id is not None


def test_conflict_decisions_are_append_only_and_cover_phase12_reason_classes(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    adapter = TransactionalRevisionedServiceAdapter()
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    action = ActionOrchestrator(store=store, host=host).execute(
        _action_request(
            adapter,
            "set_value",
            {"subject": "ticket-conflict", "value": "open"},
            idempotency_key="phase12-key-301",
            namespace="transactional",
        )
    )
    evidence_node_id = action.result_node_id
    assert evidence_node_id is not None
    engine = ConflictEngine(store=store)
    cases = [
        ("stale_external_revision", "stale_external_revision"),
        ("identity_collision", "identity_collision"),
        ("ambiguous_authority", "ambiguous_authority"),
        ("state_boundary_violation", "state_boundary_violation"),
        ("idempotency_conflict", "idempotency_conflict"),
        ("external_outcome_unknown", "unknown_outcome"),
        ("failed_evaluation", "failed_evaluation"),
        ("incomplete_lineage", "incomplete_lineage"),
        ("incomplete_lineage", "divergent_after_state"),
        ("incomplete_lineage", "unsupported_reconciliation"),
    ]
    conflict_ids: list[str] = []
    for index, (conflict_type, reason) in enumerate(cases):
        result = engine.record_conflict(
            ConflictRecordRequest(
                conflict_type=conflict_type,  # type: ignore[arg-type]
                conflict_reason=reason,
                subject_node_id=evidence_node_id,
                evidence_node_ids=(evidence_node_id,),
                principal_id="local-user",
                actor=_actor(),
                authority=_authority(),
                detected_at=TS,
                severity="high",
                required_resolution_class=f"phase12-resolution-{index}",
                summary=f"phase12 {reason}",
                details={"case": reason},
            )
        )
        conflict_ids.append(result.conflict_node_id)

    replay = store.replay()
    assert len(_phase12_conflicts(replay)) == len(cases)
    for conflict_id in conflict_ids:
        metadata = replay.nodes[conflict_id]["metadata"][PHASE12_CONFLICT_METADATA_KEY]
        assert metadata["subject_node_id"] == evidence_node_id
        assert metadata["evidence_node_ids"] == [evidence_node_id]
        assert metadata["severity"] == "high"
        assert metadata["status"] == "open"
        assert metadata["policy_version"] == "local-owner-v1"
        assert metadata["required_resolution_class"]

    resolution = engine.resolve_conflict(
        ConflictResolutionRequest(
            conflict_node_id=conflict_ids[0],
            alternatives=(
                {"outcome": "refresh", "risk": "low"},
                {"outcome": "ignore", "risk": "high"},
            ),
            chosen_outcome="refresh",
            rationale="Refresh before continuing.",
            principal_id="local-user",
            actor=_actor(),
            authority=_authority(),
            decided_at=TS,
            evidence_node_ids=(evidence_node_id,),
            continuation_operation={"operation": "adapter.observe", "reason": "refresh"},
        )
    )
    replay_after = store.replay()
    assert replay_after.nodes[conflict_ids[0]]["status"] == "open"
    assert replay_after.nodes[resolution.decision_node_id]["node_type"] == "decision"
    assert resolution.continuation_operation_node_id is not None
    assert replay_after.nodes[resolution.continuation_operation_node_id]["node_type"] == "operation"
    assert any(
        edge["relationship_type"] == "resolved_by"
        and edge["from_node_id"] == conflict_ids[0]
        and edge["to_node_id"] == resolution.decision_node_id
        for edge in replay_after.edges.values()
    )
    with pytest.raises(ConflictError):
        engine.resolve_conflict(
            ConflictResolutionRequest(
                conflict_node_id=conflict_ids[0],
                alternatives=({"outcome": "retry"},),
                chosen_outcome="retry",
                rationale="duplicate resolution should fail",
                principal_id="local-user",
                actor=_actor(),
                authority=_authority(),
                decided_at=TS,
            )
        )
