"""Phase 15 local CLI workflow facade.

The CLI delegates to the same storage, adapter, orchestration, reconciliation,
projection, and snapshot APIs used by integration tests. It does not introduce
an alternate mutation path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

from guerilla.adapters import (
    AdapterHost,
    AdapterOperationRequest,
    AsyncUnknownOutcomeAdapter,
    ReconstructedFilesystemAdapter,
    TransactionalRevisionedServiceAdapter,
    VirtualClock,
)
from guerilla.conflicts import (
    PHASE12_CONFLICT_METADATA_KEY,
    ConflictEngine,
    ConflictRecordRequest,
    ConflictResolutionRequest,
)
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.graph import GraphQuery
from guerilla.index import SQLiteGraphIndex
from guerilla.observability import ObservationIngestionRequest, ObservationIngestor
from guerilla.orchestration import ActionExecutionRequest, ActionOrchestrator
from guerilla.orchestration.actions import PHASE11_METADATA_KEY
from guerilla.projections import ProjectionEngine, SnapshotEngine, SnapshotRequest
from guerilla.reconciliation import ReconciliationEngine, ReconciliationRequest
from guerilla.storage import GraphStore, initialize_workspace

CONTRACT_VERSION = "0.2.0"
DEFAULT_TIMESTAMP = "2026-07-14T00:00:00Z"
PHASE15_METADATA_KEY = "guerilla_phase15_cli"


class CliWorkflowError(ValueError):
    """Raised for stable JSON CLI failures."""

    def __init__(self, code: str, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


@dataclass(slots=True)
class Phase15Context:
    """Injectable CLI context used by E2E tests and command dispatch."""

    root: Path
    contracts: ContractBundle
    principal_id: str = "local-user"
    clock: VirtualClock = field(default_factory=VirtualClock)
    adapters: dict[str, Any] = field(default_factory=dict)
    host: AdapterHost | None = None

    def __post_init__(self) -> None:
        if not self.adapters:
            filesystem_root = self.root / ".guerilla" / "tmp" / "phase15-filesystem"
            self.adapters = {
                "transactional": TransactionalRevisionedServiceAdapter(),
                "filesystem": ReconstructedFilesystemAdapter(filesystem_root),
                "async": AsyncUnknownOutcomeAdapter(clock=self.clock),
            }
        if self.host is None:
            self.host = AdapterHost(
                contracts=self.contracts,
                adapters=list(self.adapters.values()),
                owner_principal_id=self.principal_id,
                clock_ms=self.clock.now_ms,
            )


class Phase15Runtime:
    """Local command facade over the authoritative runtime APIs."""

    def __init__(self, context: Phase15Context) -> None:
        self.context = context

    @property
    def root(self) -> Path:
        return self.context.root

    @property
    def contracts(self) -> ContractBundle:
        return self.context.contracts

    @property
    def principal_id(self) -> str:
        return self.context.principal_id

    @property
    def host(self) -> AdapterHost:
        if self.context.host is None:  # pragma: no cover - guarded by Phase15Context
            raise CliWorkflowError("internal_error", "adapter host is not initialized")
        return self.context.host

    def store(self) -> GraphStore:
        return GraphStore(self.root, contracts=self.contracts, owner_principal_id=self.principal_id)

    def workspace_init(self, *, workspace_id: str, created_at: str) -> dict[str, Any]:
        header = initialize_workspace(
            self.root,
            workspace_id=workspace_id,
            created_at=created_at,
            contracts=self.contracts,
        )
        replay = self.store().replay()
        return {
            "workspace": header,
            "graph_revision": replay.graph_revision,
            "commit_hash": replay.last_commit_hash,
            "warnings": replay.warnings,
        }

    def workspace_show(self) -> dict[str, Any]:
        replay = self.store().replay()
        return {
            "workspace_id": replay.workspace_id,
            "graph_revision": replay.graph_revision,
            "commit_hash": replay.last_commit_hash,
            "node_count": len(replay.nodes),
            "edge_count": len(replay.edges),
            "warnings": replay.warnings,
        }

    def adapter_list(self) -> dict[str, Any]:
        adapters = []
        for alias, adapter in sorted(self.context.adapters.items()):
            descriptor = adapter.descriptor
            adapters.append(
                {
                    "alias": alias,
                    "adapter_id": descriptor["adapter_id"],
                    "name": descriptor["name"],
                    "version": descriptor["version"],
                    "system_id": descriptor["system_id"],
                    "state_boundary_ids": [
                        boundary["state_boundary_id"] for boundary in descriptor["state_boundaries"]
                    ],
                    "capabilities": [
                        capability["capability"]
                        for capability in descriptor["capabilities"]
                        if capability.get("supported") is True
                    ],
                }
            )
        return {"adapters": adapters}

    def adapter_describe(self, adapter_ref: str, *, at: str) -> dict[str, Any]:
        adapter = self._adapter(adapter_ref)
        descriptor = adapter.descriptor
        boundary_id = str(descriptor["state_boundaries"][0]["state_boundary_id"])
        result = self.host.invoke(
            AdapterOperationRequest(
                workspace_id=self.store().replay().workspace_id,
                adapter_id=str(descriptor["adapter_id"]),
                adapter_version=str(descriptor["version"]),
                system_id=str(descriptor["system_id"]),
                state_boundary_id=boundary_id,
                operation_id=str(self.store().ids.generate("message")),
                principal_id=self.principal_id,
                actor=_actor(self.principal_id),
                authority=_authority(self.principal_id),
                contract_version=CONTRACT_VERSION,
                requested_at=at,
                capability="describe",
                data={},
            )
        )
        return result.to_dict()

    def adapter_validate(self) -> dict[str, Any]:
        # Host construction has already validated every descriptor and boundary.
        return {
            "validated": True,
            "adapter_count": len(self.context.adapters),
            "boundary_count": len(self.host.boundaries.boundaries),
        }

    def create_local_node(
        self,
        *,
        node_type: str,
        status: str,
        metadata: dict[str, Any],
        created_at: str,
        expected_graph_revision: int | None,
        source_node_ids: list[str] | None = None,
        relationships: list[tuple[str, str, str]] | None = None,
    ) -> dict[str, Any]:
        store = self.store()
        self._require_expected_revision(store, expected_graph_revision)
        replay = store.replay()
        node_id = str(store.ids.generate("node"))
        source_ids = [] if source_node_ids is None else source_node_ids
        node = {
            "record_type": "node",
            "protocol_version": CONTRACT_VERSION,
            "workspace_id": replay.workspace_id,
            "node_id": node_id,
            "entity_id": str(store.ids.generate("entity")),
            "node_type": node_type,
            "created_at": created_at,
            "actor": _actor(self.principal_id),
            "authority": _authority(self.principal_id),
            "status": status,
            "provenance": {
                "source": "guerilla.phase15.cli",
                "source_record_ids": source_ids,
                "metadata": {"phase": 15, "node_type": node_type},
            },
            "payload_ref": {"retention_class": "metadata", "metadata": metadata},
            "metadata": {
                PHASE15_METADATA_KEY: {
                    "kind": node_type,
                    "status": status,
                    "details": metadata,
                }
            },
            "extensions": {},
            "record_hash": "0" * 64,
        }
        members: list[dict[str, Any]] = [node]
        for relationship_type, from_node_id, to_node_id in relationships or []:
            members.append(
                self._edge(
                    store=store,
                    workspace_id=replay.workspace_id,
                    relationship_type=relationship_type,
                    from_node_id=from_node_id,
                    to_node_id=to_node_id,
                    created_at=created_at,
                    source_record_ids=[from_node_id, to_node_id],
                )
            )
        commit = store.append_transaction(
            members,
            actor=_actor(self.principal_id),
            created_at=created_at,
            committed_at=created_at,
            principal_id=self.principal_id,
        )
        return {
            "node_id": node_id,
            "node_type": node_type,
            "graph_revision": commit["graph_revision"],
            "commit_hash": commit["commit_hash"],
            "transaction_id": commit["transaction_id"],
        }

    def observe(
        self,
        adapter_ref: str,
        *,
        selector: dict[str, Any],
        at: str,
        expected_graph_revision: int | None,
        root: str | None = None,
        namespace: str | None = None,
    ) -> dict[str, Any]:
        adapter = self._adapter(adapter_ref)
        self._require_expected_revision(self.store(), expected_graph_revision)
        result = ObservationIngestor(store=self.store(), host=self.host).ingest(
            ObservationIngestionRequest(
                adapter_id=str(adapter.adapter_id),
                state_boundary_id=str(adapter.boundary_id),
                selector=selector,
                principal_id=self.principal_id,
                actor=_actor(self.principal_id),
                authority=_authority(self.principal_id),
                requested_at=at,
                received_at=at,
                commit_at=at,
                root=root,
                namespace=namespace,
                correlation_id=f"phase15-observe-{adapter_ref}",
            )
        )
        return result.to_dict()

    def act(
        self,
        adapter_ref: str,
        *,
        action: str,
        arguments: dict[str, Any],
        idempotency_key: str,
        at: str,
        expected_graph_revision: int | None,
        expected_external_revision: str | None = None,
        root: str | None = None,
        namespace: str | None = None,
        after_state_selector: dict[str, Any] | None = None,
        fail_at: str | None = None,
    ) -> dict[str, Any]:
        adapter = self._adapter(adapter_ref)
        result = ActionOrchestrator(store=self.store(), host=self.host).execute(
            ActionExecutionRequest(
                adapter_id=str(adapter.adapter_id),
                state_boundary_id=str(adapter.boundary_id),
                action=action,
                arguments=arguments,
                idempotency_key=idempotency_key,
                principal_id=self.principal_id,
                actor=_actor(self.principal_id),
                authority=_authority(self.principal_id),
                requested_at=at,
                intent_committed_at=at,
                invocation_started_at=at,
                result_committed_at=at,
                expected_graph_revision=expected_graph_revision,
                expected_external_revision=expected_external_revision,
                root=root,
                namespace=namespace,
                correlation_id=f"phase15-action-{idempotency_key}",
                causation_id=f"phase15-cause-{idempotency_key}",
                after_state_selector=after_state_selector,
                after_state_observed_at=at if after_state_selector is not None else None,
                fail_at=fail_at,
            )
        )
        return result.to_dict()

    def reconcile(
        self,
        adapter_ref: str,
        *,
        intent_node_id: str,
        idempotency_key: str,
        at: str,
        expected_graph_revision: int | None,
        namespace: str | None = None,
        root: str | None = None,
        after_state_selector: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        adapter = self._adapter(adapter_ref)
        self._require_expected_revision(self.store(), expected_graph_revision)
        result = ReconciliationEngine(store=self.store(), host=self.host).reconcile(
            ReconciliationRequest(
                adapter_id=str(adapter.adapter_id),
                state_boundary_id=str(adapter.boundary_id),
                intent_node_id=intent_node_id,
                idempotency_key=idempotency_key,
                principal_id=self.principal_id,
                actor=_actor(self.principal_id),
                authority=_authority(self.principal_id),
                requested_at=at,
                reconciled_at=at,
                root=root,
                namespace=namespace,
                correlation_id=f"phase15-reconcile-{idempotency_key}",
                after_state_selector=after_state_selector,
                after_state_observed_at=at if after_state_selector is not None else None,
            )
        )
        return result.to_dict()

    def unresolved_intents(self) -> dict[str, Any]:
        replay = self.store().replay()
        result_nodes_by_key = _phase11_by_key(replay, "action_result_event")
        unresolved = []
        for node in _phase11_nodes_by_kind(replay, "action_request_event"):
            metadata = node["metadata"][PHASE11_METADATA_KEY]
            key = str(metadata["idempotency_key"])
            result_nodes = result_nodes_by_key.get(key, [])
            has_unknown_result = any(
                result_node["metadata"][PHASE11_METADATA_KEY].get("pending_or_unknown") is True
                for result_node in result_nodes
            )
            if not result_nodes or has_unknown_result:
                unresolved.append(
                    {
                        "intent_node_id": node["node_id"],
                        "idempotency_key": key,
                        "adapter_id": metadata["adapter_id"],
                        "state_boundary_id": metadata["state_boundary_id"],
                        "has_result": bool(result_nodes),
                        "pending_or_unknown": has_unknown_result,
                    }
                )
        return {"unresolved_intents": unresolved}

    def conflict_list(self) -> dict[str, Any]:
        replay = self.store().replay()
        conflicts = []
        resolved_ids = {
            str(edge["from_node_id"])
            for edge in replay.edges.values()
            if edge["relationship_type"] == "resolved_by"
        }
        for node in replay.nodes.values():
            metadata = node["metadata"].get(PHASE12_CONFLICT_METADATA_KEY)
            if node["node_type"] == "conflict" and isinstance(metadata, dict):
                conflicts.append(
                    {
                        "conflict_node_id": node["node_id"],
                        "conflict_type": metadata["conflict_type"],
                        "status": (
                            "resolved" if node["node_id"] in resolved_ids else metadata["status"]
                        ),
                        "severity": metadata["severity"],
                        "reason": metadata["conflict_reason"],
                    }
                )
        return {"conflicts": sorted(conflicts, key=lambda item: item["conflict_node_id"])}

    def conflict_inspect(self, conflict_node_id: str) -> dict[str, Any]:
        return GraphQuery(self.store().replay()).node(conflict_node_id).to_dict()

    def conflict_record(
        self,
        *,
        conflict_type: str,
        subject_node_id: str,
        evidence_node_ids: tuple[str, ...],
        reason: str,
        summary: str,
        at: str,
        expected_graph_revision: int | None,
    ) -> dict[str, Any]:
        self._require_expected_revision(self.store(), expected_graph_revision)
        result = ConflictEngine(store=self.store()).record_conflict(
            ConflictRecordRequest(
                conflict_type=conflict_type,  # type: ignore[arg-type]
                conflict_reason=reason,
                subject_node_id=subject_node_id,
                evidence_node_ids=evidence_node_ids,
                principal_id=self.principal_id,
                actor=_actor(self.principal_id),
                authority=_authority(self.principal_id),
                detected_at=at,
                severity="medium",
                required_resolution_class="decision",
                summary=summary,
            )
        )
        return result.to_dict()

    def conflict_resolve(
        self,
        *,
        conflict_node_id: str,
        chosen_outcome: str,
        rationale: str,
        at: str,
        expected_graph_revision: int | None,
    ) -> dict[str, Any]:
        self._require_expected_revision(self.store(), expected_graph_revision)
        result = ConflictEngine(store=self.store()).resolve_conflict(
            ConflictResolutionRequest(
                conflict_node_id=conflict_node_id,
                alternatives=({"outcome": chosen_outcome},),
                chosen_outcome=chosen_outcome,
                rationale=rationale,
                principal_id=self.principal_id,
                actor=_actor(self.principal_id),
                authority=_authority(self.principal_id),
                decided_at=at,
            )
        )
        return result.to_dict()

    def lineage(
        self,
        *,
        node_id: str,
        direction: str,
        revision: int | None = None,
    ) -> dict[str, Any]:
        query = GraphQuery(self.store().replay())
        if direction == "ancestors":
            return query.ancestors(node_id, revision=revision).to_dict()
        if direction == "descendants":
            return query.descendants(node_id, revision=revision).to_dict()
        raise CliWorkflowError(
            "invalid_message",
            "lineage direction must be ancestors or descendants",
        )

    def view(
        self,
        view_type: str,
        *,
        node_id: str | None,
        revision: int | None,
        generated_at: str,
        persist: bool,
    ) -> dict[str, Any]:
        engine = ProjectionEngine(store=self.store())
        if view_type == "lineage":
            if node_id is None:
                raise CliWorkflowError("invalid_message", "lineage view requires node_id")
            result = engine.lineage(node_id, revision=revision, generated_at=generated_at)
        elif view_type == "dependency":
            result = engine.dependency(revision=revision, generated_at=generated_at)
        elif view_type == "conflict":
            result = engine.conflict(revision=revision, generated_at=generated_at)
        elif view_type == "progress":
            result = engine.progress(revision=revision, generated_at=generated_at)
        elif view_type == "traceability":
            result = engine.traceability(revision=revision, generated_at=generated_at)
        elif view_type == "manifest":
            result = engine.manifest(revision=revision, generated_at=generated_at)
        else:
            raise CliWorkflowError("invalid_message", f"unsupported view type: {view_type}")
        response = result.to_dict()
        if persist:
            persisted = engine.persist(result)
            response["persisted"] = {
                "path": str(persisted.path),
                "result_hash": persisted.result_hash,
                "graph_revision": persisted.graph_revision,
                "view_type": persisted.view_type,
            }
        return response

    def snapshot_create(
        self,
        *,
        revision: int | None,
        at: str,
        expected_graph_revision: int | None,
        persist_summary: bool,
    ) -> dict[str, Any]:
        self._require_expected_revision(self.store(), expected_graph_revision)
        result = SnapshotEngine(store=self.store()).create_snapshot(
            SnapshotRequest(
                principal_id=self.principal_id,
                actor=_actor(self.principal_id),
                authority=_authority(self.principal_id),
                created_at=at,
                revision=revision,
                persist_summary=persist_summary,
            )
        )
        return result.to_dict()

    def snapshot_verify(self, snapshot_node_id: str) -> dict[str, Any]:
        return SnapshotEngine(store=self.store()).verify_snapshot(snapshot_node_id).to_dict()

    def snapshot_resume(self, snapshot_node_id: str) -> dict[str, Any]:
        return SnapshotEngine(store=self.store()).resume_context(snapshot_node_id).to_dict()

    def graph_verify(self) -> dict[str, Any]:
        replay = self.store().replay()
        status = SQLiteGraphIndex(self.root).status(replay)
        return {
            "verified": True,
            "workspace_id": replay.workspace_id,
            "graph_revision": replay.graph_revision,
            "commit_hash": replay.last_commit_hash,
            "warnings": replay.warnings,
            "index": {
                "status": status.status,
                "source_revision": status.source_revision,
                "source_commit_hash": status.source_commit_hash,
                "reason": status.reason,
            },
        }

    def graph_replay(self) -> dict[str, Any]:
        replay = self.store().replay()
        return {
            "workspace_id": replay.workspace_id,
            "graph_revision": replay.graph_revision,
            "commit_hash": replay.last_commit_hash,
            "node_count": len(replay.nodes),
            "edge_count": len(replay.edges),
            "warnings": replay.warnings,
        }

    def graph_heads(self) -> dict[str, Any]:
        return GraphQuery(self.store().replay()).heads().to_dict()

    def graph_rebuild_index(self) -> dict[str, Any]:
        replay = self.store().replay()
        SQLiteGraphIndex(self.root).rebuild(replay)
        status = SQLiteGraphIndex(self.root).status(replay)
        return {
            "rebuilt": True,
            "status": status.status,
            "source_revision": status.source_revision,
            "source_commit_hash": status.source_commit_hash,
        }

    def _adapter(self, adapter_ref: str) -> Any:
        if adapter_ref in self.context.adapters:
            return self.context.adapters[adapter_ref]
        for adapter in self.context.adapters.values():
            if str(adapter.descriptor["adapter_id"]) == adapter_ref:
                return adapter
        raise CliWorkflowError("unknown_adapter", f"unknown adapter: {adapter_ref}")

    def _require_expected_revision(
        self,
        store: GraphStore,
        expected_graph_revision: int | None,
    ) -> None:
        if expected_graph_revision is None:
            return
        actual = store.replay().graph_revision
        if expected_graph_revision != actual:
            raise CliWorkflowError(
                "stale_graph_revision",
                f"expected graph revision {expected_graph_revision}, current revision {actual}",
            )

    def _edge(
        self,
        *,
        store: GraphStore,
        workspace_id: str,
        relationship_type: str,
        from_node_id: str,
        to_node_id: str,
        created_at: str,
        source_record_ids: list[str],
    ) -> dict[str, Any]:
        return {
            "record_type": "edge",
            "protocol_version": CONTRACT_VERSION,
            "workspace_id": workspace_id,
            "edge_id": str(store.ids.generate("edge")),
            "relationship_type": relationship_type,
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "created_at": created_at,
            "actor": _actor(self.principal_id),
            "provenance": {
                "source": "guerilla.phase15.cli",
                "source_record_ids": source_record_ids,
            },
            "metadata": {PHASE15_METADATA_KEY: {"kind": "relationship"}},
            "extensions": {},
            "record_hash": "0" * 64,
        }


def load_runtime(root: Path, contracts_root: Path | None, *, principal_id: str) -> Phase15Runtime:
    contract_source = contracts_root or find_contract_root(Path.cwd())
    contracts = load_contract_bundle(contract_source)
    return Phase15Runtime(Phase15Context(root=root, contracts=contracts, principal_id=principal_id))


def find_contract_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "schemas").is_dir() and (candidate / "registries").is_dir():
            return candidate
    return start


def emit_success(stdout: TextIO, operation: str, result: dict[str, Any]) -> None:
    json.dump(
        {"ok": True, "operation": operation, "result": result},
        stdout,
        indent=2,
        sort_keys=True,
    )
    stdout.write("\n")


def emit_error(stderr: TextIO, exc: BaseException) -> int:
    code = getattr(exc, "code", "internal_error")
    message = str(exc)
    exit_code = getattr(exc, "exit_code", 1)
    json.dump(
        {"ok": False, "error": {"code": code, "message": message}},
        stderr,
        indent=2,
        sort_keys=True,
    )
    stderr.write("\n")
    return int(exit_code)


def load_input_mapping(value: str | None, file_path: str | None) -> dict[str, Any]:
    if value is not None and file_path is not None:
        raise CliWorkflowError("invalid_message", "--input and --input-file are mutually exclusive")
    if file_path is not None:
        raw = Path(file_path).read_text(encoding="utf-8")
    else:
        raw = "{}" if value is None else value
    decoded = json.loads(raw)
    if not isinstance(decoded, dict):
        raise CliWorkflowError("invalid_message", "structured input must be a JSON object")
    return decoded


def _actor(principal_id: str) -> dict[str, Any]:
    return {"actor_id": principal_id, "actor_kind": "human"}


def _authority(principal_id: str) -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": principal_id, "profile": "local-owner-v1"}


def _phase11_by_key(replay: Any, kind: str) -> dict[str, list[dict[str, Any]]]:
    matches: dict[str, list[dict[str, Any]]] = {}
    for node in _phase11_nodes_by_kind(replay, kind):
        metadata = node.get("metadata", {}).get(PHASE11_METADATA_KEY)
        if isinstance(metadata, dict):
            key = str(metadata["idempotency_key"])
            matches.setdefault(key, []).append(node)
    return matches


def _phase11_nodes_by_kind(replay: Any, kind: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for node in replay.nodes.values():
        metadata = node.get("metadata", {}).get(PHASE11_METADATA_KEY)
        if isinstance(metadata, dict) and metadata.get("kind") == kind:
            nodes.append(node)
    return nodes
