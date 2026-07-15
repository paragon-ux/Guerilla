"""Evidence-backed conflict and decision records for Phase 12."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, TypeAlias

from guerilla.storage import GraphStore

CONTRACT_VERSION = "0.2.0"
PHASE12_CONFLICT_METADATA_KEY = "guerilla_phase12_conflict"

ConflictType: TypeAlias = Literal[
    "stale_external_revision",
    "identity_collision",
    "ambiguous_authority",
    "state_boundary_violation",
    "lineage_cycle",
    "missing_endpoint",
    "idempotency_conflict",
    "external_outcome_unknown",
    "failed_evaluation",
    "incomplete_lineage",
]
ConflictSeverity: TypeAlias = Literal["low", "medium", "high", "critical"]
ConflictStatus: TypeAlias = Literal["open", "deferred", "resolved_by_reconciliation"]


class ConflictError(ValueError):
    """Raised when a conflict or decision record cannot be appended safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ConflictRecordRequest:
    """Append-only request for one evidence-backed conflict node."""

    conflict_type: ConflictType
    conflict_reason: str
    subject_node_id: str
    evidence_node_ids: tuple[str, ...]
    principal_id: str
    actor: dict[str, Any]
    authority: dict[str, Any]
    detected_at: str
    severity: ConflictSeverity
    required_resolution_class: str
    summary: str
    expected_graph_revision: int | None = None
    status: ConflictStatus = "open"
    policy_version: str = "local-owner-v1"
    limitations: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)
    extensions: dict[str, Any] = field(default_factory=dict)
    fail_at: str | None = None


@dataclass(frozen=True, slots=True)
class ConflictRecordResult:
    """Derived response for a committed conflict."""

    workspace_id: str
    graph_revision: int
    commit_hash: str
    transaction_id: str
    conflict_node_id: str
    conflict_type: ConflictType
    status: ConflictStatus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConflictResolutionRequest:
    """Append-only request for a decision resolving one conflict."""

    conflict_node_id: str
    alternatives: tuple[dict[str, Any], ...]
    chosen_outcome: str
    rationale: str
    principal_id: str
    actor: dict[str, Any]
    authority: dict[str, Any]
    decided_at: str
    expected_graph_revision: int | None = None
    evidence_node_ids: tuple[str, ...] = ()
    continuation_operation: dict[str, Any] | None = None
    policy_version: str = "local-owner-v1"
    limitations: tuple[str, ...] = ()
    extensions: dict[str, Any] = field(default_factory=dict)
    fail_at: str | None = None


