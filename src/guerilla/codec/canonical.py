"""Canonical JSON and timestamp handling for `guerilla-cjson-v1`."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, NoReturn

SAFE_INT_MIN = -9007199254740991
SAFE_INT_MAX = 9007199254740991

TIMESTAMP_FIELD_NAMES = frozenset(
    {
        "created_at",
        "effective_at",
        "committed_at",
        "sent_at",
        "generated_at",
        "requested_at",
        "retry_after",
    }
)

_TIMESTAMP_RE = re.compile(
    r"^(?!0000)(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])-"
    r"(?P<day>0[1-9]|[12][0-9]|3[01])T"
    r"(?P<hour>[01][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9])"
    r"(?:\.(?P<fraction>[0-9]{1,9}))?(?P<zone>Z|[+-][0-9]{2}:[0-9]{2})$"
)


class CanonicalJsonError(ValueError):
    """Raised when input cannot be represented by `guerilla-cjson-v1`."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _reject(code: str, message: str) -> NoReturn:
    raise CanonicalJsonError(code, message)


def _parse_int(token: str) -> int:
    if token == "-0":
        _reject("negative_zero", "negative zero is not permitted")
    value = int(token)
    if value < SAFE_INT_MIN or value > SAFE_INT_MAX:
        _reject("json_safe_integer_exceeded", "integer exceeds JSON-safe bounds")
    return value


def _parse_float(token: str) -> int:
    if "." in token:
        _reject("decimal_point", "decimal JSON numbers are not permitted")
    _reject("exponent_notation", "exponent JSON numbers are not permitted")


def _parse_constant(token: str) -> int:
    _reject("nan_or_infinity", f"{token} is not permitted")


