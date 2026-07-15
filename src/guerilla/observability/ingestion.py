"""Observation ingestion into the authoritative graph."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from guerilla.adapters import AdapterHost, AdapterOperationRequest, AdapterOperationResult
from guerilla.codec import canonical_bytes, payload_hash
from guerilla.storage import GraphStore
from guerilla.storage.payload_store import write_payload

ObservationClassification = Literal[
    "first_observation",
    "exact_duplicate_observation",
    "duplicate_event",
    "same_revision_changed_content",
    "stale_revision",
    "out_of_order_event",
    "unknown_ordering",
    "absent_external_revision",
    "incomplete_adapter_lineage",
    "rename",
    "deletion",
    "identity_reuse",
]

PHASE10_METADATA_KEY = "guerilla_phase10_observation"


class ObservationIngestionError(ValueError):
    """Raised when an observation cannot be safely normalized."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ObservationIngestionRequest:
    """Validated observe-only request consumed by the ingestion path."""

    adapter_id: str
    state_boundary_id: str
    selector: dict[str, Any]
    principal_id: str
    actor: dict[str, Any]
    authority: dict[str, Any]
    requested_at: str
    received_at: str
    commit_at: str
    operation_id: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    expected_previous_external_revision: str | None = None
    root: str | None = None
    endpoint: str | None = None
    namespace: str | None = None
    timeout_ms: int = 1_000
    deadline_ms: int | None = None
    payload_bytes: bytes | None = None
    payload_media_type: str = "application/octet-stream"
    payload_retention_class: Literal["none", "metadata", "content_addressed"] = "none"
    payload_metadata: dict[str, Any] = field(default_factory=dict)
    redacted: bool = False
    redaction_policy_version: str | None = None
    freshness: str = "observed_at_request_time"
    consistency: str = "adapter_declared"
    extensions: dict[str, Any] = field(default_factory=dict)
    fail_at: str | None = None


