"""Append-only graph store and replay."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from guerilla.authority import LocalAuthorizationProfile, validate_member_authority
from guerilla.codec import (
    ZERO_SHA256,
    CanonicalJsonError,
    canonical_bytes,
    canonical_jsonl,
    commit_hash,
    parse_raw_json,
    record_hash,
    transaction_hash,
    transaction_hash_envelope,
)
from guerilla.contracts import ContractBundle
from guerilla.graph import GraphIntegrityError, validate_transaction_integrity
from guerilla.identity import IdentifierGenerator
from guerilla.storage.errors import ReplayError, StorageError
from guerilla.storage.fsync import fsync_directory, fsync_file
from guerilla.storage.lock import WriterLock


@dataclass(frozen=True, slots=True)
class CommitInfo:
    graph_revision: int
    commit_hash: str
    transaction_hash: str
    transaction_id: str


@dataclass(slots=True)
class ReplayResult:
    workspace_id: str
    graph_revision: int = 0
    last_commit_hash: str = ZERO_SHA256
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: dict[str, dict[str, Any]] = field(default_factory=dict)
    record_revisions: dict[str, int] = field(default_factory=dict)
    commits: list[CommitInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _primary_id(record: dict[str, Any]) -> str:
    if record["record_type"] == "node":
        return str(record["node_id"])
    if record["record_type"] == "edge":
        return str(record["edge_id"])
    raise StorageError("unsupported_record_type", "only node and edge members are supported")


def _member_schema(record: dict[str, Any]) -> str:
    if record.get("record_type") == "node":
        return "node.schema.json"
    if record.get("record_type") == "edge":
        return "edge.schema.json"
    raise StorageError("unsupported_record_type", "only node and edge members are supported")


def _ordered_members(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rank = {"node": 0, "edge": 1}
    return sorted(
        members,
        key=lambda item: (rank.get(str(item.get("record_type")), 99), _primary_id(item)),
    )


def _complete_lines(active: Path) -> tuple[list[bytes], bool]:
    data = active.read_bytes()
    if not data:
        return [], False
    complete = data.endswith(b"\n")
    parts = data.split(b"\n")
    if complete:
        return parts[:-1], False
    return parts[:-1], True


def _parse_record(raw_line: bytes) -> dict[str, Any]:
    try:
        record = parse_raw_json(raw_line)
    except CanonicalJsonError as exc:
        raise ReplayError(
            "invalid_jsonl_record",
            "complete graph record is not canonical JSON",
        ) from exc
    if not isinstance(record, dict):
        raise ReplayError("invalid_jsonl_record", "complete graph record must be an object")
    if canonical_bytes(record) != raw_line:
        raise ReplayError("noncanonical_jsonl_record", "complete graph record is not canonical")
    return record


class GraphStore:
    def __init__(
        self,
        root: Path,
        *,
        contracts: ContractBundle,
        owner_principal_id: str = "local-user",
    ) -> None:
        self.root = root
        self.contracts = contracts
        self.authorization = LocalAuthorizationProfile(owner_principal_id=owner_principal_id)
        self.active_path = root / ".guerilla" / "graph" / "active.jsonl"
        self.tmp_dir = root / ".guerilla" / "tmp"
        self.locks_dir = root / ".guerilla" / "locks"
        self.ids = IdentifierGenerator()

    def replay(self) -> ReplayResult:
        lines, had_tail = _complete_lines(self.active_path)
        if not lines:
            raise ReplayError("missing_graph_header", "active graph is empty")
        header = _parse_record(lines[0])
        self.contracts.assert_valid("graph_header.schema.json", header)
        result = ReplayResult(workspace_id=str(header["workspace_id"]))
        if had_tail:
            result.warnings.append("incomplete_tail")

        pending_begin: dict[str, Any] | None = None
        pending_members: list[dict[str, Any]] = []
        for raw_line in lines[1:]:
            record = _parse_record(raw_line)
            record_type = record.get("record_type")
            if record_type == "transaction_begin":
                if pending_begin is not None:
                    result.warnings.append("transaction_incomplete")
                pending_begin = record
                pending_members = []
                continue
            if pending_begin is None:
                raise ReplayError("orphan_record", "record appeared outside a transaction")
            if record_type in {"node", "edge"}:
                pending_members.append(record)
                continue
            if record_type == "transaction_commit":
                self._apply_committed_transaction(result, pending_begin, pending_members, record)
                pending_begin = None
                pending_members = []
                continue
            result.warnings.append("transaction_incomplete")
            break
        if pending_begin is not None:
            result.warnings.append("transaction_incomplete")
        return result

    def _apply_committed_transaction(
        self,
        result: ReplayResult,
        begin: dict[str, Any],
        members: list[dict[str, Any]],
        commit: dict[str, Any],
    ) -> None:
        self.contracts.assert_valid("transaction_begin.schema.json", begin)
        if begin["workspace_id"] != result.workspace_id:
            raise ReplayError("workspace_mismatch", "transaction workspace mismatch")
        if begin["expected_previous_commit_hash"] != result.last_commit_hash:
            raise ReplayError("previous_commit_mismatch", "transaction expected previous mismatch")
        if begin["expected_graph_revision"] != result.graph_revision:
            raise ReplayError("graph_revision_mismatch", "transaction expected revision mismatch")
        ordered = _ordered_members(members)
        member_ids = [_primary_id(member) for member in ordered]
        if len(set(member_ids)) != len(member_ids):
            raise ReplayError("duplicate_id", "transaction contains duplicate identifiers")
        for member in ordered:
            if member.get("workspace_id") != result.workspace_id:
                raise ReplayError("workspace_mismatch", "member workspace mismatch")
            identifier = _primary_id(member)
            if identifier in result.nodes or identifier in result.edges:
                raise ReplayError("duplicate_id", "committed identifier already exists")
            expected_hash = member.get("record_hash")
            actual_hash = record_hash(member)
            if expected_hash != actual_hash:
                raise ReplayError("record_hash_mismatch", "record hash mismatch")
            self.contracts.assert_valid(_member_schema(member), member)
        try:
            validate_transaction_integrity(
                committed_nodes=result.nodes,
                committed_edges=result.edges,
                members=ordered,
                registries=self.contracts.registries,
            )
        except GraphIntegrityError as exc:
            raise ReplayError(exc.code, str(exc)) from exc
        envelope = transaction_hash_envelope(
            actor=begin["actor"],
            created_at=begin["created_at"],
            expected_graph_revision=begin["expected_graph_revision"],
            expected_previous_commit_hash=begin["expected_previous_commit_hash"],
            member_record_hashes=[member["record_hash"] for member in ordered],
            transaction_id=begin["transaction_id"],
            workspace_id=begin["workspace_id"],
        )
        expected_tx_hash = transaction_hash(envelope)
        if commit.get("workspace_id") != result.workspace_id:
            raise ReplayError("workspace_mismatch", "commit workspace mismatch")
        if commit.get("transaction_id") != begin["transaction_id"]:
            raise ReplayError("transaction_id_mismatch", "commit transaction id mismatch")
        if commit.get("committed_record_ids") != member_ids:
            raise ReplayError("committed_record_ids_mismatch", "commit member order mismatch")
        if commit.get("transaction_hash") != expected_tx_hash:
            raise ReplayError("transaction_hash_mismatch", "transaction hash mismatch")
        if commit.get("previous_commit_hash") != result.last_commit_hash:
            raise ReplayError("previous_commit_mismatch", "previous commit mismatch")
        if commit.get("graph_revision") != result.graph_revision + 1:
            raise ReplayError("graph_revision_mismatch", "graph revision mismatch")
        if commit.get("commit_hash") != commit_hash(commit):
            raise ReplayError("commit_hash_mismatch", "commit hash mismatch")
        self.contracts.assert_valid("transaction_commit.schema.json", commit)
        for member in ordered:
            identifier = _primary_id(member)
            if member["record_type"] == "node":
                result.nodes[identifier] = member
            else:
                result.edges[identifier] = member
            result.record_revisions[identifier] = int(commit["graph_revision"])
        result.graph_revision = int(commit["graph_revision"])
        result.last_commit_hash = str(commit["commit_hash"])
        result.commits.append(
            CommitInfo(
                graph_revision=int(commit["graph_revision"]),
                commit_hash=str(commit["commit_hash"]),
                transaction_hash=str(commit["transaction_hash"]),
                transaction_id=str(commit["transaction_id"]),
            )
        )

    def append_transaction(
        self,
        members: list[dict[str, Any]],
        *,
        actor: dict[str, Any],
        created_at: str,
        committed_at: str,
        principal_id: str = "local-user",
        expected_graph_revision: int | None = None,
        fail_at: str | None = None,
    ) -> dict[str, Any]:
        if not members:
            raise StorageError("transaction_empty", "transaction must contain members")
        self.authorization.require(principal_id, "graph.append")
        validate_member_authority(members, effective_principal_id=principal_id)
        lock_workspace = self.replay().workspace_id
        with WriterLock.acquire(
            self.locks_dir,
            workspace_id=lock_workspace,
            acquired_at=created_at,
        ):
            head = self.replay()
            if (
                expected_graph_revision is not None
                and expected_graph_revision != head.graph_revision
            ):
                raise StorageError(
                    "stale_graph_revision",
                    f"expected graph revision {expected_graph_revision}, "
                    f"current revision {head.graph_revision}",
                )
            prepared_members = _ordered_members([dict(member) for member in members])
            seen = set(head.nodes) | set(head.edges)
            for member in prepared_members:
                if member.get("workspace_id") != head.workspace_id:
                    raise StorageError("workspace_mismatch", "member workspace mismatch")
                identifier = _primary_id(member)
                if identifier in seen:
                    raise StorageError("duplicate_id", "duplicate committed identifier")
                seen.add(identifier)
                member["record_hash"] = record_hash(member)
                self.contracts.assert_valid(_member_schema(member), member)
            validate_transaction_integrity(
                committed_nodes=head.nodes,
                committed_edges=head.edges,
                members=prepared_members,
                registries=self.contracts.registries,
            )
            transaction_id = str(self.ids.generate("transaction"))
            commit_id = str(self.ids.generate("commit"))
            begin = {
                "record_type": "transaction_begin",
                "protocol_version": "0.2.0",
                "workspace_id": head.workspace_id,
                "transaction_id": transaction_id,
                "expected_previous_commit_hash": head.last_commit_hash,
                "expected_graph_revision": head.graph_revision,
                "actor": actor,
                "created_at": created_at,
                "extensions": {},
            }
            envelope = transaction_hash_envelope(
                actor=actor,
                created_at=created_at,
                expected_graph_revision=head.graph_revision,
                expected_previous_commit_hash=head.last_commit_hash,
                member_record_hashes=[member["record_hash"] for member in prepared_members],
                transaction_id=transaction_id,
                workspace_id=head.workspace_id,
            )
            tx_hash = transaction_hash(envelope)
            commit = {
                "record_type": "transaction_commit",
                "protocol_version": "0.2.0",
                "workspace_id": head.workspace_id,
                "transaction_id": transaction_id,
                "commit_id": commit_id,
                "committed_record_ids": [_primary_id(member) for member in prepared_members],
                "transaction_hash": tx_hash,
                "graph_revision": head.graph_revision + 1,
                "previous_commit_hash": head.last_commit_hash,
                "commit_hash": ZERO_SHA256,
                "committed_at": committed_at,
                "canonicalization_id": "guerilla-cjson-v1",
                "hash_algorithm": "sha256",
                "extensions": {},
            }
            commit["commit_hash"] = commit_hash(commit)
            self.contracts.assert_valid("transaction_begin.schema.json", begin)
            self.contracts.assert_valid("transaction_commit.schema.json", commit)
            staged = self.tmp_dir / f"{transaction_id}.jsonl"
            staged.parent.mkdir(parents=True, exist_ok=True)
            with staged.open("xb") as staged_file:
                for record in [begin, *prepared_members, commit]:
                    staged_file.write(canonical_jsonl(record))
                fsync_file(staged_file)
            fsync_directory(self.tmp_dir)
            if fail_at == "after_stage":
                raise StorageError("injected_failure", "failure after staging")
            with self.active_path.open("ab") as active:
                for record in [begin, *prepared_members]:
                    active.write(canonical_jsonl(record))
                fsync_file(active)
                if fail_at == "after_members_fsync":
                    raise StorageError("injected_failure", "failure after member fsync")
                active.write(canonical_jsonl(commit))
                fsync_file(active)
            fsync_directory(self.active_path.parent)
            staged.unlink()
            fsync_directory(self.tmp_dir)
            self._refresh_index_after_commit()
            return commit

    def _refresh_index_after_commit(self) -> None:
        try:
            from guerilla.index import SQLiteGraphIndex, mark_index_invalid

            SQLiteGraphIndex(self.root).rebuild(self.replay())
        except Exception as exc:  # pragma: no cover - defensive non-authoritative path
            mark_index_invalid(self.root, f"{type(exc).__name__}: {exc}")
