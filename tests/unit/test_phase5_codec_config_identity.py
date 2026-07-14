from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from guerilla.codec import (
    CanonicalJsonError,
    archive_seal_hash,
    canonical_bytes,
    canonical_jsonl,
    commit_hash,
    normalize_timestamp,
    parse_raw_json,
    payload_hash,
    record_hash,
    segment_hash,
    sha256_hex,
    transaction_hash,
)
from guerilla.config import ConfigError, load_workspace_config
from guerilla.contracts import ContractError, ImmutableContractValue, load_contract_bundle
from guerilla.identity import (
    IDENTIFIER_FAMILIES,
    IdentifierError,
    IdentifierGenerator,
    parse_identifier,
    uuidv7_from_parts,
)
from guerilla.payloads import verify_payload_reference
from guerilla.protocol import validate_protocol_request

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "contracts"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_fixtures() -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        _load_json(FIXTURE_DIR / "canonicalization" / "canonical_hash_vectors.json")["fixtures"],
    )


def _valid_fixture(fixture_id: str) -> dict[str, Any]:
    fixtures = _load_json(FIXTURE_DIR / "valid" / "schema_examples.json")["fixtures"]
    return cast(
        dict[str, Any],
        next(fixture for fixture in fixtures if fixture["fixture_id"] == fixture_id)["instance"],
    )


def _mutate_mapping(mapping: Any) -> None:
    mapping["status"] = "closed"


def test_canonical_json_reproduces_gate_a_vector():
    fixture = next(item for item in _canonical_fixtures() if item["kind"] == "canonical_json")
    canonical = canonical_bytes(fixture["input"])
    assert canonical.hex() == fixture["exact_bytes_hex"]
    domain = fixture["digest_domain"].encode("ascii").decode("unicode_escape").encode()
    assert sha256_hex(domain + canonical) == fixture["expected_digest"]
    assert canonical_jsonl(fixture["input"]) == canonical + b"\n"


def test_timestamp_vectors_and_rejections():
    fixture = next(item for item in _canonical_fixtures() if item["kind"] == "timestamp")
    assert (
        normalize_timestamp(fixture["input_timestamp"]) == fixture["expected_canonical_timestamp"]
    )
    semantics = next(
        item
        for item in _canonical_fixtures()
        if item["fixture_id"] == "timestamp.calendar_semantics"
    )
    for timestamp in semantics["valid_timestamps"]:
        assert normalize_timestamp(timestamp, allow_offset=False) == timestamp
    for timestamp, reason in semantics["invalid_timestamps"].items():
        with pytest.raises(CanonicalJsonError) as exc_info:
            normalize_timestamp(timestamp, allow_offset=False)
        assert exc_info.value.code == reason


def test_raw_json_lexical_fixture_rejections():
    for fixture in _canonical_fixtures():
        if fixture["kind"] != "raw_json_lexical":
            continue
        raw = bytes.fromhex(fixture["raw_json_hex"])
        if fixture["expected_outcome"] == "valid":
            parse_raw_json(raw)
        else:
            with pytest.raises(CanonicalJsonError) as exc_info:
                parse_raw_json(raw)
            assert exc_info.value.code == fixture["expected_failure_reason"]


def test_identifier_families_and_invalid_forms():
    fixture = next(item for item in _canonical_fixtures() if item["kind"] == "identifier_families")
    aliases = {
        "logical_entity": "entity",
        "graph_segment": "segment",
        "protocol_message": "message",
    }
    for family, identifier in fixture["identifiers"].items():
        expected_family = aliases.get(family, family)
        parsed = parse_identifier(identifier, expected_family=expected_family)
        assert str(parsed) == identifier
    invalid = next(item for item in _canonical_fixtures() if item["kind"] == "identifier_invalid")
    for identifier in invalid["identifiers"]:
        with pytest.raises(IdentifierError):
            parse_identifier(identifier)


def test_uuidv7_generation_is_monotonic_within_same_millisecond():
    generator = IdentifierGenerator()
    generated = [generator.generate("node", now_ms=1_800_000_000_000) for _ in range(4)]
    uuid_texts = [identifier.uuid_text for identifier in generated]
    assert uuid_texts == sorted(uuid_texts)
    assert len({str(identifier) for identifier in generated}) == 4


def test_hash_vectors_reproduce_gate_a_digests():
    for fixture in _canonical_fixtures():
        if fixture["kind"] == "payload_hash":
            assert (
                payload_hash(bytes.fromhex(fixture["payload_bytes_hex"]))
                == fixture["expected_digest"]
            )
        elif fixture["kind"] == "hash":
            preimage_json = fixture["preimage_canonical_json"]
            expected = fixture["expected_digest"]
            if fixture["hash_name"] == "record_hash":
                record = json.loads(preimage_json)
                record["record_hash"] = "f" * 64
                assert record_hash(record) == expected
            elif fixture["hash_name"] == "transaction_hash":
                assert transaction_hash(json.loads(preimage_json)) == expected
            elif fixture["hash_name"] == "commit_hash":
                commit = json.loads(preimage_json)
                commit["commit_hash"] = "f" * 64
                assert commit_hash(commit) == expected
            elif fixture["hash_name"] == "segment_hash":
                assert segment_hash(json.loads(preimage_json)) == expected
            elif fixture["hash_name"] == "archive_seal_hash":
                seal = json.loads(preimage_json)
                seal["archive_seal_hash"] = "f" * 64
                assert archive_seal_hash(seal) == expected


def test_hash_domains_are_separated_for_same_canonical_payload():
    payload = {"a": 1}
    assert record_hash({"a": 1, "record_hash": "0" * 64}) != transaction_hash(payload)


