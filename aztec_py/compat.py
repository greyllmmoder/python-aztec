"""Compatibility fixture loading utilities for production validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import cast


@dataclass(frozen=True)
class CompatCase:
    """Single compatibility validation case."""

    case_id: str
    payload: str | bytes
    ec_percent: int
    charset: str
    decode_expected: bool
    tags: tuple[str, ...]


def _as_dict(value: object, message: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(message)
    return cast(dict[str, object], value)


def _as_str(value: object, message: str) -> str:
    if not isinstance(value, str):
        raise ValueError(message)
    return value


def _as_non_empty_str(value: object, message: str) -> str:
    text = _as_str(value, message)
    if not text:
        raise ValueError(message)
    return text


def _as_int(value: object, message: str) -> int:
    if not isinstance(value, int):
        raise ValueError(message)
    return value


def _as_bool(value: object, message: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(message)
    return value


def _as_tags(value: object, case_id: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Case '{case_id}': tags must be a list")
    tags: list[str] = []
    for tag in value:
        if not isinstance(tag, str) or not tag:
            raise ValueError(f"Case '{case_id}': each tag must be a non-empty string")
        tags.append(tag)
    return tuple(tags)


def _decode_payload(raw: object, case_id: str) -> str | bytes:
    payload_obj = _as_dict(raw, f"Case '{case_id}': payload must be an object")
    kind = _as_str(payload_obj.get("kind"), f"Case '{case_id}': payload.kind must be a string")

    if kind == "text":
        return _as_str(payload_obj.get("value"), f"Case '{case_id}': text payload.value must be a string")

    if kind == "bytes_hex":
        value = _as_str(payload_obj.get("value"), f"Case '{case_id}': bytes_hex payload.value must be a string")
        if len(value) % 2 != 0:
            raise ValueError(f"Case '{case_id}': bytes_hex payload must have even length")
        try:
            return bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError(f"Case '{case_id}': bytes_hex payload is invalid") from exc

    if kind == "bytes_repeat":
        byte_value = _as_str(payload_obj.get("byte"), f"Case '{case_id}': bytes_repeat byte must be a string")
        count = _as_int(payload_obj.get("count"), f"Case '{case_id}': bytes_repeat count must be an integer")
        if not 0 <= count <= 5000:
            raise ValueError(f"Case '{case_id}': bytes_repeat count out of range")
        try:
            unit = bytes.fromhex(byte_value)
        except ValueError as exc:
            raise ValueError(f"Case '{case_id}': bytes_repeat byte must be valid hex") from exc
        if len(unit) != 1:
            raise ValueError(f"Case '{case_id}': bytes_repeat byte must represent exactly one byte")
        return unit * count

    raise ValueError(f"Case '{case_id}': unsupported payload kind '{kind}'")


def load_compat_cases(path: str | Path) -> list[CompatCase]:
    """Load compatibility cases from JSON fixtures.

    Args:
        path: Path to JSON fixture file.

    Returns:
        Parsed and validated compatibility cases.

    Raises:
        ValueError: If fixture file contains invalid schema.
    """
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        raw_data = json.load(handle)

    root = _as_dict(raw_data, "Fixture root must be an object")
    raw_cases = root.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("Fixture root must contain a 'cases' list")

    parsed_cases: list[CompatCase] = []
    seen: set[str] = set()
    for index, raw_case in enumerate(raw_cases):
        case_obj = _as_dict(raw_case, f"Case #{index}: must be an object")

        case_id = _as_non_empty_str(case_obj.get("id"), f"Case #{index}: 'id' must be a non-empty string")
        if case_id in seen:
            raise ValueError(f"Duplicate case id '{case_id}'")
        seen.add(case_id)

        payload = _decode_payload(case_obj.get("payload"), case_id)

        ec_percent = _as_int(case_obj.get("ec_percent", 23), f"Case '{case_id}': ec_percent must be an integer")
        if not 5 <= ec_percent <= 95:
            raise ValueError(f"Case '{case_id}': ec_percent must be between 5 and 95")

        charset = _as_non_empty_str(case_obj.get("charset", "UTF-8"), f"Case '{case_id}': charset must be non-empty")
        decode_expected = _as_bool(
            case_obj.get("decode_expected", isinstance(payload, str)),
            f"Case '{case_id}': decode_expected must be a boolean",
        )
        tags = _as_tags(case_obj.get("tags", []), case_id)

        parsed_cases.append(
            CompatCase(
                case_id=case_id,
                payload=payload,
                ec_percent=ec_percent,
                charset=charset,
                decode_expected=decode_expected,
                tags=tags,
            )
        )

    return parsed_cases