@dataclass(frozen=True, slots=True)
class ObservationIngestionResult:
    """Derived, non-authoritative response for one committed observation."""

    workspace_id: str
    graph_revision: int
    commit_hash: str
    transaction_id: str
    operation_node_id: str
    event_node_id: str
    artifact_node_id: str
    observation_classification: ObservationClassification
    external_identity: dict[str, Any]
    external_revision: str | None
    content_hash: str
    previous_artifact_node_id: str | None = None
    duplicate_of_node_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ObservationIngestor:
    """Normalize trusted adapter observations into one graph transaction."""

    def __init__(self, *, store: GraphStore, host: AdapterHost) -> None:
        self.store = store
        self.host = host

    def ingest(self, request: ObservationIngestionRequest) -> ObservationIngestionResult:
        replay_before = self.store.replay()
        descriptor = self.host.descriptor(request.adapter_id)
        system_id = str(descriptor["system_id"])
        adapter_version = str(descriptor["version"])
        operation_id = request.operation_id or str(self.store.ids.generate("message"))
        observe_contract = {
            "operation_type": "adapter.observe",
            "adapter_id": request.adapter_id,
            "system_id": system_id,
            "state_boundary_id": request.state_boundary_id,
            "actor": request.actor,
            "authority": request.authority,
            "requested_at": request.requested_at,
            "selector": request.selector,
            "extensions": request.extensions,
        }
        self.store.contracts.assert_valid("adapter_observe.schema.json", observe_contract)
        adapter_request = AdapterOperationRequest(
            workspace_id=replay_before.workspace_id,
            adapter_id=request.adapter_id,
            adapter_version=adapter_version,
            system_id=system_id,
            state_boundary_id=request.state_boundary_id,
            operation_id=operation_id,
            principal_id=request.principal_id,
            actor=request.actor,
            authority=request.authority,
            contract_version="0.2.0",
            requested_at=request.requested_at,
            capability="observe",
            data=request.selector,
            deadline_ms=request.deadline_ms,
            timeout_ms=request.timeout_ms,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            root=request.root,
            endpoint=request.endpoint,
            namespace=request.namespace,
            extensions=request.extensions,
        )
        adapter_result = self.host.invoke(adapter_request)
        normalized = self._normalize_result(
            request=request,
            adapter_result=adapter_result,
            descriptor=descriptor,
            workspace_id=replay_before.workspace_id,
            operation_id=operation_id,
            replay_before=replay_before,
        )
        commit = self.store.append_transaction(
            normalized.members,
            actor=request.actor,
            created_at=request.received_at,
            committed_at=request.commit_at,
            principal_id=request.principal_id,
            fail_at=request.fail_at,
        )
        return ObservationIngestionResult(
            workspace_id=replay_before.workspace_id,
            graph_revision=int(commit["graph_revision"]),
            commit_hash=str(commit["commit_hash"]),
            transaction_id=str(commit["transaction_id"]),
            operation_node_id=normalized.operation_node_id,
            event_node_id=normalized.event_node_id,
            artifact_node_id=normalized.artifact_node_id,
            observation_classification=normalized.classification,
            external_identity=normalized.external_identity,
            external_revision=normalized.external_revision,
            content_hash=normalized.content_hash,
            previous_artifact_node_id=normalized.previous_artifact_node_id,
            duplicate_of_node_id=normalized.duplicate_of_node_id,
        )

    def _normalize_result(
        self,
        *,
        request: ObservationIngestionRequest,
        adapter_result: AdapterOperationResult,
        descriptor: dict[str, Any],
        workspace_id: str,
        operation_id: str,
        replay_before: Any,
    ) -> _NormalizedObservation:
        if adapter_result.classification != "observed":
            raise ObservationIngestionError(
                "adapter_error",
                "observe result must be classified as observed",
            )
        if not adapter_result.evidence:
            raise ObservationIngestionError(
                "incomplete_lineage",
                "observation result must include provenance evidence",
            )
        if adapter_result.external_identity is None:
            raise ObservationIngestionError(
                "incomplete_lineage",
                "observation result must include an external identity",
            )
        external_identity = dict(adapter_result.external_identity)
        self.store.contracts.assert_valid("external_identity.schema.json", external_identity)
        external_revision = adapter_result.external_revision
        if external_revision is None and "external_revision" in external_identity:
            external_revision = str(external_identity["external_revision"])
        payload_ref = self._payload_ref(request, adapter_result)
        content = {
            "data": adapter_result.data,
            "evidence": adapter_result.evidence,
            "external_identity": external_identity,
            "external_revision": external_revision,
            "payload_ref": payload_ref,
        }
        content_hash = payload_hash(canonical_bytes(content))
        previous = _find_previous_observations(replay_before, external_identity)
        classification, previous_artifact_id, duplicate_of_id = _classify_observation(
            previous=previous,
            external_identity=external_identity,
            external_revision=external_revision,
            content_hash=content_hash,
            correlation_id=request.correlation_id,
            expected_previous_external_revision=request.expected_previous_external_revision,
        )
        operation_node_id = str(self.store.ids.generate("node"))
        event_node_id = str(self.store.ids.generate("node"))
        artifact_node_id = str(self.store.ids.generate("node"))
        operation_entity_id = str(self.store.ids.generate("entity"))
        event_entity_id = str(self.store.ids.generate("entity"))
        artifact_entity_id = str(self.store.ids.generate("entity"))
        operation_node = self._node(
            workspace_id=workspace_id,
            node_id=operation_node_id,
            entity_id=operation_entity_id,
            node_type="operation",
            created_at=request.received_at,
            actor=request.actor,
            authority=request.authority,
            status="completed",
            provenance={
                "source": "guerilla.phase10.observation_ingestion",
                "source_record_ids": [],
                "metadata": {"operation_id": operation_id},
            },
            payload_ref={"retention_class": "none"},
            metadata={
                PHASE10_METADATA_KEY: {
                    "kind": "bounded_observation_operation",
                    "adapter_id": adapter_result.adapter_id,
                    "adapter_version": adapter_result.adapter_version,
                    "system_id": adapter_result.system_id,
                    "state_boundary_id": adapter_result.state_boundary_id,
                    "selector": request.selector,
                    "correlation_id": request.correlation_id,
                    "causation_id": request.causation_id,
                }
            },
        )
        event_node = self._node(
            workspace_id=workspace_id,
            node_id=event_node_id,
            entity_id=event_entity_id,
            node_type="event",
            created_at=request.received_at,
            actor=request.actor,
            authority=request.authority,
            status="observed",
            provenance={
                "source": "adapter.observe",
                "source_record_ids": [operation_node_id],
                "causation_id": operation_node_id,
                "observed_at": adapter_result.occurred_at,
                "external_identity": external_identity,
                "metadata": {
                    "adapter_evidence": adapter_result.evidence,
                    "local_receipt_time": request.received_at,
                },
            },
            payload_ref={"retention_class": "none"},
            metadata={
                PHASE10_METADATA_KEY: {
                    "kind": "observation_event",
                    "operation_id": operation_id,
                    "adapter_id": adapter_result.adapter_id,
                    "adapter_version": adapter_result.adapter_version,
                    "system_id": adapter_result.system_id,
                    "state_boundary_id": adapter_result.state_boundary_id,
                    "external_revision": external_revision,
                    "external_effective_time": adapter_result.occurred_at,
                    "local_receipt_time": request.received_at,
                    "graph_commit_time": request.commit_at,
                    "correlation_id": request.correlation_id,
                    "causation_id": request.causation_id,
                    "classification": classification,
                    "freshness": request.freshness,
                    "consistency": request.consistency,
                    "warnings": list(adapter_result.warnings),
                    "limitations": list(adapter_result.limitations),
                }
            },
            effective_at=adapter_result.occurred_at,
            state_boundary_id=request.state_boundary_id,
        )
        artifact_node = self._node(
            workspace_id=workspace_id,
            node_id=artifact_node_id,
            entity_id=artifact_entity_id,
            node_type="artifact",
            created_at=request.received_at,
            actor=request.actor,
            authority=request.authority,
            status=classification,
            provenance={
                "source": "adapter.observe",
                "source_record_ids": [event_node_id],
                "causation_id": event_node_id,
                "observed_at": adapter_result.occurred_at,
                "external_identity": external_identity,
                "metadata": {
                    "adapter_evidence": adapter_result.evidence,
                    "adapter_result_data": adapter_result.data,
                },
            },
            payload_ref=payload_ref,
            metadata={
                PHASE10_METADATA_KEY: {
                    "kind": "external_state_revision",
                    "adapter_id": adapter_result.adapter_id,
                    "adapter_version": adapter_result.adapter_version,
                    "system_id": adapter_result.system_id,
                    "state_boundary_id": adapter_result.state_boundary_id,
                    "external_identity": external_identity,
                    "external_identity_key": _identity_key(external_identity),
                    "external_revision": external_revision,
                    "content_hash": content_hash,
                    "classification": classification,
                    "previous_artifact_node_id": previous_artifact_id,
                    "duplicate_of_node_id": duplicate_of_id,
                    "external_effective_time": adapter_result.occurred_at,
                    "local_receipt_time": request.received_at,
                    "graph_commit_time": request.commit_at,
                    "correlation_id": request.correlation_id,
                    "causation_id": request.causation_id,
                    "freshness": request.freshness,
                    "consistency": request.consistency,
                    "payload_retention": payload_ref,
                    "warnings": list(adapter_result.warnings),
                    "limitations": list(adapter_result.limitations),
                    "descriptor_system_type": descriptor.get("system_type"),
                }
            },
            effective_at=adapter_result.occurred_at,
            state_boundary_id=request.state_boundary_id,
        )
        edges = [
            self._edge(
                workspace_id=workspace_id,
                relationship_type="causes",
                from_node_id=operation_node_id,
                to_node_id=event_node_id,
                created_at=request.received_at,
                actor=request.actor,
                source_record_ids=[operation_node_id, event_node_id],
                metadata={"kind": "observation_operation_caused_event"},
            ),
            self._edge(
                workspace_id=workspace_id,
                relationship_type="produces",
                from_node_id=event_node_id,
                to_node_id=artifact_node_id,
                created_at=request.received_at,
                actor=request.actor,
                source_record_ids=[event_node_id, artifact_node_id],
                metadata={"kind": "observation_event_produced_external_revision"},
            ),
            self._edge(
                workspace_id=workspace_id,
                relationship_type="evidences",
                from_node_id=event_node_id,
                to_node_id=artifact_node_id,
                created_at=request.received_at,
                actor=request.actor,
                source_record_ids=[event_node_id, artifact_node_id],
                metadata={"kind": "observation_event_evidences_external_revision"},
            ),
        ]
        if previous_artifact_id is not None and previous_artifact_id != artifact_node_id:
            edges.append(
                self._edge(
                    workspace_id=workspace_id,
                    relationship_type="superseded_by",
                    from_node_id=previous_artifact_id,
                    to_node_id=artifact_node_id,
                    created_at=request.received_at,
                    actor=request.actor,
                    source_record_ids=[previous_artifact_id, artifact_node_id],
                    metadata={
                        "kind": "external_revision_followup",
                        "classification": classification,
                    },
                )
            )
        return _NormalizedObservation(
            members=[operation_node, event_node, artifact_node, *edges],
            operation_node_id=operation_node_id,
            event_node_id=event_node_id,
            artifact_node_id=artifact_node_id,
            classification=classification,
            external_identity=external_identity,
            external_revision=external_revision,
            content_hash=content_hash,
            previous_artifact_node_id=previous_artifact_id,
            duplicate_of_node_id=duplicate_of_id,
        )

    def _payload_ref(
        self,
        request: ObservationIngestionRequest,
        adapter_result: AdapterOperationResult,
    ) -> dict[str, Any]:
        if request.payload_retention_class == "content_addressed":
            if request.payload_bytes is None:
                raise ObservationIngestionError(
                    "payload_hash_mismatch",
                    "content-addressed observation payload bytes are required",
                )
            digest = write_payload(self.store.root, request.payload_bytes)
            payload_ref: dict[str, Any] = {
                "retention_class": "content_addressed",
                "payload_hash": digest,
                "media_type": request.payload_media_type,
                "size_bytes": len(request.payload_bytes),
                "redacted": request.redacted,
            }
        elif request.payload_retention_class == "metadata":
            payload_ref = {"retention_class": "metadata"}
        else:
            payload_ref = (
                {"retention_class": "none"}
                if adapter_result.payload_ref is None
                else dict(adapter_result.payload_ref)
            )
        if request.redaction_policy_version is not None:
            payload_ref["redaction_policy_version"] = request.redaction_policy_version
        if request.payload_metadata:
            payload_ref["metadata"] = dict(request.payload_metadata)
        if request.redacted and "redacted" not in payload_ref:
            payload_ref["redacted"] = True
        self.store.contracts.assert_valid("payload_ref.schema.json", payload_ref)
        return payload_ref

    def _node(
        self,
        *,
        workspace_id: str,
        node_id: str,
        entity_id: str,
        node_type: str,
        created_at: str,
        actor: dict[str, Any],
        authority: dict[str, Any],
        status: str,
        provenance: dict[str, Any],
        payload_ref: dict[str, Any],
        metadata: dict[str, Any],
        effective_at: str | None = None,
        state_boundary_id: str | None = None,
    ) -> dict[str, Any]:
        node: dict[str, Any] = {
            "record_type": "node",
            "protocol_version": "0.2.0",
            "workspace_id": workspace_id,
            "node_id": node_id,
            "entity_id": entity_id,
            "node_type": node_type,
            "created_at": created_at,
            "actor": actor,
            "authority": authority,
            "status": status,
            "provenance": provenance,
            "payload_ref": payload_ref,
            "metadata": metadata,
            "extensions": {},
            "record_hash": "0" * 64,
        }
        if effective_at is not None:
            node["effective_at"] = effective_at
        if state_boundary_id is not None:
            node["state_boundary_id"] = state_boundary_id
        return node

    def _edge(
        self,
        *,
        workspace_id: str,
        relationship_type: str,
        from_node_id: str,
        to_node_id: str,
        created_at: str,
        actor: dict[str, Any],
        source_record_ids: list[str],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "record_type": "edge",
            "protocol_version": "0.2.0",
            "workspace_id": workspace_id,
            "edge_id": str(self.store.ids.generate("edge")),
            "relationship_type": relationship_type,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "created_at": created_at,
            "actor": actor,
            "provenance": {
                "source": "guerilla.phase10.observation_ingestion",
                "source_record_ids": source_record_ids,
            },
            "metadata": {PHASE10_METADATA_KEY: metadata},
            "extensions": {},
            "record_hash": "0" * 64,
        }


