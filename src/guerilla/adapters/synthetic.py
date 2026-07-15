"""Synthetic in-process adapters used for Gate C Phase 9 conformance."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from guerilla.adapters.errors import AdapterOperationError
from guerilla.adapters.types import (
    AdapterCapability,
    AdapterOperationRequest,
    AdapterOperationResult,
)
from guerilla.codec import canonical_bytes
from guerilla.identity import IDENTIFIER_FAMILIES, uuidv7_from_parts

PHASE9_TS = "2026-07-14T00:00:00Z"


@dataclass(slots=True)
class VirtualClock:
    """Deterministic millisecond clock for synthetic async behavior."""

    current_ms: int = 0

    def now_ms(self) -> int:
        return self.current_ms

    def advance(self, milliseconds: int) -> None:
        if milliseconds < 0:
            raise ValueError("milliseconds must be non-negative")
        self.current_ms += milliseconds


def deterministic_identifier(family: str, seed: int) -> str:
    prefix = IDENTIFIER_FAMILIES[family]
    uuid_text = str(uuidv7_from_parts(1_721_000_900_000 + seed, seed & 0xFFF, seed))
    return f"{prefix}_{uuid_text}"


def request_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(data)).hexdigest()


def _external_identity(
    *,
    system_id: str,
    boundary_id: str,
    external_kind: str,
    external_id: str,
    external_revision: str | None = None,
    namespace: str | None = None,
    lifecycle_state: str | None = None,
) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "system_id": system_id,
        "state_boundary_id": boundary_id,
        "external_kind": external_kind,
        "external_id": external_id,
    }
    if namespace is not None:
        identity["namespace"] = namespace
    if external_revision is not None:
        identity["external_revision"] = external_revision
    if lifecycle_state is not None:
        identity["lifecycle_state"] = lifecycle_state
    return identity


def _boundary(
    *,
    seed: int,
    system_id: str,
    name: str,
    continuity_mode: str,
    permitted_roots: list[str] | None = None,
    resource_namespaces: list[str] | None = None,
) -> dict[str, Any]:
    boundary: dict[str, Any] = {
        "state_boundary_id": deterministic_identifier("state_boundary", seed),
        "system_id": system_id,
        "name": name,
        "system_of_record": True,
        "continuity_mode": continuity_mode,
        "ownership": "external_application_state",
        "permitted_operations": ["observe", "act", "evaluate", "reconcile"],
        "lineage_crossing": "intent_before_action",
        "conflict_behavior": "require_reconciliation",
        "extensions": {},
    }
    if permitted_roots is not None:
        boundary["permitted_roots"] = permitted_roots
    if resource_namespaces is not None:
        boundary["resource_namespaces"] = resource_namespaces
    return boundary


def _capability(
    capability: AdapterCapability,
    boundary_id: str,
    *,
    read_consistency: str,
    write_behavior: str,
    event_ordering: str,
    concurrency: str,
    conflict_handling: str,
    replay_support: str,
    snapshot_support: str,
    identity_stability: str,
    lineage_completeness: str,
    idempotency: str,
    limitations: list[str],
    mutating_actions: list[str] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "read_consistency": read_consistency,
        "write_behavior": write_behavior,
        "event_ordering": event_ordering,
        "concurrency": concurrency,
        "conflict_handling": conflict_handling,
        "replay_support": replay_support,
        "snapshot_support": snapshot_support,
        "identity_stability": identity_stability,
        "lineage_completeness": lineage_completeness,
        "idempotency": idempotency,
        "schemas": {
            "request": f"phase9.{capability}.request",
            "response": f"phase9.{capability}.response",
        },
        "limitations": limitations,
    }
    if mutating_actions is not None:
        metadata["mutating_actions"] = mutating_actions
    return {
        "capability": capability,
        "supported": True,
        "state_boundary_ids": [boundary_id],
        "limitations": limitations,
        "metadata": metadata,
    }


def _descriptor(
    *,
    seed: int,
    system_name: str,
    system_type: str,
    boundary: dict[str, Any],
    capabilities: list[dict[str, Any]],
    limitations: list[str],
) -> dict[str, Any]:
    return {
        "adapter_id": deterministic_identifier("adapter", seed),
        "system_id": boundary["system_id"],
        "name": system_name,
        "version": "0.2.0",
        "trust_model": "trusted_in_process_python",
        "state_boundaries": [boundary],
        "capabilities": capabilities,
        "authentication": {"required": False, "credential_storage": "none"},
        "limitations": [*limitations, f"synthetic {system_type} only"],
        "extensions": {},
    }


class SyntheticAdapterBase:
    """Shared descriptor/result helpers for synthetic adapters."""

    def __init__(self, descriptor: dict[str, Any]) -> None:
        self._descriptor = descriptor
        self.calls: dict[str, int] = {
            "describe": 0,
            "observe": 0,
            "act": 0,
            "evaluate": 0,
            "reconcile": 0,
        }

    @property
    def descriptor(self) -> dict[str, Any]:
        return self._descriptor

    @property
    def adapter_id(self) -> str:
        return str(self._descriptor["adapter_id"])

    @property
    def adapter_version(self) -> str:
        return str(self._descriptor["version"])

    @property
    def system_id(self) -> str:
        return str(self._descriptor["system_id"])

    @property
    def boundary_id(self) -> str:
        return str(self._descriptor["state_boundaries"][0]["state_boundary_id"])

    def _result(
        self,
        request: AdapterOperationRequest,
        *,
        classification: str,
        evidence: dict[str, Any],
        data: dict[str, Any] | None = None,
        external_revision: str | None = None,
        external_identity: dict[str, Any] | None = None,
        retry: str = "not_applicable",
        warnings: tuple[str, ...] = (),
        limitations: tuple[str, ...] = (),
    ) -> AdapterOperationResult:
        return AdapterOperationResult(
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            system_id=self.system_id,
            state_boundary_id=self.boundary_id,
            capability=request.capability,
            classification=classification,  # type: ignore[arg-type]
            occurred_at=PHASE9_TS,
            evidence=evidence,
            retry=retry,  # type: ignore[arg-type]
            data={} if data is None else data,
            external_revision=external_revision,
            external_identity=external_identity,
            warnings=warnings,
            limitations=limitations,
            payload_ref={"retention_class": "none"},
        )

    def describe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["describe"] += 1
        return self._result(
            request,
            classification="described",
            evidence={"descriptor_hash": request_hash(self._descriptor)},
            data={"descriptor": self._descriptor},
            limitations=tuple(self._descriptor["limitations"]),
        )

    def evaluate(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["evaluate"] += 1
        subject = str(request.data.get("subject", "unknown"))
        return self._result(
            request,
            classification="evaluated",
            evidence={"subject": subject, "criteria": request.data.get("criteria", {})},
            data={"result": "pass", "confidence": "synthetic"},
        )

    def export_state(self) -> dict[str, Any]:
        return {}


class TransactionalRevisionedServiceAdapter(SyntheticAdapterBase):
    """Atomic compare-and-set synthetic service with native idempotency."""

    def __init__(self, *, seed: int = 100) -> None:
        system_id = deterministic_identifier("external_system", seed)
        boundary = _boundary(
            seed=seed + 1,
            system_id=system_id,
            name="transactional revisioned boundary",
            continuity_mode="online",
            resource_namespaces=["transactional"],
        )
        boundary_id = str(boundary["state_boundary_id"])
        caps = [
            _capability(
                "describe",
                boundary_id,
                read_consistency="strong",
                write_behavior="transactional",
                event_ordering="total",
                concurrency="externally_serialized",
                conflict_handling="reject",
                replay_support="query-only",
                snapshot_support="point-in-time read",
                identity_stability="stable",
                lineage_completeness="complete within boundary",
                idempotency="native",
                limitations=["synthetic state is in memory"],
            ),
            _capability(
                "observe",
                boundary_id,
                read_consistency="strong",
                write_behavior="transactional",
                event_ordering="total",
                concurrency="externally_serialized",
                conflict_handling="reject",
                replay_support="query-only",
                snapshot_support="point-in-time read",
                identity_stability="stable",
                lineage_completeness="complete within boundary",
                idempotency="native",
                limitations=["synthetic state is in memory"],
            ),
            _capability(
                "act",
                boundary_id,
                read_consistency="strong",
                write_behavior="transactional",
                event_ordering="total",
                concurrency="externally_serialized",
                conflict_handling="reject",
                replay_support="query-only",
                snapshot_support="point-in-time read",
                identity_stability="stable",
                lineage_completeness="complete within boundary",
                idempotency="native",
                limitations=["synthetic state is in memory"],
                mutating_actions=["set_value"],
            ),
            _capability(
                "evaluate",
                boundary_id,
                read_consistency="strong",
                write_behavior="transactional",
                event_ordering="total",
                concurrency="externally_serialized",
                conflict_handling="reject",
                replay_support="query-only",
                snapshot_support="point-in-time read",
                identity_stability="stable",
                lineage_completeness="complete within boundary",
                idempotency="native",
                limitations=["synthetic state is in memory"],
            ),
            _capability(
                "reconcile",
                boundary_id,
                read_consistency="strong",
                write_behavior="transactional",
                event_ordering="total",
                concurrency="externally_serialized",
                conflict_handling="reject",
                replay_support="query-only",
                snapshot_support="point-in-time read",
                identity_stability="stable",
                lineage_completeness="complete within boundary",
                idempotency="native",
                limitations=["synthetic state is in memory"],
            ),
        ]
        super().__init__(
            _descriptor(
                seed=seed + 2,
                system_name="synthetic transactional service",
                system_type="transactional_service",
                boundary=boundary,
                capabilities=caps,
                limitations=["atomic compare-and-set only"],
            )
        )
        self.records: dict[str, dict[str, Any]] = {}
        self.actions: dict[str, AdapterOperationResult] = {}

    def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["observe"] += 1
        subject = str(request.data["subject"])
        record = self.records.get(subject)
        revision = None if record is None else str(record["revision"])
        identity = _external_identity(
            system_id=self.system_id,
            boundary_id=self.boundary_id,
            external_kind="transactional_record",
            external_id=subject,
            external_revision=revision,
            namespace="transactional",
        )
        return self._result(
            request,
            classification="observed",
            evidence={"subject": subject, "exists": record is not None},
            data={"value": None if record is None else record["value"]},
            external_revision=revision,
            external_identity=identity,
        )

    def act(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["act"] += 1
        if request.data.get("action") != "set_value":
            return self._result(
                request,
                classification="rejected",
                evidence={"reason": "unsupported_action"},
                retry="never",
            )
        if request.idempotency is None:
            raise AdapterOperationError("idempotency_conflict", "idempotency context required")
        existing = self.actions.get(request.idempotency.key)
        if existing is not None:
            if existing.evidence.get("request_hash") != request.idempotency.request_hash:
                return self._result(
                    request,
                    classification="rejected",
                    evidence={"reason": "idempotency_conflict"},
                    retry="never",
                )
            return existing
        subject = str(request.data["subject"])
        expected_revision = request.data.get("expected_revision")
        current = self.records.get(subject)
        current_revision = None if current is None else str(current["revision"])
        if expected_revision is not None and expected_revision != current_revision:
            result = self._result(
                request,
                classification="rejected",
                evidence={
                    "reason": "stale_external_revision",
                    "current_revision": current_revision,
                    "request_hash": request.idempotency.request_hash,
                },
                external_revision=current_revision,
                retry="after_refresh",
            )
            self.actions[request.idempotency.key] = result
            return result
        next_revision_number = 1 if current is None else int(str(current["revision"])[4:]) + 1
        revision = f"rev-{next_revision_number}"
        self.records[subject] = {"value": request.data.get("value"), "revision": revision}
        result = self._result(
            request,
            classification="accepted",
            evidence={
                "native_idempotency": True,
                "request_hash": request.idempotency.request_hash,
            },
            data={"subject": subject, "value": request.data.get("value")},
            external_revision=revision,
            external_identity=_external_identity(
                system_id=self.system_id,
                boundary_id=self.boundary_id,
                external_kind="transactional_record",
                external_id=subject,
                external_revision=revision,
                namespace="transactional",
            ),
            retry="idempotent_replay",
        )
        self.actions[request.idempotency.key] = result
        return result

    def reconcile(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["reconcile"] += 1
        key = str(request.data.get("idempotency_key", ""))
        prior = self.actions.get(key)
        if prior is None:
            return self._result(
                request,
                classification="unknown",
                evidence={"idempotency_key": key, "history": "missing"},
                retry="after_reconcile",
            )
        classification = (
            "confirmed_accepted" if prior.classification == "accepted" else "confirmed_rejected"
        )
        return self._result(
            request,
            classification=classification,
            evidence={"idempotency_key": key, "prior": prior.classification},
            data=prior.data,
            external_revision=prior.external_revision,
            external_identity=prior.external_identity,
        )

    def export_state(self) -> dict[str, Any]:
        return {
            "records": self.records,
            "actions": {key: value.to_dict() for key, value in self.actions.items()},
        }


class ReconstructedFilesystemAdapter(SyntheticAdapterBase):
    """Reconstruct state from files under a declared temporary root."""

    def __init__(self, root: Path, *, seed: int = 200) -> None:
        self.root = root.resolve(strict=False)
        self.root.mkdir(parents=True, exist_ok=True)
        self.actions: dict[str, tuple[str, AdapterOperationResult]] = {}
        system_id = deterministic_identifier("external_system", seed)
        boundary = _boundary(
            seed=seed + 1,
            system_id=system_id,
            name="reconstructed filesystem boundary",
            continuity_mode="reconstructed",
            permitted_roots=[str(self.root)],
            resource_namespaces=["filesystem"],
        )
        boundary_id = str(boundary["state_boundary_id"])
        caps = [
            _capability(
                capability,
                boundary_id,
                read_consistency="reconstructed",
                write_behavior="manual" if capability != "act" else "non-transactional",
                event_ordering="unordered",
                concurrency="none",
                conflict_handling="manual",
                replay_support="query-only",
                snapshot_support="reconstructed snapshot",
                identity_stability="renameable",
                lineage_completeness="best effort",
                idempotency="adapter-emulated",
                limitations=["filesystem state is reconstructed from current files"],
                mutating_actions=["write_file", "rename", "delete", "multi_write"]
                if capability == "act"
                else None,
            )
            for capability in ("describe", "observe", "act", "evaluate", "reconcile")
        ]
        super().__init__(
            _descriptor(
                seed=seed + 2,
                system_name="synthetic reconstructed filesystem",
                system_type="reconstructed_filesystem",
                boundary=boundary,
                capabilities=caps,
                limitations=["no native rollback", "partial multi-file writes are possible"],
            )
        )

    def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["observe"] += 1
        path = str(request.data.get("path", "."))
        target = self._resolve(path)
        revision = self._revision()
        exists = target.exists()
        lifecycle = "deleted" if not exists and path != "." else "observed"
        return self._result(
            request,
            classification="observed",
            evidence={"path": path, "exists": exists, "revision_kind": "content_hash"},
            data={"path": path, "exists": exists},
            external_revision=revision,
            external_identity=_external_identity(
                system_id=self.system_id,
                boundary_id=self.boundary_id,
                external_kind="file_path",
                external_id=path,
                external_revision=revision,
                namespace="filesystem",
                lifecycle_state=lifecycle,
            ),
            limitations=("state reconstructed from filesystem contents",),
        )

    def act(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["act"] += 1
        if request.idempotency is None:
            raise AdapterOperationError("idempotency_conflict", "idempotency context required")
        existing = self.actions.get(request.idempotency.key)
        if existing is not None:
            existing_hash, existing_result = existing
            if existing_hash != request.idempotency.request_hash:
                return self._result(
                    request,
                    classification="rejected",
                    evidence={"reason": "idempotency_conflict"},
                    retry="never",
                )
            return existing_result
        action = str(request.data.get("action"))
        try:
            if action == "write_file":
                result = self._write_file(request)
            elif action == "rename":
                result = self._rename(request)
            elif action == "delete":
                result = self._delete(request)
            elif action == "multi_write":
                result = self._multi_write(request)
            else:
                result = self._result(
                    request,
                    classification="rejected",
                    evidence={"reason": "unsupported_action"},
                    retry="never",
                )
        except AdapterOperationError as exc:
            result = self._result(
                request,
                classification="failed",
                evidence={"reason": exc.code, "message": str(exc)},
                retry="after_reconcile",
            )
        self.actions[request.idempotency.key] = (request.idempotency.request_hash, result)
        return result

    def reconcile(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["reconcile"] += 1
        key = str(request.data.get("idempotency_key", ""))
        existing = self.actions.get(key)
        if existing is None:
            return self._result(
                request,
                classification="unknown",
                evidence={"idempotency_key": key, "history": "not queryable"},
                retry="after_reconcile",
            )
        result = existing[1]
        if result.classification == "failed":
            classification = "confirmed_failed"
        elif result.classification == "rejected":
            classification = "confirmed_rejected"
        else:
            classification = "confirmed_accepted"
        return self._result(
            request,
            classification=classification,
            evidence={"idempotency_key": key, "emulated_history": True},
            data=result.data,
            external_revision=self._revision(),
        )

    def export_state(self) -> dict[str, Any]:
        return {"root": str(self.root), "revision": self._revision(), "files": self._files()}

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve(strict=False)
        if target != self.root and self.root not in target.parents:
            raise AdapterOperationError("state_boundary_violation", "path escapes synthetic root")
        return target

    def _revision(self) -> str:
        digest = hashlib.sha256()
        for rel_path, content in self._files().items():
            digest.update(rel_path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(content.encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()

    def _files(self) -> dict[str, str]:
        items: dict[str, str] = {}
        for path in sorted(self.root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(self.root).as_posix()
                items[rel] = path.read_text(encoding="utf-8")
        return items

    def _write_file(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        path = str(request.data["path"])
        content = str(request.data.get("content", ""))
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return self._result(
            request,
            classification="accepted",
            evidence={
                "action": "write_file",
                "path": path,
                "request_hash": request_hash(request.data),
            },
            data={"path": path},
            external_revision=self._revision(),
            external_identity=_external_identity(
                system_id=self.system_id,
                boundary_id=self.boundary_id,
                external_kind="file_path",
                external_id=path,
                external_revision=self._revision(),
                namespace="filesystem",
            ),
            retry="idempotent_replay",
        )

    def _rename(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        source = str(request.data["source_path"])
        target_path = str(request.data["target_path"])
        source_path = self._resolve(source)
        target = self._resolve(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(target)
        return self._result(
            request,
            classification="accepted",
            evidence={"action": "rename", "source": source, "target": target_path},
            data={"source_path": source, "target_path": target_path},
            external_revision=self._revision(),
            external_identity=_external_identity(
                system_id=self.system_id,
                boundary_id=self.boundary_id,
                external_kind="file_path",
                external_id=target_path,
                external_revision=self._revision(),
                namespace="filesystem",
                lifecycle_state="renamed",
            ),
        )

    def _delete(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        path = str(request.data["path"])
        target = self._resolve(path)
        if target.exists():
            target.unlink()
        return self._result(
            request,
            classification="accepted",
            evidence={"action": "delete", "path": path},
            data={"path": path, "deleted": True},
            external_revision=self._revision(),
            external_identity=_external_identity(
                system_id=self.system_id,
                boundary_id=self.boundary_id,
                external_kind="file_path",
                external_id=path,
                external_revision=self._revision(),
                namespace="filesystem",
                lifecycle_state="deleted",
            ),
        )

    def _multi_write(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        writes = request.data.get("writes", [])
        if not isinstance(writes, list):
            raise AdapterOperationError("invalid_message", "writes must be a list")
        fail_after = request.data.get("fail_after")
        written: list[str] = []
        for index, item in enumerate(writes):
            if not isinstance(item, dict):
                raise AdapterOperationError("invalid_message", "write item must be an object")
            if isinstance(fail_after, int) and index >= fail_after:
                return self._result(
                    request,
                    classification="failed",
                    evidence={"action": "multi_write", "partial": True, "written": written},
                    data={"written": written, "partial": True},
                    external_revision=self._revision(),
                    retry="after_reconcile",
                    warnings=("partial filesystem mutation occurred",),
                )
            path = str(item["path"])
            target = self._resolve(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(item.get("content", "")), encoding="utf-8")
            written.append(path)
        return self._result(
            request,
            classification="accepted",
            evidence={"action": "multi_write", "written": written},
            data={"written": written, "partial": False},
            external_revision=self._revision(),
        )


@dataclass(slots=True)
class _AsyncOperation:
    action_id: str
    subject: str
    accepted_at_ms: int
    complete_at_ms: int
    request_hash: str
    unknown: bool = False


class AsyncUnknownOutcomeAdapter(SyntheticAdapterBase):
    """Synthetic asynchronous service with pending and unknown outcomes."""

    def __init__(self, *, seed: int = 300, clock: VirtualClock | None = None) -> None:
        self.clock = clock or VirtualClock()
        self.operations: dict[str, _AsyncOperation] = {}
        self.completed_subjects: dict[str, str] = {}
        self._sequence = 0
        system_id = deterministic_identifier("external_system", seed)
        boundary = _boundary(
            seed=seed + 1,
            system_id=system_id,
            name="asynchronous unknown-outcome boundary",
            continuity_mode="online",
            resource_namespaces=["async"],
        )
        boundary_id = str(boundary["state_boundary_id"])
        caps = [
            _capability(
                capability,
                boundary_id,
                read_consistency="eventual",
                write_behavior="append-only" if capability == "act" else "read-only",
                event_ordering="source-sequence",
                concurrency="multi-writer",
                conflict_handling="report-only",
                replay_support="query-only",
                snapshot_support="none",
                identity_stability="stable",
                lineage_completeness="action-only",
                idempotency="native",
                limitations=["history is partially queryable", "outcomes can remain unknown"],
                mutating_actions=["submit_job"] if capability == "act" else None,
            )
            for capability in ("describe", "observe", "act", "evaluate", "reconcile")
        ]
        super().__init__(
            _descriptor(
                seed=seed + 2,
                system_name="synthetic asynchronous unknown-outcome service",
                system_type="asynchronous_unknown_outcome",
                boundary=boundary,
                capabilities=caps,
                limitations=["uses deterministic virtual time", "some outcomes are unknowable"],
            )
        )

    def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["observe"] += 1
        self._complete_ready()
        subject = str(request.data.get("subject", "unknown"))
        revision = self.completed_subjects.get(subject)
        return self._result(
            request,
            classification="observed",
            evidence={"subject": subject, "completed": revision is not None},
            data={"subject": subject, "completed_revision": revision},
            external_revision=revision,
            external_identity=_external_identity(
                system_id=self.system_id,
                boundary_id=self.boundary_id,
                external_kind="async_subject",
                external_id=subject,
                external_revision=revision,
                namespace="async",
            ),
        )

    def act(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["act"] += 1
        if request.idempotency is None:
            raise AdapterOperationError("idempotency_conflict", "idempotency context required")
        if request.data.get("action") != "submit_job":
            return self._result(
                request,
                classification="rejected",
                evidence={"reason": "unsupported_action"},
                retry="never",
            )
        existing = self.operations.get(request.idempotency.key)
        if existing is not None:
            if existing.request_hash != request.idempotency.request_hash:
                return self._result(
                    request,
                    classification="rejected",
                    evidence={"reason": "idempotency_conflict"},
                    retry="never",
                )
            return self._result(
                request,
                classification="duplicated",
                evidence={"action_id": existing.action_id, "duplicate": True},
                data={"action_id": existing.action_id},
                retry="idempotent_replay",
            )
        self._sequence += 1
        subject = str(request.data["subject"])
        delay = int(request.data.get("completion_delay_ms", 100))
        unknown = bool(request.data.get("force_unknown", False))
        action_id = f"async-{self._sequence}"
        self.operations[request.idempotency.key] = _AsyncOperation(
            action_id=action_id,
            subject=subject,
            accepted_at_ms=self.clock.now_ms(),
            complete_at_ms=self.clock.now_ms() + delay,
            request_hash=request.idempotency.request_hash,
            unknown=unknown,
        )
        classification = "outcome_unknown" if unknown else "pending"
        return self._result(
            request,
            classification=classification,
            evidence={
                "action_id": action_id,
                "accepted": True,
                "request_hash": request.idempotency.request_hash,
            },
            data={"action_id": action_id, "subject": subject},
            retry="after_reconcile" if unknown else "after_backoff",
        )

    def reconcile(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["reconcile"] += 1
        self._complete_ready()
        key = str(request.data.get("idempotency_key", ""))
        operation = self.operations.get(key)
        if operation is None:
            return self._result(
                request,
                classification="unknown",
                evidence={"idempotency_key": key, "history": "missing"},
                retry="after_reconcile",
            )
        if operation.unknown:
            return self._result(
                request,
                classification="unknown",
                evidence={"idempotency_key": key, "history": "not queryable"},
                retry="after_reconcile",
            )
        revision = self.completed_subjects.get(operation.subject)
        if revision is None:
            return self._result(
                request,
                classification="still_pending",
                evidence={"idempotency_key": key, "action_id": operation.action_id},
                retry="after_backoff",
            )
        return self._result(
            request,
            classification="confirmed_accepted",
            evidence={"idempotency_key": key, "action_id": operation.action_id},
            data={"subject": operation.subject, "action_id": operation.action_id},
            external_revision=revision,
        )

    def export_state(self) -> dict[str, Any]:
        return {
            "clock_ms": self.clock.now_ms(),
            "operations": {
                key: {
                    "action_id": operation.action_id,
                    "subject": operation.subject,
                    "accepted_at_ms": operation.accepted_at_ms,
                    "complete_at_ms": operation.complete_at_ms,
                    "request_hash": operation.request_hash,
                    "unknown": operation.unknown,
                }
                for key, operation in sorted(self.operations.items())
            },
            "completed_subjects": dict(sorted(self.completed_subjects.items())),
        }

    def _complete_ready(self) -> None:
        for operation in self.operations.values():
            if operation.unknown:
                continue
            if operation.subject in self.completed_subjects:
                continue
            if self.clock.now_ms() >= operation.complete_at_ms:
                self.completed_subjects[operation.subject] = f"async-rev-{operation.action_id}"
