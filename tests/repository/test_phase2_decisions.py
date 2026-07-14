"""Semantic checks for frozen Phase 2 decisions.

These tests validate decision content and published decision vectors only. They
do not import or exercise future Guerilla runtime modules.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DECISION_VECTOR_DIR = REPO_ROOT / "docs" / "decision_vectors"

REQUIRED_DECISION_IDS = {
    "AD-001",
    "AD-002",
    "AD-003",
    "AD-004",
    "AD-005",
    "AD-006",
    "AD-007",
    "AD-008",
    "AD-009",
    "AD-010",
    "AD-011",
    "AD-012",
    "AD-013",
    "AD-014",
}

REQUIRED_RELATIONSHIP_DIRECTIONS = {
    "depends_on": "prerequisite",
    "produces": "producer",
    "derives": "source",
    "causes": "cause",
    "evidences": "evidence",
    "evaluated_by": "subject",
    "superseded_by": "earlier",
    "resolved_by": "unresolved",
    "captured_by": "included",
}

REQUIRED_GLOSSARY_TERMS = [
    "Node",
    "Edge",
    "Lineage",
    "Continuity",
    "Authoritative graph",
    "Projection / View",
    "Adapter",
    "External system",
    "System of record",
    "Artifact",
    "Actor",
    "Revision",
    "Event",
    "Snapshot",
    "Manifest",
    "Status",
    "Conflict",
    "Provenance",
    "Relationship type",
    "State boundary",
]

REQUIRED_NODE_TYPES = [
    "Goal",
    "Artifact",
    "Operation",
    "Event",
    "Evaluation",
    "Decision",
    "Conflict",
    "Snapshot",
]


def _load_vector(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((DECISION_VECTOR_DIR / name).read_text(encoding="utf-8")),
    )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _normalize_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value)
    normalized = parsed.astimezone(UTC)
    if normalized.microsecond == 0:
        return normalized.strftime("%Y-%m-%dT%H:%M:%SZ")
    fraction = f"{normalized.microsecond:06d}".rstrip("0")
    return normalized.strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction}Z"


def test_architecture_decisions_are_frozen_and_complete():
    content = (REPO_ROOT / "docs" / "ARCHITECTURE_DECISIONS.md").read_text(encoding="utf-8")
    assert "**Status:** FROZEN -- Phase 2 complete" in content
    assert "PLACEHOLDER" not in content
    missing = sorted(
        decision_id for decision_id in REQUIRED_DECISION_IDS if decision_id not in content
    )
    assert not missing, f"Missing architecture decisions: {missing}"
    assert "No open Phase 2 decision remains" in content
    assert "docs/decision_vectors/" in content


def test_relationship_directions_match_normative_model():
    glossary = (REPO_ROOT / "docs" / "GLOSSARY.md").read_text(encoding="utf-8")
    decisions = (REPO_ROOT / "docs" / "ARCHITECTURE_DECISIONS.md").read_text(encoding="utf-8")
    concept = (REPO_ROOT / "docs" / "architecture" / "GUERILLA_CONCEPT_PAPER.md").read_text(
        encoding="utf-8"
    )
    implementation = (
        REPO_ROOT / "docs" / "architecture" / "GUERILLA_IMPLEMENTATION_SPEC.md"
    ).read_text(encoding="utf-8")
    for relationship, direction_start in REQUIRED_RELATIONSHIP_DIRECTIONS.items():
        assert f"`{relationship}`" in glossary
        assert f"`{relationship}`" in decisions
        assert f"`{relationship}`" in concept
        assert f"`{relationship}`" in implementation
        glossary_line = next(
            line for line in glossary.splitlines() if line.startswith(f"| `{relationship}` |")
        )
        assert direction_start in glossary_line.lower(), glossary_line


def test_canonical_json_decision_is_semantic_and_vectorized():
    content = (REPO_ROOT / "docs" / "ARCHITECTURE_DECISIONS.md").read_text(encoding="utf-8")
    for required_phrase in [
        "Duplicate object member names are invalid",
        "Unicode scalar values",
        "isolated surrogate code points are invalid",
        "The solidus (`/`) is not escaped",
        "lowercase six-byte `\\u00xx`",
        "leap seconds (`:60`) are invalid",
        "-9007199254740991",
        "9007199254740991",
        "Hash input is the canonical JSON object bytes without the stored JSONL LF terminator",
    ]:
        assert required_phrase in content

    vector = _load_vector("canonical_json.json")["vectors"][0]
    canonical = _canonical_json_bytes(vector["input"])
    assert canonical.hex() == vector["expected_canonical_hex"]
    prefix = vector["digest_preimage_prefix"].encode("ascii").decode("unicode_escape").encode()
    assert hashlib.sha256(prefix + canonical).hexdigest() == vector["expected_vector_digest"]

    timestamp_vector = _load_vector("canonical_json.json")["vectors"][1]
    assert (
        _normalize_timestamp(timestamp_vector["input_timestamp"])
        == timestamp_vector["expected_canonical_timestamp"]
    )


def test_identifier_decision_validates_uuidv7_prefixes_and_migration_policy():
    content = (REPO_ROOT / "docs" / "ARCHITECTURE_DECISIONS.md").read_text(encoding="utf-8")
    for required_phrase in [
        "The UUID version nibble MUST be `7`",
        "represented by lowercase `8`, `9`, `a`, or `b`",
        "Legacy Guerilla identifiers from unsupported families MUST NOT be accepted",
        "Migrating legacy Guerilla records creates new UUIDv7-prefixed records",
        "Graph segment",
    ]:
        assert required_phrase in content

    vector = _load_vector("identifiers.json")
    pattern = re.compile(vector["uuidv7_regex"])
    prefixes = vector["prefixes"]
    assert prefixes["node"] == "grn_"
    assert prefixes["graph_segment"] == "gsg_"
    for valid_case in vector["valid"]:
        assert pattern.match(valid_case["id"]), valid_case
        assert valid_case["id"].startswith(prefixes[valid_case["family"]])
    for invalid_case in vector["invalid"]:
        assert not pattern.match(invalid_case["id"]), invalid_case
    assert vector["collision_policy"]["submitted_duplicate"] == "duplicate_id"
    assert vector["collision_policy"]["generated_collision"] == "regenerate_before_validation"


def test_hash_decision_preimages_recalculate_exact_digests():
    content = (REPO_ROOT / "docs" / "ARCHITECTURE_DECISIONS.md").read_text(encoding="utf-8")
    for required_phrase in [
        "exactly 64 lowercase hexadecimal characters",
        "genesis previous-commit hash is exactly 64 zero characters",
        "transaction-hash envelope covers transaction metadata",
        "final commit record covers commit metadata",
        "archive_seal_hash",
        "Domain separators are ASCII strings ending in exactly one LF byte",
    ]:
        assert required_phrase in content

    vectors = _load_vector("hashes.json")["vectors"]
    for name, vector in vectors.items():
        prefix = vector["domain"].encode("ascii").decode("unicode_escape").encode()
        preimage = prefix + vector["canonical_json"].encode("utf-8")
        digest = hashlib.sha256(preimage).hexdigest()
        assert digest == vector["expected_digest"], name


def test_transaction_ordering_decision_is_not_presence_only():
    vector = _load_vector("transaction_ordering.json")
    rank = {family: index for index, family in enumerate(vector["family_rank"])}
    ordered = sorted(
        vector["input_order"],
        key=lambda item: (rank[item["record_type"]], item["id"]),
    )
    assert [item["id"] for item in ordered] == vector["expected_order"]
    assert vector["duplicate_policy"] == "duplicate_id"
    assert (
        vector["same_transaction_endpoint_policy"]
        == "endpoints_may_reference_node_members_in_same_transaction"
    )
    assert "registered_extension_families" in vector["extension_family_policy"]


def test_durability_decision_has_complete_recovery_classification():
    vector = _load_vector("durability.json")
    assert vector["final_commit_record_is_boundary"] is True
    assert "active_segment_after_final_commit_record" in vector["required_fsyncs"]
    assert "active_segment_directory_after_final_commit_record" in vector["required_fsyncs"]
    required_classifications = {
        "no_graph_mutation",
        "stale_lock_no_staged_mutation",
        "incomplete_staged_transaction",
        "staged_but_uncommitted",
        "incomplete_active_tail",
        "prepared_without_commit",
        "torn_commit_record",
        "commit_uncertain",
        "committed_directory_uncertain",
        "committed_with_leftover_lock",
        "archive_seal_incomplete",
    }
    assert set(vector["interruption_classifications"]) == required_classifications


def test_local_authorization_profile_is_mandatory_and_not_programmable_policy_engine():
    content = (REPO_ROOT / "docs" / "ARCHITECTURE_DECISIONS.md").read_text(encoding="utf-8")
    assert "The fixed profile id is `local-owner-v1`; it is mandatory" in content
    assert "Actor fields are lineage attribution only and do not grant authority" in content
    assert "A general programmable policy engine is deferred" in content
    assert (
        "Payload content, adapter descriptors, client actor fields, and extension metadata"
        in content
    )


def test_glossary_contains_required_terms_and_types():
    content = (REPO_ROOT / "docs" / "GLOSSARY.md").read_text(encoding="utf-8")
    assert "**Status:** FROZEN -- Phase 2 complete" in content
    assert "PLACEHOLDER" not in content
    for term in REQUIRED_GLOSSARY_TERMS:
        assert f"| {term} |" in content, f"Missing glossary term: {term}"
    for node_type in REQUIRED_NODE_TYPES:
        assert f"| {node_type} |" in content, f"Missing node type: {node_type}"


def test_mvp_scope_contains_acceptance_criteria_and_exclusions():
    content = (REPO_ROOT / "docs" / "MVP_SCOPE.md").read_text(encoding="utf-8")
    assert "**Status:** FROZEN -- Phase 2 complete" in content
    assert "PLACEHOLDER" not in content
    for number in range(1, 16):
        assert f"| {number} |" in content, f"Missing MVP acceptance criterion {number}"
    for excluded in [
        "remote graph service",
        "multiple concurrent writers",
        "adapter process sandboxing",
        "cross-workspace federation",
        "real external adapters before synthetic adapter conformance passes",
    ]:
        assert excluded in content
