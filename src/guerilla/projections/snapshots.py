"""Verified snapshots and resume contexts for Phase 14."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from guerilla.codec import canonical_bytes, parse_raw_json, payload_hash
from guerilla.graph import GraphQuery
from guerilla.orchestration.actions import PHASE11_METADATA_KEY
from guerilla.projections.views import (
    DEFAULT_POLICY_VERSION,
    DERIVED_AUTHORITY,
    TRANSFORMATION_VERSION,
    ProjectionEngine,
)
from guerilla.storage import GraphStore

SNAPSHOT_METADATA_KEY = "guerilla_phase14_snapshot"
SNAPSHOT_TRANSFORMATION_VERSION = "phase14-snapshot-v1"
RESUME_CONTEXT_VERSION = "phase14-resume-context-v1"
CONTRACT_VERSION = "0.2.0"


class SnapshotError(ValueError):
    """Raised when a snapshot or resume context cannot be verified."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class SnapshotRequest:
    """Request to capture one verified graph boundary."""

    principal_id: str
    actor: dict[str, Any]
    authority: dict[str, Any]
    created_at: str
    revision: int | None = None
    policy_version: str = DEFAULT_POLICY_VERSION
    persist_summary: bool = True


@dataclass(frozen=True, slots=True)
class SnapshotResult:
    """Result of committing an authoritative snapshot record."""

    snapshot_node_id: str
    workspace_id: str
    source_graph_revision: int
    source_commit_hash: str
    graph_revision: int
    commit_hash: str
    transaction_id: str
    summary_hash: str
    source_node_ids: tuple[str, ...]
    materialized_summary_path: Path | None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_node_ids"] = list(self.source_node_ids)
        value["materialized_summary_path"] = (
            None if self.materialized_summary_path is None else str(self.materialized_summary_path)
        )
        return value


@dataclass(frozen=True, slots=True)
class SnapshotVerificationResult:
    """Verification status for one snapshot record and optional summary file."""

    snapshot_node_id: str
    verified: bool
    source_graph_revision: int | None
    source_commit_hash: str | None
    summary_hash: str | None
    regenerated_summary_hash: str | None
    materialized_summary_status: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["errors"] = list(self.errors)
        value["warnings"] = list(self.warnings)
        return value


@dataclass(frozen=True, slots=True)
class ResumeContext:
    """Bounded derived context for resuming from an authoritative snapshot."""

    snapshot_node_id: str
    context_version: str
    authoritative_facts: dict[str, Any]
    derived_summaries: dict[str, Any]
    stale_observations: tuple[dict[str, Any], ...]
    unknown_outcomes: tuple[dict[str, Any], ...]
    open_goals: tuple[dict[str, Any], ...]
    eligible_operations: tuple[dict[str, Any], ...]
    blocked_operations: tuple[dict[str, Any], ...]
    unresolved_conflicts: tuple[dict[str, Any], ...]
    pending_reconciliation: tuple[dict[str, Any], ...]
    required_refresh_observations: tuple[dict[str, Any], ...]
    relevant_artifact_revisions: tuple[dict[str, Any], ...]
    omitted_information: tuple[str, ...]
    automatic_actions_executed: bool

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for key in (
            "stale_observations",
            "unknown_outcomes",
            "open_goals",
            "eligible_operations",
            "blocked_operations",
            "unresolved_conflicts",
            "pending_reconciliation",
            "required_refresh_observations",
            "relevant_artifact_revisions",
            "omitted_information",
        ):
            value[key] = list(value[key])
        return value


