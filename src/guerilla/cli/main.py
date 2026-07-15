"""CLI entry point and Phase 15 local command dispatch."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO

from guerilla import __version__
from guerilla.identity import IdentifierGenerator

DEFAULT_TIMESTAMP = "2026-07-14T00:00:00Z"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="guerilla",
        description="Guerilla -- authoritative causal-lineage and continuity layer",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"guerilla {__version__}",
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root for local graph operations",
    )
    parser.add_argument(
        "--contracts",
        default=None,
        help="Repository root containing schemas/ and registries/",
    )
    parser.add_argument(
        "--principal",
        default="local-user",
        help="Effective local authorization principal",
    )
    subparsers = parser.add_subparsers(dest="command", required=False)

    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument(
        "--json",
        action="store_true",
        help="Output version as JSON",
    )

    workspace = subparsers.add_parser("workspace", help="Initialize and inspect workspaces")
    workspace_sub = workspace.add_subparsers(dest="workspace_command", required=True)
    workspace_init = workspace_sub.add_parser("init", help="Initialize a local workspace")
    workspace_init.add_argument("--workspace-id", default=None)
    workspace_init.add_argument("--at", default=DEFAULT_TIMESTAMP)
    workspace_sub.add_parser("verify", help="Verify workspace replay")
    workspace_sub.add_parser("show", help="Show current graph revision and commit")

    adapter = subparsers.add_parser("adapter", help="List and inspect configured adapters")
    adapter_sub = adapter.add_subparsers(dest="adapter_command", required=True)
    adapter_sub.add_parser("list", help="List configured adapters")
    adapter_describe = adapter_sub.add_parser("describe", help="Describe one adapter")
    adapter_describe.add_argument("adapter")
    adapter_describe.add_argument("--at", default=DEFAULT_TIMESTAMP)
    adapter_sub.add_parser("validate", help="Validate configured adapter descriptors")

    goal = subparsers.add_parser("goal", help="Create local goal records")
    goal_sub = goal.add_subparsers(dest="goal_command", required=True)
    goal_create = goal_sub.add_parser("create", help="Create a goal node")
    goal_create.add_argument("--title", required=True)
    goal_create.add_argument("--status", default="open")
    goal_create.add_argument("--at", default=DEFAULT_TIMESTAMP)
    goal_create.add_argument("--expected-graph-revision", type=int, default=None)
    _add_input_options(goal_create)

    operation = subparsers.add_parser("operation", help="Create local operation records")
    operation_sub = operation.add_subparsers(dest="operation_command", required=True)
    operation_create = operation_sub.add_parser("create", help="Create an operation node")
    operation_create.add_argument("--title", required=True)
    operation_create.add_argument("--status", default="planned")
    operation_create.add_argument("--depends-on", action="append", default=[])
    operation_create.add_argument("--at", default=DEFAULT_TIMESTAMP)
    operation_create.add_argument("--expected-graph-revision", type=int, default=None)
    _add_input_options(operation_create)

    evaluation = subparsers.add_parser("evaluation", help="Create local evaluation records")
    evaluation_sub = evaluation.add_subparsers(dest="evaluation_command", required=True)
    evaluation_create = evaluation_sub.add_parser("create", help="Create an evaluation node")
    evaluation_create.add_argument("--subject", required=True)
    evaluation_create.add_argument("--result", default="pass")
    evaluation_create.add_argument("--summary", default="")
    evaluation_create.add_argument("--at", default=DEFAULT_TIMESTAMP)
    evaluation_create.add_argument("--expected-graph-revision", type=int, default=None)
    _add_input_options(evaluation_create)

    observe = subparsers.add_parser("observe", help="Request and ingest bounded observations")
    observe_sub = observe.add_subparsers(dest="observe_command", required=True)
    observe_request = observe_sub.add_parser("request", help="Request an adapter observation")
    observe_request.add_argument("adapter")
    observe_request.add_argument("--root", default=None)
    observe_request.add_argument("--namespace", default=None)
    observe_request.add_argument("--at", default=DEFAULT_TIMESTAMP)
    observe_request.add_argument("--expected-graph-revision", type=int, default=None)
    _add_input_options(observe_request)

    act = subparsers.add_parser("act", help="Commit intent and invoke a bounded action")
    act_sub = act.add_subparsers(dest="act_command", required=True)
    act_request = act_sub.add_parser("request", help="Run one intent-before-action flow")
    act_request.add_argument("adapter")
    act_request.add_argument("--action", required=True)
    act_request.add_argument("--idempotency-key", required=True)
    act_request.add_argument("--root", default=None)
    act_request.add_argument("--namespace", default=None)
    act_request.add_argument("--expected-graph-revision", type=int, default=None)
    act_request.add_argument("--expected-external-revision", default=None)
    act_request.add_argument("--after-state", default=None)
    act_request.add_argument("--fail-at", default=None)
    act_request.add_argument("--at", default=DEFAULT_TIMESTAMP)
    _add_input_options(act_request)

    reconcile = subparsers.add_parser("reconcile", help="List or reconcile uncertain intents")
    reconcile_sub = reconcile.add_subparsers(dest="reconcile_command", required=True)
    reconcile_sub.add_parser("list", help="List unresolved intents")
    reconcile_run = reconcile_sub.add_parser("run", help="Reconcile one action intent")
    reconcile_run.add_argument("adapter")
    reconcile_run.add_argument("--intent-node-id", required=True)
    reconcile_run.add_argument("--idempotency-key", required=True)
    reconcile_run.add_argument("--namespace", default=None)
    reconcile_run.add_argument("--root", default=None)
    reconcile_run.add_argument("--after-state", default=None)
    reconcile_run.add_argument("--expected-graph-revision", type=int, default=None)
    reconcile_run.add_argument("--at", default=DEFAULT_TIMESTAMP)

    conflict = subparsers.add_parser("conflict", help="List, inspect, record, or resolve conflicts")
    conflict_sub = conflict.add_subparsers(dest="conflict_command", required=True)
    conflict_sub.add_parser("list", help="List conflicts")
    conflict_inspect = conflict_sub.add_parser("inspect", help="Inspect a conflict node")
    conflict_inspect.add_argument("conflict_node_id")
    conflict_record = conflict_sub.add_parser("record", help="Record a conflict")
    conflict_record.add_argument("--type", required=True)
    conflict_record.add_argument("--subject", required=True)
    conflict_record.add_argument("--evidence", action="append", default=[])
    conflict_record.add_argument("--reason", required=True)
    conflict_record.add_argument("--summary", default="")
    conflict_record.add_argument("--expected-graph-revision", type=int, default=None)
    conflict_record.add_argument("--at", default=DEFAULT_TIMESTAMP)
    for name in ("decide", "resolve"):
        conflict_resolve = conflict_sub.add_parser(name, help="Resolve a conflict append-only")
        conflict_resolve.add_argument("conflict_node_id")
        conflict_resolve.add_argument("--chosen-outcome", required=True)
        conflict_resolve.add_argument("--rationale", required=True)
        conflict_resolve.add_argument("--expected-graph-revision", type=int, default=None)
        conflict_resolve.add_argument("--at", default=DEFAULT_TIMESTAMP)

    lineage = subparsers.add_parser("lineage", help="Run graph lineage queries")
    lineage_sub = lineage.add_subparsers(dest="lineage_command", required=True)
    for name in ("ancestors", "descendants"):
        lineage_query = lineage_sub.add_parser(name, help=f"List {name}")
        lineage_query.add_argument("node_id")
        lineage_query.add_argument("--revision", type=int, default=None)

    view = subparsers.add_parser("view", help="Generate source-bound derived views")
    view_sub = view.add_subparsers(dest="view_command", required=True)
    for name in ("lineage", "dependency", "conflict", "progress", "traceability"):
        view_parser = view_sub.add_parser(name, help=f"Generate {name} view")
        view_parser.add_argument("--node-id", default=None)
        view_parser.add_argument("--revision", type=int, default=None)
        view_parser.add_argument("--at", default=DEFAULT_TIMESTAMP)
        view_parser.add_argument("--persist", action="store_true")

    manifest = subparsers.add_parser("manifest", help="Generate or show manifests")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    for name in ("generate", "show"):
        manifest_parser = manifest_sub.add_parser(name, help=f"{name.title()} manifest")
        manifest_parser.add_argument("--revision", type=int, default=None)
        manifest_parser.add_argument("--at", default=DEFAULT_TIMESTAMP)
        manifest_parser.add_argument("--persist", action="store_true")

    snapshot = subparsers.add_parser("snapshot", help="Create, verify, and resume snapshots")
    snapshot_sub = snapshot.add_subparsers(dest="snapshot_command", required=True)
    snapshot_create = snapshot_sub.add_parser("create", help="Create a snapshot")
    snapshot_create.add_argument("--revision", type=int, default=None)
    snapshot_create.add_argument("--expected-graph-revision", type=int, default=None)
    snapshot_create.add_argument("--at", default=DEFAULT_TIMESTAMP)
    snapshot_create.add_argument("--no-summary", action="store_true")
    snapshot_verify = snapshot_sub.add_parser("verify", help="Verify a snapshot")
    snapshot_verify.add_argument("snapshot_node_id")
    snapshot_resume = snapshot_sub.add_parser("resume", help="Build resume context")
    snapshot_resume.add_argument("snapshot_node_id")

    graph = subparsers.add_parser("graph", help="Verify, replay, query, and rebuild the graph")
    graph_sub = graph.add_subparsers(dest="graph_command", required=True)
    graph_sub.add_parser("verify", help="Verify graph replay and index status")
    graph_sub.add_parser("replay", help="Replay graph without invoking adapters")
    graph_sub.add_parser("heads", help="Show graph heads")
    graph_sub.add_parser("rebuild-index", help="Rebuild non-authoritative SQLite index")

    return parser


def run(
    argv: Sequence[str] | None = None,
    *,
    context: Any | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        if args.json:
            json.dump(
                {
                    "package": "guerilla",
                    "version": __version__,
                    "python": sys.version,
                },
                stdout,
                indent=2,
            )
            stdout.write("\n")
        else:
            print(f"guerilla {__version__}", file=stdout)
        return 0
    if args.command is None:
        parser.print_help()
        return 0

    from .workflows import CliWorkflowError, emit_error, emit_success

    try:
        runtime = _runtime(args, context)
        operation, result = _dispatch(args, runtime)
    except (CliWorkflowError, ValueError, OSError) as exc:
        return emit_error(stderr, exc)
    emit_success(stdout, operation, result)
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    sys.exit(run(argv))


def _runtime(args: Any, context: Any | None) -> Any:
    from .workflows import Phase15Runtime, load_runtime

    if context is not None:
        return Phase15Runtime(context)
    contracts_root = None if args.contracts is None else Path(str(args.contracts)).resolve()
    return load_runtime(
        Path(str(args.workspace)).resolve(),
        contracts_root,
        principal_id=str(args.principal),
    )


def _dispatch(args: Any, runtime: Any) -> tuple[str, dict[str, Any]]:
    from .workflows import load_input_mapping

    command = str(args.command)
    if command == "workspace":
        return _dispatch_workspace(args, runtime)
    if command == "adapter":
        return _dispatch_adapter(args, runtime)
    if command == "goal":
        metadata = load_input_mapping(args.input, args.input_file)
        metadata.setdefault("title", args.title)
        result = runtime.create_local_node(
            node_type="goal",
            status=str(args.status),
            metadata=metadata,
            created_at=str(args.at),
            expected_graph_revision=args.expected_graph_revision,
        )
        return "goal.create", result
    if command == "operation":
        metadata = load_input_mapping(args.input, args.input_file)
        metadata.setdefault("title", args.title)
        relationships = [
            ("depends_on", str(dependency), "__new_node__") for dependency in list(args.depends_on)
        ]
        result = _create_node_with_new_to_edges(
            runtime,
            node_type="operation",
            status=str(args.status),
            metadata=metadata,
            created_at=str(args.at),
            expected_graph_revision=args.expected_graph_revision,
            relationships=relationships,
        )
        return "operation.create", result
    if command == "evaluation":
        metadata = load_input_mapping(args.input, args.input_file)
        metadata.update({"result": args.result, "summary": args.summary})
        result = _create_node_with_new_to_edges(
            runtime,
            node_type="evaluation",
            status=str(args.result),
            metadata=metadata,
            created_at=str(args.at),
            expected_graph_revision=args.expected_graph_revision,
            source_node_ids=[str(args.subject)],
            relationships=[("evaluated_by", str(args.subject), "__new_node__")],
        )
        return "evaluation.create", result
    if command == "observe":
        selector = load_input_mapping(args.input, args.input_file)
        return (
            "observe.request",
            runtime.observe(
                str(args.adapter),
                selector=selector,
                at=str(args.at),
                expected_graph_revision=args.expected_graph_revision,
                root=args.root,
                namespace=args.namespace,
            ),
        )
    if command == "act":
        after_state = None if args.after_state is None else json.loads(str(args.after_state))
        return (
            "act.request",
            runtime.act(
                str(args.adapter),
                action=str(args.action),
                arguments=load_input_mapping(args.input, args.input_file),
                idempotency_key=str(args.idempotency_key),
                at=str(args.at),
                expected_graph_revision=args.expected_graph_revision,
                expected_external_revision=args.expected_external_revision,
                root=args.root,
                namespace=args.namespace,
                after_state_selector=after_state,
                fail_at=args.fail_at,
            ),
        )
    if command == "reconcile":
        return _dispatch_reconcile(args, runtime)
    if command == "conflict":
        return _dispatch_conflict(args, runtime)
    if command == "lineage":
        return (
            f"lineage.{args.lineage_command}",
            runtime.lineage(
                node_id=str(args.node_id),
                direction=str(args.lineage_command),
                revision=args.revision,
            ),
        )
    if command == "view":
        return (
            f"view.{args.view_command}",
            runtime.view(
                str(args.view_command),
                node_id=args.node_id,
                revision=args.revision,
                generated_at=str(args.at),
                persist=bool(args.persist),
            ),
        )
    if command == "manifest":
        return (
            f"manifest.{args.manifest_command}",
            runtime.view(
                "manifest",
                node_id=None,
                revision=args.revision,
                generated_at=str(args.at),
                persist=bool(args.persist),
            ),
        )
    if command == "snapshot":
        return _dispatch_snapshot(args, runtime)
    if command == "graph":
        return _dispatch_graph(args, runtime)
    raise ValueError(f"unsupported command: {command}")


def _dispatch_workspace(args: Any, runtime: Any) -> tuple[str, dict[str, Any]]:
    subcommand = str(args.workspace_command)
    if subcommand == "init":
        workspace_id = args.workspace_id or str(IdentifierGenerator().generate("workspace"))
        return "workspace.init", runtime.workspace_init(
            workspace_id=workspace_id,
            created_at=str(args.at),
        )
    if subcommand in {"verify", "show"}:
        return f"workspace.{subcommand}", runtime.workspace_show()
    raise ValueError(f"unsupported workspace command: {subcommand}")


def _dispatch_adapter(args: Any, runtime: Any) -> tuple[str, dict[str, Any]]:
    subcommand = str(args.adapter_command)
    if subcommand == "list":
        return "adapter.list", runtime.adapter_list()
    if subcommand == "describe":
        return "adapter.describe", runtime.adapter_describe(str(args.adapter), at=str(args.at))
    if subcommand == "validate":
        return "adapter.validate", runtime.adapter_validate()
    raise ValueError(f"unsupported adapter command: {subcommand}")


def _dispatch_reconcile(args: Any, runtime: Any) -> tuple[str, dict[str, Any]]:
    subcommand = str(args.reconcile_command)
    if subcommand == "list":
        return "reconcile.list", runtime.unresolved_intents()
    if subcommand == "run":
        after_state = None if args.after_state is None else json.loads(str(args.after_state))
        return (
            "reconcile.run",
            runtime.reconcile(
                str(args.adapter),
                intent_node_id=str(args.intent_node_id),
                idempotency_key=str(args.idempotency_key),
                at=str(args.at),
                expected_graph_revision=args.expected_graph_revision,
                namespace=args.namespace,
                root=args.root,
                after_state_selector=after_state,
            ),
        )
    raise ValueError(f"unsupported reconcile command: {subcommand}")


def _dispatch_conflict(args: Any, runtime: Any) -> tuple[str, dict[str, Any]]:
    subcommand = str(args.conflict_command)
    if subcommand == "list":
        return "conflict.list", runtime.conflict_list()
    if subcommand == "inspect":
        return "conflict.inspect", runtime.conflict_inspect(str(args.conflict_node_id))
    if subcommand == "record":
        return (
            "conflict.record",
            runtime.conflict_record(
                conflict_type=str(args.type),
                subject_node_id=str(args.subject),
                evidence_node_ids=tuple(str(item) for item in args.evidence),
                reason=str(args.reason),
                summary=str(args.summary),
                at=str(args.at),
                expected_graph_revision=args.expected_graph_revision,
            ),
        )
    if subcommand in {"decide", "resolve"}:
        return (
            f"conflict.{subcommand}",
            runtime.conflict_resolve(
                conflict_node_id=str(args.conflict_node_id),
                chosen_outcome=str(args.chosen_outcome),
                rationale=str(args.rationale),
                at=str(args.at),
                expected_graph_revision=args.expected_graph_revision,
            ),
        )
    raise ValueError(f"unsupported conflict command: {subcommand}")


def _dispatch_snapshot(args: Any, runtime: Any) -> tuple[str, dict[str, Any]]:
    subcommand = str(args.snapshot_command)
    if subcommand == "create":
        return (
            "snapshot.create",
            runtime.snapshot_create(
                revision=args.revision,
                at=str(args.at),
                expected_graph_revision=args.expected_graph_revision,
                persist_summary=not bool(args.no_summary),
            ),
        )
    if subcommand == "verify":
        return "snapshot.verify", runtime.snapshot_verify(str(args.snapshot_node_id))
    if subcommand == "resume":
        return "snapshot.resume", runtime.snapshot_resume(str(args.snapshot_node_id))
    raise ValueError(f"unsupported snapshot command: {subcommand}")


def _dispatch_graph(args: Any, runtime: Any) -> tuple[str, dict[str, Any]]:
    subcommand = str(args.graph_command)
    if subcommand == "verify":
        return "graph.verify", runtime.graph_verify()
    if subcommand == "replay":
        return "graph.replay", runtime.graph_replay()
    if subcommand == "heads":
        return "graph.heads", runtime.graph_heads()
    if subcommand == "rebuild-index":
        return "graph.rebuild-index", runtime.graph_rebuild_index()
    raise ValueError(f"unsupported graph command: {subcommand}")


def _create_node_with_new_to_edges(
    runtime: Any,
    *,
    node_type: str,
    status: str,
    metadata: dict[str, Any],
    created_at: str,
    expected_graph_revision: int | None,
    relationships: list[tuple[str, str, str]],
    source_node_ids: list[str] | None = None,
) -> dict[str, Any]:
    # Generate the node first, then resolve placeholder relationship endpoints.
    store = runtime.store()
    runtime._require_expected_revision(store, expected_graph_revision)
    replay = store.replay()
    new_node_id = str(store.ids.generate("node"))
    resolved_relationships = [
        (relationship_type, from_id, new_node_id if to_id == "__new_node__" else to_id)
        for relationship_type, from_id, to_id in relationships
    ]
    node = {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": replay.workspace_id,
        "node_id": new_node_id,
        "entity_id": str(store.ids.generate("entity")),
        "node_type": node_type,
        "created_at": created_at,
        "actor": {"actor_id": runtime.principal_id, "actor_kind": "human"},
        "authority": {
            "authority_type": "guerilla",
            "principal_id": runtime.principal_id,
            "profile": "local-owner-v1",
        },
        "status": status,
        "provenance": {
            "source": "guerilla.phase15.cli",
            "source_record_ids": [] if source_node_ids is None else source_node_ids,
            "metadata": {"phase": 15, "node_type": node_type},
        },
        "payload_ref": {"retention_class": "metadata", "metadata": metadata},
        "metadata": {
            "guerilla_phase15_cli": {
                "kind": node_type,
                "status": status,
                "details": metadata,
            }
        },
        "extensions": {},
        "record_hash": "0" * 64,
    }
    members = [node]
    for relationship_type, from_node_id, to_node_id in resolved_relationships:
        members.append(
            runtime._edge(
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
        actor={"actor_id": runtime.principal_id, "actor_kind": "human"},
        created_at=created_at,
        committed_at=created_at,
        principal_id=runtime.principal_id,
    )
    return {
        "node_id": new_node_id,
        "node_type": node_type,
        "graph_revision": commit["graph_revision"],
        "commit_hash": commit["commit_hash"],
        "transaction_id": commit["transaction_id"],
    }


def _add_input_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", default=None, help="JSON object input")
    parser.add_argument("--input-file", default=None, help="Path to a JSON object input file")
