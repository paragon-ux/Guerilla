"""UUIDv7-prefixed Guerilla identifier primitives."""

from __future__ import annotations

import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Final

UUIDV7_RE: Final[re.Pattern[str]] = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)

IDENTIFIER_FAMILIES: Final[dict[str, str]] = {
    "workspace": "grw",
    "entity": "gri",
    "node": "grn",
    "edge": "gre",
    "transaction": "grt",
    "commit": "grm",
    "segment": "gsg",
    "snapshot": "grs",
    "adapter": "gra",
    "projection": "grp",
    "message": "gmsg",
    "state_boundary": "gsb",
    "external_system": "gxs",
    "extension_namespace": "gxe",
}

PREFIX_TO_FAMILY: Final[dict[str, str]] = {
    prefix: family for family, prefix in IDENTIFIER_FAMILIES.items()
}


class IdentifierError(ValueError):
    """Raised when an identifier violates the frozen UUIDv7 profile."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class GuerillaIdentifier:
    """Opaque parsed Guerilla identifier."""

    family: str
    prefix: str
    uuid_text: str

    def __str__(self) -> str:
        return f"{self.prefix}_{self.uuid_text}"


def _family_prefix(family: str) -> str:
    try:
        return IDENTIFIER_FAMILIES[family]
    except KeyError as exc:
        raise IdentifierError(
            "unsupported_family", f"unsupported identifier family: {family}"
        ) from exc


def validate_uuidv7(uuid_text: str) -> None:
    if not UUIDV7_RE.fullmatch(uuid_text):
        raise IdentifierError("invalid_uuidv7", "UUID text is not lowercase RFC 4122 UUIDv7")


def parse_identifier(text: str, *, expected_family: str | None = None) -> GuerillaIdentifier:
    prefix, separator, uuid_text = text.partition("_")
    if not separator:
        raise IdentifierError("missing_prefix", "identifier must include a registered prefix")
    family = PREFIX_TO_FAMILY.get(prefix)
    if family is None:
        raise IdentifierError("unsupported_family", f"unsupported identifier prefix: {prefix}")
    if expected_family is not None and family != expected_family:
        raise IdentifierError(
            "wrong_identifier_family", f"expected {expected_family}, got {family}"
        )
    validate_uuidv7(uuid_text)
    return GuerillaIdentifier(family=family, prefix=prefix, uuid_text=uuid_text)


def validate_identifier(text: str, *, expected_family: str | None = None) -> bool:
    try:
        parse_identifier(text, expected_family=expected_family)
    except IdentifierError:
        return False
    return True


def uuidv7_from_parts(unix_ms: int, rand_a: int, rand_b: int) -> uuid.UUID:
    if not (0 <= unix_ms < 1 << 48):
        raise IdentifierError("timestamp_out_of_range", "UUIDv7 millisecond timestamp out of range")
    if not (0 <= rand_a < 1 << 12):
        raise IdentifierError("sequence_out_of_range", "UUIDv7 rand_a out of range")
    if not (0 <= rand_b < 1 << 62):
        raise IdentifierError("random_out_of_range", "UUIDv7 rand_b out of range")
    value = unix_ms << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return uuid.UUID(int=value)


class IdentifierGenerator:
    """Generate UUIDv7-prefixed identifiers with same-millisecond monotonic rand_a."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_ms = -1
        self._sequence = -1

    def generate(
        self,
        family: str,
        *,
        now_ms: int | None = None,
        random_b: int | None = None,
    ) -> GuerillaIdentifier:
        prefix = _family_prefix(family)
        with self._lock:
            current_ms = int(time.time_ns() // 1_000_000) if now_ms is None else now_ms
            if current_ms < self._last_ms:
                current_ms = self._last_ms
            if current_ms == self._last_ms:
                self._sequence = (self._sequence + 1) & 0xFFF
                if self._sequence == 0:
                    current_ms += 1
            else:
                self._sequence = secrets.randbits(12)
            self._last_ms = current_ms
            rand_a = self._sequence
        rand_b_value = secrets.randbits(62) if random_b is None else random_b
        uuid_text = str(uuidv7_from_parts(current_ms, rand_a, rand_b_value))
        return GuerillaIdentifier(family=family, prefix=prefix, uuid_text=uuid_text)

    def generate_unique(
        self,
        family: str,
        existing: set[str],
        *,
        max_attempts: int = 32,
        now_ms: int | None = None,
    ) -> GuerillaIdentifier:
        for _ in range(max_attempts):
            identifier = self.generate(family, now_ms=now_ms)
            if str(identifier) not in existing:
                return identifier
        raise IdentifierError("identity_collision", "generated identifier collided repeatedly")