@dataclass(frozen=True, slots=True)
class ConflictResolutionResult:
    """Derived response for a committed conflict decision."""

    workspace_id: str
    graph_revision: int
    commit_hash: str
    transaction_id: str
    conflict_node_id: str
    decision_node_id: str
    continuation_operation_node_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConflictEngine:
    """Append conflict and resolution lineage without rewriting prior records."""

    def __init__(self, *, store: GraphStore) -> None:
        self.store = store

    def record_conflict(self, request: ConflictRecordRequest) -> ConflictRecordResult:
        replay = self.store.replay()
        self._require_registered_conflict_type(request.conflict_type)
        self._require_existing_node(replay, request.subject_node_id)
        for evidence_node_id in request.evidence_node_ids:
            self._require_evidence_node(replay, evidence_node_id)

        conflict_node_id = str(self.store.ids.generate("node"))
        conflict_node = self._node(
            workspace_id=replay.workspace_id,
            node_id=conflict_node_id,
            entity_id=str(self.store.ids.generate("entity")),
            node_type="conflict",
            created_at=request.detected_at,
            actor=request.actor,
            authority=request.authority,
            status=request.status,
            provenance={
                "source": "guerilla.phase12.conflict_engine",
                "source_record_ids": _unique_ids(
                    [request.subject_node_id, *request.evidence_node_ids]
                ),
                "metadata": {
                    "conflict_type": request.conflict_type,
                    "conflict_reason": request.conflict_reason,
                },
            },
            metadata={
                "conflict_type": request.conflict_type,
                "summary": request.summary,
                PHASE12_CONFLICT_METADATA_KEY: {
                    "kind": "conflict",
                    "conflict_type": request.conflict_type,
                    "conflict_reason": request.conflict_reason,
                    "subject_node_id": request.subject_node_id,
                    "evidence_node_ids": list(request.evidence_node_ids),
                    "authority": request.authority,
                    "severity": request.severity,
                    "status": request.status,
                    "detected_at": request.detected_at,
                    "policy_version": request.policy_version,
                    "required_resolution_class": request.required_resolution_class,
                    "limitations": list(request.limitations),
                    "details": request.details,
                },
            },
            extensions=request.extensions,
        )
        members = [conflict_node]
        for evidence_node_id in request.evidence_node_ids:
            members.append(
                self._edge(
                    workspace_id=replay.workspace_id,
                    relationship_type="evidences",
                    from_node_id=evidence_node_id,
                    to_node_id=conflict_node_id,
                    created_at=request.detected_at,
                    actor=request.actor,
                    source_record_ids=[evidence_node_id, conflict_node_id],
                    metadata={
                        "kind": "conflict_evidence",
                        "conflict_type": request.conflict_type,
                    },
                )
            )
        commit = self.store.append_transaction(
            members,
            actor=request.actor,
            created_at=request.detected_at,
            committed_at=request.detected_at,
            principal_id=request.principal_id,
            expected_graph_revision=request.expected_graph_revision,
            fail_at="after_stage" if request.fail_at == "conflict_commit_after_stage" else None,
        )
        return ConflictRecordResult(
            workspace_id=replay.workspace_id,
            graph_revision=int(commit["graph_revision"]),
            commit_hash=str(commit["commit_hash"]),
            transaction_id=str(commit["transaction_id"]),
            conflict_node_id=conflict_node_id,
            conflict_type=request.conflict_type,
            status=request.status,
        )

    def resolve_conflict(self, request: ConflictResolutionRequest) -> ConflictResolutionResult:
        replay = self.store.replay()
        conflict = self._require_existing_node(replay, request.conflict_node_id)
        if conflict["node_type"] != "conflict":
            raise ConflictError("invalid_message", "resolved node must be a conflict")
        if self._has_resolution(replay, request.conflict_node_id):
            raise ConflictError("conflict_already_resolved", "conflict already has a resolution")
        for evidence_node_id in request.evidence_node_ids:
            self._require_evidence_node(replay, evidence_node_id)

        decision_node_id = str(self.store.ids.generate("node"))
        decision_node = self._node(
            workspace_id=replay.workspace_id,
            node_id=decision_node_id,
            entity_id=str(self.store.ids.generate("entity")),
            node_type="decision",
            created_at=request.decided_at,
            actor=request.actor,
            authority=request.authority,
            status="resolved",
            provenance={
                "source": "guerilla.phase12.conflict_engine",
                "source_record_ids": _unique_ids(
                    [request.conflict_node_id, *request.evidence_node_ids]
                ),
                "metadata": {"resolved_conflict_node_id": request.conflict_node_id},
            },
            metadata={
                PHASE12_CONFLICT_METADATA_KEY: {
                    "kind": "conflict_resolution_decision",
                    "conflict_node_id": request.conflict_node_id,
                    "alternatives": list(request.alternatives),
                    "chosen_outcome": request.chosen_outcome,
                    "rationale": request.rationale,
                    "responsible_principal_id": request.principal_id,
                    "responsible_actor": request.actor,
                    "evidence_node_ids": list(request.evidence_node_ids),
                    "policy_version": request.policy_version,
                    "limitations": list(request.limitations),
                    "continuation_operation": request.continuation_operation,
                }
            },
            extensions=request.extensions,
        )
        members = [
            decision_node,
            self._edge(
                workspace_id=replay.workspace_id,
                relationship_type="resolved_by",
                from_node_id=request.conflict_node_id,
                to_node_id=decision_node_id,
                created_at=request.decided_at,
                actor=request.actor,
                source_record_ids=[request.conflict_node_id, decision_node_id],
                metadata={"kind": "conflict_resolved_by_decision"},
            ),
        ]
        for evidence_node_id in request.evidence_node_ids:
            members.append(
                self._edge(
                    workspace_id=replay.workspace_id,
                    relationship_type="evidences",
                    from_node_id=evidence_node_id,
                    to_node_id=decision_node_id,
                    created_at=request.decided_at,
                    actor=request.actor,
                    source_record_ids=[evidence_node_id, decision_node_id],
                    metadata={"kind": "decision_evidence"},
                )
            )

        continuation_node_id = None
        if request.continuation_operation is not None:
            continuation_node_id = str(self.store.ids.generate("node"))
            members.append(
                self._node(
                    workspace_id=replay.workspace_id,
                    node_id=continuation_node_id,
                    entity_id=str(self.store.ids.generate("entity")),
                    node_type="operation",
                    created_at=request.decided_at,
                    actor=request.actor,
                    authority=request.authority,
                    status="continuation_planned",
                    provenance={
                        "source": "guerilla.phase12.conflict_engine",
                        "source_record_ids": [decision_node_id],
                    },
                    metadata={
                        PHASE12_CONFLICT_METADATA_KEY: {
                            "kind": "continuation_operation",
                            "decision_node_id": decision_node_id,
                            "conflict_node_id": request.conflict_node_id,
                            "operation": request.continuation_operation,
                        }
                    },
                    extensions={},
                )
            )
            members.append(
                self._edge(
                    workspace_id=replay.workspace_id,
                    relationship_type="depends_on",
                    from_node_id=decision_node_id,
                    to_node_id=continuation_node_id,
                    created_at=request.decided_at,
                    actor=request.actor,
                    source_record_ids=[decision_node_id, continuation_node_id],
                    metadata={"kind": "decision_prerequisite_for_continuation"},
                )
            )

        commit = self.store.append_transaction(
            members,
            actor=request.actor,
            created_at=request.decided_at,
            committed_at=request.decided_at,
            principal_id=request.principal_id,
            expected_graph_revision=request.expected_graph_revision,
            fail_at="after_stage" if request.fail_at == "decision_commit_after_stage" else None,
        )
        return ConflictResolutionResult(
            workspace_id=replay.workspace_id,
            graph_revision=int(commit["graph_revision"]),
            commit_hash=str(commit["commit_hash"]),
            transaction_id=str(commit["transaction_id"]),
            conflict_node_id=request.conflict_node_id,
            decision_node_id=decision_node_id,
            continuation_operation_node_id=continuation_node_id,
        )

    def _require_registered_conflict_type(self, conflict_type: str) -> None:
        entries = self.store.contracts.registries["conflict_types.json"]["entries"]
        registered = {str(entry["value"]) for entry in entries}
        if conflict_type not in registered:
            raise ConflictError("unsupported_conflict_type", "conflict type is not registered")

    @staticmethod
    def _require_existing_node(replay: Any, node_id: str) -> dict[str, Any]:
        node = replay.nodes.get(node_id)
        if not isinstance(node, dict):
            raise ConflictError("missing_endpoint", "node does not exist")
        return node

    def _require_evidence_node(self, replay: Any, node_id: str) -> dict[str, Any]:
        node = self._require_existing_node(replay, node_id)
        if node["node_type"] not in {"artifact", "event", "evaluation"}:
            raise ConflictError(
                "incompatible_endpoint_type",
                "conflict evidence must be an artifact, event, or evaluation node",
            )
        return node

    @staticmethod
    def _has_resolution(replay: Any, conflict_node_id: str) -> bool:
        return any(
            edge["relationship_type"] == "resolved_by" and edge["from_node_id"] == conflict_node_id
            for edge in replay.edges.values()
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
        extensions: dict[str, Any],
    ) -> dict[str, Any]:
        return {
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
            "extensions": extensions,
            "record_hash": "0" * 64,
        }

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
                "source": "guerilla.phase12.conflict_engine",
                "source_record_ids": source_record_ids,
            },
            "metadata": {PHASE12_CONFLICT_METADATA_KEY: metadata},
            "extensions": {},
            "record_hash": "0" * 64,
        }


def _unique_ids(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
