from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from guerilla.adapters import (
    AdapterHost,
    AdapterOperationRequest,
    AdapterOperationResult,
    AsyncUnknownOutcomeAdapter,
    ReconstructedFilesystemAdapter,
    TransactionalRevisionedServiceAdapter,
    VirtualClock,
)
from guerilla.adapters.errors import AdapterHostError
from guerilla.adapters.synthetic import deterministic_identifier
from guerilla.authority import AuthorityError, BoundaryError
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.index import SQLiteGraphIndex
from guerilla.observability import (
    ObservationIngestionError,
    ObservationIngestionRequest,
    ObservationIngestor,
)
from guerilla.observability.ingestion import PHASE10_METADATA_KEY
from guerilla.storage import GraphStore, StorageError, initialize_workspace, read_payload

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase10-local-user", "actor_kind": "human"}


def _authority(principal_id: str = "local-user") -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": principal_id, "profile": "local-owner-v1"}


def _store(tmp_path: Path, contracts: ContractBundle) -> GraphStore:
    workspace_id = deterministic_identifier("workspace", 1000)
    initialize_workspace(tmp_path, workspace_id=workspace_id, created_at=TS, contracts=contracts)
    return GraphStore(tmp_path, contracts=contracts)


def _request(
    adapter: Any,
    selector: dict[str, Any],
    *,
    principal_id: str = "local-user",
    root: str | None = None,
    namespace: str | None = None,
    correlation_id: str | None = None,
    expected_previous_external_revision: str | None = None,
    payload_bytes: bytes | None = None,
    payload_retention_class: str = "none",
    payload_metadata: dict[str, Any] | None = None,
    redacted: bool = False,
    redaction_policy_version: str | None = None,
    fail_at: str | None = None,
) -> ObservationIngestionRequest:
    return ObservationIngestionRequest(
        adapter_id=adapter.adapter_id,
        state_boundary_id=adapter.boundary_id,
        selector=selector,
        principal_id=principal_id,
        actor=_actor(),
        authority=_authority(principal_id),
        requested_at=TS,
        received_at=TS,
        commit_at=TS,
        correlation_id=correlation_id,
        causation_id="phase10-causation",
        expected_previous_external_revision=expected_previous_external_revision,
        root=root,
        namespace=namespace,
        payload_bytes=payload_bytes,
        payload_media_type="text/plain",
        payload_retention_class=payload_retention_class,  # type: ignore[arg-type]
        payload_metadata={} if payload_metadata is None else payload_metadata,
        redacted=redacted,
        redaction_policy_version=redaction_policy_version,
        fail_at=fail_at,
    )


def _phase10_metadata(node: dict[str, Any]) -> dict[str, Any]:
    metadata = node["metadata"][PHASE10_METADATA_KEY]
    assert isinstance(metadata, dict)
    return metadata


