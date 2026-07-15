from __future__ import annotations

import inspect
import shutil
from pathlib import Path
from typing import Any

import pytest

from guerilla.adapters.synthetic import deterministic_identifier
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.identity import IdentifierGenerator
from guerilla.observability.ingestion import PHASE10_METADATA_KEY
from guerilla.orchestration.actions import PHASE11_METADATA_KEY
from guerilla.projections import (
    SNAPSHOT_METADATA_KEY,
    SnapshotEngine,
    SnapshotRequest,
)
from guerilla.storage import GraphStore, initialize_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase14-local-user", "actor_kind": "human"}


def _authority() -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": "local-user", "profile": "local-owner-v1"}


def _store(tmp_path: Path, contracts: ContractBundle) -> tuple[GraphStore, str]:
    workspace_id = deterministic_identifier("workspace", 1400)
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts), workspace_id


def _node(
    ids: IdentifierGenerator,
    workspace_id: str,
    node_type: str,
    random_b: int,
    *,
    status: str = "open",
    metadata: dict[str, Any] | None = None,
    state_boundary_id: str | None = None,
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "node_id": str(ids.generate("node", now_ms=1_721_000_400_000, random_b=random_b)),
        "entity_id": str(ids.generate("entity", now_ms=1_721_000_400_001, random_b=random_b)),
        "node_type": node_type,
        "created_at": TS,
        "actor": _actor(),
        "authority": _authority(),
        "status": status,
        "provenance": {"source": "phase14-test", "source_record_ids": []},
        "payload_ref": {"retention_class": "none"},
        "metadata": metadata or {},
        "extensions": {},
    }
    if state_boundary_id is not None:
        node["state_boundary_id"] = state_boundary_id
    return node


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
        "edge_id": str(ids.generate("edge", now_ms=1_721_000_400_002, random_b=random_b)),
        "relationship_type": relationship_type,
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "created_at": TS,
        "actor": _actor(),
        "provenance": {"source": "phase14-test", "source_record_ids": []},
        "metadata": {},
        "extensions": {},
    }


def _observation_metadata(
    *,
    boundary_id: str,
    external_id: str,
    external_revision: str,
    content_hash: str,
    lifecycle_state: str | None = None,
) -> dict[str, Any]:
    external_identity = {
        "system_id": "phase14-system",
        "state_boundary_id": boundary_id,
        "external_kind": "record",
        "external_id": external_id,
        "external_revision": external_revision,
        "namespace": "phase14",
    }
    if lifecycle_state is not None:
        external_identity["lifecycle_state"] = lifecycle_state
    return {
        PHASE10_METADATA_KEY: {
            "kind": "external_state_revision",
            "external_identity": external_identity,
            "external_identity_key": external_id,
            "external_revision": external_revision,
            "content_hash": content_hash,
            "freshness": "observed_at_request_time",
            "consistency": "adapter_declared",
        }
    }


def _action_metadata(
    *,
    kind: str,
    intent_node_id: str,
    operation_node_id: str,
    idempotency_key: str,
    classification: str | None = None,
    invocation_node_id: str | None = None,
    result_node_id: str | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "kind": kind,
        "operation_node_id": operation_node_id,
        "intent_node_id": intent_node_id,
        "idempotency_key": idempotency_key,
        "request_hash": "e" * 64,
        "adapter_id": "phase14-adapter",
        "adapter_version": "1.0.0",
        "system_id": "phase14-system",
        "state_boundary_id": deterministic_identifier("state_boundary", 1499),
        "action": "mutate",
        "arguments": {"id": idempotency_key},
        "action_data": {"id": idempotency_key},
    }
    if invocation_node_id is not None:
        metadata["invocation_node_id"] = invocation_node_id
    if result_node_id is not None:
        metadata["result_node_id"] = result_node_id
    if classification is not None:
        metadata["state"] = classification
        metadata["external_result_classification"] = classification
        metadata["pending_or_unknown"] = classification in {"pending", "outcome_unknown"}
    return {PHASE11_METADATA_KEY: metadata}