def test_contract_loader_validates_with_two_paths_and_immutable_values():
    contracts = load_contract_bundle(REPO_ROOT)
    node = _valid_fixture("valid.node.goal")
    result = contracts.validate("node.schema.json", node)
    assert result.valid
    invalid_node = dict(node)
    invalid_node["protocol_version"] = "9.9.9"
    invalid_result = contracts.validate("node.schema.json", invalid_node)
    assert not invalid_result.valid
    assert invalid_result.python_valid == invalid_result.rust_valid

    frozen = ImmutableContractValue.from_mapping("node.schema.json", node, contracts=contracts)
    assert isinstance(frozen.data, MappingProxyType)
    assert frozen.to_builtin() == node
    with pytest.raises(TypeError):
        _mutate_mapping(frozen.data)


def test_protocol_validation_rejects_unknown_critical_extension():
    contracts = load_contract_bundle(REPO_ROOT)
    request = _valid_fixture("valid.protocol_request")
    request["extensions"] = {
        "example.unknown.critical": {
            "critical": True,
            "namespace_id": "gxe_018f1f8e-5d4b-7a10-8a20-0c9b0b23c901",
            "value": {},
        }
    }
    with pytest.raises(ContractError) as exc_info:
        validate_protocol_request(request, contracts)
    assert exc_info.value.code == "unknown_critical_extension"

    request["extensions"]["example.unknown.critical"]["critical"] = False
    validate_protocol_request(request, contracts)


def test_protocol_validation_rejects_calendar_invalid_timestamp():
    contracts = load_contract_bundle(REPO_ROOT)
    request = _valid_fixture("valid.protocol_request")
    request["sent_at"] = "2026-02-31T00:00:00Z"

    with pytest.raises(ContractError) as exc_info:
        validate_protocol_request(request, contracts)

    assert exc_info.value.code == "invalid_calendar_date"


def test_config_loads_and_fails_closed(tmp_path: Path) -> None:
    config_path = tmp_path / ".guerilla" / "config.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        """
[workspace]
id = "grw_018f1f8e-5d4b-7a10-8a20-0c9b0b23c004"

[versions]
protocol = "0.2.0"
graph_format = "guerilla-graph-jsonl-v1"

[canonical]
canonicalization_id = "guerilla-cjson-v1"
hash_algorithm = "sha256"

[storage.paths]
graph_active = ".guerilla/graph/active.jsonl"
graph_archives = ".guerilla/graph/archives"
payloads = ".guerilla/payloads/sha256"
projections = ".guerilla/projections"
snapshots = ".guerilla/snapshots"
indexes = ".guerilla/indexes"
locks = ".guerilla/locks"
logs = ".guerilla/logs"
tmp = ".guerilla/tmp"

[filesystem]
profile = "local-fsync-v1"

[payload]
default_retention_class = "metadata"
max_size_bytes = 10485760

[archive]
max_active_segment_bytes = 67108864
max_commits_per_segment = 50000

[authorization]
profile = "local-owner-v1"
owner_principal = "local-user"

[extensions]
namespaces = []
""",
        encoding="utf-8",
    )
    config = load_workspace_config(config_path)
    assert config.workspace_id.startswith("grw_")

    bad_text = config_path.read_text(encoding="utf-8").replace(
        'profile = "local-owner-v1"',
        'profile = "programmable-policy"',
    )
    config_path.write_text(bad_text, encoding="utf-8")
    with pytest.raises(ConfigError) as exc_info:
        load_workspace_config(config_path)
    assert exc_info.value.code == "unsupported_authorization_profile"


def test_payload_verification_distinguishes_missing_and_mismatch():
    payload = b"redacted fixture payload\n"
    reference = {
        "retention_class": "content_addressed",
        "payload_hash": payload_hash(payload),
    }
    assert verify_payload_reference(reference, payload).status == "verified"
    assert verify_payload_reference(reference, None).status == "missing_payload"
    assert verify_payload_reference(reference, b"other").status == "payload_hash_mismatch"


def test_no_graph_state_side_effects(tmp_path: Path) -> None:
    canonical_bytes({"a": 1})
    IdentifierGenerator().generate("node", now_ms=1_800_000_000_000)
    assert not (tmp_path / ".guerilla").exists()


def test_cross_process_canonical_hash_determinism():
    script = (
        "from guerilla.codec import record_hash;"
        "record={'record_type':'node','record_hash':'0'*64,'created_at':'2026-07-13T00:00:00Z'};"
        "print(record_hash(record))"
    )
    outputs = [
        subprocess.check_output([sys.executable, "-c", script], text=True).strip() for _ in range(2)
    ]
    assert outputs[0] == outputs[1]


@given(
    st.dictionaries(st.text(min_size=1, max_size=8), st.integers(min_value=-1000, max_value=1000))
)
def test_canonicalization_idempotence_property(value: dict[str, int]) -> None:
    assert canonical_bytes(json.loads(canonical_bytes(value))) == canonical_bytes(value)


@given(st.sampled_from(sorted(IDENTIFIER_FAMILIES)))
def test_identifier_round_trip_property(family: str) -> None:
    identifier = IdentifierGenerator().generate(family, now_ms=1_800_000_000_000)
    assert parse_identifier(str(identifier), expected_family=family) == identifier


@given(st.binary(max_size=64))
def test_payload_hash_determinism_property(payload: bytes) -> None:
    assert payload_hash(payload) == payload_hash(payload)


def test_uuidv7_from_parts_produces_variant_and_version() -> None:
    uuid_text = str(uuidv7_from_parts(1_800_000_000_000, 1, 1))
    assert uuid_text[14] == "7"
    assert uuid_text[19] in "89ab"
