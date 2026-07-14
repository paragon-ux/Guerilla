from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from guerilla.authority import (
    REGISTRY_METADATA_KEY,
    AdapterIdentityRegistry,
    AuthorityError,
    BoundaryError,
    BoundaryRegistry,
    ExternalIdentityRegistry,
    IdentityConflictError,
    LocalAuthorizationProfile,
)
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.graph import GraphQuery
from guerilla.identity import IdentifierGenerator
from guerilla.index import SQLiteGraphIndex
from guerilla.storage import GraphStore, initialize_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor(actor_id: str = "phase8-local-user") -> dict[str, Any]:
    return {"actor_id": actor_id, "actor_kind": "human"}


def _authority(principal_id: str = "local-user") -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": principal_id, "profile": "local-owner-v1"}


def _node(
    ids: IdentifierGenerator,
    workspace_id: str,
    *,
    node_type: str = "decision",
    metadata: dict[str, Any] | None = None,
    authority: dict[str, Any] | None = None,
    random_b: int,
) -> dict[str, Any]:
    return {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": workspace_id,
        "node_id": str(ids.generate("node", now_ms=1_721_000_200_000, random_b=random_b)),
        "entity_id": str(ids.generate("entity", now_ms=1_721_000_200_001, random_b=random_b)),
        "node_type": node_type,
        "created_at": TS,
        "actor": _actor(),
        "authority": _authority() if authority is None else authority,
        "status": "open",
        "provenance": {"source": "phase8-test", "source_record_ids": []},
        "payload_ref": {"retention_class": "none"},
        "metadata": {} if metadata is None else metadata,
        "extensions": {},
    }


def _initialized_store(tmp_path: Path, contracts: ContractBundle) -> tuple[GraphStore, str]:
    ids = IdentifierGenerator()
    workspace_id = str(ids.generate("workspace", now_ms=1_721_000_200_010, random_b=1))
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts), workspace_id


def _append(
    store: GraphStore,
    members: list[dict[str, Any]],
    *,
    principal_id: str = "local-user",
) -> None:
    store.append_transaction(
        members,
        actor=_actor(),
        created_at=TS,
        committed_at=TS,
        principal_id=principal_id,
    )


def _boundary(
    ids: IdentifierGenerator,
    *,
    system_id: str | None = None,
    operations: list[str] | None = None,
    roots: list[str] | None = None,
    endpoints: list[str] | None = None,
    namespaces: list[str] | None = None,
    random_b: int,
) -> dict[str, Any]:
    return {
        "state_boundary_id": str(
            ids.generate("state_boundary", now_ms=1_721_000_200_020, random_b=random_b)
        ),
        "system_id": system_id
        or str(ids.generate("external_system", now_ms=1_721_000_200_021, random_b=random_b)),
        "name": f"boundary-{random_b}",
        "system_of_record": True,
        "continuity_mode": "reconstructed",
        "ownership": "external_application_state",
        "permitted_operations": ["observe"] if operations is None else operations,
        "permitted_roots": [] if roots is None else roots,
        "permitted_endpoints": [] if endpoints is None else endpoints,
        "resource_namespaces": [] if namespaces is None else namespaces,
        "lineage_crossing": "intent_before_action",
        "conflict_behavior": "require_reconciliation",
        "extensions": {},
    }


def _external_identity(
    ids: IdentifierGenerator,
    boundary: dict[str, Any],
    *,
    external_id: str,
    revision: str | None,
) -> dict[str, Any]:
    identity = {
        "system_id": boundary["system_id"],
        "state_boundary_id": boundary["state_boundary_id"],
        "external_kind": "file",
        "external_id": external_id,
        "namespace": "repo",
        "metadata": {},
    }
    if revision is not None:
        identity["external_revision"] = revision
    return identity


