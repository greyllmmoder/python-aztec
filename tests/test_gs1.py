"""GS1 helper tests."""

from __future__ import annotations

import pytest

from aztec_py import GROUP_SEPARATOR, GS1Element, build_gs1_payload


def test_build_gs1_payload_with_fixed_and_variable_fields() -> None:
    payload = build_gs1_payload(
        [
            GS1Element(ai="01", data="03453120000011"),
            GS1Element(ai="17", data="120508"),
            GS1Element(ai="10", data="ABCD1234", variable_length=True),
            GS1Element(ai="410", data="9501101020917"),
        ]
    )
    assert payload == f"01034531200000111712050810ABCD1234{GROUP_SEPARATOR}4109501101020917"


def test_build_gs1_payload_omits_trailing_separator_for_last_variable_field() -> None:
    payload = build_gs1_payload(
        [
            GS1Element(ai="01", data="03453120000011"),
            GS1Element(ai="10", data="LOT123", variable_length=True),
        ]
    )
    assert payload == "010345312000001110LOT123"


@pytest.mark.parametrize(
    "elements",
    [
        [],
        [GS1Element(ai="A1", data="123")],
        [GS1Element(ai="1", data="123")],
        [GS1Element(ai="12345", data="123")],
        [GS1Element(ai="10", data="")],
        [GS1Element(ai="10", data="AB\x1dCD")],
    ],
)
def test_build_gs1_payload_validates_inputs(elements: list[GS1Element]) -> None:
    with pytest.raises(ValueError):
        build_gs1_payload(elements)