def _build_phase14_history(store: GraphStore, workspace_id: str) -> dict[str, Any]:
    ids = IdentifierGenerator()
    boundary_id = deterministic_identifier("state_boundary", 1401)
    goal = _node(ids, workspace_id, "goal", 10, status="active")
    operation = _node(ids, workspace_id, "operation", 11, status="running")
    artifact = _node(
        ids,
        workspace_id,
        "artifact",
        12,
        status="observed",
        metadata=_observation_metadata(
            boundary_id=boundary_id,
            external_id="ticket-1",
            external_revision="rev-1",
            content_hash="a" * 64,
        ),
        state_boundary_id=boundary_id,
    )
    renamed = _node(
        ids,
        workspace_id,
        "artifact",
        13,
        status="rename",
        metadata=_observation_metadata(
            boundary_id=boundary_id,
            external_id="ticket-2",
            external_revision="rev-2",
            content_hash="b" * 64,
            lifecycle_state="renamed",
        ),
        state_boundary_id=boundary_id,
    )
    deleted = _node(
        ids,
        workspace_id,
        "artifact",
        14,
        status="deletion",
        metadata=_observation_metadata(
            boundary_id=boundary_id,
            external_id="ticket-3",
            external_revision="rev-3",
            content_hash="c" * 64,
            lifecycle_state="deleted",
        ),
        state_boundary_id=boundary_id,
    )
    conflict = _node(
        ids,
        workspace_id,
        "conflict",
        15,
        status="open",
        metadata={"conflict_type": "external_outcome_unknown"},
    )
    pending_intent = _node(ids, workspace_id, "event", 16, status="intent_committed")
    pending_invocation = _node(ids, workspace_id, "event", 17, status="invocation_started")
    unknown_intent = _node(ids, workspace_id, "event", 18, status="intent_committed")
    unknown_invocation = _node(ids, workspace_id, "event", 19, status="invocation_started")
    unknown_result = _node(ids, workspace_id, "event", 20, status="outcome_unknown")
    pending_intent["metadata"] = _action_metadata(
        kind="action_request_event",
        intent_node_id=pending_intent["node_id"],
        operation_node_id=operation["node_id"],
        idempotency_key="pending-key",
    )
    pending_invocation["metadata"] = _action_metadata(
        kind="invocation_started_event",
        intent_node_id=pending_intent["node_id"],
        operation_node_id=operation["node_id"],
        idempotency_key="pending-key",
        invocation_node_id=pending_invocation["node_id"],
    )
    unknown_intent["metadata"] = _action_metadata(
        kind="action_request_event",
        intent_node_id=unknown_intent["node_id"],
        operation_node_id=operation["node_id"],
        idempotency_key="unknown-key",
    )
    unknown_invocation["metadata"] = _action_metadata(
        kind="invocation_started_event",
        intent_node_id=unknown_intent["node_id"],
        operation_node_id=operation["node_id"],
        idempotency_key="unknown-key",
        invocation_node_id=unknown_invocation["node_id"],
    )
    unknown_result["metadata"] = _action_metadata(
        kind="action_result_event",
        intent_node_id=unknown_intent["node_id"],
        operation_node_id=operation["node_id"],
        idempotency_key="unknown-key",
        classification="outcome_unknown",
        invocation_node_id=unknown_invocation["node_id"],
        result_node_id=unknown_result["node_id"],
    )
    members = [
        goal,
        operation,
        artifact,
        renamed,
        deleted,
        conflict,
        pending_intent,
        pending_invocation,
        unknown_intent,
        unknown_invocation,
        unknown_result,
        _edge(ids, workspace_id, "depends_on", goal["node_id"], operation["node_id"], 30),
        _edge(ids, workspace_id, "produces", operation["node_id"], artifact["node_id"], 31),
        _edge(ids, workspace_id, "produces", operation["node_id"], renamed["node_id"], 32),
        _edge(ids, workspace_id, "produces", operation["node_id"], deleted["node_id"], 33),
        _edge(ids, workspace_id, "causes", operation["node_id"], pending_intent["node_id"], 34),
        _edge(
            ids,
            workspace_id,
            "causes",
            pending_intent["node_id"],
            pending_invocation["node_id"],
            35,
        ),
        _edge(ids, workspace_id, "causes", operation["node_id"], unknown_intent["node_id"], 36),
        _edge(
            ids,
            workspace_id,
            "causes",
            unknown_intent["node_id"],
            unknown_invocation["node_id"],
            37,
        ),
        _edge(
            ids,
            workspace_id,
            "causes",
            unknown_invocation["node_id"],
            unknown_result["node_id"],
            38,
        ),
        _edge(ids, workspace_id, "evidences", unknown_result["node_id"], conflict["node_id"], 39),
    ]
    store.append_transaction(members, actor=_actor(), created_at=TS, committed_at=TS)
    return {
        "goal": goal,
        "operation": operation,
        "artifact": artifact,
        "renamed": renamed,
        "deleted": deleted,
        "conflict": conflict,
        "pending_intent": pending_intent,
        "unknown_result": unknown_result,
    }