@dataclass(frozen=True, slots=True)
class _PreviousObservation:
    node_id: str
    external_revision: str | None
    content_hash: str
    correlation_id: str | None
    graph_revision: int


@dataclass(frozen=True, slots=True)
class _NormalizedObservation:
    members: list[dict[str, Any]]
    operation_node_id: str
    event_node_id: str
    artifact_node_id: str
    classification: ObservationClassification
    external_identity: dict[str, Any]
    external_revision: str | None
    content_hash: str
    previous_artifact_node_id: str | None
    duplicate_of_node_id: str | None


def _find_previous_observations(
    replay: Any, external_identity: dict[str, Any]
) -> list[_PreviousObservation]:
    key = _identity_key(external_identity)
    previous: list[_PreviousObservation] = []
    for node_id, node in replay.nodes.items():
        metadata = node.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        observation = metadata.get(PHASE10_METADATA_KEY)
        if not isinstance(observation, dict):
            continue
        if observation.get("kind") != "external_state_revision":
            continue
        if observation.get("external_identity_key") != key:
            continue
        previous.append(
            _PreviousObservation(
                node_id=str(node_id),
                external_revision=_optional_str(observation.get("external_revision")),
                content_hash=str(observation["content_hash"]),
                correlation_id=_optional_str(observation.get("correlation_id")),
                graph_revision=int(replay.record_revisions[str(node_id)]),
            )
        )
    previous.sort(key=lambda item: (item.graph_revision, item.node_id))
    return previous


