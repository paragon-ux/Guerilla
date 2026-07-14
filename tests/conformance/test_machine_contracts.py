"""Phase 3 machine-contract conformance tests.

These tests validate schemas, registries, and examples without importing future
Guerilla runtime modules.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import jsonschema
import jsonschema_rs
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_DIR = REPO_ROOT / "schemas"
REGISTRY_DIR = REPO_ROOT / "registries"

EXPECTED_SCHEMA_FILES = {
    "common.schema.json",
    "actor.schema.json",
    "authority.schema.json",
    "external_identity.schema.json",
    "payload_ref.schema.json",
    "provenance.schema.json",
    "node.schema.json",
    "edge.schema.json",
    "transaction_begin.schema.json",
    "transaction_commit.schema.json",
    "graph_header.schema.json",
    "archive_seal.schema.json",
    "state_boundary.schema.json",
    "capability.schema.json",
    "adapter_descriptor.schema.json",
    "protocol_envelope.schema.json",
    "protocol_response.schema.json",
    "error.schema.json",
    "extension_namespace.schema.json",
    "derived_projection.schema.json",
}

RELATIONSHIP_DIRECTIONS = {
    "depends_on": "prerequisite -> dependent",
    "produces": "producer -> product",
    "derives": "source -> derived",
    "causes": "cause -> effect",
    "evidences": "evidence -> supported record",
    "evaluated_by": "subject -> evaluation",
    "superseded_by": "earlier -> later",
    "resolved_by": "unresolved item -> resolution",
    "captured_by": "included source -> snapshot",
}

WS = "grw_018f1f8e-5d4b-7a10-8a20-0c9b0b23c004"
ENTITY = "gri_018f1f8e-5d4b-7a10-8a20-0c9b0b23c002"
ACTOR = "gri_018f1f8e-5d4b-7a10-8a20-0c9b0b23c001"
NODE_A = "grn_018f1f8e-5d4b-7a10-8a20-0c9b0b23c003"
NODE_B = "grn_018f1f8e-5d4b-7a10-8a20-0c9b0b23c013"
EDGE = "gre_018f1f8e-5d4b-7a10-8a20-0c9b0b23c020"
TX = "grt_018f1f8e-5d4b-7a10-8a20-0c9b0b23c005"
COMMIT = "grm_018f1f8e-5d4b-7a10-8a20-0c9b0b23c006"
SEGMENT = "gsg_018f1f8e-5d4b-7a10-8a20-0c9b0b23c007"
ADAPTER = "gra_018f1f8e-5d4b-7a10-8a20-0c9b0b23c030"
PROJECTION = "grp_018f1f8e-5d4b-7a10-8a20-0c9b0b23c040"
MSG = "gmsg_018f1f8e-5d4b-7a10-8a20-0c9b0b23c050"
MSG2 = "gmsg_018f1f8e-5d4b-7a10-8a20-0c9b0b23c051"
BOUNDARY = "gsb_018f1f8e-5d4b-7a10-8a20-0c9b0b23c060"
SYSTEM = "gxs_018f1f8e-5d4b-7a10-8a20-0c9b0b23c070"
EXT_NS = "gxe_018f1f8e-5d4b-7a10-8a20-0c9b0b23c900"
HASH = "a" * 64
ZERO_HASH = "0" * 64
TIMESTAMP = "2026-07-13T00:00:00Z"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _schemas() -> dict[str, dict[str, Any]]:
    return {path.name: _load_json(path) for path in sorted(SCHEMA_DIR.glob("*.schema.json"))}


def _registries() -> dict[str, dict[str, Any]]:
    return {path.name: _load_json(path) for path in sorted(REGISTRY_DIR.glob("*.json"))}


def _jsonschema_registry(schemas: dict[str, dict[str, Any]]) -> Registry:
    resources = [(schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()]
    return Registry().with_resources(resources)


def _rs_registry(schemas: dict[str, dict[str, Any]]) -> jsonschema_rs.Registry:
    return jsonschema_rs.Registry([(schema["$id"], schema) for schema in schemas.values()])


def _validate_both(schema_name: str, instance: Any) -> tuple[bool, bool]:
    schemas = _schemas()
    schema = schemas[schema_name]
    py_validator = jsonschema.Draft202012Validator(
        schema,
        registry=_jsonschema_registry(schemas),
    )
    py_valid = not list(py_validator.iter_errors(instance))
    rs_validator = jsonschema_rs.Draft202012Validator(
        schema,
        registry=_rs_registry(schemas),
    )
    rs_valid = rs_validator.is_valid(instance)
    return py_valid, rs_valid


def _actor() -> dict[str, Any]:
    return {"actor_id": ACTOR, "actor_kind": "human"}


def _authority() -> dict[str, Any]:
    return {"authority_type": "guerilla", "principal_id": "local-user", "profile": "local-owner-v1"}


def _payload_ref() -> dict[str, Any]:
    return {"retention_class": "none"}


def _provenance() -> dict[str, Any]:
    return {"source": "phase3-example", "source_record_ids": []}


def _node() -> dict[str, Any]:
    return {
        "record_type": "node",
        "protocol_version": "0.2.0",
        "workspace_id": WS,
        "node_id": NODE_A,
        "entity_id": ENTITY,
        "node_type": "goal",
        "created_at": TIMESTAMP,
        "actor": _actor(),
        "authority": _authority(),
        "status": "open",
        "provenance": _provenance(),
        "payload_ref": _payload_ref(),
        "metadata": {},
        "extensions": {},
        "record_hash": HASH,
    }


def _edge() -> dict[str, Any]:
    return {
        "record_type": "edge",
        "protocol_version": "0.2.0",
        "workspace_id": WS,
        "edge_id": EDGE,
        "relationship_type": "depends_on",
        "from_node_id": NODE_A,
        "to_node_id": NODE_B,
        "created_at": TIMESTAMP,
        "actor": _actor(),
        "provenance": _provenance(),
        "metadata": {},
        "extensions": {},
        "record_hash": HASH,
    }


def _state_boundary() -> dict[str, Any]:
    return {
        "state_boundary_id": BOUNDARY,
        "system_id": SYSTEM,
        "name": "fixture boundary",
        "system_of_record": True,
        "continuity_mode": "reconstructed",
        "ownership": "external_application_state",
        "permitted_operations": ["observe", "act", "reconcile"],
        "lineage_crossing": "intent_before_action",
        "conflict_behavior": "require_reconciliation",
        "extensions": {},
    }


def _capability() -> dict[str, Any]:
    return {
        "capability": "observe",
        "supported": True,
        "state_boundary_ids": [BOUNDARY],
    }


def _extension_namespace() -> dict[str, Any]:
    return cast(dict[str, Any], _registries()["extension_namespaces.json"]["entries"][0])


VALID_EXAMPLES: dict[str, Any] = {
    "common.schema.json": {},
    "actor.schema.json": _actor(),
    "authority.schema.json": _authority(),
    "external_identity.schema.json": {
        "system_id": SYSTEM,
        "state_boundary_id": BOUNDARY,
        "external_kind": "file",
        "external_id": "README.md",
        "external_revision": "abc123",
    },
    "payload_ref.schema.json": _payload_ref(),
    "provenance.schema.json": _provenance(),
    "node.schema.json": _node(),
    "edge.schema.json": _edge(),
    "transaction_begin.schema.json": {
        "record_type": "transaction_begin",
        "protocol_version": "0.2.0",
        "workspace_id": WS,
        "transaction_id": TX,
        "expected_previous_commit_hash": ZERO_HASH,
        "expected_graph_revision": 0,
        "actor": _actor(),
        "created_at": TIMESTAMP,
        "extensions": {},
    },
    "transaction_commit.schema.json": {
        "record_type": "transaction_commit",
        "protocol_version": "0.2.0",
        "workspace_id": WS,
        "transaction_id": TX,
        "commit_id": COMMIT,
        "committed_record_ids": [NODE_A, EDGE],
        "transaction_hash": HASH,
        "graph_revision": 1,
        "previous_commit_hash": ZERO_HASH,
        "commit_hash": HASH,
        "committed_at": TIMESTAMP,
        "canonicalization_id": "guerilla-cjson-v1",
        "hash_algorithm": "sha256",
        "extensions": {},
    },
    "graph_header.schema.json": {
        "record_type": "graph_header",
        "protocol_version": "0.2.0",
        "workspace_id": WS,
        "graph_format_version": "guerilla-graph-jsonl-v1",
        "canonicalization_id": "guerilla-cjson-v1",
        "hash_algorithm": "sha256",
        "created_at": TIMESTAMP,
        "authority_class": "authoritative_graph",
        "extensions": {},
    },
    "archive_seal.schema.json": {
        "record_type": "archive_seal",
        "protocol_version": "0.2.0",
        "workspace_id": WS,
        "segment_id": SEGMENT,
        "first_graph_revision": 1,
        "last_graph_revision": 1,
        "previous_segment_hash": ZERO_HASH,
        "segment_hash": HASH,
        "archive_seal_hash": HASH,
        "record_count": 3,
        "commit_count": 1,
        "created_at": TIMESTAMP,
        "canonicalization_id": "guerilla-cjson-v1",
        "hash_algorithm": "sha256",
        "extensions": {},
    },
    "state_boundary.schema.json": _state_boundary(),
    "capability.schema.json": _capability(),
    "adapter_descriptor.schema.json": {
        "adapter_id": ADAPTER,
        "system_id": SYSTEM,
        "name": "fixture adapter",
        "version": "0.2.0",
        "trust_model": "trusted_in_process_python",
        "state_boundaries": [_state_boundary()],
        "capabilities": [_capability()],
        "authentication": {"required": False, "credential_storage": "none"},
        "limitations": ["fixture only"],
        "extensions": {},
    },
    "protocol_envelope.schema.json": {
        "protocol": "glcp",
        "version": "0.2.0",
        "message_id": MSG,
        "message_type": "request",
        "operation": "graph.append",
        "sent_at": TIMESTAMP,
        "workspace_id": WS,
        "actor": _actor(),
        "correlation_id": MSG2,
        "extensions": {},
        "body": {"dry_run": True},
    },
    "protocol_response.schema.json": {
        "request_message_id": MSG,
        "status": "success",
        "graph_revision": 1,
        "commit_id": COMMIT,
        "result": {"accepted": True},
        "errors": [],
        "conflicts": [],
        "retry": "not_applicable",
        "warnings": [],
    },
    "error.schema.json": {
        "code": "schema_violation",
        "message": "fixture error",
        "retriable": "never",
        "details": {},
    },
    "extension_namespace.schema.json": _extension_namespace(),
    "derived_projection.schema.json": {
        "projection_id": PROJECTION,
        "workspace_id": WS,
        "authority_class": "derived_non_authoritative",
        "authoritative": False,
        "source_graph_revision": 1,
        "source_node_ids": [NODE_A],
        "transformation_id": "fixture.projection",
        "transformation_version": "0.2.0",
        "policy_version": "0.2.0",
        "generated_at": TIMESTAMP,
        "freshness": "graph_revision_bound",
        "information_loss": ["omits payload bytes"],
        "result_hash": HASH,
        "extensions": {},
    },
}


def test_schema_inventory_is_complete():
    assert {path.name for path in SCHEMA_DIR.glob("*.schema.json")} == EXPECTED_SCHEMA_FILES
    assert set(_registries()) == {
        "node_types.json",
        "relationship_types.json",
        "conflict_types.json",
        "capabilities.json",
        "error_codes.json",
        "extension_namespaces.json",
    }


def test_schemas_meta_validate_and_references_resolve():
    schemas = _schemas()
    for name, schema in schemas.items():
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema_rs.Draft202012Validator(schema, registry=_rs_registry(schemas))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", name
        assert schema["$id"].startswith("https://guerilla.dev/schemas/"), name


def test_valid_examples_pass_both_validators():
    for schema_name, example in VALID_EXAMPLES.items():
        assert _validate_both(schema_name, example) == (True, True), schema_name


def test_invalid_examples_fail_both_validators():
    invalid_cases: list[tuple[str, Any]] = []
    for schema_name, example in VALID_EXAMPLES.items():
        invalid = copy.deepcopy(example)
        invalid["unexpected_field"] = True
        invalid_cases.append((schema_name, invalid))

    bad_node = copy.deepcopy(VALID_EXAMPLES["node.schema.json"])
    bad_node["node_id"] = "grn_018f1f8e-5d4b-4a10-8a20-0c9b0b23c003"
    invalid_cases.append(("node.schema.json", bad_node))

    bad_time = copy.deepcopy(VALID_EXAMPLES["node.schema.json"])
    bad_time["created_at"] = "2026-07-13T00:00:60Z"
    invalid_cases.append(("node.schema.json", bad_time))

    bad_number = copy.deepcopy(VALID_EXAMPLES["node.schema.json"])
    bad_number["metadata"] = {"too_large": 9007199254740992}
    invalid_cases.append(("node.schema.json", bad_number))

    bad_authority = copy.deepcopy(VALID_EXAMPLES["authority.schema.json"])
    bad_authority["profile"] = "programmable-policy"
    invalid_cases.append(("authority.schema.json", bad_authority))

    bad_projection = copy.deepcopy(VALID_EXAMPLES["derived_projection.schema.json"])
    bad_projection["authoritative"] = True
    invalid_cases.append(("derived_projection.schema.json", bad_projection))

    for schema_name, example in invalid_cases:
        assert _validate_both(schema_name, example) == (False, False), schema_name


def test_registries_synchronize_with_schema_enums():
    common = _schemas()["common.schema.json"]["$defs"]
    registries = _registries()
    assert common["coreNodeType"]["enum"] == [
        entry["value"] for entry in registries["node_types.json"]["entries"]
    ]
    assert common["coreRelationshipType"]["enum"] == [
        entry["value"] for entry in registries["relationship_types.json"]["entries"]
    ]
    assert common["conflictType"]["enum"] == [
        entry["value"] for entry in registries["conflict_types.json"]["entries"]
    ]
    assert common["capabilityValue"]["enum"] == [
        entry["value"] for entry in registries["capabilities.json"]["entries"]
    ]
    assert common["errorCode"]["enum"] == [
        entry["value"] for entry in registries["error_codes.json"]["entries"]
    ]


def test_relationship_registry_preserves_phase2_directions():
    relationships = {
        entry["value"]: entry for entry in _registries()["relationship_types.json"]["entries"]
    }
    assert set(relationships) == set(RELATIONSHIP_DIRECTIONS)
    for relationship, direction in RELATIONSHIP_DIRECTIONS.items():
        entry = relationships[relationship]
        assert entry["direction"] == direction
        assert entry["direct_edge_must_remain_acyclic"] is True


def test_uuidv7_timestamp_number_and_authority_rules_are_machine_checkable():
    good_node = copy.deepcopy(VALID_EXAMPLES["node.schema.json"])
    assert _validate_both("node.schema.json", good_node) == (True, True)

    for bad_id in [
        "grn_018f1f8e-5d4b-4a10-8a20-0c9b0b23c003",
        "grn_018f1f8e-5d4b-7a10-ca20-0c9b0b23c003",
        "GRN_018F1F8E-5D4B-7A10-8A20-0C9B0B23C003",
    ]:
        candidate = copy.deepcopy(good_node)
        candidate["node_id"] = bad_id
        assert _validate_both("node.schema.json", candidate) == (False, False)

    for bad_timestamp in [
        "2026-07-13T00:00:00-04:00",
        "2026-07-13t00:00:00z",
        "2026-07-13T00:00:00.000Z",
    ]:
        candidate = copy.deepcopy(good_node)
        candidate["created_at"] = bad_timestamp
        assert _validate_both("node.schema.json", candidate) == (False, False)

    actor_escalation = copy.deepcopy(VALID_EXAMPLES["protocol_envelope.schema.json"])
    actor_escalation["actor"]["authorized_operations"] = ["graph.append"]
    assert _validate_both("protocol_envelope.schema.json", actor_escalation) == (False, False)


def test_extension_namespace_registry_and_extension_objects_are_validated():
    namespace = _extension_namespace()
    assert _validate_both("extension_namespace.schema.json", namespace) == (True, True)

    node_with_optional_extension = copy.deepcopy(VALID_EXAMPLES["node.schema.json"])
    node_with_optional_extension["extensions"] = {
        "dev.guerilla.core-fixtures.note": {
            "critical": False,
            "namespace_id": EXT_NS,
            "value": {"note": "optional fixture extension"},
        }
    }
    assert _validate_both("node.schema.json", node_with_optional_extension) == (True, True)

    node_with_bad_extension = copy.deepcopy(node_with_optional_extension)
    node_with_bad_extension["extensions"]["not_namespaced"] = {
        "critical": False,
        "namespace_id": EXT_NS,
        "value": {},
    }
    assert _validate_both("node.schema.json", node_with_bad_extension) == (False, False)
