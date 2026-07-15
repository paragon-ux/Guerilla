from __future__ import annotations

import inspect
import shutil
from pathlib import Path
from typing import Any

import pytest

from guerilla.adapters.synthetic import deterministic_identifier
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.identity import IdentifierGenerator
from guerilla.index import SQLiteGraphIndex
from guerilla.observability.ingestion import PHASE10_METADATA_KEY
from guerilla.projections import DERIVED_AUTHORITY, ProjectionEngine
from guerilla.storage import GraphStore, initialize_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase13-local-user", "actor_kind": "human"}


def _authority() -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": "local-user", "profile": "local-owner-v1"}


def _store(tmp_path: Path, contracts: ContractBundle) -> tuple[GraphStore, str]:
    workspace_id = deterministic_identifier("workspace", 1300)
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts), workspace_id


def _node(
    ids: IdentifierGenerator,
    workspace_id: str,
    node_type: str,
    random_b: int,
    *,
    status: str = "open",
    entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    state_boundary_id: str | None = None,
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "node_id": str(ids.generate("node", now_ms=1_721_000_300_000, random_b=random_b)),
        "entity_id": entity_id
        or str(ids.generate("entity", now_ms=1_721_000_300_001, random_b=random_b)),
        "node_type": node_type,
        "created_at": TS,
        "actor": _actor(),
        "authority": _authority(),
        "status": status,
        "provenance": {"source": "phase13-test", "source_record_ids": []},
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
        "edge_id": str(ids.generate("edge", now_ms=1_721_000_300_002, random_b=random_b)),
        "relationship_type": relationship_type,
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "created_at": TS,
        "actor": _actor(),
        "provenance": {"source": "phase13-test", "source_record_ids": []},
        "metadata": {},
        "extensions": {},
    }


def _observation_metadata(
    *,
    system_id: str,
    boundary_id: str,
    external_kind: str,
    external_id: str,
    external_revision: str,
    content_hash: str,
    namespace: str | None = None,
) -> dict[str, Any]:
    external_identity = {
        "system_id": system_id,
        "state_boundary_id": boundary_id,
        "external_kind": external_kind,
        "external_id": external_id,
        "external_revision": external_revision,
        "namespace": namespace if namespace is not None else system_id,
    }
    return {
        PHASE10_METADATA_KEY: {
            "kind": "external_state_revision",
            "external_identity": external_identity,
            "external_revision": external_revision,
            "content_hash": content_hash,
            "freshness": "observed_at_request_time",
            "consistency": "adapter_declared",
        }
    }


