from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import pytest

from guerilla.adapters import (
    AdapterHost,
    AdapterHostError,
    AdapterOperationRequest,
    AdapterOperationResult,
    AdapterValidationError,
    AsyncUnknownOutcomeAdapter,
    IdempotencyContext,
    ReconstructedFilesystemAdapter,
    TransactionalRevisionedServiceAdapter,
    VirtualClock,
    request_hash,
)
from guerilla.adapters.host import AdapterHost as AdapterHostClass
from guerilla.adapters.synthetic import deterministic_identifier
from guerilla.authority import AuthorityError, BoundaryError
from guerilla.contracts import ContractBundle, ContractError, load_contract_bundle

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _actor() -> dict[str, Any]:
    return {"actor_id": "phase9-local-user", "actor_kind": "human"}


def _authority(principal_id: str = "local-user") -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": principal_id, "profile": "local-owner-v1"}


def _request(
    adapter: Any,
    capability: str,
    data: dict[str, Any],
    *,
    principal_id: str = "local-user",
    idempotency_key: str | None = None,
    root: str | None = None,
    namespace: str | None = None,
    timeout_ms: int = 1_000,
    deadline_ms: int | None = None,
    extensions: dict[str, Any] | None = None,
) -> AdapterOperationRequest:
    idempotency = None
    if idempotency_key is not None:
        idempotency = IdempotencyContext(
            key=idempotency_key,
            request_hash=request_hash(data),
            native_supported=True,
        )
    return AdapterOperationRequest(
        workspace_id=deterministic_identifier("workspace", 901),
        adapter_id=adapter.adapter_id,
        adapter_version=adapter.adapter_version,
        system_id=adapter.system_id,
        state_boundary_id=adapter.boundary_id,
        operation_id=deterministic_identifier("message", 902),
        principal_id=principal_id,
        actor=_actor(),
        authority=_authority(principal_id),
        contract_version="0.2.0",
        requested_at=TS,
        capability=capability,  # type: ignore[arg-type]
        data=data,
        deadline_ms=deadline_ms,
        timeout_ms=timeout_ms,
        idempotency=idempotency,
        root=root,
        namespace=namespace,
        extensions={} if extensions is None else extensions,
    )


