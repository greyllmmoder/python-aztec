"""GS1 payload helpers for Aztec integration workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


GROUP_SEPARATOR = "\x1d"


@dataclass(frozen=True)
class GS1Element:
    """Single GS1 element string component.

    Attributes:
        ai: Application Identifier digits (2 to 4 characters).
        data: Field value for this AI.
        variable_length: If true, inserts a group separator when another element follows.
    """

    ai: str
    data: str
    variable_length: bool = False


def _validate_element(element: GS1Element) -> None:
    if not element.ai or not element.ai.isdigit():
        raise ValueError(f"Invalid AI '{element.ai}': AI must contain digits only")
    if not 2 <= len(element.ai) <= 4:
        raise ValueError(f"Invalid AI '{element.ai}': AI length must be between 2 and 4")
    if not element.data:
        raise ValueError(f"Invalid value for AI '{element.ai}': data must not be empty")
    if GROUP_SEPARATOR in element.ai or GROUP_SEPARATOR in element.data:
        raise ValueError("Element values must not include raw group separator characters")


def build_gs1_payload(elements: Sequence[GS1Element]) -> str:
    """Build a GS1-style element string payload.

    This utility adds the ASCII group separator (GS, ``0x1D``) only between
    variable-length fields and their subsequent element, reducing manual errors
    in payload assembly.

    Args:
        elements: Ordered GS1 elements.

    Returns:
        Joined GS1 payload string.

    Raises:
        ValueError: If elements are missing or contain invalid values.
    """
    if not elements:
        raise ValueError("elements must not be empty")

    parts: list[str] = []
    for index, element in enumerate(elements):
        _validate_element(element)
        parts.append(f"{element.ai}{element.data}")
        has_next = index + 1 < len(elements)
        if element.variable_length and has_next:
            parts.append(GROUP_SEPARATOR)

    return "".join(parts)
