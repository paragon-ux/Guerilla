"""Graph-backed action intent and idempotency orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from guerilla.adapters import (
    AdapterHost,
    AdapterHostError,
    AdapterOperationRequest,
    AdapterOperationResult,
    IdempotencyContext,
)
from guerilla.codec import canonical_bytes, payload_hash
from guerilla.observability import (
    ObservationIngestionRequest,
    ObservationIngestor,
)
from guerilla.storage import GraphStore

PHASE11_METADATA_KEY = "guerilla_phase11_action"
CONTRACT_VERSION = "0.2.0"

ActionClassification = Literal[
    "accepted",
    "rejected",
    "failed",
    "pending",
    "outcome_unknown",
    "duplicated",
]
IdempotencyStatus = Literal[
    "new_intent",
    "resumed_after_intent",
    "replayed_result",
    "prior_outcome_unknown",
]


class ActionExecutionError(ValueError):
    """Raised when an external action cannot be initiated safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ActionExecutionRequest:
    """Validated request for one graph-backed external action."""

    adapter_id: str
    state_boundary_id: str
    action: str
    arguments: dict[str, Any]
    idempotency_key: str
    principal_id: str
    actor: dict[str, Any]
    authority: dict[str, Any]
    requested_at: str
    intent_committed_at: str
    invocation_started_at: str
    result_committed_at: str
    expected_graph_revision: int | None = None
    expected_external_revision: str | None = None
    root: str | None = None
    endpoint: str | None = None
    namespace: str | None = None
    timeout_ms: int = 1_000
    deadline_ms: int | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    retry_policy: str = "no_blind_retry"
    retention_policy: str = "phase11-idempotency-v1"
    after_state_selector: dict[str, Any] | None = None
    after_state_observed_at: str | None = None
    extensions: dict[str, Any] = field(default_factory=dict)
    fail_at: str | None = None