def _object_pairs(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _reject("duplicate_key", f"duplicate object key: {key}")
        result[key] = value
    return result


def _classify_json_decode_error(text: str) -> str:
    if re.search(r":\s*\+", text):
        return "leading_plus"
    if re.search(r":\s*-?0[0-9]", text):
        return "invalid_leading_zero"
    return "invalid_json"


def _ensure_json_value(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if value < SAFE_INT_MIN or value > SAFE_INT_MAX:
            _reject("json_safe_integer_exceeded", "integer exceeds JSON-safe bounds")
        return value
    if isinstance(value, float):
        _reject("float_not_permitted", "floating-point values are not permitted")
    if isinstance(value, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            _reject("isolated_surrogate", "isolated surrogate code points are invalid")
        return value
    if isinstance(value, list | tuple):
        return [_ensure_json_value(item) for item in value]
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                _reject("non_string_key", "JSON object keys must be strings")
            if any(0xD800 <= ord(char) <= 0xDFFF for char in key):
                _reject("isolated_surrogate", "isolated surrogate code points are invalid")
            if key in result:
                _reject("duplicate_key", f"duplicate object key: {key}")
            result[key] = _ensure_json_value(item)
        return result
    _reject("unsupported_value", f"unsupported JSON value: {type(value).__name__}")


def parse_raw_json(raw: bytes) -> Any:
    """Parse raw UTF-8 JSON bytes using the Guerilla lexical profile."""

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CanonicalJsonError("invalid_utf8", "input is not valid UTF-8") from exc
    if text.startswith("\ufeff"):
        _reject("bom_not_permitted", "UTF-8 byte-order marks are not permitted")
    try:
        value = json.loads(
            text,
            parse_int=_parse_int,
            parse_float=_parse_float,
            parse_constant=_parse_constant,
            object_pairs_hook=_object_pairs,
        )
    except json.JSONDecodeError as exc:
        code = _classify_json_decode_error(text)
        raise CanonicalJsonError(code, exc.msg) from exc
    return _ensure_json_value(value)


def _timezone_from_text(zone: str) -> timezone:
    if zone == "Z":
        return UTC
    sign = 1 if zone[0] == "+" else -1
    hours = int(zone[1:3])
    minutes = int(zone[4:6])
    if hours > 23 or minutes > 59:
        _reject("timestamp_offset_invalid", "timestamp offset is invalid")
    return timezone(sign * timedelta(hours=hours, minutes=minutes))


def normalize_timestamp(value: str, *, allow_offset: bool = True) -> str:
    """Normalize a contract timestamp to stored UTC `Z` form."""

    if "t" in value:
        _reject("lowercase_t", "timestamp separator must be uppercase T")
    if value.endswith("z"):
        _reject("lowercase_z", "timestamp zone must be uppercase Z")
    match = _TIMESTAMP_RE.match(value)
    if match is None:
        if value.startswith("0000-"):
            _reject("year_zero", "timestamp year 0000 is invalid")
        if ".Z" in value:
            _reject("empty_fraction", "timestamp fraction must not be empty")
        if re.search(r"\.[0-9]{10,}(?:Z|[+-][0-9]{2}:[0-9]{2})$", value):
            _reject("fraction_too_long", "timestamp fraction exceeds nine digits")
        if re.search(r"\.[0-9]*0(?:Z|[+-][0-9]{2}:[0-9]{2})$", value):
            _reject("fraction_trailing_zero", "timestamp fraction must be normalized")
        if ":60" in value:
            _reject("leap_second", "leap seconds are invalid")
        if re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(?:Z|[+-])", value):
            _reject("missing_seconds", "timestamp seconds are required")
        _reject("timestamp_grammar", "timestamp does not match canonical grammar")

    groups = match.groupdict()
    fraction = groups["fraction"] or ""
    zone = groups["zone"]
    if fraction.endswith("0") and (zone == "Z" or not allow_offset):
        _reject("fraction_trailing_zero", "timestamp fraction must be normalized")
    if zone != "Z" and not allow_offset:
        _reject("stored_offset", "stored timestamps must use UTC Z")

    year = int(groups["year"])
    month = int(groups["month"])
    day = int(groups["day"])
    hour = int(groups["hour"])
    minute = int(groups["minute"])
    second = int(groups["second"])
    microsecond = int((fraction[:6]).ljust(6, "0")) if fraction else 0
    try:
        parsed = datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
            microsecond,
            tzinfo=_timezone_from_text(zone),
        )
    except ValueError as exc:
        code = "invalid_leap_day" if month == 2 and day == 29 else "invalid_calendar_date"
        raise CanonicalJsonError(code, "timestamp calendar date is invalid") from exc

    normalized = parsed.astimezone(UTC)
    fraction_out = fraction.rstrip("0")
    base = (
        f"{normalized.year:04d}-{normalized.month:02d}-{normalized.day:02d}"
        f"T{normalized.hour:02d}:{normalized.minute:02d}:{normalized.second:02d}"
    )
    return f"{base}.{fraction_out}Z" if fraction_out else f"{base}Z"


def _normalize_semantic_value(value: Any, timestamp_fields: frozenset[str], key: str | None) -> Any:
    value = _ensure_json_value(value)
    if isinstance(value, str):
        if key in timestamp_fields:
            return normalize_timestamp(value)
        return value
    if isinstance(value, list):
        return [_normalize_semantic_value(item, timestamp_fields, None) for item in value]
    if isinstance(value, dict):
        return {
            item_key: _normalize_semantic_value(item, timestamp_fields, item_key)
            for item_key, item in value.items()
        }
    return value


def canonicalize(value: Any, *, timestamp_fields: frozenset[str] = TIMESTAMP_FIELD_NAMES) -> Any:
    """Return a JSON-compatible value normalized for canonical encoding."""

    return _normalize_semantic_value(value, timestamp_fields, None)


def canonical_bytes(
    value: Any, *, timestamp_fields: frozenset[str] = TIMESTAMP_FIELD_NAMES
) -> bytes:
    """Return canonical UTF-8 bytes without a JSONL newline terminator."""

    normalized = canonicalize(value, timestamp_fields=timestamp_fields)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_jsonl(
    value: Any, *, timestamp_fields: frozenset[str] = TIMESTAMP_FIELD_NAMES
) -> bytes:
    """Return canonical JSON Lines bytes with exactly one LF terminator."""

    return canonical_bytes(value, timestamp_fields=timestamp_fields) + b"\n"
