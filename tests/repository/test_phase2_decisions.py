"""Decision-document checks for Phase 2.

These tests verify architecture-decision coverage and terminology/scope
documentation only. They do not validate or implement runtime behavior.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

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

REQUIRED_RELATIONSHIP_TYPES = [
    "`depends_on`",
    "`produces`",
    "`derives`",
    "`causes`",
    "`evidences`",
    "`evaluated_by`",
    "`superseded_by`",
    "`resolved_by`",
    "`captured_by`",
]


def test_architecture_decisions_are_frozen_and_complete():
    content = (REPO_ROOT / "docs" / "ARCHITECTURE_DECISIONS.md").read_text(encoding="utf-8")
    assert "**Status:** FROZEN -- Phase 2 complete" in content
    assert "PLACEHOLDER" not in content
    missing = sorted(
        decision_id for decision_id in REQUIRED_DECISION_IDS if decision_id not in content
    )
    assert not missing, f"Missing architecture decisions: {missing}"
    assert "No open Phase 2 decision remains" in content


def test_glossary_contains_required_terms_and_types():
    content = (REPO_ROOT / "docs" / "GLOSSARY.md").read_text(encoding="utf-8")
    assert "**Status:** FROZEN -- Phase 2 complete" in content
    assert "PLACEHOLDER" not in content
    for term in REQUIRED_GLOSSARY_TERMS:
        assert f"| {term} |" in content, f"Missing glossary term: {term}"
    for node_type in REQUIRED_NODE_TYPES:
        assert f"| {node_type} |" in content, f"Missing node type: {node_type}"
    for relationship_type in REQUIRED_RELATIONSHIP_TYPES:
        assert relationship_type in content, f"Missing relationship type: {relationship_type}"


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


def test_phase2_did_not_create_machine_contracts():
    schema_files = list((REPO_ROOT / "schemas").glob("*.schema.json"))
    registry_files = list((REPO_ROOT / "registries").glob("*.json"))
    assert not schema_files, (
        f"Phase 2 must not create schemas: {[path.name for path in schema_files]}"
    )
    assert not registry_files, (
        f"Phase 2 must not create registries: {[path.name for path in registry_files]}"
    )