@dataclass(frozen=True, slots=True)
class ActionExecutionResult:
    """Derived response for one action orchestration attempt."""

    workspace_id: str
    graph_revision: int
    commit_hash: str
    transaction_id: str | None
    operation_node_id: str
    intent_node_id: str
    invocation_node_id: str | None
    result_node_id: str | None
    action_classification: ActionClassification
    idempotency_status: IdempotencyStatus
    idempotency_key: str
    request_hash: str
    external_revision: str | None = None
    external_identity: dict[str, Any] | None = None
    after_state_observation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ActionOrchestrator:
    """Commit action intent before invoking one trusted adapter action path."""

    def __init__(self, *, store: GraphStore, host: AdapterHost) -> None:
        self.store = store
        self.host = host

    def execute(self, request: ActionExecutionRequest) -> ActionExecutionResult:
        if request.fail_at == "before_intent_validation":
            raise ActionExecutionError("injected_failure", "failure before intent validation")

        replay_before = self.store.replay()
        descriptor = self.host.descriptor(request.adapter_id)
        system_id = str(descriptor["system_id"])
        adapter_version = str(descriptor["version"])
        action_data = _action_data(request)
        request_hash = payload_hash(canonical_bytes(action_data))
        prior = _find_idempotency_entry(
            replay_before,
            idempotency_key=request.idempotency_key,
        )
        if prior is not None and prior.request_hash != request_hash:
            raise ActionExecutionError(
                "idempotency_conflict",
                "idempotency key was already used with different request content",
            )
        if prior is not None and prior.result_node_id is not None:
            return _result_from_prior(replay_before, prior)
        if prior is not None and prior.invocation_node_id is not None:
            return _unknown_prior_outcome(replay_before, prior)
        if (
            prior is None
            and request.expected_graph_revision is not None
            and request.expected_graph_revision != replay_before.graph_revision
        ):
            raise ActionExecutionError(
                "stale_graph_revision",
                "expected graph revision does not match current revision",
            )

        operation_node_id = (
            str(self.store.ids.generate("node")) if prior is None else prior.operation_node_id
        )
        intent_node_id = (
            str(self.store.ids.generate("node")) if prior is None else prior.intent_node_id
        )
        adapter_request = AdapterOperationRequest(
            workspace_id=replay_before.workspace_id,
            adapter_id=request.adapter_id,
            adapter_version=adapter_version,
            system_id=system_id,
            state_boundary_id=request.state_boundary_id,
            operation_id=operation_node_id,
            principal_id=request.principal_id,
            actor=request.actor,
            authority=request.authority,
            contract_version=CONTRACT_VERSION,
            requested_at=request.requested_at,
            capability="act",
            data=action_data,
            deadline_ms=request.deadline_ms,
            timeout_ms=request.timeout_ms,
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            idempotency=IdempotencyContext(
                key=request.idempotency_key,
                request_hash=request_hash,
                retention_policy=request.retention_policy,
                native_supported=_native_idempotency_supported(
                    descriptor,
                    request.state_boundary_id,
                ),
            ),
            root=request.root,
            endpoint=request.endpoint,
            namespace=request.namespace,
            extensions=request.extensions,
        )
        self._validate_intent_contract(
            request=request,
            system_id=system_id,
            intent_node_id=intent_node_id,
        )
        self.host.validate_request(adapter_request)
        if request.fail_at == "before_intent_commit":
            raise ActionExecutionError("injected_failure", "failure before intent commit")

        if prior is None:
            self._commit_intent(
                request=request,
                descriptor=descriptor,
                workspace_id=replay_before.workspace_id,
                operation_node_id=operation_node_id,
                intent_node_id=intent_node_id,
                action_data=action_data,
                request_hash=request_hash,
            )
            idempotency_status: IdempotencyStatus = "new_intent"
        else:
            idempotency_status = "resumed_after_intent"

        replay_after_intent = self.store.replay()
        _require_durable_intent(replay_after_intent, intent_node_id)
        if request.fail_at in {"after_intent_commit", "after_intent_commit_before_invocation"}:
            raise ActionExecutionError("injected_failure", "failure after intent commit")

        invocation_node_id = str(self.store.ids.generate("node"))
        self._commit_invocation_started(
            request=request,
            workspace_id=replay_after_intent.workspace_id,
            intent_node_id=intent_node_id,
            invocation_node_id=invocation_node_id,
            request_hash=request_hash,
        )
        if request.fail_at == "after_invocation_started":
            raise ActionExecutionError("injected_failure", "failure after invocation start")

        try:
            adapter_result = self.host.invoke(adapter_request)
        except AdapterHostError as exc:
            adapter_result = _adapter_failure_result(
                request=adapter_request,
                occurred_at=request.result_committed_at,
                code=exc.code,
                message=str(exc),
            )

        if request.fail_at in {
            "during_adapter_call",
            "after_external_completion_before_adapter_return",
            "after_adapter_return_before_result_commit",
        }:
            raise ActionExecutionError(
                "injected_failure",
                "failure after invocation before result commit",
            )

        result_node_id = str(self.store.ids.generate("node"))
        result_commit = self._commit_result(
            request=request,
            adapter_result=adapter_result,
            workspace_id=replay_after_intent.workspace_id,
            intent_node_id=intent_node_id,
            invocation_node_id=invocation_node_id,
            result_node_id=result_node_id,
            request_hash=request_hash,
            fail_at="after_stage" if request.fail_at == "result_commit_after_stage" else None,
        )
        if request.fail_at in {
            "after_result_commit",
            "after_result_commit_before_after_state_request",
        }:
            raise ActionExecutionError("injected_failure", "failure after result commit")

        after_state = self._observe_after_state(
            request=request,
            adapter_result=adapter_result,
            intent_node_id=intent_node_id,
            result_node_id=result_node_id,
        )
        final_replay = self.store.replay()
        return ActionExecutionResult(
            workspace_id=final_replay.workspace_id,
            graph_revision=final_replay.graph_revision,
            commit_hash=final_replay.last_commit_hash,
            transaction_id=str(result_commit["transaction_id"]),
            operation_node_id=operation_node_id,
            intent_node_id=intent_node_id,
            invocation_node_id=invocation_node_id,
            result_node_id=result_node_id,
            action_classification=adapter_result.classification,  # type: ignore[arg-type]
            idempotency_status=idempotency_status,
            idempotency_key=request.idempotency_key,
            request_hash=request_hash,
            external_revision=adapter_result.external_revision,
            external_identity=adapter_result.external_identity,
            after_state_observation=after_state,
        )

    def _validate_intent_contract(
        self,
        *,
        request: ActionExecutionRequest,
        system_id: str,
        intent_node_id: str,
    ) -> None:
        self.store.contracts.assert_valid(
            "adapter_act.schema.json",
            {
                "operation_type": "adapter.act",
                "adapter_id": request.adapter_id,
                "system_id": system_id,
                "state_boundary_id": request.state_boundary_id,
                "intent_node_id": intent_node_id,
                "idempotency_key": request.idempotency_key,
                "actor": request.actor,
                "authority": request.authority,
                "requested_at": request.requested_at,
                "action": request.action,
                "arguments": request.arguments,
                "extensions": request.extensions,
            },
        )

    def _commit_intent(
        self,
        *,
        request: ActionExecutionRequest,
        descriptor: dict[str, Any],
        workspace_id: str,
        operation_node_id: str,
        intent_node_id: str,
        action_data: dict[str, Any],
        request_hash: str,
    ) -> dict[str, Any]:
        operation_entity_id = str(self.store.ids.generate("entity"))
        intent_entity_id = str(self.store.ids.generate("entity"))
        metadata = {
            "adapter_id": request.adapter_id,
            "adapter_version": descriptor["version"],
            "system_id": descriptor["system_id"],
            "state_boundary_id": request.state_boundary_id,
            "action": request.action,
            "arguments": request.arguments,
            "action_data": action_data,
            "expected_graph_revision": request.expected_graph_revision,
            "expected_external_revision": request.expected_external_revision,
            "idempotency_key": request.idempotency_key,
            "request_hash": request_hash,
            "correlation_id": request.correlation_id,
            "causation_id": request.causation_id,
            "retry_policy": request.retry_policy,
            "retention_policy": request.retention_policy,
            "timeout_ms": request.timeout_ms,
            "deadline_ms": request.deadline_ms,
            "root": request.root,
            "endpoint": request.endpoint,
            "namespace": request.namespace,
        }
        operation_node = self._node(
            workspace_id=workspace_id,
            node_id=operation_node_id,
            entity_id=operation_entity_id,
            node_type="operation",
            created_at=request.intent_committed_at,
            actor=request.actor,
            authority=request.authority,
            status="intent_committed",
            provenance={
                "source": "guerilla.phase11.action_orchestration",
                "source_record_ids": [],
                "metadata": {"idempotency_key": request.idempotency_key},
            },
            metadata={
                PHASE11_METADATA_KEY: {
                    "kind": "action_intent_operation",
                    **metadata,
                    "operation_node_id": operation_node_id,
                    "intent_node_id": intent_node_id,
                }
            },
            state_boundary_id=request.state_boundary_id,
        )
        intent_event = self._node(
            workspace_id=workspace_id,
            node_id=intent_node_id,
            entity_id=intent_entity_id,
            node_type="event",
            created_at=request.intent_committed_at,
            actor=request.actor,
            authority=request.authority,
            status="intent_committed",
            provenance={
                "source": "adapter.act.intent",
                "source_record_ids": [operation_node_id],
                "causation_id": operation_node_id,
                "metadata": {"idempotency_key": request.idempotency_key},
            },
            metadata={
                PHASE11_METADATA_KEY: {
                    "kind": "action_request_event",
                    **metadata,
                    "operation_node_id": operation_node_id,
                    "intent_node_id": intent_node_id,
                    "state": "intent_committed",
                }
            },
            effective_at=request.requested_at,
            state_boundary_id=request.state_boundary_id,
        )
        return self.store.append_transaction(
            [
                operation_node,
                intent_event,
                self._edge(
                    workspace_id=workspace_id,
                    relationship_type="causes",
                    from_node_id=operation_node_id,
                    to_node_id=intent_node_id,
                    created_at=request.intent_committed_at,
                    actor=request.actor,
                    source_record_ids=[operation_node_id, intent_node_id],
                    metadata={"kind": "operation_caused_action_intent"},
                ),
            ],
            actor=request.actor,
            created_at=request.intent_committed_at,
            committed_at=request.intent_committed_at,
            principal_id=request.principal_id,
            fail_at="after_stage" if request.fail_at == "intent_commit_after_stage" else None,
        )

    def _commit_invocation_started(
        self,
        *,
        request: ActionExecutionRequest,
        workspace_id: str,
        intent_node_id: str,
        invocation_node_id: str,
        request_hash: str,
    ) -> dict[str, Any]:
        invocation = self._node(
            workspace_id=workspace_id,
            node_id=invocation_node_id,
            entity_id=str(self.store.ids.generate("entity")),
            node_type="event",
            created_at=request.invocation_started_at,
            actor=request.actor,
            authority=request.authority,
            status="invocation_started",
            provenance={
                "source": "adapter.act.invocation_started",
                "source_record_ids": [intent_node_id],
                "causation_id": intent_node_id,
            },
            metadata={
                PHASE11_METADATA_KEY: {
                    "kind": "invocation_started_event",
                    "state": "invocation_started",
                    "intent_node_id": intent_node_id,
                    "invocation_node_id": invocation_node_id,
                    "idempotency_key": request.idempotency_key,
                    "request_hash": request_hash,
                    "adapter_id": request.adapter_id,
                    "state_boundary_id": request.state_boundary_id,
                    "action": request.action,
                    "correlation_id": request.correlation_id,
                }
            },
            effective_at=request.invocation_started_at,
            state_boundary_id=request.state_boundary_id,
        )
        return self.store.append_transaction(
            [
                invocation,
                self._edge(
                    workspace_id=workspace_id,
                    relationship_type="causes",
                    from_node_id=intent_node_id,
                    to_node_id=invocation_node_id,
                    created_at=request.invocation_started_at,
                    actor=request.actor,
                    source_record_ids=[intent_node_id, invocation_node_id],
                    metadata={"kind": "action_intent_caused_invocation"},
                ),
            ],
            actor=request.actor,
            created_at=request.invocation_started_at,
            committed_at=request.invocation_started_at,
            principal_id=request.principal_id,
        )

    def _commit_result(
        self,
        *,
        request: ActionExecutionRequest,
        adapter_result: AdapterOperationResult,
        workspace_id: str,
        intent_node_id: str,
        invocation_node_id: str,
        result_node_id: str,
        request_hash: str,
        fail_at: str | None,
    ) -> dict[str, Any]:
        provenance: dict[str, Any] = {
            "source": "adapter.act.result",
            "source_record_ids": [intent_node_id, invocation_node_id],
            "causation_id": invocation_node_id,
            "observed_at": adapter_result.occurred_at,
            "metadata": {"adapter_evidence": adapter_result.evidence},
        }
        if adapter_result.external_identity is not None:
            provenance["external_identity"] = adapter_result.external_identity
        result = self._node(
            workspace_id=workspace_id,
            node_id=result_node_id,
            entity_id=str(self.store.ids.generate("entity")),
            node_type="event",
            created_at=request.result_committed_at,
            actor=request.actor,
            authority=request.authority,
            status=adapter_result.classification,
            provenance=provenance,
            metadata={
                PHASE11_METADATA_KEY: {
                    "kind": "action_result_event",
                    "state": adapter_result.classification,
                    "intent_node_id": intent_node_id,
                    "invocation_node_id": invocation_node_id,
                    "result_node_id": result_node_id,
                    "idempotency_key": request.idempotency_key,
                    "request_hash": request_hash,
                    "adapter_id": adapter_result.adapter_id,
                    "adapter_version": adapter_result.adapter_version,
                    "system_id": adapter_result.system_id,
                    "state_boundary_id": adapter_result.state_boundary_id,
                    "action": request.action,
                    "external_result_classification": adapter_result.classification,
                    "external_revision": adapter_result.external_revision,
                    "external_identity": adapter_result.external_identity,
                    "result_data": adapter_result.data,
                    "retry": adapter_result.retry,
                    "warnings": list(adapter_result.warnings),
                    "limitations": list(adapter_result.limitations),
                    "correlation_id": request.correlation_id,
                    "pending_or_unknown": adapter_result.classification
                    in {"pending", "outcome_unknown"},
                }
            },
            effective_at=adapter_result.occurred_at,
            state_boundary_id=request.state_boundary_id,
        )
        return self.store.append_transaction(
            [
                result,
                self._edge(
                    workspace_id=workspace_id,
                    relationship_type="causes",
                    from_node_id=invocation_node_id,
                    to_node_id=result_node_id,
                    created_at=request.result_committed_at,
                    actor=request.actor,
                    source_record_ids=[invocation_node_id, result_node_id],
                    metadata={"kind": "adapter_invocation_caused_action_result"},
                ),
            ],
            actor=request.actor,
            created_at=request.result_committed_at,
            committed_at=request.result_committed_at,
            principal_id=request.principal_id,
            fail_at=fail_at,
        )

    def _observe_after_state(
        self,
        *,
        request: ActionExecutionRequest,
        adapter_result: AdapterOperationResult,
        intent_node_id: str,
        result_node_id: str,
    ) -> dict[str, Any] | None:
        if request.after_state_selector is None:
            return None
        if adapter_result.classification == "rejected":
            return None
        observed_at = request.after_state_observed_at or request.result_committed_at
        observation = ObservationIngestor(store=self.store, host=self.host).ingest(
            ObservationIngestionRequest(
                adapter_id=request.adapter_id,
                state_boundary_id=request.state_boundary_id,
                selector=request.after_state_selector,
                principal_id=request.principal_id,
                actor=request.actor,
                authority=request.authority,
                requested_at=observed_at,
                received_at=observed_at,
                commit_at=observed_at,
                correlation_id=request.correlation_id,
                causation_id=result_node_id,
                root=request.root,
                endpoint=request.endpoint,
                namespace=request.namespace,
                timeout_ms=request.timeout_ms,
                deadline_ms=request.deadline_ms,
                fail_at=(
                    "after_stage"
                    if request.fail_at
                    in {"during_after_state_observation", "after_state_commit_after_stage"}
                    else None
                ),
            )
        )
        after_state = observation.to_dict()
        after_state["scheduled_by_intent_node_id"] = intent_node_id
        after_state["scheduled_by_result_node_id"] = result_node_id
        return after_state

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
        metadata: dict[str, Any],
        effective_at: str | None = None,
        state_boundary_id: str | None = None,
    ) -> dict[str, Any]:
        node: dict[str, Any] = {
            "record_type": "node",
            "protocol_version": CONTRACT_VERSION,
            "workspace_id": workspace_id,
            "node_id": node_id,
            "entity_id": entity_id,
            "node_type": node_type,
            "created_at": created_at,
            "actor": actor,
            "authority": authority,
            "status": status,
            "provenance": provenance,
            "payload_ref": {"retention_class": "none"},
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
            "protocol_version": CONTRACT_VERSION,
            "workspace_id": workspace_id,
            "edge_id": str(self.store.ids.generate("edge")),
            "relationship_type": relationship_type,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "created_at": created_at,
            "actor": actor,
            "provenance": {
                "source": "guerilla.phase11.action_orchestration",
                "source_record_ids": source_record_ids,
            },
            "metadata": {PHASE11_METADATA_KEY: metadata},
            "extensions": {},
            "record_hash": "0" * 64,
        }