def _classify_observation(
    *,
    previous: list[_PreviousObservation],
    external_identity: dict[str, Any],
    external_revision: str | None,
    content_hash: str,
    correlation_id: str | None,
    expected_previous_external_revision: str | None,
) -> tuple[ObservationClassification, str | None, str | None]:
    lifecycle = external_identity.get("lifecycle_state")
    previous_latest = previous[-1] if previous else None
    previous_artifact_id = None if previous_latest is None else previous_latest.node_id
    if lifecycle == "renamed":
        return "rename", previous_artifact_id, None
    if lifecycle == "deleted":
        return "deletion", previous_artifact_id, None
    if lifecycle == "reused":
        return "identity_reuse", previous_artifact_id, None
    if external_revision is None:
        return "absent_external_revision", previous_artifact_id, None
    if not previous:
        return "first_observation", None, None
    if correlation_id is not None:
        for item in previous:
            if item.correlation_id == correlation_id:
                return "duplicate_event", item.node_id, item.node_id
    for item in previous:
        if item.external_revision == external_revision and item.content_hash == content_hash:
            return "exact_duplicate_observation", item.node_id, item.node_id
        if item.external_revision == external_revision and item.content_hash != content_hash:
            return "same_revision_changed_content", item.node_id, None
    if (
        expected_previous_external_revision is not None
        and previous_latest is not None
        and previous_latest.external_revision != expected_previous_external_revision
    ):
        return "out_of_order_event", previous_latest.node_id, None
    current_rank = _revision_rank(external_revision)
    previous_ranks = [
        rank
        for rank in (_revision_rank(item.external_revision) for item in previous)
        if rank is not None
    ]
    if current_rank is None or not previous_ranks:
        return "unknown_ordering", previous_artifact_id, None
    if current_rank < max(previous_ranks):
        return "stale_revision", previous_artifact_id, None
    return "first_observation", previous_artifact_id, None


def _identity_key(external_identity: dict[str, Any]) -> str:
    parts = [
        str(external_identity["system_id"]),
        str(external_identity["state_boundary_id"]),
        str(external_identity["external_kind"]),
        str(external_identity["external_id"]),
        str(external_identity.get("namespace", "")),
    ]
    return "\u001f".join(parts)


def _revision_rank(external_revision: str | None) -> int | None:
    if external_revision is None:
        return None
    if external_revision.startswith("rev-"):
        suffix = external_revision[4:]
        if suffix.isdecimal():
            return int(suffix)
    return None


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)