def test_local_authorization_owner_and_non_owner_reads_and_appends(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    profile = LocalAuthorizationProfile(owner_principal_id="local-user")
    assert profile.require("local-user", "graph.append").allowed is True
    with pytest.raises(AuthorityError) as denied:
        profile.require("intruder", "graph.append")
    assert denied.value.code == "unauthorized"

    store, workspace_id = _initialized_store(tmp_path, contracts)
    node = _node(IdentifierGenerator(), workspace_id, random_b=10)
    with pytest.raises(AuthorityError):
        _append(store, [node], principal_id="intruder")
    assert store.replay().graph_revision == 0

    _append(store, [node], principal_id="local-user")
    with pytest.raises(AuthorityError):
        GraphQuery(store.replay(), principal_id="intruder")


def test_actor_and_record_authority_cannot_escalate_append(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = IdentifierGenerator()
    node_claiming_other_principal = _node(
        ids,
        workspace_id,
        authority=_authority("intruder"),
        random_b=20,
    )

    with pytest.raises(AuthorityError) as excinfo:
        _append(store, [node_claiming_other_principal], principal_id="local-user")

    assert excinfo.value.code == "authority_escalation"
    assert store.replay().graph_revision == 0


def test_boundary_operations_scope_and_ambiguous_writers(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    ids = IdentifierGenerator()
    boundary = _boundary(
        ids,
        operations=["observe", "act"],
        roots=[str(tmp_path / "allowed")],
        endpoints=["https://example.test/api"],
        namespaces=["repo"],
        random_b=30,
    )
    registry = BoundaryRegistry(contracts=contracts)
    registry.register(boundary)
    registry.require_operation(
        boundary["state_boundary_id"], "act", root=str(tmp_path / "allowed" / "a.txt")
    )
    registry.require_operation(
        boundary["state_boundary_id"],
        "observe",
        endpoint="https://example.test/api",
        namespace="repo",
    )
    with pytest.raises(BoundaryError) as escape:
        registry.require_operation(
            boundary["state_boundary_id"], "act", root=str(tmp_path / "other")
        )
    assert escape.value.code == "state_boundary_violation"

    read_overlap = _boundary(
        ids,
        system_id=boundary["system_id"],
        operations=["observe"],
        namespaces=["repo"],
        random_b=31,
    )
    registry.register(read_overlap)
    competing_writer = _boundary(
        ids,
        system_id=boundary["system_id"],
        operations=["act"],
        namespaces=["repo"],
        random_b=32,
    )
    with pytest.raises(BoundaryError) as ambiguous:
        registry.register(competing_writer)
    assert ambiguous.value.code == "ambiguous_authority"


def test_adapter_identity_registration_declares_but_does_not_invoke(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    ids = IdentifierGenerator()
    boundary = _boundary(ids, operations=["observe"], namespaces=["repo"], random_b=40)
    boundary_registry = BoundaryRegistry(contracts=contracts)
    boundary_registry.register(boundary)
    adapter_registry = AdapterIdentityRegistry(
        contracts=contracts,
        boundary_registry=boundary_registry,
    )
    descriptor = {
        "adapter_id": str(ids.generate("adapter", now_ms=1_721_000_200_030, random_b=41)),
        "system_id": boundary["system_id"],
        "name": "phase8 descriptor",
        "version": "0.2.0",
        "trust_model": "trusted_in_process_python",
        "state_boundaries": [boundary],
        "capabilities": [
            {
                "capability": "observe",
                "supported": True,
                "state_boundary_ids": [boundary["state_boundary_id"]],
            }
        ],
        "authentication": {"required": False, "credential_storage": "none"},
        "limitations": ["registration only"],
        "extensions": {},
    }

    adapter_registry.register(descriptor)

    assert descriptor["adapter_id"] in adapter_registry.adapters
    assert not hasattr(adapter_registry, "invoke")


def test_external_identity_lifecycle_preserves_revisions_and_conflicts(
    contracts: ContractBundle,
) -> None:
    ids = IdentifierGenerator()
    boundary = _boundary(ids, operations=["observe"], namespaces=["repo"], random_b=50)
    registry = ExternalIdentityRegistry(contracts=contracts)
    first = _external_identity(ids, boundary, external_id="README.md", revision="abc123")
    renamed = _external_identity(ids, boundary, external_id="README-renamed.md", revision="def456")
    no_revision = _external_identity(ids, boundary, external_id="LICENSE", revision=None)

    registry.record_observed(first)
    registry.record_observed(no_revision)
    registry.record_renamed(first, renamed)
    registry.record_deleted(renamed)

    assert any(item.get("external_revision") == "abc123" for item in registry.identities.values())
    assert any(item.get("external_id") == "LICENSE" for item in registry.identities.values())
    assert any(
        item.get("external_id") == "README-renamed.md" for item in registry.identities.values()
    )
    assert any(item.get("lifecycle_state") == "deleted" for item in registry.identities.values())
    with pytest.raises(IdentityConflictError) as reused:
        registry.record_reused(first)
    assert reused.value.code == "identity_collision"
    with pytest.raises(IdentityConflictError) as alias:
        registry.record_alias(first, renamed)
    assert alias.value.code == "alias_requires_reified_assertion"
    registry.record_alias(
        first, renamed, decision_node_id="grn_018f1f8e-5d4b-7a10-8a20-0c9b0b23c003"
    )
    assert any(
        "decision_node_id" in item.get("metadata", {}) for item in registry.identities.values()
    )


def test_committed_boundary_registry_replays_and_indexes(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store, workspace_id = _initialized_store(tmp_path, contracts)
    ids = IdentifierGenerator()
    boundary = _boundary(
        ids,
        operations=["observe"],
        roots=[str(tmp_path / "observed")],
        namespaces=["repo"],
        random_b=60,
    )
    registry_node = _node(
        ids,
        workspace_id,
        metadata={REGISTRY_METADATA_KEY: {"kind": "state_boundary", "value": boundary}},
        random_b=61,
    )
    _append(store, [registry_node])
    replay = store.replay()
    replay_registry = BoundaryRegistry.from_replay(replay, contracts)
    index_replay = SQLiteGraphIndex(tmp_path).to_replay_result()
    index_registry = BoundaryRegistry.from_replay(index_replay, contracts)

    assert boundary["state_boundary_id"] in replay_registry.boundaries
    assert index_registry.boundaries == replay_registry.boundaries