@dataclass(slots=True)
class _IdempotencyEntry:
    idempotency_key: str
    request_hash: str
    operation_node_id: str
    intent_node_id: str
    intent_revision: int
    invocation_node_id: str | None = None
    result_node_id: str | None = None
    result_revision: int | None = None
    result_metadata: dict[str, Any] | None = None


def _action_data(request: ActionExecutionRequest) -> dict[str, Any]:
    data = {"action": request.action, **request.arguments}
    if request.expected_external_revision is not None and "expected_revision" not in data:
        data["expected_revision"] = request.expected_external_revision
    return data


def _find_idempotency_entry(
    replay: Any,
    *,
    idempotency_key: str,
) -> _IdempotencyEntry | None:
    entries: dict[str, _IdempotencyEntry] = {}
    ordered_nodes = sorted(
        replay.nodes.items(),
        key=lambda item: (replay.record_revisions[item[0]], item[0]),
    )
    for node_id, node in ordered_nodes:
        metadata = node.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        action_metadata = metadata.get(PHASE11_METADATA_KEY)
        if not isinstance(action_metadata, dict):
            continue
        kind = action_metadata.get("kind")
        key = action_metadata.get("idempotency_key")
        if key != idempotency_key:
            continue
        if kind == "action_request_event":
            entries[str(node_id)] = _IdempotencyEntry(
                idempotency_key=str(key),
                request_hash=str(action_metadata["request_hash"]),
                operation_node_id=str(action_metadata["operation_node_id"]),
                intent_node_id=str(node_id),
                intent_revision=int(replay.record_revisions[node_id]),
            )
        elif kind == "invocation_started_event":
            intent_node_id = str(action_metadata["intent_node_id"])
            entry = entries.get(intent_node_id)
            if entry is not None:
                entry.invocation_node_id = str(node_id)
        elif kind == "action_result_event":
            intent_node_id = str(action_metadata["intent_node_id"])
            entry = entries.get(intent_node_id)
            if entry is not None:
                entry.result_node_id = str(node_id)
                entry.result_revision = int(replay.record_revisions[node_id])
                entry.result_metadata = dict(action_metadata)
    matching = list(entries.values())
    if not matching:
        return None
    matching.sort(key=lambda item: (item.intent_revision, item.intent_node_id))
    return matching[0]


