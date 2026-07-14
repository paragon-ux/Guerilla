"""Phase 4 conformance fixture runner.

The fixture runner validates corpus data with two independent JSON Schema
validators and checks canonicalization/hash vectors with local test code only.
It does not import future Guerilla runtime modules.
"""

from __future__ import annotations

import calendar
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
TIMESTAMP_RE = re.compile(
    r"^(?!0000)([0-9]{4})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])"
    r"T([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])"
    r"(?:\.([0-9]{0,8}[1-9]))?Z$"
)
SAFE_INT_MIN = -9007199254740991
SAFE_INT_MAX = 9007199254740991


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


def _contains_surrogate(value: Any) -> bool:
    if isinstance(value, str):
        return any(0xD800 <= ord(char) <= 0xDFFF for char in value)
    if isinstance(value, list):
        return any(_contains_surrogate(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_surrogate(key) or _contains_surrogate(item) for key, item in value.items()
        )
    return False


def _raw_json_path_a(raw: bytes) -> str | None:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return "invalid_utf8"

    def parse_int(token: str) -> int:
        if token == "-0":
            raise ValueError("negative_zero")
        value = int(token)
        if value < SAFE_INT_MIN or value > SAFE_INT_MAX:
            raise ValueError("json_safe_integer_exceeded")
        return value

    def parse_float(token: str) -> int:
        if "." in token:
            raise ValueError("decimal_point")
        raise ValueError("exponent_notation")

    def parse_constant(_token: str) -> int:
        raise ValueError("nan_or_infinity")

    def pairs_to_dict(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result

    try:
        value = json.loads(
            text,
            parse_int=parse_int,
            parse_float=parse_float,
            parse_constant=parse_constant,
            object_pairs_hook=pairs_to_dict,
        )
    except ValueError as error:
        message = str(error)
        for code in [
            "negative_zero",
            "json_safe_integer_exceeded",
            "decimal_point",
            "exponent_notation",
            "nan_or_infinity",
            "duplicate_key",
        ]:
            if code in message:
                return code
        if re.search(r":\s*\+", text):
            return "leading_plus"
        if re.search(r":\s*-?0[0-9]", text):
            return "invalid_leading_zero"
        return "invalid_json"
    if _contains_surrogate(value):
        return "isolated_surrogate"
    return None


def _raw_json_path_b(raw: bytes) -> str | None:
    decoder = json.JSONDecoder(
        parse_int=lambda token: token,
        parse_float=lambda token: token,
        parse_constant=lambda token: token,
        object_pairs_hook=lambda pairs: pairs,
    )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return "invalid_utf8"
    try:
        value, end = decoder.raw_decode(text)
    except json.JSONDecodeError:
        if re.search(r":\s*\+", text):
            return "leading_plus"
        if re.search(r":\s*-?0[0-9]", text):
            return "invalid_leading_zero"
        return "invalid_json"
    if text[end:].strip():
        return "invalid_json"

    def inspect(item: Any) -> str | None:
        if isinstance(item, str):
            if item in {"NaN", "Infinity", "-Infinity"}:
                return "nan_or_infinity"
            if re.fullmatch(r"-?\d+", item):
                if item == "-0":
                    return "negative_zero"
                if int(item) < SAFE_INT_MIN or int(item) > SAFE_INT_MAX:
                    return "json_safe_integer_exceeded"
            if re.fullmatch(r"-?\d+\.\d+(?:[eE][+-]?\d+)?", item):
                return "decimal_point"
            if re.fullmatch(r"-?\d+[eE][+-]?\d+", item):
                return "exponent_notation"
            if any(0xD800 <= ord(char) <= 0xDFFF for char in item):
                return "isolated_surrogate"
            return None
        if isinstance(item, list):
            if item and all(
                isinstance(pair, (list, tuple)) and len(pair) == 2 and isinstance(pair[0], str)
                for pair in item
            ):
                seen: set[str] = set()
                for key, value in item:
                    if key in seen:
                        return "duplicate_key"
                    seen.add(key)
                    nested = inspect(value)
                    if nested is not None:
                        return nested
                return None
            for value in item:
                nested = inspect(value)
                if nested is not None:
                    return nested
        return None

    return inspect(value)


def _timestamp_path_a(value: str) -> str | None:
    match = TIMESTAMP_RE.match(value)
    if match is None:
        if value.startswith("0000-"):
            return "year_zero"
        if "t" in value:
            return "lowercase_t"
        if value.endswith("z"):
            return "lowercase_z"
        if re.search(r"[+-][0-9]{2}:[0-9]{2}$", value):
            return "stored_offset"
        if re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}Z$", value):
            return "missing_seconds"
        if ".Z" in value:
            return "empty_fraction"
        if re.search(r"\.[0-9]{10,}Z$", value):
            return "fraction_too_long"
        if re.search(r"\.[0-9]*0Z$", value):
            return "fraction_trailing_zero"
        if ":60" in value:
            return "leap_second"
        return "timestamp_grammar"
    year, month, day, hour, minute, second = (int(part) for part in match.groups()[:6])
    try:
        datetime(year, month, day, hour, minute, second, tzinfo=UTC)
    except ValueError:
        if month == 2 and day == 29:
            return "invalid_leap_day"
        return "invalid_calendar_date"
    return None


def _timestamp_path_b(value: str) -> str | None:
    if re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}Z$", value):
        return "missing_seconds"
    if len(value) < 20 or value[10] != "T":
        return "lowercase_t" if "t" in value else "timestamp_grammar"
    if not value.endswith("Z"):
        if value.endswith("z"):
            return "lowercase_z"
        if re.search(r"[+-][0-9]{2}:[0-9]{2}$", value):
            return "stored_offset"
        return "timestamp_grammar"
    core = value[:-1]
    date_text, _, time_text = core.partition("T")
    if len(date_text) != 10:
        return "timestamp_grammar"
    if "." in time_text:
        time_main, fraction = time_text.split(".", 1)
        if not fraction:
            return "empty_fraction"
        if len(fraction) > 9:
            return "fraction_too_long"
        if fraction.endswith("0"):
            return "fraction_trailing_zero"
    else:
        time_main = time_text
    if len(time_main) != 8:
        return "missing_seconds"
    try:
        year = int(date_text[0:4])
        month = int(date_text[5:7])
        day = int(date_text[8:10])
        hour = int(time_main[0:2])
        minute = int(time_main[3:5])
        second = int(time_main[6:8])
    except ValueError:
        return "timestamp_grammar"
    if year == 0:
        return "year_zero"
    if second == 60:
        return "leap_second"
    if not (1 <= month <= 12 and 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return "timestamp_grammar"
    max_day = calendar.monthrange(year, month)[1]
    if not (1 <= day <= max_day):
        if month == 2 and day == 29:
            return "invalid_leap_day"
        return "invalid_calendar_date"
    return None


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
    for raw_json in numeric_forms["invalid_json_texts"]:
        raw = raw_json.encode("utf-8")
        assert _raw_json_path_a(raw) is not None, raw_json
        assert _raw_json_path_b(raw) is not None, raw_json

    timestamp_semantics = fixtures["timestamp.calendar_semantics"]
    for timestamp_value in timestamp_semantics["valid_timestamps"]:
        assert _timestamp_path_a(timestamp_value) is None
        assert _timestamp_path_b(timestamp_value) is None
    for timestamp_value, expected_reason in timestamp_semantics["invalid_timestamps"].items():
        assert _timestamp_path_a(timestamp_value) == expected_reason
        assert _timestamp_path_b(timestamp_value) == expected_reason


def test_raw_json_lexical_fixtures_use_independent_byte_validators():
    for fixture in _canonical_corpus()["fixtures"]:
        if fixture["kind"] != "raw_json_lexical":
            continue
        raw = bytes.fromhex(fixture["raw_json_hex"])
        result_a = _raw_json_path_a(raw)
        result_b = _raw_json_path_b(raw)
        assert result_a == result_b, fixture["fixture_id"]
        expected = fixture["expected_failure_reason"]
        if fixture["expected_outcome"] == "valid":
            assert result_a is None
            assert expected is None
        else:
            assert result_a == expected


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
