"""Immutable values validated against frozen contract schemas."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from guerilla.contracts.loader import ContractBundle


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return copy.deepcopy(value)


def _thaw(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return copy.deepcopy(value)


@dataclass(frozen=True, slots=True)
class ImmutableContractValue:
    """Frozen data object whose shape has been validated by a schema."""

    schema_name: str
    _data: Any

    @classmethod
    def from_mapping(
        cls,
        schema_name: str,
        data: dict[str, Any],
        *,
        contracts: ContractBundle,
    ) -> ImmutableContractValue:
        contracts.assert_valid(schema_name, data)
        return cls(schema_name=schema_name, _data=_freeze(data))

    @property
    def data(self) -> Any:
        return self._data

    def to_builtin(self) -> Any:
        return _thaw(self._data)