def _result_from_prior(replay: Any, entry: _IdempotencyEntry) -> ActionExecutionResult:
    assert entry.result_node_id is not None
    assert entry.result_metadata is not None
    commit = _commit_for_revision(replay, entry.result_revision or replay.graph_revision)
    return ActionExecutionResult(
        workspace_id=replay.workspace_id,
        graph_revision=replay.graph_revision,
        commit_hash=replay.last_commit_hash,
        transaction_id=commit.transaction_id if commit is not None else None,
        operation_node_id=entry.operation_node_id,
        intent_node_id=entry.intent_node_id,
        invocation_node_id=entry.invocation_node_id,
        result_node_id=entry.result_node_id,
        action_classification=entry.result_metadata["external_result_classification"],
        idempotency_status="replayed_result",
        idempotency_key=entry.idempotency_key,
        request_hash=entry.request_hash,
        external_revision=entry.result_metadata.get("external_revision"),
        external_identity=entry.result_metadata.get("external_identity"),
    )


def _unknown_prior_outcome(replay: Any, entry: _IdempotencyEntry) -> ActionExecutionResult:
    return ActionExecutionResult(
        workspace_id=replay.workspace_id,
        graph_revision=replay.graph_revision,
        commit_hash=replay.last_commit_hash,
        transaction_id=None,
        operation_node_id=entry.operation_node_id,
        intent_node_id=entry.intent_node_id,
        invocation_node_id=entry.invocation_node_id,
        result_node_id=None,
        action_classification="outcome_unknown",
        idempotency_status="prior_outcome_unknown",
        idempotency_key=entry.idempotency_key,
        request_hash=entry.request_hash,
    )