def test_all_synthetic_observations_use_one_ingestion_flow(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    transactional = TransactionalRevisionedServiceAdapter()
    transactional.records["ticket-1"] = {"value": "open", "revision": "rev-1"}
    filesystem = ReconstructedFilesystemAdapter(tmp_path / "fs")
    (filesystem.root / "README.md").write_text("phase 10", encoding="utf-8")
    async_adapter = AsyncUnknownOutcomeAdapter(clock=VirtualClock())
    async_adapter.completed_subjects["job-1"] = "rev-1"
    host = AdapterHost(contracts=contracts, adapters=[transactional, filesystem, async_adapter])
    ingestor = ObservationIngestor(store=store, host=host)

    cases = [
        (transactional, {"subject": "ticket-1"}, None, "transactional", "rev-1"),
        (filesystem, {"path": "README.md"}, str(filesystem.root / "README.md"), "filesystem", None),
        (async_adapter, {"subject": "job-1"}, None, "async", "rev-1"),
    ]
    results = []
    for adapter, selector, root, namespace, expected_revision in cases:
        result = ingestor.ingest(_request(adapter, selector, root=root, namespace=namespace))
        results.append(result)
        assert result.observation_classification == "first_observation"
        if expected_revision is not None:
            assert result.external_revision == expected_revision

    replay = store.replay()
    assert replay.graph_revision == 3
    assert len(replay.nodes) == 9
    assert len(replay.edges) == 9
    for result in results:
        operation = replay.nodes[result.operation_node_id]
        event = replay.nodes[result.event_node_id]
        artifact = replay.nodes[result.artifact_node_id]
        assert operation["node_type"] == "operation"
        assert event["node_type"] == "event"
        assert artifact["node_type"] == "artifact"
        artifact_metadata = _phase10_metadata(artifact)
        assert artifact_metadata["adapter_id"] in {
            transactional.adapter_id,
            filesystem.adapter_id,
            async_adapter.adapter_id,
        }
        assert (
            artifact_metadata["external_identity"]["state_boundary_id"]
            == artifact["state_boundary_id"]
        )
        assert artifact_metadata["graph_commit_time"] == TS
        assert artifact_metadata["payload_retention"]["retention_class"] == "none"

    assert transactional.calls["observe"] == 1
    assert filesystem.calls["observe"] == 1
    assert async_adapter.calls["observe"] == 1
    assert transactional.calls["act"] == filesystem.calls["act"] == async_adapter.calls["act"] == 0
    source = inspect.getsource(ObservationIngestor.ingest).lower()
    assert "transactional" not in source
    assert "filesystem" not in source
    assert "async" not in source


def test_duplicate_conflict_and_ordering_classifications(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    adapter = TransactionalRevisionedServiceAdapter()
    adapter.records["ticket-1"] = {"value": "open", "revision": "rev-1"}
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    ingestor = ObservationIngestor(store=store, host=host)

    first = ingestor.ingest(_request(adapter, {"subject": "ticket-1"}, namespace="transactional"))
    exact = ingestor.ingest(_request(adapter, {"subject": "ticket-1"}, namespace="transactional"))
    duplicate_event = ingestor.ingest(
        _request(
            adapter,
            {"subject": "ticket-1"},
            namespace="transactional",
            correlation_id="correlation-1",
        )
    )
    duplicate_event_repeat = ingestor.ingest(
        _request(
            adapter,
            {"subject": "ticket-1"},
            namespace="transactional",
            correlation_id="correlation-1",
        )
    )
    adapter.records["ticket-1"] = {"value": "changed", "revision": "rev-1"}
    changed = ingestor.ingest(_request(adapter, {"subject": "ticket-1"}, namespace="transactional"))
    adapter.records["ticket-1"] = {"value": "later", "revision": "rev-3"}
    later = ingestor.ingest(_request(adapter, {"subject": "ticket-1"}, namespace="transactional"))
    adapter.records["ticket-1"] = {"value": "stale", "revision": "rev-2"}
    stale = ingestor.ingest(_request(adapter, {"subject": "ticket-1"}, namespace="transactional"))
    adapter.records["ticket-1"] = {"value": "out-of-order", "revision": "rev-4"}
    out_of_order = ingestor.ingest(
        _request(
            adapter,
            {"subject": "ticket-1"},
            namespace="transactional",
            expected_previous_external_revision="rev-1",
        )
    )

    assert first.observation_classification == "first_observation"
    assert exact.observation_classification == "exact_duplicate_observation"
    assert exact.duplicate_of_node_id == first.artifact_node_id
    assert duplicate_event.observation_classification == "exact_duplicate_observation"
    assert duplicate_event_repeat.observation_classification == "duplicate_event"
    assert duplicate_event_repeat.duplicate_of_node_id == duplicate_event.artifact_node_id
    assert changed.observation_classification == "same_revision_changed_content"
    assert later.observation_classification == "first_observation"
    assert stale.observation_classification == "stale_revision"
    assert out_of_order.observation_classification == "out_of_order_event"


def test_absent_revision_unknown_ordering_deletion_rename_and_identity_reuse(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    filesystem = ReconstructedFilesystemAdapter(tmp_path / "fs")
    (filesystem.root / "README.md").write_text("initial", encoding="utf-8")
    host = AdapterHost(contracts=contracts, adapters=[filesystem])
    ingestor = ObservationIngestor(store=store, host=host)

    first = ingestor.ingest(
        _request(
            filesystem,
            {"path": "README.md"},
            root=str(filesystem.root / "README.md"),
            namespace="filesystem",
        )
    )
    (filesystem.root / "README.md").write_text("changed", encoding="utf-8")
    unknown = ingestor.ingest(
        _request(
            filesystem,
            {"path": "README.md"},
            root=str(filesystem.root / "README.md"),
            namespace="filesystem",
        )
    )
    deleted = ingestor.ingest(
        _request(
            filesystem,
            {"path": "missing.md"},
            root=str(filesystem.root / "missing.md"),
            namespace="filesystem",
        )
    )

    async_adapter = AsyncUnknownOutcomeAdapter(clock=VirtualClock())
    async_host = AdapterHost(contracts=contracts, adapters=[async_adapter])
    async_ingestor = ObservationIngestor(store=store, host=async_host)
    absent = async_ingestor.ingest(
        _request(async_adapter, {"subject": "not-done"}, namespace="async")
    )

    class LifecycleAdapter(TransactionalRevisionedServiceAdapter):
        def __init__(self, lifecycle_state: str) -> None:
            super().__init__(seed=800)
            self.lifecycle_state = lifecycle_state
            self.records["ticket-2"] = {"value": lifecycle_state, "revision": "rev-1"}

        def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
            result = super().observe(request)
            assert result.external_identity is not None
            identity = dict(result.external_identity)
            identity["lifecycle_state"] = self.lifecycle_state
            return replace(result, external_identity=identity)

    rename_adapter = LifecycleAdapter("renamed")
    rename_host = AdapterHost(contracts=contracts, adapters=[rename_adapter])
    rename = ObservationIngestor(store=store, host=rename_host).ingest(
        _request(rename_adapter, {"subject": "ticket-2"}, namespace="transactional")
    )
    reuse_adapter = LifecycleAdapter("reused")
    reuse_host = AdapterHost(contracts=contracts, adapters=[reuse_adapter])
    reuse = ObservationIngestor(store=store, host=reuse_host).ingest(
        _request(reuse_adapter, {"subject": "ticket-2"}, namespace="transactional")
    )

    assert first.observation_classification == "first_observation"
    assert unknown.observation_classification == "unknown_ordering"
    assert deleted.observation_classification == "deletion"
    assert absent.observation_classification == "absent_external_revision"
    assert rename.observation_classification == "rename"
    assert reuse.observation_classification == "identity_reuse"


def test_payload_retention_metadata_and_redaction_are_preserved(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    adapter = TransactionalRevisionedServiceAdapter()
    adapter.records["ticket-1"] = {"value": "open", "revision": "rev-1"}
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    ingestor = ObservationIngestor(store=store, host=host)

    retained = ingestor.ingest(
        _request(
            adapter,
            {"subject": "ticket-1"},
            namespace="transactional",
            payload_bytes=b"redacted payload",
            payload_retention_class="content_addressed",
            payload_metadata={"retained": "after-redaction"},
            redacted=True,
            redaction_policy_version="phase10-redaction-v1",
        )
    )
    metadata_only = ingestor.ingest(
        _request(
            adapter,
            {"subject": "ticket-1"},
            namespace="transactional",
            payload_retention_class="metadata",
            payload_metadata={"payload": "metadata-only"},
        )
    )

    replay = store.replay()
    retained_payload_ref = replay.nodes[retained.artifact_node_id]["payload_ref"]
    assert retained_payload_ref["retention_class"] == "content_addressed"
    assert retained_payload_ref["redacted"] is True
    assert retained_payload_ref["redaction_policy_version"] == "phase10-redaction-v1"
    assert retained_payload_ref["metadata"] == {"retained": "after-redaction"}
    assert read_payload(tmp_path, retained_payload_ref["payload_hash"]) == b"redacted payload"
    metadata_payload_ref = replay.nodes[metadata_only.artifact_node_id]["payload_ref"]
    assert metadata_payload_ref == {
        "retention_class": "metadata",
        "metadata": {"payload": "metadata-only"},
    }


def test_failures_do_not_append_and_happen_before_unsafe_invocation(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    adapter = TransactionalRevisionedServiceAdapter()
    adapter.records["ticket-1"] = {"value": "open", "revision": "rev-1"}
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    ingestor = ObservationIngestor(store=store, host=host)

    with pytest.raises(AuthorityError):
        ingestor.ingest(
            _request(
                adapter,
                {"subject": "ticket-1"},
                principal_id="intruder",
                namespace="transactional",
            )
        )
    assert adapter.calls["observe"] == 0
    assert store.replay().graph_revision == 0

    filesystem = ReconstructedFilesystemAdapter(tmp_path / "fs")
    filesystem_host = AdapterHost(contracts=contracts, adapters=[filesystem])
    filesystem_ingestor = ObservationIngestor(store=store, host=filesystem_host)
    with pytest.raises(BoundaryError):
        filesystem_ingestor.ingest(
            _request(
                filesystem,
                {"path": "x.txt"},
                root=str(tmp_path / "outside" / "x.txt"),
                namespace="filesystem",
            )
        )
    assert filesystem.calls["observe"] == 0
    assert store.replay().graph_revision == 0

    class RaisingAdapter(TransactionalRevisionedServiceAdapter):
        def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
            raise RuntimeError("synthetic observe failure")

    raising = RaisingAdapter(seed=810)
    raising_host = AdapterHost(contracts=contracts, adapters=[raising])
    with pytest.raises(AdapterHostError) as adapter_error:
        ObservationIngestor(store=store, host=raising_host).ingest(
            _request(raising, {"subject": "ticket-1"}, namespace="transactional")
        )
    assert adapter_error.value.code == "adapter_error"
    assert store.replay().graph_revision == 0

    class MissingProvenanceAdapter(TransactionalRevisionedServiceAdapter):
        def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
            return replace(super().observe(request), evidence={})

    missing = MissingProvenanceAdapter(seed=820)
    missing.records["ticket-1"] = {"value": "open", "revision": "rev-1"}
    missing_host = AdapterHost(contracts=contracts, adapters=[missing])
    with pytest.raises(ObservationIngestionError) as missing_error:
        ObservationIngestor(store=store, host=missing_host).ingest(
            _request(missing, {"subject": "ticket-1"}, namespace="transactional")
        )
    assert missing_error.value.code == "incomplete_lineage"
    assert store.replay().graph_revision == 0

    class MissingIdentityAdapter(TransactionalRevisionedServiceAdapter):
        def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
            return replace(super().observe(request), external_identity=None)

    missing_identity = MissingIdentityAdapter(seed=830)
    missing_identity.records["ticket-1"] = {"value": "open", "revision": "rev-1"}
    missing_identity_host = AdapterHost(contracts=contracts, adapters=[missing_identity])
    with pytest.raises(ObservationIngestionError) as identity_error:
        ObservationIngestor(store=store, host=missing_identity_host).ingest(
            _request(missing_identity, {"subject": "ticket-1"}, namespace="transactional")
        )
    assert identity_error.value.code == "incomplete_lineage"
    assert store.replay().graph_revision == 0

    with pytest.raises(StorageError) as injected:
        ingestor.ingest(
            _request(
                adapter,
                {"subject": "ticket-1"},
                namespace="transactional",
                fail_at="after_stage",
            )
        )
    assert injected.value.code == "injected_failure"
    assert store.replay().graph_revision == 0


def test_replay_and_index_rebuild_do_not_invoke_adapters(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    store = _store(tmp_path, contracts)
    adapter = TransactionalRevisionedServiceAdapter()
    adapter.records["ticket-1"] = {"value": "open", "revision": "rev-1"}
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    result = ObservationIngestor(store=store, host=host).ingest(
        _request(adapter, {"subject": "ticket-1"}, namespace="transactional")
    )
    calls_after_ingest = dict(adapter.calls)

    replay = GraphStore(tmp_path, contracts=contracts).replay()
    assert adapter.calls == calls_after_ingest
    index = SQLiteGraphIndex(tmp_path)
    if index.path.exists():
        index.path.unlink()
    assert index.status(replay).status == "missing"
    index.rebuild(replay)
    assert adapter.calls == calls_after_ingest
    assert index.status(replay).status == "current"
    indexed_artifact = index.query().node(result.artifact_node_id).items[0]
    assert _phase10_metadata(indexed_artifact)["content_hash"] == result.content_hash