def test_one_host_path_supports_all_three_synthetic_systems(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    transactional = TransactionalRevisionedServiceAdapter()
    filesystem = ReconstructedFilesystemAdapter(tmp_path / "fs")
    async_adapter = AsyncUnknownOutcomeAdapter(clock=VirtualClock())
    host = AdapterHost(contracts=contracts, adapters=[transactional, filesystem, async_adapter])

    for adapter, observe_data, namespace, root in (
        (transactional, {"subject": "ticket-1"}, "transactional", None),
        (filesystem, {"path": "README.md"}, "filesystem", str(filesystem.root / "README.md")),
        (async_adapter, {"subject": "job-1"}, "async", None),
    ):
        described = host.invoke(_request(adapter, "describe", {}, namespace=namespace, root=root))
        observed = host.invoke(
            _request(adapter, "observe", observe_data, namespace=namespace, root=root)
        )
        evaluated = host.invoke(
            _request(
                adapter,
                "evaluate",
                {"subject": "synthetic", "criteria": {"check": "available"}},
                namespace=namespace,
                root=root,
            )
        )
        assert described.classification == "described"
        assert observed.classification == "observed"
        assert evaluated.classification == "evaluated"

    host_source = inspect.getsource(AdapterHostClass.invoke).lower()
    assert "transactional" not in host_source
    assert "filesystem" not in host_source
    assert "async" not in host_source


def test_descriptor_validation_rejects_incomplete_duplicate_and_critical_extension(
    contracts: ContractBundle,
) -> None:
    adapter = TransactionalRevisionedServiceAdapter()
    adapter.descriptor["capabilities"][0].pop("metadata")
    with pytest.raises(AdapterValidationError) as incomplete:
        AdapterHost(contracts=contracts, adapters=[adapter])
    assert incomplete.value.code == "schema_violation"

    duplicate = TransactionalRevisionedServiceAdapter()
    host = AdapterHost(contracts=contracts, adapters=[duplicate])
    with pytest.raises(AdapterHostError) as duplicate_error:
        host.register(duplicate)
    assert duplicate_error.value.code == "duplicate_id"

    critical = TransactionalRevisionedServiceAdapter(seed=120)
    critical.descriptor["extensions"] = {
        "example.unknown.critical": {
            "critical": True,
            "namespace_id": deterministic_identifier("extension_namespace", 999),
            "value": {"claim": "must reject"},
        }
    }
    with pytest.raises(ContractError) as extension_error:
        AdapterHost(contracts=contracts, adapters=[critical])
    assert extension_error.value.code == "unknown_critical_extension"


def test_unsupported_capability_and_malformed_requests_are_rejected_before_invocation(
    contracts: ContractBundle,
) -> None:
    adapter = TransactionalRevisionedServiceAdapter()
    adapter.descriptor["capabilities"] = [
        capability
        for capability in adapter.descriptor["capabilities"]
        if capability["capability"] != "act"
    ]
    host = AdapterHost(contracts=contracts, adapters=[adapter])

    with pytest.raises(AdapterHostError) as unsupported:
        host.invoke(
            _request(
                adapter,
                "act",
                {"action": "set_value", "subject": "a", "value": "b"},
                idempotency_key="phase9-key-001",
                namespace="transactional",
            )
        )
    assert unsupported.value.code == "unsupported_capability"
    assert adapter.calls["act"] == 0

    with pytest.raises(AdapterValidationError) as unsafe:
        host.invoke(_request(adapter, "observe", {"subject": 1.25}, namespace="transactional"))
    assert unsafe.value.code == "invalid_message"
    assert adapter.calls["observe"] == 0


def test_authorization_and_boundary_checks_precede_adapter_invocation(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    transactional = TransactionalRevisionedServiceAdapter()
    host = AdapterHost(contracts=contracts, adapters=[transactional])
    with pytest.raises(AuthorityError):
        host.invoke(
            _request(
                transactional,
                "observe",
                {"subject": "ticket-1"},
                principal_id="intruder",
                namespace="transactional",
            )
        )
    assert transactional.calls["observe"] == 0

    filesystem = ReconstructedFilesystemAdapter(tmp_path / "fs")
    host = AdapterHost(contracts=contracts, adapters=[filesystem])
    outside = tmp_path / "outside" / "x.txt"
    with pytest.raises(BoundaryError) as escape:
        host.invoke(
            _request(
                filesystem,
                "act",
                {"action": "write_file", "path": "x.txt", "content": "no"},
                idempotency_key="phase9-key-002",
                root=str(outside),
                namespace="filesystem",
            )
        )
    assert escape.value.code == "state_boundary_violation"
    assert filesystem.calls["act"] == 0


class _BadResultAdapter(TransactionalRevisionedServiceAdapter):
    def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
        self.calls["observe"] += 1
        return AdapterOperationResult(
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            system_id=self.system_id,
            state_boundary_id=deterministic_identifier("state_boundary", 808),
            capability="observe",
            classification="observed",
            occurred_at=TS,
            evidence={"bad": True},
            retry="not_applicable",
            data={},
            payload_ref={"retention_class": "none"},
        )


def test_malformed_result_timeout_and_adapter_exception_are_normalized_or_rejected(
    contracts: ContractBundle,
) -> None:
    bad = _BadResultAdapter(seed=130)
    host = AdapterHost(contracts=contracts, adapters=[bad])
    with pytest.raises(AdapterValidationError) as invalid_result:
        host.invoke(_request(bad, "observe", {"subject": "x"}, namespace="transactional"))
    assert invalid_result.value.code == "schema_violation"

    clock = VirtualClock()

    class SlowAdapter(TransactionalRevisionedServiceAdapter):
        def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
            clock.advance(10)
            return super().observe(request)

    slow = SlowAdapter(seed=140)
    timeout_host = AdapterHost(contracts=contracts, adapters=[slow], clock_ms=clock.now_ms)
    with pytest.raises(AdapterHostError) as timeout:
        timeout_host.invoke(
            _request(slow, "observe", {"subject": "x"}, namespace="transactional", timeout_ms=5)
        )
    assert timeout.value.code == "adapter_unavailable"

    class RaisingAdapter(TransactionalRevisionedServiceAdapter):
        def observe(self, request: AdapterOperationRequest) -> AdapterOperationResult:
            raise RuntimeError("synthetic failure")

    raising = RaisingAdapter(seed=150)
    raising_host = AdapterHost(contracts=contracts, adapters=[raising])
    with pytest.raises(AdapterHostError) as adapter_error:
        raising_host.invoke(
            _request(raising, "observe", {"subject": "x"}, namespace="transactional")
        )
    assert adapter_error.value.code == "adapter_error"


def test_transactional_service_revisions_rejection_idempotency_and_reconcile(
    contracts: ContractBundle,
) -> None:
    adapter = TransactionalRevisionedServiceAdapter()
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    data = {"action": "set_value", "subject": "ticket-1", "value": "open"}
    accepted = host.invoke(
        _request(
            adapter,
            "act",
            data,
            idempotency_key="phase9-key-101",
            namespace="transactional",
        )
    )
    assert accepted.classification == "accepted"
    assert accepted.external_revision == "rev-1"

    same = host.invoke(
        _request(
            adapter,
            "act",
            data,
            idempotency_key="phase9-key-101",
            namespace="transactional",
        )
    )
    assert same.external_revision == "rev-1"

    conflict_data = {"action": "set_value", "subject": "ticket-1", "value": "closed"}
    rejected = host.invoke(
        _request(
            adapter,
            "act",
            conflict_data,
            idempotency_key="phase9-key-101",
            namespace="transactional",
        )
    )
    assert rejected.classification == "rejected"
    assert rejected.evidence["reason"] == "idempotency_conflict"

    stale = host.invoke(
        _request(
            adapter,
            "act",
            {**conflict_data, "expected_revision": "rev-0"},
            idempotency_key="phase9-key-102",
            namespace="transactional",
        )
    )
    assert stale.classification == "rejected"
    assert stale.retry == "after_refresh"

    reconciled = host.invoke(
        _request(
            adapter,
            "reconcile",
            {"idempotency_key": "phase9-key-101"},
            namespace="transactional",
        )
    )
    assert reconciled.classification == "confirmed_accepted"


def test_reconstructed_filesystem_models_hash_revisions_partial_failure_and_lifecycle(
    contracts: ContractBundle, tmp_path: Path
) -> None:
    adapter = ReconstructedFilesystemAdapter(tmp_path / "fs")
    host = AdapterHost(contracts=contracts, adapters=[adapter])
    write_data = {"action": "write_file", "path": "README.md", "content": "print('not executed')"}
    written = host.invoke(
        _request(
            adapter,
            "act",
            write_data,
            idempotency_key="phase9-key-201",
            root=str(adapter.root / "README.md"),
            namespace="filesystem",
        )
    )
    assert written.classification == "accepted"
    assert (adapter.root / "README.md").read_text(encoding="utf-8") == "print('not executed')"
    assert not (adapter.root / "not-executed-marker").exists()

    observed = host.invoke(
        _request(
            adapter,
            "observe",
            {"path": "README.md"},
            root=str(adapter.root / "README.md"),
            namespace="filesystem",
        )
    )
    assert observed.external_revision == written.external_revision

    partial = host.invoke(
        _request(
            adapter,
            "act",
            {
                "action": "multi_write",
                "writes": [
                    {"path": "a.txt", "content": "a"},
                    {"path": "b.txt", "content": "b"},
                ],
                "fail_after": 1,
            },
            idempotency_key="phase9-key-202",
            root=str(adapter.root / "a.txt"),
            namespace="filesystem",
        )
    )
    assert partial.classification == "failed"
    assert partial.data["partial"] is True
    assert (adapter.root / "a.txt").is_file()
    assert not (adapter.root / "b.txt").exists()

    renamed = host.invoke(
        _request(
            adapter,
            "act",
            {"action": "rename", "source_path": "README.md", "target_path": "README2.md"},
            idempotency_key="phase9-key-203",
            root=str(adapter.root / "README.md"),
            namespace="filesystem",
        )
    )
    assert renamed.external_identity is not None
    assert renamed.external_identity["lifecycle_state"] == "renamed"

    deleted = host.invoke(
        _request(
            adapter,
            "act",
            {"action": "delete", "path": "README2.md"},
            idempotency_key="phase9-key-204",
            root=str(adapter.root / "README2.md"),
            namespace="filesystem",
        )
    )
    assert deleted.external_identity is not None
    assert deleted.external_identity["lifecycle_state"] == "deleted"


def test_async_unknown_outcome_service_pending_completion_duplicate_and_unknown(
    contracts: ContractBundle,
) -> None:
    clock = VirtualClock()
    adapter = AsyncUnknownOutcomeAdapter(clock=clock)
    host = AdapterHost(contracts=contracts, adapters=[adapter], clock_ms=clock.now_ms)
    data = {"action": "submit_job", "subject": "job-1", "completion_delay_ms": 50}
    pending = host.invoke(
        _request(adapter, "act", data, idempotency_key="phase9-key-301", namespace="async")
    )
    assert pending.classification == "pending"

    duplicate = host.invoke(
        _request(adapter, "act", data, idempotency_key="phase9-key-301", namespace="async")
    )
    assert duplicate.classification == "duplicated"

    still_pending = host.invoke(
        _request(
            adapter,
            "reconcile",
            {"idempotency_key": "phase9-key-301"},
            namespace="async",
        )
    )
    assert still_pending.classification == "still_pending"

    clock.advance(50)
    confirmed = host.invoke(
        _request(
            adapter,
            "reconcile",
            {"idempotency_key": "phase9-key-301"},
            namespace="async",
        )
    )
    assert confirmed.classification == "confirmed_accepted"
    assert confirmed.external_revision == "async-rev-async-1"

    unknown_data = {
        "action": "submit_job",
        "subject": "job-2",
        "completion_delay_ms": 1,
        "force_unknown": True,
    }
    unknown_result = host.invoke(
        _request(
            adapter,
            "act",
            unknown_data,
            idempotency_key="phase9-key-302",
            namespace="async",
        )
    )
    assert unknown_result.classification == "outcome_unknown"
    clock.advance(100)
    unknown_reconcile = host.invoke(
        _request(
            adapter,
            "reconcile",
            {"idempotency_key": "phase9-key-302"},
            namespace="async",
        )
    )
    assert unknown_reconcile.classification == "unknown"


def test_synthetic_state_export_is_deterministic_and_fixture_exists(
    contracts: ContractBundle,
) -> None:
    first_clock = VirtualClock()
    first = AsyncUnknownOutcomeAdapter(seed=330, clock=first_clock)
    second_clock = VirtualClock()
    second = AsyncUnknownOutcomeAdapter(seed=330, clock=second_clock)
    first_host = AdapterHost(contracts=contracts, adapters=[first], clock_ms=first_clock.now_ms)
    second_host = AdapterHost(contracts=contracts, adapters=[second], clock_ms=second_clock.now_ms)
    data = {"action": "submit_job", "subject": "job", "completion_delay_ms": 5}
    first_host.invoke(
        _request(first, "act", data, idempotency_key="phase9-key-401", namespace="async")
    )
    second_host.invoke(
        _request(second, "act", data, idempotency_key="phase9-key-401", namespace="async")
    )
    first_clock.advance(5)
    second_clock.advance(5)
    first_host.invoke(
        _request(first, "reconcile", {"idempotency_key": "phase9-key-401"}, namespace="async")
    )
    second_host.invoke(
        _request(second, "reconcile", {"idempotency_key": "phase9-key-401"}, namespace="async")
    )
    assert first.export_state() == second.export_state()
    assert (REPO_ROOT / "tests" / "fixtures" / "adapters" / "synthetic_systems.json").is_file()