def _require_durable_intent(replay: Any, intent_node_id: str) -> None:
    node = replay.nodes.get(intent_node_id)
    if node is None:
        raise ActionExecutionError("intent_not_durable", "intent node is not committed")
    metadata = node.get("metadata", {}).get(PHASE11_METADATA_KEY)
    if not isinstance(metadata, dict) or metadata.get("kind") != "action_request_event":
        raise ActionExecutionError("intent_not_durable", "intent node metadata is invalid")


def _commit_for_revision(replay: Any, revision: int) -> Any:
    for commit in replay.commits:
        if commit.graph_revision == revision:
            return commit
    return None


def _native_idempotency_supported(descriptor: dict[str, Any], boundary_id: str) -> bool:
    for capability in descriptor["capabilities"]:
        if (
            capability.get("capability") != "act"
            or boundary_id not in capability["state_boundary_ids"]
        ):
            continue
        metadata = capability.get("metadata", {})
        return str(metadata.get("idempotency")) == "native"
    return False


def _adapter_failure_result(
    *,
    request: AdapterOperationRequest,
    occurred_at: str,
    code: str,
    message: str,
) -> AdapterOperationResult:
    return AdapterOperationResult(
        adapter_id=request.adapter_id,
        adapter_version=request.adapter_version,
        system_id=request.system_id,
        state_boundary_id=request.state_boundary_id,
        capability="act",
        classification="failed",
        occurred_at=occurred_at,
        evidence={"error_code": code, "message": message},
        retry="after_reconcile",
        data={},
        warnings=(message,),
        limitations=("adapter failure recorded by Phase 11 orchestration",),
        payload_ref={"retention_class": "none"},
    )
