"""Read-only schema and registry loading for frozen Guerilla contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import jsonschema_rs
from referencing import Registry, Resource


class ContractError(ValueError):
    """Raised when contract loading or validation fails."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    path: str
    keyword: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    python_valid: bool
    rust_valid: bool
    issues: tuple[ValidationIssue, ...]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_pointer(parts: list[str]) -> str:
    if not parts:
        return "/"
    escaped = [part.replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped)


@dataclass(frozen=True, slots=True)
class ContractBundle:
    """Loaded schema/registry bundle with independent validators."""

    schemas: dict[str, dict[str, Any]]
    registries: dict[str, dict[str, Any]]

    def __post_init__(self) -> None:
        for name, schema in self.schemas.items():
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                raise ContractError("unsupported_schema_draft", f"{name} is not Draft 2020-12")
            jsonschema.Draft202012Validator.check_schema(schema)

    @property
    def _jsonschema_registry(self) -> Registry:
        resources = [
            (schema["$id"], Resource.from_contents(schema)) for schema in self.schemas.values()
        ]
        return Registry().with_resources(resources)

    @property
    def _rs_registry(self) -> jsonschema_rs.Registry:
        return jsonschema_rs.Registry([(schema["$id"], schema) for schema in self.schemas.values()])

    def schema(self, schema_name: str) -> dict[str, Any]:
        try:
            return self.schemas[schema_name]
        except KeyError as exc:
            raise ContractError("unknown_schema", f"unknown schema: {schema_name}") from exc

    def validate(self, schema_name: str, instance: Any) -> ValidationResult:
        schema = self.schema(schema_name)
        py_validator = jsonschema.Draft202012Validator(
            schema,
            registry=self._jsonschema_registry,
        )
        py_errors = sorted(py_validator.iter_errors(instance), key=lambda error: list(error.path))
        python_valid = not py_errors
        issues = tuple(
            ValidationIssue(
                code="schema_violation",
                path=_json_pointer([str(part) for part in error.path]),
                keyword=error.validator,
                message=error.message,
            )
            for error in py_errors
        )
        rs_validator = jsonschema_rs.Draft202012Validator(
            schema,
            registry=self._rs_registry,
        )
        rust_valid = rs_validator.is_valid(instance)
        return ValidationResult(
            valid=python_valid and rust_valid,
            python_valid=python_valid,
            rust_valid=rust_valid,
            issues=issues,
        )

    def assert_valid(self, schema_name: str, instance: Any) -> None:
        result = self.validate(schema_name, instance)
        if result.python_valid != result.rust_valid:
            raise ContractError(
                "validator_disagreement",
                f"validators disagree for {schema_name}",
            )
        if not result.valid:
            issue = result.issues[0] if result.issues else None
            message = issue.message if issue else f"{schema_name} failed validation"
            raise ContractError("schema_violation", message)


def load_contract_bundle(root: Path) -> ContractBundle:
    schema_dir = root / "schemas"
    registry_dir = root / "registries"
    schemas = {path.name: _load_json(path) for path in sorted(schema_dir.glob("*.schema.json"))}
    registries = {path.name: _load_json(path) for path in sorted(registry_dir.glob("*.json"))}
    if not schemas:
        raise ContractError("missing_schema", "no schemas found")
    if not registries:
        raise ContractError("missing_registry", "no registries found")
    return ContractBundle(schemas=schemas, registries=registries)