def _build_phase13_history(
    store: GraphStore,
    workspace_id: str,
) -> dict[str, Any]:
    ids = IdentifierGenerator()
    transactional_boundary = deterministic_identifier("state_boundary", 1301)
    filesystem_boundary = deterministic_identifier("state_boundary", 1302)
    async_boundary = deterministic_identifier("state_boundary", 1303)
    shared_artifact_entity = str(ids.generate("entity", now_ms=1_721_000_300_010, random_b=1))

    goal = _node(ids, workspace_id, "goal", 10, status="active")
    operation = _node(ids, workspace_id, "operation", 11, status="running")
    event = _node(ids, workspace_id, "event", 12, status="observed")
    artifact_old = _node(
        ids,
        workspace_id,
        "artifact",
        13,
        status="observed",
        entity_id=shared_artifact_entity,
        metadata=_observation_metadata(
            system_id="transactional",
            boundary_id=transactional_boundary,
            external_kind="record",
            external_id="ticket-1",
            external_revision="rev-1",
            content_hash="a" * 64,
        ),
        state_boundary_id=transactional_boundary,
    )
    filesystem_artifact = _node(
        ids,
        workspace_id,
        "artifact",
        14,
        status="observed",
        metadata=_observation_metadata(
            system_id="filesystem",
            boundary_id=filesystem_boundary,
            external_kind="file",
            external_id="note.txt",
            external_revision="fs-rev-1",
            content_hash="b" * 64,
        ),
        state_boundary_id=filesystem_boundary,
    )
    async_artifact = _node(
        ids,
        workspace_id,
        "artifact",
        15,
        status="observed",
        metadata=_observation_metadata(
            system_id="async",
            boundary_id=async_boundary,
            external_kind="job",
            external_id="job-1",
            external_revision="async-rev-1",
            content_hash="c" * 64,
        ),
        state_boundary_id=async_boundary,
    )
    conflict = _node(
        ids,
        workspace_id,
        "conflict",
        16,
        status="open",
        metadata={
            "conflict_type": "external_outcome_unknown",
            "summary": "phase13 unresolved conflict",
        },
    )
    base_edges = [
        _edge(ids, workspace_id, "depends_on", goal["node_id"], operation["node_id"], 30),
        _edge(ids, workspace_id, "produces", operation["node_id"], artifact_old["node_id"], 31),
        _edge(
            ids, workspace_id, "produces", operation["node_id"], filesystem_artifact["node_id"], 32
        ),
        _edge(ids, workspace_id, "produces", operation["node_id"], async_artifact["node_id"], 33),
        _edge(ids, workspace_id, "evidences", event["node_id"], conflict["node_id"], 34),
    ]
    store.append_transaction(
        [
            goal,
            operation,
            event,
            artifact_old,
            filesystem_artifact,
            async_artifact,
            conflict,
            *base_edges,
        ],
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
    )

    artifact_new = _node(
        ids,
        workspace_id,
        "artifact",
        17,
        status="observed",
        entity_id=shared_artifact_entity,
        metadata=_observation_metadata(
            system_id="transactional",
            boundary_id=transactional_boundary,
            external_kind="record",
            external_id="ticket-1",
            external_revision="rev-2",
            content_hash="d" * 64,
        ),
        state_boundary_id=transactional_boundary,
    )
    decision = _node(ids, workspace_id, "decision", 18, status="resolved")
    store.append_transaction(
        [
            artifact_new,
            decision,
            _edge(
                ids,
                workspace_id,
                "superseded_by",
                artifact_old["node_id"],
                artifact_new["node_id"],
                35,
            ),
            _edge(ids, workspace_id, "resolved_by", conflict["node_id"], decision["node_id"], 36),
        ],
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
    )
    return {
        "goal": goal,
        "operation": operation,
        "event": event,
        "artifact_old": artifact_old,
        "artifact_new": artifact_new,
        "filesystem_artifact": filesystem_artifact,
        "async_artifact": async_artifact,
        "conflict": conflict,
        "decision": decision,
    }


def _assert_projection_contract(result: Any) -> None:
    assert result.authoritative_status == DERIVED_AUTHORITY
    assert result.graph_revision >= 0
    assert result.commit_hash
    assert result.source_node_ids
    assert result.source_query
    assert result.transformation_version
    assert result.policy_version
    assert result.freshness["source_graph_revision"] == result.graph_revision
    assert result.information_loss
    assert result.result_hash


