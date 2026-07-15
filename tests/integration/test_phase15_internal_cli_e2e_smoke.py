from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Any, cast

import pytest

from guerilla.adapters import (
    AsyncUnknownOutcomeAdapter,
    ReconstructedFilesystemAdapter,
    TransactionalRevisionedServiceAdapter,
    VirtualClock,
)
from guerilla.adapters.synthetic import deterministic_identifier
from guerilla.cli.main import run
from guerilla.cli.workflows import Phase15Context
from guerilla.contracts import ContractBundle, load_contract_bundle
from guerilla.index import SQLiteGraphIndex
from guerilla.storage import GraphStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TS = "2026-07-14T00:00:00Z"


@pytest.fixture(scope="session")
def contracts() -> ContractBundle:
    return load_contract_bundle(REPO_ROOT)


def _context(
    tmp_path: Path,
    contracts: ContractBundle,
) -> tuple[Phase15Context, dict[str, Any]]:
    clock = VirtualClock()
    adapters = {
        "transactional": TransactionalRevisionedServiceAdapter(),
        "filesystem": ReconstructedFilesystemAdapter(tmp_path / "fs"),
        "async": AsyncUnknownOutcomeAdapter(clock=clock),
    }
    context = Phase15Context(
        root=tmp_path,
        contracts=contracts,
        clock=clock,
        adapters=adapters,
    )
    return context, adapters


def _invoke(context: Phase15Context, *argv: str) -> dict[str, Any]:
    stdout = StringIO()
    stderr = StringIO()
    code = run(argv, context=context, stdout=stdout, stderr=stderr)
    assert code == 0, stderr.getvalue()
    decoded = json.loads(stdout.getvalue())
    assert decoded["ok"] is True
    return cast(dict[str, Any], decoded["result"])


def _invoke_error(context: Phase15Context, *argv: str) -> dict[str, Any]:
    stdout = StringIO()
    stderr = StringIO()
    code = run(argv, context=context, stdout=stdout, stderr=stderr)
    assert code != 0
    assert stdout.getvalue() == ""
    decoded = json.loads(stderr.getvalue())
    assert decoded["ok"] is False
    return cast(dict[str, Any], decoded["error"])


def _init_workspace(context: Phase15Context, seed: int) -> None:
    result = _invoke(
        context,
        "workspace",
        "init",
        "--workspace-id",
        deterministic_identifier("workspace", seed),
    )
    assert result["graph_revision"] == 0


def _append_interleaving_event(root: Path, contracts: ContractBundle) -> None:
    store = GraphStore(root, contracts=contracts)
    replay = store.replay()
    node = {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": replay.workspace_id,
        "node_id": str(store.ids.generate("node")),
        "entity_id": str(store.ids.generate("entity")),
        "node_type": "event",
        "created_at": TS,
        "actor": {"actor_id": "local-user", "actor_kind": "human"},
        "authority": {
            "authority_type": "guerilla",
            "principal_id": "local-user",
            "profile": "local-owner-v1",
        },
        "status": "interleaving_write",
        "provenance": {
            "source": "test.phase15.interleaving_writer",
            "source_record_ids": [],
        },
        "payload_ref": {"retention_class": "none"},
        "metadata": {"phase15_interleaving_test": {"kind": "interleaving_write"}},
        "extensions": {},
        "record_hash": "0" * 64,
    }
    store.append_transaction(
        [node],
        actor={"actor_id": "local-user", "actor_kind": "human"},
        created_at=TS,
        committed_at=TS,
    )


