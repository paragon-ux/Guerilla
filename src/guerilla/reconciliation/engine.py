"""Unknown-outcome reconciliation engine for Phase 12."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, TypeAlias, cast

from guerilla.adapters import AdapterHost, AdapterHostError, AdapterOperationRequest
from guerilla.conflicts import PHASE12_CONFLICT_METADATA_KEY
from guerilla.conflicts.engine import ConflictSeverity, ConflictType
from guerilla.observability import ObservationIngestionRequest, ObservationIngestor
from guerilla.orchestration.actions import PHASE11_METADATA_KEY
from guerilla.storage import GraphStore

CONTRACT_VERSION = "0.2.0"
PHASE12_RECONCILIATION_METADATA_KEY = "guerilla_phase12_reconciliation"

ReconciliationClassification: TypeAlias = Literal[
    "confirmed_accepted",
    "confirmed_rejected",
    "confirmed_failed",
    "still_pending",
    "duplicated",
    "externally_completed_missing_lineage",
    "unknown",
]


class ReconciliationError(ValueError):
    """Raised when an action cannot be reconciled safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ReconciliationRequest:
    """Request to reconcile one previously committed Phase 11 action intent."""

    adapter_id: str
    state_boundary_id: str
    intent_node_id: str
    idempotency_key: str
    principal_id: str
    actor: dict[str, Any]
    authority: dict[str, Any]
    requested_at: str
    reconciled_at: str
    operation_id: str | None = None
    root: str | None = None
    endpoint: str | None = None
    namespace: str | None = None
    timeout_ms: int = 1_000
    deadline_ms: int | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    after_state_selector: dict[str, Any] | None = None
    after_state_observed_at: str | None = None
    policy_version: str = "local-owner-v1"
    extensions: dict[str, Any] = field(default_factory=dict)
    fail_at: str | None = None


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Derived response for one reconciliation attempt."""

    workspace_id: str
    graph_revision: int
    commit_hash: str
    transaction_id: str
    reconciliation_node_id: str
    classification: ReconciliationClassification
    intent_node_id: str
    idempotency_key: str
    recovered_result_node_id: str | None = None
    conflict_node_ids: tuple[str, ...] = ()
    after_state_observation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReconciliationEngine:
    """Classify uncertain external action outcomes without duplicate mutation."""

    def __init__(self, *, store: GraphStore, host: AdapterHost) -> None:
        self.store = store
        self.host = host

    def reconcile(self, request: ReconciliationRequest) -> ReconciliationResult:
        replay_before = self.store.replay()
        attempt = _find_action_attempt(
            replay_before,
            intent_node_id=request.intent_node_id,
            idempotency_key=request.idempotency_key,
        )
        if attempt is None:
            raise ReconciliationError("missing_endpoint", "action intent was not found")
        if attempt.adapter_id != request.adapter_id:
            raise ReconciliationError("invalid_message", "request adapter does not match intent")
        if attempt.state_boundary_id != request.state_boundary_id:
            raise ReconciliationError("invalid_message", "request boundary does not match intent")
        if request.fail_at == "before_reconciliation_validation":
            raise ReconciliationError(
                "injected_failure", "failure before reconciliation validation"
            )

        descriptor = self.host.descriptor(request.adapter_id)
        if attempt.invocation_node_id is None:
            return self._commit_local_classification(
                request=request,
                attempt=attempt,
                workspace_id=replay_before.workspace_id,
                classification="unknown",
                evidence={"reason": "intent_committed_without_invocation"},
                conflict_specs=(),
            )

        adapter_request = AdapterOperationRequest(
            workspace_id=replay_before.workspace_id,
            adapter_id=request.adapter_id,
            adapter_version=str(descriptor["version"]),
            system_id=str(descriptor["system_id"]),
            state_boundary_id=request.state_boundary_id,
            operation_id=request.operation_id or str(self.store.ids.generate("message")),
            principal_id=request.principal_id,
            actor=request.actor,
            authority=request.authority,
            contract_version=CONTRACT_VERSION,
            requested_at=request.requested_at,
            capability="reconcile",
            data={
                "intent_node_id": attempt.intent_node_id,
                "idempotency_key": attempt.idempotency_key,
                "request_hash": attempt.request_hash,
                "action": attempt.action,
                "prior_result_node_id": attempt.result_node_id,
                "prior_result_classification": attempt.result_classification,
            },
            deadline_ms=request.deadline_ms,
            timeout_ms=request.timeout_ms,
            correlation_id=request.correlation_id or attempt.correlation_id,
            causation_id=request.causation_id or attempt.invocation_node_id,
            root=request.root if request.root is not None else attempt.root,
            endpoint=request.endpoint if request.endpoint is not None else attempt.endpoint,
            namespace=request.namespace if request.namespace is not None else attempt.namespace,
            extensions=request.extensions,
        )
        try:
            self.host.validate_request(adapter_request)
        except AdapterHostError as exc:
            if exc.code != "unsupported_capability":
                raise
            return self._commit_local_classification(
                request=request,
                attempt=attempt,
                workspace_id=replay_before.workspace_id,
                classification="unknown",
                evidence={"reason": "unsupported_reconciliation", "error_code": exc.code},
                conflict_specs=(
                    _ConflictSpec(
                        conflict_type="incomplete_lineage",
                        conflict_reason="unsupported_reconciliation",
                        severity="high",
                        required_resolution_class="manual_external_investigation",
                        summary="Adapter does not support reconciliation for this boundary.",
                        details={"error_code": exc.code},
                    ),
                ),
            )
        if request.fail_at == "during_reconciliation":
            raise ReconciliationError("injected_failure", "failure during reconciliation")

        try:
            adapter_result = self.host.invoke(adapter_request)
        except AdapterHostError as exc:
            if exc.code != "adapter_unavailable":
                raise
            return self._commit_local_classification(
                request=request,
                attempt=attempt,
                workspace_id=replay_before.workspace_id,
                classification="unknown",
                evidence={"reason": "reconciliation_timeout", "error_code": exc.code},
                conflict_specs=(
                    _ConflictSpec(
                        conflict_type="external_outcome_unknown",
                        conflict_reason="reconciliation_timeout",
                        severity="high",
                        required_resolution_class="retry_reconciliation_or_manual_check",
                        summary="Reconciliation did not complete before timeout.",
                        details={"error_code": exc.code},
                    ),
                ),
            )
        classification = cast(ReconciliationClassification, adapter_result.classification)
        self.store.contracts.assert_valid(
            "adapter_reconcile.schema.json",
            {
                "operation_type": "adapter.reconcile",
                "adapter_id": request.adapter_id,
                "system_id": str(descriptor["system_id"]),
                "state_boundary_id": request.state_boundary_id,
                "intent_node_id": attempt.intent_node_id,
                "idempotency_key": attempt.idempotency_key,
                "actor": request.actor,
                "authority": request.authority,
                "requested_at": request.requested_at,
                "reported_outcome": classification,
                "evidence": adapter_result.evidence,
                "extensions": request.extensions,
            },
        )
        if request.fail_at == "after_reconcile_before_commit":
            raise ReconciliationError(
                "injected_failure",
                "failure after adapter reconciliation before commit",
            )

        conflict_specs = _conflict_specs_for_result(
            replay_before,
            attempt=attempt,
            classification=classification,
            evidence=adapter_result.evidence,
            policy_version=request.policy_version,
        )
        recovered_status = _recovered_action_status(classification, attempt)
        commit_result = self._commit_reconciliation(
            request=request,
            attempt=attempt,
            workspace_id=replay_before.workspace_id,
            classification=classification,
            evidence=adapter_result.evidence,
            result_data=adapter_result.data,
            external_revision=adapter_result.external_revision,
            external_identity=adapter_result.external_identity,
            retry=adapter_result.retry,
            warnings=list(adapter_result.warnings),
            limitations=list(adapter_result.limitations),
            conflict_specs=conflict_specs,
            recovered_action_status=recovered_status,
        )
        if request.fail_at in {
            "after_reconciliation_commit",
            "after_reconciliation_commit_before_after_state",
        }:
            raise ReconciliationError("injected_failure", "failure after reconciliation commit")

        after_state = self._observe_after_state(
            request=request,
            classification=classification,
            recovered_result_node_id=commit_result.recovered_result_node_id,
        )
        if after_state is None:
            return commit_result
        final_replay = self.store.replay()
        return ReconciliationResult(
            workspace_id=final_replay.workspace_id,
            graph_revision=final_replay.graph_revision,
            commit_hash=final_replay.last_commit_hash,
            transaction_id=commit_result.transaction_id,
            reconciliation_node_id=commit_result.reconciliation_node_id,
            classification=commit_result.classification,
            intent_node_id=commit_result.intent_node_id,
            idempotency_key=commit_result.idempotency_key,
            recovered_result_node_id=commit_result.recovered_result_node_id,
            conflict_node_ids=commit_result.conflict_node_ids,
            after_state_observation=after_state,
        )

    def _commit_local_classification(
        self,
        *,
        request: ReconciliationRequest,
        attempt: _ActionAttempt,
        workspace_id: str,
        classification: ReconciliationClassification,
        evidence: dict[str, Any],
        conflict_specs: tuple[_ConflictSpec, ...],
    ) -> ReconciliationResult:
        return self._commit_reconciliation(
            request=request,
            attempt=attempt,
            workspace_id=workspace_id,
            classification=classification,
            evidence=evidence,
            result_data={},
            external_revision=None,
            external_identity=None,
            retry="after_reconcile",
            warnings=[],
            limitations=[],
            conflict_specs=conflict_specs,
            recovered_action_status=None,
        )

    def _commit_reconciliation(
        self,
        *,
        request: ReconciliationRequest,
        attempt: _ActionAttempt,
        workspace_id: str,
        classification: ReconciliationClassification,
        evidence: dict[str, Any],
        result_data: dict[str, Any],
        external_revision: str | None,
        external_identity: dict[str, Any] | None,
        retry: str,
        warnings: list[str],
        limitations: list[str],
        conflict_specs: tuple[_ConflictSpec, ...],
        recovered_action_status: str | None,
    ) -> ReconciliationResult:
        reconciliation_node_id = str(self.store.ids.generate("node"))
        reconciliation_node = self._node(
            workspace_id=workspace_id,
            node_id=reconciliation_node_id,
            entity_id=str(self.store.ids.generate("entity")),
            node_type="event",
            created_at=request.reconciled_at,
            actor=request.actor,
            authority=request.authority,
            status=classification,
            provenance={
                "source": "adapter.reconcile.result",
                "source_record_ids": _source_ids(attempt),
                "causation_id": attempt.invocation_node_id or attempt.intent_node_id,
                "metadata": {"adapter_evidence": evidence},
            },
            metadata={
                PHASE12_RECONCILIATION_METADATA_KEY: {
                    "kind": "reconciliation_event",
                    "classification": classification,
                    "intent_node_id": attempt.intent_node_id,
                    "invocation_node_id": attempt.invocation_node_id,
                    "prior_result_node_id": attempt.result_node_id,
                    "idempotency_key": attempt.idempotency_key,
                    "request_hash": attempt.request_hash,
                    "adapter_id": attempt.adapter_id,
                    "state_boundary_id": attempt.state_boundary_id,
                    "action": attempt.action,
                    "evidence": evidence,
                    "result_data": result_data,
                    "external_revision": external_revision,
                    "external_identity": external_identity,
                    "retry": retry,
                    "warnings": warnings,
                    "limitations": limitations,
                    "policy_version": request.policy_version,
                }
            },
            effective_at=request.reconciled_at,
            state_boundary_id=attempt.state_boundary_id,
        )
        members = [reconciliation_node]
        cause_source = attempt.invocation_node_id or attempt.intent_node_id
        members.append(
            self._edge(
                workspace_id=workspace_id,
                relationship_type="causes",
                from_node_id=cause_source,
                to_node_id=reconciliation_node_id,
                created_at=request.reconciled_at,
                actor=request.actor,
                source_record_ids=[cause_source, reconciliation_node_id],
                metadata={"kind": "prior_action_state_caused_reconciliation"},
            )
        )

        recovered_result_node_id = None
        if recovered_action_status is not None:
            recovered_result_node_id = str(self.store.ids.generate("node"))
            recovered = self._recovered_result_node(
                request=request,
                attempt=attempt,
                workspace_id=workspace_id,
                node_id=recovered_result_node_id,
                reconciliation_node_id=reconciliation_node_id,
                action_status=recovered_action_status,
                classification=classification,
                evidence=evidence,
                result_data=result_data,
                external_revision=external_revision,
                external_identity=external_identity,
                retry=retry,
                warnings=warnings,
                limitations=limitations,
            )
            members.append(recovered)
            members.append(
                self._edge(
                    workspace_id=workspace_id,
                    relationship_type="causes",
                    from_node_id=reconciliation_node_id,
                    to_node_id=recovered_result_node_id,
                    created_at=request.reconciled_at,
                    actor=request.actor,
                    source_record_ids=[reconciliation_node_id, recovered_result_node_id],
                    metadata={"kind": "reconciliation_recovered_action_result"},
                )
            )

        conflict_node_ids: list[str] = []
        for spec in conflict_specs:
            conflict_node_id = str(self.store.ids.generate("node"))
            conflict_node_ids.append(conflict_node_id)
            members.append(
                self._conflict_node(
                    request=request,
                    attempt=attempt,
                    workspace_id=workspace_id,
                    node_id=conflict_node_id,
                    reconciliation_node_id=reconciliation_node_id,
                    spec=spec,
                )
            )
            members.append(
                self._edge(
                    workspace_id=workspace_id,
                    relationship_type="evidences",
                    from_node_id=reconciliation_node_id,
                    to_node_id=conflict_node_id,
                    created_at=request.reconciled_at,
                    actor=request.actor,
                    source_record_ids=[reconciliation_node_id, conflict_node_id],
                    metadata={
                        "kind": "reconciliation_evidences_conflict",
                        "conflict_type": spec.conflict_type,
                    },
                )
            )
            if recovered_result_node_id is not None:
                members.append(
                    self._edge(
                        workspace_id=workspace_id,
                        relationship_type="evidences",
                        from_node_id=recovered_result_node_id,
                        to_node_id=conflict_node_id,
                        created_at=request.reconciled_at,
                        actor=request.actor,
                        source_record_ids=[recovered_result_node_id, conflict_node_id],
                        metadata={
                            "kind": "recovered_result_evidences_conflict",
                            "conflict_type": spec.conflict_type,
                        },
                    )
                )

        commit = self.store.append_transaction(
            members,
            actor=request.actor,
            created_at=request.reconciled_at,
            committed_at=request.reconciled_at,
            principal_id=request.principal_id,
            fail_at=(
                "after_stage" if request.fail_at == "reconciliation_commit_after_stage" else None
            ),
        )
        return ReconciliationResult(
            workspace_id=workspace_id,
            graph_revision=int(commit["graph_revision"]),
            commit_hash=str(commit["commit_hash"]),
            transaction_id=str(commit["transaction_id"]),
            reconciliation_node_id=reconciliation_node_id,
            classification=classification,
            intent_node_id=attempt.intent_node_id,
            idempotency_key=attempt.idempotency_key,
            recovered_result_node_id=recovered_result_node_id,
            conflict_node_ids=tuple(conflict_node_ids),
        )

    def _observe_after_state(
        self,
        *,
        request: ReconciliationRequest,
        classification: ReconciliationClassification,
        recovered_result_node_id: str | None,
    ) -> dict[str, Any] | None:
        if request.after_state_selector is None:
            return None
        if classification not in {"confirmed_accepted", "externally_completed_missing_lineage"}:
            return None
        observed_at = request.after_state_observed_at or request.reconciled_at
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
                causation_id=recovered_result_node_id,
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
        after_state["scheduled_by_reconciliation_result_node_id"] = recovered_result_node_id
        return after_state

    def _recovered_result_node(
        self,
        *,
        request: ReconciliationRequest,
        attempt: _ActionAttempt,
        workspace_id: str,
        node_id: str,
        reconciliation_node_id: str,
        action_status: str,
        classification: ReconciliationClassification,
        evidence: dict[str, Any],
        result_data: dict[str, Any],
        external_revision: str | None,
        external_identity: dict[str, Any] | None,
        retry: str,
        warnings: list[str],
        limitations: list[str],
    ) -> dict[str, Any]:
        phase11_metadata = {
            "kind": "action_result_event",
            "state": action_status,
            "intent_node_id": attempt.intent_node_id,
            "invocation_node_id": attempt.invocation_node_id,
            "result_node_id": node_id,
            "idempotency_key": attempt.idempotency_key,
            "request_hash": attempt.request_hash,
            "adapter_id": attempt.adapter_id,
            "adapter_version": attempt.adapter_version,
            "system_id": attempt.system_id,
            "state_boundary_id": attempt.state_boundary_id,
            "action": attempt.action,
            "external_result_classification": action_status,
            "external_revision": external_revision,
            "external_identity": external_identity,
            "result_data": result_data,
            "retry": retry,
            "warnings": warnings,
            "limitations": limitations,
            "correlation_id": request.correlation_id or attempt.correlation_id,
            "pending_or_unknown": action_status in {"pending", "outcome_unknown"},
        }
        return self._node(
            workspace_id=workspace_id,
            node_id=node_id,
            entity_id=str(self.store.ids.generate("entity")),
            node_type="event",
            created_at=request.reconciled_at,
            actor=request.actor,
            authority=request.authority,
            status=action_status,
            provenance={
                "source": "adapter.reconcile.recovered_action_result",
                "source_record_ids": [reconciliation_node_id, *_source_ids(attempt)],
                "causation_id": reconciliation_node_id,
                "metadata": {
                    "adapter_evidence": evidence,
                    "recovered_from_classification": classification,
                    "original_result_timestamp_fabricated": False,
                },
            },
            metadata={
                PHASE11_METADATA_KEY: phase11_metadata,
                PHASE12_RECONCILIATION_METADATA_KEY: {
                    "kind": "recovered_action_result_event",
                    "reconciliation_node_id": reconciliation_node_id,
                    "recovered_from_classification": classification,
                    "original_result_timestamp_fabricated": False,
                },
            },
            effective_at=request.reconciled_at,
            state_boundary_id=attempt.state_boundary_id,
        )

    def _conflict_node(
        self,
        *,
        request: ReconciliationRequest,
        attempt: _ActionAttempt,
        workspace_id: str,
        node_id: str,
        reconciliation_node_id: str,
        spec: _ConflictSpec,
    ) -> dict[str, Any]:
        return self._node(
            workspace_id=workspace_id,
            node_id=node_id,
            entity_id=str(self.store.ids.generate("entity")),
            node_type="conflict",
            created_at=request.reconciled_at,
            actor=request.actor,
            authority=request.authority,
            status="open",
            provenance={
                "source": "guerilla.phase12.reconciliation",
                "source_record_ids": [
                    attempt.intent_node_id,
                    reconciliation_node_id,
                ],
                "metadata": {
                    "conflict_type": spec.conflict_type,
                    "conflict_reason": spec.conflict_reason,
                },
            },
            metadata={
                "conflict_type": spec.conflict_type,
                "summary": spec.summary,
                PHASE12_CONFLICT_METADATA_KEY: {
                    "kind": "conflict",
                    "conflict_type": spec.conflict_type,
                    "conflict_reason": spec.conflict_reason,
                    "subject_node_id": attempt.intent_node_id,
                    "evidence_node_ids": [reconciliation_node_id],
                    "authority": request.authority,
                    "severity": spec.severity,
                    "status": "open",
                    "detected_at": request.reconciled_at,
                    "policy_version": request.policy_version,
                    "required_resolution_class": spec.required_resolution_class,
                    "limitations": [],
                    "details": spec.details,
                },
            },
            state_boundary_id=attempt.state_boundary_id,
        )

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
                "source": "guerilla.phase12.reconciliation",
                "source_record_ids": source_record_ids,
            },
            "metadata": {PHASE12_RECONCILIATION_METADATA_KEY: metadata},
            "extensions": {},
            "record_hash": "0" * 64,
        }


@dataclass(slots=True)
class _ActionAttempt:
    operation_node_id: str
    intent_node_id: str
    idempotency_key: str
    request_hash: str
    adapter_id: str
    adapter_version: str
    system_id: str
    state_boundary_id: str
    action: str
    arguments: dict[str, Any]
    action_data: dict[str, Any]
    correlation_id: str | None
    root: str | None
    endpoint: str | None
    namespace: str | None
    invocation_node_id: str | None = None
    result_node_id: str | None = None
    result_classification: str | None = None
    result_metadata: dict[str, Any] | None = None
    result_provenance: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class _ConflictSpec:
    conflict_type: ConflictType
    conflict_reason: str
    severity: ConflictSeverity
    required_resolution_class: str
    summary: str
    details: dict[str, Any]


def _find_action_attempt(
    replay: Any,
    *,
    intent_node_id: str,
    idempotency_key: str,
) -> _ActionAttempt | None:
    attempt: _ActionAttempt | None = None
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
        if action_metadata.get("idempotency_key") != idempotency_key:
            continue
        kind = action_metadata.get("kind")
        if kind == "action_request_event" and node_id == intent_node_id:
            attempt = _ActionAttempt(
                operation_node_id=str(action_metadata["operation_node_id"]),
                intent_node_id=str(node_id),
                idempotency_key=idempotency_key,
                request_hash=str(action_metadata["request_hash"]),
                adapter_id=str(action_metadata["adapter_id"]),
                adapter_version=str(action_metadata["adapter_version"]),
                system_id=str(action_metadata["system_id"]),
                state_boundary_id=str(action_metadata["state_boundary_id"]),
                action=str(action_metadata["action"]),
                arguments=dict(action_metadata.get("arguments", {})),
                action_data=dict(action_metadata.get("action_data", {})),
                correlation_id=_optional_string(action_metadata.get("correlation_id")),
                root=_optional_string(action_metadata.get("root")),
                endpoint=_optional_string(action_metadata.get("endpoint")),
                namespace=_optional_string(action_metadata.get("namespace")),
            )
        elif kind == "invocation_started_event" and attempt is not None:
            if action_metadata.get("intent_node_id") == intent_node_id:
                attempt.invocation_node_id = str(node_id)
        elif (
            kind == "action_result_event"
            and attempt is not None
            and action_metadata.get("intent_node_id") == intent_node_id
        ):
            attempt.result_node_id = str(node_id)
            attempt.result_classification = str(action_metadata["external_result_classification"])
            attempt.result_metadata = dict(action_metadata)
            attempt.result_provenance = dict(node.get("provenance", {}))
    return attempt


def _optional_string(value: Any) -> str | None:
    return None if value is None else str(value)


def _source_ids(attempt: _ActionAttempt) -> list[str]:
    source_ids = [attempt.intent_node_id]
    if attempt.invocation_node_id is not None:
        source_ids.append(attempt.invocation_node_id)
    if attempt.result_node_id is not None:
        source_ids.append(attempt.result_node_id)
    return source_ids


def _recovered_action_status(
    classification: ReconciliationClassification,
    attempt: _ActionAttempt,
) -> str | None:
    if attempt.result_node_id is not None and attempt.result_classification not in {
        "pending",
        "outcome_unknown",
    }:
        return None
    if classification == "confirmed_accepted":
        return "accepted"
    if classification == "externally_completed_missing_lineage":
        return "accepted"
    if classification == "confirmed_rejected":
        return "rejected"
    if classification == "confirmed_failed":
        return "failed"
    if classification == "duplicated":
        return "duplicated"
    if classification == "still_pending":
        return "pending"
    return None


def _conflict_specs_for_result(
    replay: Any,
    *,
    attempt: _ActionAttempt,
    classification: ReconciliationClassification,
    evidence: dict[str, Any],
    policy_version: str,
) -> tuple[_ConflictSpec, ...]:
    specs: list[_ConflictSpec] = []
    if classification == "unknown":
        specs.append(
            _ConflictSpec(
                conflict_type="external_outcome_unknown",
                conflict_reason=str(evidence.get("history", "unknown_outcome")),
                severity="high",
                required_resolution_class="manual_external_investigation",
                summary="External action outcome remains unknown after reconciliation.",
                details={"evidence": evidence, "policy_version": policy_version},
            )
        )
    if classification == "duplicated":
        specs.append(
            _ConflictSpec(
                conflict_type="idempotency_conflict",
                conflict_reason="externally_duplicated_mutation",
                severity="high",
                required_resolution_class="deduplicate_or_accept_external_duplicate",
                summary="Reconciliation reported a duplicated external mutation.",
                details={"evidence": evidence},
            )
        )
    if classification == "externally_completed_missing_lineage":
        specs.append(
            _ConflictSpec(
                conflict_type="incomplete_lineage",
                conflict_reason="externally_completed_missing_lineage",
                severity="medium",
                required_resolution_class="review_recovered_lineage",
                summary="External completion was recovered without rewriting original records.",
                details={"evidence": evidence},
            )
        )
    if _prior_result_reason(attempt) == "stale_external_revision":
        specs.append(
            _ConflictSpec(
                conflict_type="stale_external_revision",
                conflict_reason="adapter_confirmed_stale_external_revision",
                severity="medium",
                required_resolution_class="refresh_external_revision",
                summary="External revision was stale when the action was attempted.",
                details={"evidence": evidence},
            )
        )
    if _same_request_different_attempt_exists(replay, attempt):
        specs.append(
            _ConflictSpec(
                conflict_type="idempotency_conflict",
                conflict_reason="same_request_different_local_attempts",
                severity="high",
                required_resolution_class="inspect_duplicate_attempts",
                summary="The same action request appeared under different idempotency keys.",
                details={"request_hash": attempt.request_hash},
            )
        )
    return tuple(specs)


def _prior_result_reason(attempt: _ActionAttempt) -> str | None:
    if attempt.result_provenance is None:
        return None
    metadata = attempt.result_provenance.get("metadata")
    if not isinstance(metadata, dict):
        return None
    adapter_evidence = metadata.get("adapter_evidence")
    if not isinstance(adapter_evidence, dict):
        return None
    reason = adapter_evidence.get("reason")
    return None if reason is None else str(reason)


def _same_request_different_attempt_exists(replay: Any, attempt: _ActionAttempt) -> bool:
    for node in replay.nodes.values():
        metadata = node.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        action_metadata = metadata.get(PHASE11_METADATA_KEY)
        if not isinstance(action_metadata, dict):
            continue
        if action_metadata.get("kind") != "action_request_event":
            continue
        if action_metadata.get("request_hash") != attempt.request_hash:
            continue
        if action_metadata.get("idempotency_key") != attempt.idempotency_key:
            return True
    return False