class SnapshotEngine:
    """Create, verify, and resume from source-bound graph snapshots."""

    def __init__(self, *, store: GraphStore) -> None:
        self.store = store

    def create_snapshot(self, request: SnapshotRequest) -> SnapshotResult:
        replay = self.store.replay()
        source_revision = _target_revision(replay, request.revision)
        source_commit_hash = _commit_hash(replay, source_revision)
        snapshot_node_id = str(self.store.ids.generate("node"))
        summary = self._summary(
            snapshot_node_id=snapshot_node_id,
            source_revision=source_revision,
            source_commit_hash=source_commit_hash,
            created_at=request.created_at,
            policy_version=request.policy_version,
        )
        summary_hash = _summary_hash(summary)
        source_node_ids = tuple(summary["source_node_ids"])
        snapshot_node = self._snapshot_node(
            request=request,
            workspace_id=replay.workspace_id,
            snapshot_node_id=snapshot_node_id,
            source_revision=source_revision,
            source_commit_hash=source_commit_hash,
            summary_hash=summary_hash,
            source_node_ids=source_node_ids,
        )
        members = [snapshot_node]
        for source_node_id in source_node_ids:
            members.append(
                self._captured_by_edge(
                    workspace_id=replay.workspace_id,
                    from_node_id=source_node_id,
                    to_node_id=snapshot_node_id,
                    created_at=request.created_at,
                    actor=request.actor,
                )
            )
        commit = self.store.append_transaction(
            members,
            actor=request.actor,
            created_at=request.created_at,
            committed_at=request.created_at,
            principal_id=request.principal_id,
        )
        summary_path = None
        if request.persist_summary:
            summary_path = self._summary_path(snapshot_node_id)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_bytes(canonical_bytes(summary) + b"\n")
        return SnapshotResult(
            snapshot_node_id=snapshot_node_id,
            workspace_id=replay.workspace_id,
            source_graph_revision=source_revision,
            source_commit_hash=source_commit_hash,
            graph_revision=int(commit["graph_revision"]),
            commit_hash=str(commit["commit_hash"]),
            transaction_id=str(commit["transaction_id"]),
            summary_hash=summary_hash,
            source_node_ids=source_node_ids,
            materialized_summary_path=summary_path,
        )

    def verify_snapshot(self, snapshot_node_id: str) -> SnapshotVerificationResult:
        try:
            node, metadata = self._snapshot_metadata(snapshot_node_id)
            source_revision = int(metadata["source_graph_revision"])
            source_commit_hash = str(metadata["source_commit_hash"])
            expected_hash = str(metadata["summary_hash"])
            errors = self._snapshot_errors(snapshot_node_id, metadata)
            regenerated = self._summary(
                snapshot_node_id=snapshot_node_id,
                source_revision=source_revision,
                source_commit_hash=source_commit_hash,
                created_at=str(node["created_at"]),
                policy_version=str(metadata["policy_version"]),
            )
            regenerated_hash = _summary_hash(regenerated)
            if regenerated_hash != expected_hash:
                errors.append("summary_hash_mismatch")
            materialized_status, materialized_warning = self._materialized_summary_status(
                snapshot_node_id,
                expected_hash,
            )
            warnings = [materialized_warning] if materialized_warning is not None else []
            return SnapshotVerificationResult(
                snapshot_node_id=snapshot_node_id,
                verified=not errors,
                source_graph_revision=source_revision,
                source_commit_hash=source_commit_hash,
                summary_hash=expected_hash,
                regenerated_summary_hash=regenerated_hash,
                materialized_summary_status=materialized_status,
                errors=tuple(errors),
                warnings=tuple(warnings),
            )
        except SnapshotError as exc:
            return SnapshotVerificationResult(
                snapshot_node_id=snapshot_node_id,
                verified=False,
                source_graph_revision=None,
                source_commit_hash=None,
                summary_hash=None,
                regenerated_summary_hash=None,
                materialized_summary_status="unavailable",
                errors=(exc.code,),
                warnings=(),
            )

    def resume_context(self, snapshot_node_id: str) -> ResumeContext:
        verification = self.verify_snapshot(snapshot_node_id)
        if not verification.verified:
            raise SnapshotError("snapshot_verification_failed", ",".join(verification.errors))
        node, metadata = self._snapshot_metadata(snapshot_node_id)
        summary = self._summary(
            snapshot_node_id=snapshot_node_id,
            source_revision=int(metadata["source_graph_revision"]),
            source_commit_hash=str(metadata["source_commit_hash"]),
            created_at=str(node["created_at"]),
            policy_version=str(metadata["policy_version"]),
        )
        resume = summary["resume"]
        return ResumeContext(
            snapshot_node_id=snapshot_node_id,
            context_version=RESUME_CONTEXT_VERSION,
            authoritative_facts={
                "workspace_id": summary["workspace_id"],
                "source_graph_revision": summary["source_graph_revision"],
                "source_commit_hash": summary["source_commit_hash"],
                "snapshot_node_id": snapshot_node_id,
                "graph_heads": summary["graph_heads"],
                "captured_source_node_ids": summary["source_node_ids"],
            },
            derived_summaries={
                "manifest": summary["manifest"],
                "progress": summary["progress"],
                "traceability": summary["traceability"],
                "summary_hash": _summary_hash(summary),
                "authoritative_status": DERIVED_AUTHORITY,
            },
            stale_observations=tuple(resume["stale_observations"]),
            unknown_outcomes=tuple(resume["unknown_outcomes"]),
            open_goals=tuple(resume["open_goals"]),
            eligible_operations=tuple(resume["eligible_operations"]),
            blocked_operations=tuple(resume["blocked_operations"]),
            unresolved_conflicts=tuple(resume["unresolved_conflicts"]),
            pending_reconciliation=tuple(resume["pending_reconciliation"]),
            required_refresh_observations=tuple(resume["required_refresh_observations"]),
            relevant_artifact_revisions=tuple(resume["relevant_artifact_revisions"]),
            omitted_information=tuple(summary["information_loss"]),
            automatic_actions_executed=False,
        )

    def _summary(
        self,
        *,
        snapshot_node_id: str,
        source_revision: int,
        source_commit_hash: str,
        created_at: str,
        policy_version: str,
    ) -> dict[str, Any]:
        replay = self.store.replay()
        query = GraphQuery(replay)
        nodes = query._visible_nodes(source_revision)
        engine = ProjectionEngine(store=self.store)
        manifest = engine.manifest(revision=source_revision, policy_version=policy_version)
        progress = engine.progress(revision=source_revision, policy_version=policy_version)
        traceability = engine.traceability(revision=source_revision, policy_version=policy_version)
        conflicts = engine.conflict(
            revision=source_revision,
            status="open",
            policy_version=policy_version,
        )
        actions = _action_resume_items(nodes, replay.record_revisions)
        open_goals = _nodes_by_type(
            nodes,
            "goal",
            excluded_statuses={"completed", "closed", "resolved"},
        )
        active_operations = _nodes_by_type(
            nodes,
            "operation",
            excluded_statuses={"completed", "closed", "resolved"},
        )
        blocked_operations = active_operations if conflicts.payload["conflicts"] else []
        source_node_ids = sorted(
            node_id for node_id, node in nodes.items() if node["node_type"] != "snapshot"
        )
        freshness_requirements = list(manifest.payload["stale_observation_reports"])
        return {
            "snapshot_node_id": snapshot_node_id,
            "workspace_id": replay.workspace_id,
            "source_graph_revision": source_revision,
            "source_commit_hash": source_commit_hash,
            "graph_heads": progress.payload["structural_heads"],
            "open_goals": open_goals,
            "active_operations": active_operations,
            "blocked_operations": blocked_operations,
            "unresolved_conflicts": conflicts.payload["conflicts"],
            "latest_relevant_artifact_revisions": manifest.payload["entries"],
            "pending_unknown_external_actions": actions,
            "freshness_requirements": freshness_requirements,
            "source_query": {
                "view": "snapshot",
                "source_graph_revision": source_revision,
                "scope": "phase14-default-continuity-boundary",
            },
            "source_node_ids": source_node_ids,
            "transformation_version": SNAPSHOT_TRANSFORMATION_VERSION,
            "projection_transformation_version": TRANSFORMATION_VERSION,
            "policy_version": policy_version,
            "created_at": created_at,
            "authoritative_status": DERIVED_AUTHORITY,
            "information_loss": [
                "snapshot summary stores bounded continuity fields, not full record bodies",
                "external observations require refresh before unsafe continuation",
                "pending or unknown external outcomes require reconciliation before retry",
            ],
            "manifest": _projection_digest(manifest),
            "progress": _projection_digest(progress),
            "traceability": _projection_digest(traceability),
            "resume": {
                "authoritative_facts": {
                    "source_graph_revision": source_revision,
                    "source_commit_hash": source_commit_hash,
                    "graph_heads": progress.payload["structural_heads"],
                },
                "derived_summaries": {
                    "manifest_entries": manifest.payload["entries"],
                    "progress": progress.payload,
                    "traceability_edges": traceability.payload["edges"],
                },
                "stale_observations": freshness_requirements,
                "unknown_outcomes": [
                    item for item in actions if item["resume_classification"] == "unknown_outcome"
                ],
                "open_goals": open_goals,
                "eligible_operations": active_operations,
                "blocked_operations": blocked_operations,
                "unresolved_conflicts": conflicts.payload["conflicts"],
                "pending_reconciliation": [
                    item for item in actions if item["requires_reconciliation"]
                ],
                "required_refresh_observations": freshness_requirements,
                "relevant_artifact_revisions": manifest.payload["entries"],
                "omitted_information": [
                    "full graph record bodies",
                    "current external-system state",
                    "adapter-native history not recorded in the graph",
                ],
                "automatic_actions_executed": False,
            },
        }

    def _snapshot_node(
        self,
        *,
        request: SnapshotRequest,
        workspace_id: str,
        snapshot_node_id: str,
        source_revision: int,
        source_commit_hash: str,
        summary_hash: str,
        source_node_ids: tuple[str, ...],
    ) -> dict[str, Any]:
        return {
            "record_type": "node",
            "protocol_version": CONTRACT_VERSION,
            "workspace_id": workspace_id,
            "node_id": snapshot_node_id,
            "entity_id": str(self.store.ids.generate("entity")),
            "node_type": "snapshot",
            "created_at": request.created_at,
            "actor": request.actor,
            "authority": request.authority,
            "status": "captured",
            "provenance": {
                "source": "guerilla.phase14.snapshot",
                "source_record_ids": list(source_node_ids),
            },
            "payload_ref": {"retention_class": "none"},
            "metadata": {
                SNAPSHOT_METADATA_KEY: {
                    "kind": "snapshot_record",
                    "snapshot_node_id": snapshot_node_id,
                    "source_graph_revision": source_revision,
                    "source_commit_hash": source_commit_hash,
                    "source_query": {
                        "view": "snapshot",
                        "source_graph_revision": source_revision,
                        "scope": "phase14-default-continuity-boundary",
                    },
                    "source_node_ids": list(source_node_ids),
                    "transformation_version": SNAPSHOT_TRANSFORMATION_VERSION,
                    "projection_transformation_version": TRANSFORMATION_VERSION,
                    "policy_version": request.policy_version,
                    "summary_hash": summary_hash,
                    "information_loss": [
                        "snapshot record pins derived summary hash and source nodes",
                        "materialized summary is not authoritative",
                    ],
                    "freshness_requirements": [
                        "refresh external observations before unsafe mutation",
                        "reconcile pending or unknown actions before unsafe retry",
                    ],
                    "materialized_summary_path": str(self._summary_path(snapshot_node_id)),
                }
            },
            "extensions": {},
            "record_hash": "0" * 64,
        }

    def _captured_by_edge(
        self,
        *,
        workspace_id: str,
        from_node_id: str,
        to_node_id: str,
        created_at: str,
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "record_type": "edge",
            "protocol_version": CONTRACT_VERSION,
            "workspace_id": workspace_id,
            "edge_id": str(self.store.ids.generate("edge")),
            "relationship_type": "captured_by",
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "created_at": created_at,
            "actor": actor,
            "provenance": {
                "source": "guerilla.phase14.snapshot",
                "source_record_ids": [from_node_id, to_node_id],
            },
            "metadata": {
                SNAPSHOT_METADATA_KEY: {
                    "kind": "snapshot_captured_source",
                    "snapshot_node_id": to_node_id,
                }
            },
            "extensions": {},
            "record_hash": "0" * 64,
        }

    def _snapshot_metadata(self, snapshot_node_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        replay = self.store.replay()
        node = replay.nodes.get(snapshot_node_id)
        if node is None or node.get("node_type") != "snapshot":
            raise SnapshotError("missing_snapshot", "snapshot node was not found")
        metadata = node.get("metadata", {}).get(SNAPSHOT_METADATA_KEY)
        if not isinstance(metadata, dict):
            raise SnapshotError("invalid_snapshot", "snapshot metadata is missing")
        return node, metadata

    def _snapshot_errors(self, snapshot_node_id: str, metadata: dict[str, Any]) -> list[str]:
        replay = self.store.replay()
        errors = []
        source_revision = int(metadata["source_graph_revision"])
        if source_revision > replay.graph_revision:
            errors.append("source_revision_ahead")
            return errors
        if _commit_hash(replay, source_revision) != metadata["source_commit_hash"]:
            errors.append("source_commit_mismatch")
        source_nodes = [str(node_id) for node_id in metadata.get("source_node_ids", [])]
        visible = GraphQuery(replay)._visible_nodes(source_revision)
        missing = [node_id for node_id in source_nodes if node_id not in visible]
        if missing:
            errors.append("missing_source_nodes")
        captured = {
            str(edge["from_node_id"])
            for edge in replay.edges.values()
            if edge["relationship_type"] == "captured_by" and edge["to_node_id"] == snapshot_node_id
        }
        if set(source_nodes) - captured:
            errors.append("missing_captured_by_edges")
        if metadata.get("transformation_version") != SNAPSHOT_TRANSFORMATION_VERSION:
            errors.append("unsupported_snapshot_transformation")
        return errors

    def _materialized_summary_status(
        self,
        snapshot_node_id: str,
        expected_hash: str,
    ) -> tuple[str, str | None]:
        path = self._summary_path(snapshot_node_id)
        if not path.exists():
            return "missing", "materialized_summary_missing"
        try:
            raw = path.read_bytes()
            if not raw.endswith(b"\n"):
                return "corrupt", "materialized_summary_corrupt"
            parsed = parse_raw_json(raw[:-1])
            if not isinstance(parsed, dict):
                return "corrupt", "materialized_summary_corrupt"
            if canonical_bytes(parsed) + b"\n" != raw:
                return "corrupt", "materialized_summary_corrupt"
            if _summary_hash(parsed) != expected_hash:
                return "corrupt", "materialized_summary_hash_mismatch"
        except Exception:
            return "corrupt", "materialized_summary_corrupt"
        return "present", None

    def _summary_path(self, snapshot_node_id: str) -> Path:
        return self.store.root / ".guerilla" / "snapshots" / f"{snapshot_node_id}.summary.json"


def _target_revision(replay: Any, revision: int | None) -> int:
    target = replay.graph_revision if revision is None else revision
    if target < 0:
        raise SnapshotError("invalid_revision", "snapshot revision must be non-negative")
    if target > replay.graph_revision:
        raise SnapshotError("revision_ahead", "snapshot revision is ahead of replay")
    return int(target)


def _commit_hash(replay: Any, revision: int) -> str:
    if revision == 0:
        return "0" * 64
    for commit in replay.commits:
        if commit.graph_revision == revision:
            return str(commit.commit_hash)
    raise SnapshotError("missing_commit", "source revision has no commit")


def _summary_hash(summary: dict[str, Any]) -> str:
    return payload_hash(canonical_bytes(summary))


def _projection_digest(result: Any) -> dict[str, Any]:
    return {
        "view_type": result.view_type,
        "graph_revision": result.graph_revision,
        "commit_hash": result.commit_hash,
        "source_query": result.source_query,
        "source_node_ids": list(result.source_node_ids),
        "result_hash": result.result_hash,
        "authoritative_status": result.authoritative_status,
        "payload": result.payload,
    }


def _nodes_by_type(
    nodes: dict[str, dict[str, Any]],
    node_type: str,
    *,
    excluded_statuses: set[str],
) -> list[dict[str, Any]]:
    return [
        {
            "node_id": node["node_id"],
            "node_type": node["node_type"],
            "status": node["status"],
            "state_boundary_id": node.get("state_boundary_id"),
        }
        for node in sorted(nodes.values(), key=lambda item: (item["node_type"], item["node_id"]))
        if node["node_type"] == node_type and node["status"] not in excluded_statuses
    ]


def _action_resume_items(
    nodes: dict[str, dict[str, Any]],
    record_revisions: dict[str, int],
) -> list[dict[str, Any]]:
    attempts: dict[str, dict[str, Any]] = {}
    for node_id, node in sorted(
        nodes.items(), key=lambda item: (record_revisions[item[0]], item[0])
    ):
        metadata = node.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        action = metadata.get(PHASE11_METADATA_KEY)
        if not isinstance(action, dict):
            continue
        intent_node_id = str(action.get("intent_node_id", node_id))
        item = attempts.setdefault(
            intent_node_id,
            {
                "intent_node_id": intent_node_id,
                "invocation_node_id": None,
                "result_node_id": None,
                "idempotency_key": action.get("idempotency_key"),
                "adapter_id": action.get("adapter_id"),
                "state_boundary_id": action.get("state_boundary_id"),
                "action": action.get("action"),
                "classification": None,
                "resume_classification": "pending_reconciliation",
                "requires_reconciliation": True,
            },
        )
        kind = action.get("kind")
        if kind == "invocation_started_event":
            item["invocation_node_id"] = node_id
        if kind == "action_result_event":
            item["result_node_id"] = node_id
            classification = str(action.get("external_result_classification"))
            item["classification"] = classification
            item["requires_reconciliation"] = classification in {"pending", "outcome_unknown"}
            item["resume_classification"] = (
                "unknown_outcome"
                if classification == "outcome_unknown"
                else "pending_reconciliation"
                if classification == "pending"
                else "result_recorded"
            )
        reconciliation = metadata.get("guerilla_phase12_reconciliation")
        if (
            isinstance(reconciliation, dict)
            and reconciliation.get("kind") == "reconciliation_event"
        ):
            intent = reconciliation.get("intent_node_id")
            if intent in attempts and reconciliation.get("classification") not in {"unknown"}:
                attempts[str(intent)]["requires_reconciliation"] = False
    return [
        item
        for item in attempts.values()
        if item["requires_reconciliation"] or item["resume_classification"] == "unknown_outcome"
    ]
