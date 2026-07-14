"""Workspace configuration loading for Phase 5."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from guerilla.identity import parse_identifier

SUPPORTED_PROTOCOL_VERSION = "0.2.0"
SUPPORTED_GRAPH_FORMAT_VERSION = "guerilla-graph-jsonl-v1"
SUPPORTED_CANONICALIZATION_ID = "guerilla-cjson-v1"
SUPPORTED_HASH_ALGORITHM = "sha256"
SUPPORTED_FILESYSTEM_PROFILE = "local-fsync-v1"
SUPPORTED_AUTHORIZATION_PROFILE = "local-owner-v1"


class ConfigError(ValueError):
    """Raised when workspace configuration is invalid or unsupported."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class StoragePaths:
    graph_active: str
    graph_archives: str
    payloads: str
    projections: str
    snapshots: str
    indexes: str
    locks: str
    logs: str
    tmp: str


@dataclass(frozen=True, slots=True)
class PayloadDefaults:
    retention_class: str
    max_size_bytes: int


@dataclass(frozen=True, slots=True)
class ArchiveThresholds:
    max_active_segment_bytes: int
    max_commits_per_segment: int


@dataclass(frozen=True, slots=True)
class AuthorizationProfile:
    profile: str
    owner_principal: str


@dataclass(frozen=True, slots=True)
class WorkspaceConfig:
    workspace_id: str
    protocol_version: str
    graph_format_version: str
    canonicalization_id: str
    hash_algorithm: str
    filesystem_profile: str
    storage_paths: StoragePaths
    payload_defaults: PayloadDefaults
    archive_thresholds: ArchiveThresholds
    authorization: AuthorizationProfile
    extension_namespaces: tuple[str, ...]


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    section = data.get(name)
    if not isinstance(section, dict):
        raise ConfigError("missing_config_section", f"missing config section [{name}]")
    return section


def _string(section: dict[str, Any], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError("invalid_config_value", f"{key} must be a non-empty string")
    return value


def _int(section: dict[str, Any], key: str) -> int:
    value = section.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ConfigError("invalid_config_value", f"{key} must be a non-negative integer")
    return value


def _path_string(section: dict[str, Any], key: str) -> str:
    value = _string(section, key)
    if "\x00" in value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise ConfigError("unsafe_config_path", f"{key} must be a relative safe path")
    return value.replace("\\", "/")


def load_workspace_config(path: Path) -> WorkspaceConfig:
    if not path.is_file():
        raise ConfigError("missing_config", f"workspace config not found: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError("invalid_config", "config root must be a TOML table")

    workspace = _section(data, "workspace")
    versions = _section(data, "versions")
    canonical = _section(data, "canonical")
    storage = _section(data, "storage")
    paths = _section(storage, "paths")
    filesystem = _section(data, "filesystem")
    payload = _section(data, "payload")
    archive = _section(data, "archive")
    authorization = _section(data, "authorization")
    extensions = _section(data, "extensions")

    workspace_id = _string(workspace, "id")
    parse_identifier(workspace_id, expected_family="workspace")
    namespace_values = extensions.get("namespaces", [])
    if not isinstance(namespace_values, list) or not all(
        isinstance(namespace, str) for namespace in namespace_values
    ):
        raise ConfigError("invalid_config_value", "extensions.namespaces must be a string array")

    config = WorkspaceConfig(
        workspace_id=workspace_id,
        protocol_version=_string(versions, "protocol"),
        graph_format_version=_string(versions, "graph_format"),
        canonicalization_id=_string(canonical, "canonicalization_id"),
        hash_algorithm=_string(canonical, "hash_algorithm"),
        filesystem_profile=_string(filesystem, "profile"),
        storage_paths=StoragePaths(
            graph_active=_path_string(paths, "graph_active"),
            graph_archives=_path_string(paths, "graph_archives"),
            payloads=_path_string(paths, "payloads"),
            projections=_path_string(paths, "projections"),
            snapshots=_path_string(paths, "snapshots"),
            indexes=_path_string(paths, "indexes"),
            locks=_path_string(paths, "locks"),
            logs=_path_string(paths, "logs"),
            tmp=_path_string(paths, "tmp"),
        ),
        payload_defaults=PayloadDefaults(
            retention_class=_string(payload, "default_retention_class"),
            max_size_bytes=_int(payload, "max_size_bytes"),
        ),
        archive_thresholds=ArchiveThresholds(
            max_active_segment_bytes=_int(archive, "max_active_segment_bytes"),
            max_commits_per_segment=_int(archive, "max_commits_per_segment"),
        ),
        authorization=AuthorizationProfile(
            profile=_string(authorization, "profile"),
            owner_principal=_string(authorization, "owner_principal"),
        ),
        extension_namespaces=tuple(namespace_values),
    )
    validate_mutation_capable_config(config)
    return config


def validate_mutation_capable_config(config: WorkspaceConfig) -> None:
    checks = {
        "unsupported_protocol_version": (
            config.protocol_version,
            SUPPORTED_PROTOCOL_VERSION,
            "unsupported protocol version",
        ),
        "unsupported_graph_format_version": (
            config.graph_format_version,
            SUPPORTED_GRAPH_FORMAT_VERSION,
            "unsupported graph format version",
        ),
        "unsupported_canonicalization": (
            config.canonicalization_id,
            SUPPORTED_CANONICALIZATION_ID,
            "unsupported canonicalization profile",
        ),
        "unsupported_hash_algorithm": (
            config.hash_algorithm,
            SUPPORTED_HASH_ALGORITHM,
            "unsupported hash algorithm",
        ),
        "unsupported_filesystem_profile": (
            config.filesystem_profile,
            SUPPORTED_FILESYSTEM_PROFILE,
            "unsupported filesystem profile",
        ),
        "unsupported_authorization_profile": (
            config.authorization.profile,
            SUPPORTED_AUTHORIZATION_PROFILE,
            "unsupported authorization profile",
        ),
    }
    for code, (actual, expected, message) in checks.items():
        if actual != expected:
            raise ConfigError(code, f"{message}: {actual!r}, expected {expected!r}")
    if config.payload_defaults.retention_class not in {
        "none",
        "metadata",
        "content_addressed",
        "external_reference",
    }:
        raise ConfigError("unsupported_payload_retention", "unsupported payload retention class")
    for namespace in config.extension_namespaces:
        parse_identifier(namespace, expected_family="extension_namespace")