def test_phase13_views_are_revision_bound_source_cited_and_deterministic(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    nodes = _build_phase13_history(store, workspace_id)
    engine = ProjectionEngine(store=store)

    lineage = engine.lineage(nodes["artifact_new"]["node_id"], direction="ancestors")
    lineage_again = engine.lineage(nodes["artifact_new"]["node_id"], direction="ancestors")
    dependency = engine.dependency()
    conflicts = engine.conflict(status=None)
    manifest = engine.manifest()
    progress = engine.progress()
    traceability = engine.traceability()

    for result in (lineage, dependency, conflicts, manifest, progress, traceability):
        _assert_projection_contract(result)

    assert lineage.result_hash == lineage_again.result_hash
    assert nodes["artifact_old"]["node_id"] in lineage.source_node_ids
    lineage_edges = {
        (edge["from_node_id"], edge["to_node_id"]) for edge in lineage.payload["edges"]
    }
    assert (nodes["goal"]["node_id"], nodes["operation"]["node_id"]) in lineage_edges
    assert (nodes["operation"]["node_id"], nodes["artifact_old"]["node_id"]) in lineage_edges
    assert (nodes["artifact_old"]["node_id"], nodes["artifact_new"]["node_id"]) in lineage_edges
    assert dependency.payload["edges"]
    assert conflicts.payload["conflicts"]
    assert engine.conflict().payload["conflicts"] == []
    assert len(manifest.payload["entries"]) == 3
    assert len(manifest.payload["stale_observation_reports"]) == 3
    assert progress.payload["structural_heads"]
    assert progress.payload["blocked"] is False
    assert traceability.payload["edges"]
    assert traceability.payload["blocking_conflicts"] == []
    source = inspect.getsource(ProjectionEngine)
    assert "AdapterHost" not in source
    assert ".invoke(" not in source


def test_manifest_diff_persistence_and_index_regeneration_are_deterministic(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    nodes = _build_phase13_history(store, workspace_id)
    replay_engine = ProjectionEngine(store=store)
    index_engine = ProjectionEngine(store=store, use_index=True)

    old_manifest = replay_engine.manifest(revision=1)
    current_manifest = replay_engine.manifest()
    current_manifest_again = replay_engine.manifest()
    assert old_manifest.result_hash == replay_engine.manifest(revision=1).result_hash
    assert current_manifest.result_hash == current_manifest_again.result_hash
    assert old_manifest.result_hash != current_manifest.result_hash

    persisted = replay_engine.persist(current_manifest)
    assert persisted.path.is_file()
    shutil.rmtree(tmp_path / ".guerilla" / "projections")
    regenerated = replay_engine.manifest()
    assert regenerated.result_hash == current_manifest.result_hash

    SQLiteGraphIndex(tmp_path).path.unlink(missing_ok=True)
    index_manifest = index_engine.manifest()
    assert index_manifest.result_hash == current_manifest.result_hash
    assert SQLiteGraphIndex(tmp_path).status(store.replay()).status == "current"

    diff = replay_engine.diff(left_revision=1)
    _assert_projection_contract(diff)
    assert nodes["artifact_new"]["node_id"] in {
        item["node_id"] for item in diff.payload["added_nodes"]
    }
    assert diff.payload["superseded_nodes"] == [
        {
            "earlier_node_id": nodes["artifact_old"]["node_id"],
            "later_node_id": nodes["artifact_new"]["node_id"],
            "edge_id": next(
                edge["edge_id"]
                for edge in store.replay().edges.values()
                if edge["relationship_type"] == "superseded_by"
            ),
        }
    ]
    assert diff.payload["resolved_conflicts"] == [nodes["conflict"]["node_id"]]


def test_manifest_ambiguity_keeps_external_identity_namespaces_distinct(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    ids = IdentifierGenerator()
    system_id = "external-system"
    boundary_id = deterministic_identifier("state_boundary", 1310)
    artifact_a = _node(
        ids,
        workspace_id,
        "artifact",
        40,
        status="observed",
        metadata=_observation_metadata(
            system_id=system_id,
            boundary_id=boundary_id,
            external_kind="record",
            external_id="shared-id",
            external_revision="rev-a",
            content_hash="e" * 64,
            namespace="ns-a",
        ),
        state_boundary_id=boundary_id,
    )
    artifact_b = _node(
        ids,
        workspace_id,
        "artifact",
        41,
        status="observed",
        metadata=_observation_metadata(
            system_id=system_id,
            boundary_id=boundary_id,
            external_kind="record",
            external_id="shared-id",
            external_revision="rev-b",
            content_hash="f" * 64,
            namespace="ns-b",
        ),
        state_boundary_id=boundary_id,
    )
    store.append_transaction(
        [artifact_a, artifact_b],
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
    )

    manifest = ProjectionEngine(store=store).manifest()
    assert len(manifest.payload["entries"]) == 2
    assert manifest.payload["ambiguity_reports"] == []


def test_later_commits_do_not_change_old_revision_projection_output(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _store(tmp_path, contracts)
    nodes = _build_phase13_history(store, workspace_id)
    engine = ProjectionEngine(store=store)
    old_lineage = engine.lineage(nodes["artifact_old"]["node_id"], revision=1)

    ids = IdentifierGenerator()
    later_event = _node(ids, workspace_id, "event", 200, status="later")
    store.append_transaction(
        [later_event],
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
    )
    assert (
        engine.lineage(nodes["artifact_old"]["node_id"], revision=1).result_hash
        == old_lineage.result_hash
    )
    assert later_event["node_id"] not in old_lineage.source_node_ids