def test_cli_expected_graph_revision_rejects_interleaving_observe_write(
    contracts: ContractBundle,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, adapters = _context(tmp_path, contracts)
    adapters["transactional"].records["ticket-guard"] = {"value": "open", "revision": "rev-1"}
    _init_workspace(context, 1504)
    original_append = GraphStore.append_transaction
    injected = False

    def append_with_interleaving(
        self: GraphStore,
        members: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        nonlocal injected
        if not injected:
            injected = True
            _append_interleaving_event(tmp_path, contracts)
        return original_append(self, members, **kwargs)

    monkeypatch.setattr(GraphStore, "append_transaction", append_with_interleaving)

    error = _invoke_error(
        context,
        "observe",
        "request",
        "transactional",
        "--namespace",
        "transactional",
        "--expected-graph-revision",
        "0",
        "--input",
        json.dumps({"subject": "ticket-guard"}),
    )

    replay = GraphStore(tmp_path, contracts=contracts).replay()
    assert error["code"] == "stale_graph_revision"
    assert injected is True
    assert replay.graph_revision == 1
    assert adapters["transactional"].calls["observe"] == 1


def test_transactional_cli_e2e_intent_after_state_and_evaluation(
    contracts: ContractBundle,
    tmp_path: Path,
) -> None:
    context, adapters = _context(tmp_path, contracts)
    adapters["transactional"].records["ticket-1"] = {"value": "open", "revision": "rev-1"}
    _init_workspace(context, 1500)

    observed = _invoke(
        context,
        "observe",
        "request",
        "transactional",
        "--namespace",
        "transactional",
        "--expected-graph-revision",
        "0",
        "--input",
        json.dumps({"subject": "ticket-1"}),
    )
    assert observed["observation_classification"] == "first_observation"

    goal = _invoke(
        context,
        "goal",
        "create",
        "--title",
        "ship continuity smoke",
        "--expected-graph-revision",
        str(observed["graph_revision"]),
    )
    operation = _invoke(
        context,
        "operation",
        "create",
        "--title",
        "update ticket",
        "--depends-on",
        goal["node_id"],
        "--expected-graph-revision",
        str(goal["graph_revision"]),
    )
    action = _invoke(
        context,
        "act",
        "request",
        "transactional",
        "--action",
        "set_value",
        "--idempotency-key",
        "phase15-key-transactional",
        "--namespace",
        "transactional",
        "--expected-graph-revision",
        str(operation["graph_revision"]),
        "--after-state",
        json.dumps({"subject": "ticket-1"}),
        "--input",
        json.dumps({"subject": "ticket-1", "value": "done"}),
    )
    assert action["action_classification"] == "accepted"
    assert action["after_state_observation"] is not None

    evaluation = _invoke(
        context,
        "evaluation",
        "create",
        "--subject",
        operation["node_id"],
        "--result",
        "pass",
        "--summary",
        "transactional CLI path completed",
        "--expected-graph-revision",
        str(action["graph_revision"]),
    )
    replay = _invoke(context, "graph", "replay")
    assert replay["graph_revision"] == evaluation["graph_revision"]
    assert adapters["transactional"].calls["act"] == 1


def test_snapshot_manifest_cli_smoke_uses_derived_view_path(
    contracts: ContractBundle,
    tmp_path: Path,
) -> None:
    context, _adapters = _context(tmp_path, contracts)
    _init_workspace(context, 1503)
    goal = _invoke(context, "goal", "create", "--title", "snapshot smoke")
    manifest = _invoke(context, "manifest", "generate")
    progress = _invoke(context, "view", "progress")
    snapshot = _invoke(
        context,
        "snapshot",
        "create",
        "--expected-graph-revision",
        str(goal["graph_revision"]),
    )
    verification = _invoke(context, "snapshot", "verify", snapshot["snapshot_node_id"])
    resume = _invoke(context, "snapshot", "resume", snapshot["snapshot_node_id"])

    assert manifest["view_type"] == "manifest"
    assert progress["authoritative_status"] == "derived_non_authoritative"
    assert verification["verified"] is True
    assert resume["context_version"] == "phase14-resume-context-v1"


def test_reconstructed_filesystem_cli_e2e_conflict_decision_and_rebuild(
    contracts: ContractBundle,
    tmp_path: Path,
) -> None:
    context, adapters = _context(tmp_path, contracts)
    filesystem = adapters["filesystem"]
    _init_workspace(context, 1501)
    (filesystem.root / "README.md").write_text("initial", encoding="utf-8")

    first = _invoke(
        context,
        "observe",
        "request",
        "filesystem",
        "--namespace",
        "filesystem",
        "--root",
        str(filesystem.root / "README.md"),
        "--expected-graph-revision",
        "0",
        "--input",
        json.dumps({"path": "README.md"}),
    )
    partial = _invoke(
        context,
        "act",
        "request",
        "filesystem",
        "--action",
        "multi_write",
        "--idempotency-key",
        "phase15-key-filesystem",
        "--namespace",
        "filesystem",
        "--root",
        str(filesystem.root / "a.txt"),
        "--expected-graph-revision",
        str(first["graph_revision"]),
        "--after-state",
        json.dumps({"path": "a.txt"}),
        "--input",
        json.dumps(
            {
                "writes": [
                    {"path": "a.txt", "content": "a"},
                    {"path": "b.txt", "content": "b"},
                ],
                "fail_after": 1,
            }
        ),
    )
    assert partial["action_classification"] == "failed"

    conflict = _invoke(
        context,
        "conflict",
        "record",
        "--type",
        "incomplete_lineage",
        "--subject",
        partial["result_node_id"],
        "--evidence",
        partial["result_node_id"],
        "--reason",
        "partial filesystem write requires decision",
        "--summary",
        "multi_write failed after one write",
        "--expected-graph-revision",
        str(partial["graph_revision"]),
    )
    resolved = _invoke(
        context,
        "conflict",
        "decide",
        conflict["conflict_node_id"],
        "--chosen-outcome",
        "continue_from_observed_partial_state",
        "--rationale",
        "Phase 15 smoke records the partial state and continues",
        "--expected-graph-revision",
        str(conflict["graph_revision"]),
    )
    assert resolved["decision_node_id"]
    lineage = _invoke(context, "lineage", "ancestors", resolved["decision_node_id"])
    conflict_view = _invoke(context, "view", "conflict")
    assert conflict["conflict_node_id"] in lineage["items"]
    assert conflict_view["view_type"] == "conflict"

    index = SQLiteGraphIndex(tmp_path)
    if index.path.exists():
        index.path.unlink()
    rebuilt = _invoke(context, "graph", "rebuild-index")
    snapshot = _invoke(
        context,
        "snapshot",
        "create",
        "--expected-graph-revision",
        str(rebuilt["source_revision"]),
    )
    calls_before_replay = dict(filesystem.calls)
    replayed = _invoke(context, "graph", "replay")

    assert replayed["graph_revision"] == snapshot["graph_revision"]
    assert filesystem.calls == calls_before_replay
    listed = _invoke(context, "conflict", "list")
    assert listed["conflicts"][0]["status"] == "resolved"


def test_async_unknown_cli_reconciliation_and_replay_safety(
    contracts: ContractBundle,
    tmp_path: Path,
) -> None:
    context, adapters = _context(tmp_path, contracts)
    async_adapter = adapters["async"]
    _init_workspace(context, 1502)
    assert _invoke(context, "adapter", "validate")["validated"] is True
    assert _invoke(context, "adapter", "describe", "async")["classification"] == "described"
    assert len(_invoke(context, "adapter", "list")["adapters"]) == 3

    unknown = _invoke(
        context,
        "act",
        "request",
        "async",
        "--action",
        "submit_job",
        "--idempotency-key",
        "phase15-key-async-unknown",
        "--namespace",
        "async",
        "--expected-graph-revision",
        "0",
        "--input",
        json.dumps({"subject": "job-unknown", "force_unknown": True}),
    )
    assert unknown["action_classification"] == "outcome_unknown"
    unresolved = _invoke(context, "reconcile", "list")
    assert unresolved["unresolved_intents"][0]["intent_node_id"] == unknown["intent_node_id"]

    reconciliation = _invoke(
        context,
        "reconcile",
        "run",
        "async",
        "--intent-node-id",
        unknown["intent_node_id"],
        "--idempotency-key",
        "phase15-key-async-unknown",
        "--namespace",
        "async",
        "--expected-graph-revision",
        str(unknown["graph_revision"]),
    )
    assert reconciliation["classification"] == "unknown"
    assert len(reconciliation["conflict_node_ids"]) == 1

    stale = _invoke_error(
        context,
        "act",
        "request",
        "async",
        "--action",
        "submit_job",
        "--idempotency-key",
        "phase15-key-stale",
        "--namespace",
        "async",
        "--expected-graph-revision",
        "0",
        "--input",
        json.dumps({"subject": "job-stale"}),
    )
    assert stale["code"] == "stale_graph_revision"

    snapshot = _invoke(
        context,
        "snapshot",
        "create",
        "--expected-graph-revision",
        str(reconciliation["graph_revision"]),
    )
    resume = _invoke(context, "snapshot", "resume", snapshot["snapshot_node_id"])
    calls_before_replay = dict(async_adapter.calls)
    GraphStore(tmp_path, contracts=contracts).replay()
    _invoke(context, "graph", "verify")

    assert resume["pending_reconciliation"]
    assert async_adapter.calls == calls_before_replay
