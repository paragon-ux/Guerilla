"""Phase 4 conformance fixture runner.

The fixture runner validates corpus data with two independent JSON Schema
validators and checks canonicalization/hash vectors with local test code only.
It does not import future Guerilla runtime modules.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import jsonschema
import jsonschema_rs
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_DIR = REPO_ROOT / "schemas"
REGISTRY_DIR = REPO_ROOT / "registries"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "contracts"

REQUIRED_FIXTURE_FIELDS = {
    "fixture_id",
    "contract_version",
    "governing_decision",
    "expected_outcome",
    "expected_failure_reason",
}

UUIDV7_WITH_PREFIX = re.compile(
    r"^[a-z0-9]+_[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


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


def _valid_corpus() -> dict[str, Any]:
    return cast(dict[str, Any], _load_json(FIXTURE_DIR / "valid" / "schema_examples.json"))


def _invalid_corpus() -> dict[str, Any]:
    return cast(dict[str, Any], _load_json(FIXTURE_DIR / "invalid" / "schema_examples.json"))


def _compatibility_corpus() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        _load_json(FIXTURE_DIR / "compatibility" / "compatibility_cases.json"),
    )


def _canonical_corpus() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        _load_json(FIXTURE_DIR / "canonicalization" / "canonical_hash_vectors.json"),
    )


def _base_fixtures() -> dict[str, dict[str, Any]]:
    return {fixture["fixture_id"]: fixture for fixture in _valid_corpus()["fixtures"]}


def _pointer_parts(path: str) -> list[str]:
    assert path.startswith("/"), path
    return [part.replace("~1", "/").replace("~0", "~") for part in path.split("/")[1:]]


def _apply_mutation(instance: Any, mutation: dict[str, Any]) -> Any:
    result = copy.deepcopy(instance)
    parts = _pointer_parts(mutation["path"])
    target = result
    for part in parts[:-1]:
        target = target[part]
    key = parts[-1]
    if mutation["op"] in {"set", "add"}:
        target[key] = mutation["value"]
    elif mutation["op"] == "remove":
        del target[key]
    else:
        raise AssertionError(f"Unsupported mutation op: {mutation['op']}")
    return result


def _materialize(fixture: dict[str, Any]) -> Any:
    if "instance" in fixture:
        return copy.deepcopy(fixture["instance"])
    base = copy.deepcopy(_base_fixtures()[fixture["base_fixture_id"]]["instance"])
    mutations = fixture["mutations"] if "mutations" in fixture else [fixture["mutation"]]
    for mutation in mutations:
        base = _apply_mutation(base, mutation)
    return base


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


def _semantic_valid(fixture: dict[str, Any], instance: Any) -> bool:
    check = fixture.get("semantic_check")
    if check == "edge_not_self_loop":
        return bool(instance["from_node_id"] != instance["to_node_id"])
    if check == "extension_invariants_do_not_redefine_core":
        return bool(all("redefine core" not in item.lower() for item in instance["invariants"]))

    behavior = fixture.get("compatibility_behavior")
    if behavior == "unknown_optional_extension_ignored_with_warning":
        return bool(all(not value["critical"] for value in instance["extensions"].values()))
    if behavior == "reject_if_critical":
        known_namespaces = {
            entry["namespace_id"] for entry in _registries()["extension_namespaces.json"]["entries"]
        }
        return bool(
            all(
                (not value["critical"]) or value["namespace_id"] in known_namespaces
                for value in instance["extensions"].values()
            )
        )
    return True


def _assert_fixture_shape(fixture: dict[str, Any]) -> None:
    missing = REQUIRED_FIXTURE_FIELDS - set(fixture)
    assert not missing, f"{fixture.get('fixture_id', '<unknown>')} missing {missing}"
    assert fixture["contract_version"] == "0.2.0"
    assert fixture["governing_decision"].startswith("AD-")
    assert fixture["expected_outcome"] in {"valid", "invalid"}
    if fixture["expected_outcome"] == "valid":
        assert fixture["expected_failure_reason"] is None
    else:
        assert isinstance(fixture["expected_failure_reason"], str)


def test_every_fixture_declares_outcome_reason_and_governing_decision():
    corpora = [
        _valid_corpus(),
        _invalid_corpus(),
        _compatibility_corpus(),
        _canonical_corpus(),
    ]
    for corpus in corpora:
        assert corpus["contract_version"] == "0.2.0"
        for fixture in corpus["fixtures"]:
            _assert_fixture_shape(fixture)


def test_valid_schema_fixtures_cover_every_schema_and_pass_both_validators():
    fixtures = _valid_corpus()["fixtures"]
    assert {fixture["schema"] for fixture in fixtures} == {
        path.name for path in SCHEMA_DIR.glob("*.schema.json")
    }
    for fixture in fixtures:
        instance = _materialize(fixture)
        results = _validate_both(fixture["schema"], instance)
        assert results == (True, True), fixture["fixture_id"]


def test_invalid_schema_fixtures_cover_every_schema_and_fail_deterministically():
    fixtures = _invalid_corpus()["fixtures"]
    assert {fixture["schema"] for fixture in fixtures} == {
        path.name for path in SCHEMA_DIR.glob("*.schema.json")
    }
    for fixture in fixtures:
        instance = _materialize(fixture)
        py_valid, rs_valid = _validate_both(fixture["schema"], instance)
        assert py_valid == rs_valid, fixture["fixture_id"]
        combined_valid = py_valid and _semantic_valid(fixture, instance)
        assert combined_valid is False, fixture["fixture_id"]


def test_compatibility_fixtures_demonstrate_downgrade_behavior():
    for fixture in _compatibility_corpus()["fixtures"]:
        instance = _materialize(fixture)
        py_valid, rs_valid = _validate_both(fixture["schema"], instance)
        assert py_valid == rs_valid, fixture["fixture_id"]
        combined_valid = py_valid and _semantic_valid(fixture, instance)
        assert combined_valid == (fixture["expected_outcome"] == "valid"), fixture["fixture_id"]


def test_canonicalization_vectors_have_exact_bytes_and_digests():
    for fixture in _canonical_corpus()["fixtures"]:
        if fixture["kind"] != "canonical_json":
            continue
        canonical = _canonical_json_bytes(fixture["input"])
        assert canonical.hex() == fixture["exact_bytes_hex"]
        domain = fixture["digest_domain"].encode("ascii").decode("unicode_escape").encode()
        assert hashlib.sha256(domain + canonical).hexdigest() == fixture["expected_digest"]


def test_timestamp_and_numeric_canonicalization_fixtures_are_deterministic():
    fixtures = {fixture["fixture_id"]: fixture for fixture in _canonical_corpus()["fixtures"]}
    timestamp = fixtures["canon.timestamp_offset_normalized"]
    assert (
        _normalize_timestamp(timestamp["input_timestamp"])
        == timestamp["expected_canonical_timestamp"]
    )

    integer_bounds = fixtures["canon.integer_bounds_valid"]
    for value in integer_bounds["valid_values"]:
        assert isinstance(value, int)
        assert -9007199254740991 <= value <= 9007199254740991

    numeric_forms = fixtures["canon.numeric_forms_rejected"]
    prohibited = re.compile(r":(?:\+|-0(?:[,}])|0[0-9]|[0-9]+\.[0-9]+|[0-9]+e[0-9]+|NaN|Infinity)")
    for raw_json in numeric_forms["invalid_json_texts"]:
        assert prohibited.search(raw_json), raw_json


def test_identifier_family_fixtures_cover_every_prefix_and_reject_invalid_forms():
    fixtures = {fixture["fixture_id"]: fixture for fixture in _canonical_corpus()["fixtures"]}
    valid = fixtures["ids.every_family_valid"]
    assert set(valid["identifiers"]) == set(
        _load_json(REPO_ROOT / "docs" / "decision_vectors" / "identifiers.json")["prefixes"]
    )
    for identifier in valid["identifiers"].values():
        assert UUIDV7_WITH_PREFIX.match(identifier), identifier

    invalid = fixtures["ids.unsupported_families_rejected"]
    for identifier in invalid["identifiers"]:
        assert not UUIDV7_WITH_PREFIX.match(identifier), identifier


def test_hash_vectors_reproduce_preimages_and_digests():
    for fixture in _canonical_corpus()["fixtures"]:
        if fixture["kind"] == "hash":
            domain = fixture["domain"].encode("ascii").decode("unicode_escape").encode()
            preimage = domain + fixture["preimage_canonical_json"].encode("utf-8")
            assert hashlib.sha256(preimage).hexdigest() == fixture["expected_digest"]
        elif fixture["kind"] == "payload_hash":
            payload = bytes.fromhex(fixture["payload_bytes_hex"])
            assert hashlib.sha256(payload).hexdigest() == fixture["expected_digest"]


def test_relationship_direction_fixture_matches_registry():
    fixture = next(
        item
        for item in _canonical_corpus()["fixtures"]
        if item["fixture_id"] == "relationship.directions"
    )
    registry = {
        entry["value"]: entry["direction"]
        for entry in _registries()["relationship_types.json"]["entries"]
    }
    assert fixture["directions"] == registry