def _snapshot_request(revision: int | None = None) -> SnapshotRequest:
    return SnapshotRequest(
        principal_id="local-user",
        actor=_actor(),
        authority=_authority(),
        created_at=TS,
        revision=revision,
    )


def test_snapshot_creation_verification_and_resume_context_are_grounded(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    nodes = _build_phase14_history(store, workspace_id)
    engine = SnapshotEngine(store=store)
    source_revision = store.replay().graph_revision

    result = engine.create_snapshot(_snapshot_request())
    verification = engine.verify_snapshot(result.snapshot_node_id)
    resume = engine.resume_context(result.snapshot_node_id)
    replay = store.replay()
    snapshot = replay.nodes[result.snapshot_node_id]
    metadata = snapshot["metadata"][SNAPSHOT_METADATA_KEY]

    assert result.source_graph_revision == source_revision
    assert verification.verified is True
    assert verification.materialized_summary_status == "present"
    assert metadata["source_graph_revision"] == source_revision
    assert metadata["summary_hash"] == result.summary_hash
    assert result.materialized_summary_path is not None
    assert result.materialized_summary_path.is_file()
    captured_sources = {
        edge["from_node_id"]
        for edge in replay.edges.values()
        if edge["relationship_type"] == "captured_by"
        and edge["to_node_id"] == result.snapshot_node_id
    }
    assert captured_sources == set(result.source_node_ids)
    assert nodes["goal"]["node_id"] in {item["node_id"] for item in resume.open_goals}
    assert nodes["operation"]["node_id"] in {item["node_id"] for item in resume.blocked_operations}
    assert nodes["conflict"]["node_id"] in {item["node_id"] for item in resume.unresolved_conflicts}
    assert nodes["pending_intent"]["node_id"] in {
        item["intent_node_id"] for item in resume.pending_reconciliation
    }
    assert nodes["unknown_result"]["node_id"] in {
        item["result_node_id"] for item in resume.unknown_outcomes
    }
    assert len(resume.stale_observations) == 3
    assert len(resume.required_refresh_observations) == 3
    assert len(resume.relevant_artifact_revisions) == 3
    assert resume.authoritative_facts["source_graph_revision"] == source_revision
    assert resume.derived_summaries["authoritative_status"] == "derived_non_authoritative"
    assert resume.automatic_actions_executed is False
    source = inspect.getsource(SnapshotEngine)
    assert "AdapterHost" not in source
    assert ".invoke(" not in source


def test_missing_or_corrupt_materialized_summary_does_not_destroy_continuity(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    _build_phase14_history(store, workspace_id)
    engine = SnapshotEngine(store=store)
    result = engine.create_snapshot(_snapshot_request())
    assert result.materialized_summary_path is not None

    result.materialized_summary_path.unlink()
    missing = engine.verify_snapshot(result.snapshot_node_id)
    assert missing.verified is True
    assert missing.materialized_summary_status == "missing"
    assert missing.warnings == ("materialized_summary_missing",)

    result.materialized_summary_path.write_text("not-json\n", encoding="utf-8")
    corrupt = engine.verify_snapshot(result.snapshot_node_id)
    assert corrupt.verified is True
    assert corrupt.materialized_summary_status == "corrupt"
    assert corrupt.warnings == ("materialized_summary_corrupt",)
    resume = engine.resume_context(result.snapshot_node_id)
    assert resume.authoritative_facts["snapshot_node_id"] == result.snapshot_node_id


def test_old_revision_resume_survives_later_commits_deleted_index_and_projection_cache(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    _build_phase14_history(store, workspace_id)
    source_revision = store.replay().graph_revision
    ids = IdentifierGenerator()
    later_event = _node(ids, workspace_id, "event", 200, status="later")
    store.append_transaction([later_event], actor=_actor(), created_at=TS, committed_at=TS)
    engine = SnapshotEngine(store=store)
    result = engine.create_snapshot(_snapshot_request(revision=source_revision))
    first_verify = engine.verify_snapshot(result.snapshot_node_id)
    assert first_verify.verified is True

    sqlite_index = tmp_path / ".guerilla" / "indexes" / "graph.sqlite"
    sqlite_index.unlink(missing_ok=True)
    projections = tmp_path / ".guerilla" / "projections"
    if projections.exists():
        shutil.rmtree(projections)
    newest_event = _node(ids, workspace_id, "event", 201, status="newer")
    store.append_transaction([newest_event], actor=_actor(), created_at=TS, committed_at=TS)

    second_verify = engine.verify_snapshot(result.snapshot_node_id)
    resume = engine.resume_context(result.snapshot_node_id)
    assert second_verify.verified is True
    assert second_verify.regenerated_summary_hash == first_verify.regenerated_summary_hash
    assert resume.authoritative_facts["source_graph_revision"] == source_revision
    assert later_event["node_id"] not in resume.authoritative_facts["captured_source_node_ids"]
    assert newest_event["node_id"] not in resume.authoritative_facts["captured_source_node_ids"]


def test_source_commit_mismatch_is_rejected_without_adapter_or_summary_authority(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    nodes = _build_phase14_history(store, workspace_id)
    replay = store.replay()
    ids = IdentifierGenerator()
    snapshot = _node(
        ids,
        workspace_id,
        "snapshot",
        300,
        status="captured",
        metadata={
            SNAPSHOT_METADATA_KEY: {
                "kind": "snapshot_record",
                "snapshot_node_id": "pending",
                "source_graph_revision": replay.graph_revision,
                "source_commit_hash": "f" * 64,
                "source_query": {"view": "snapshot"},
                "source_node_ids": [nodes["goal"]["node_id"]],
                "transformation_version": "phase14-snapshot-v1",
                "projection_transformation_version": "phase13-projections-v1",
                "policy_version": "phase13-default-policy-v1",
                "summary_hash": "0" * 64,
                "information_loss": [],
                "freshness_requirements": [],
                "materialized_summary_path": ".guerilla/snapshots/bogus.summary.json",
            }
        },
    )
    snapshot["metadata"][SNAPSHOT_METADATA_KEY]["snapshot_node_id"] = snapshot["node_id"]
    edge = _edge(
        ids,
        workspace_id,
        "captured_by",
        nodes["goal"]["node_id"],
        snapshot["node_id"],
        301,
    )
    store.append_transaction([snapshot, edge], actor=_actor(), created_at=TS, committed_at=TS)

    verification = SnapshotEngine(store=store).verify_snapshot(snapshot["node_id"])
    assert verification.verified is False
    assert "source_commit_mismatch" in verification.errors
    assert "summary_hash_mismatch" in verification.errors
