"""GS1 helper tests."""

from __future__ import annotations

import pytest

from aztec_py import GROUP_SEPARATOR, AztecCode, GS1Element, build_gs1_payload
from aztec_py.core import Misc, Shift, find_optimal_sequence


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


# --- gs1=True flag tests ---


def test_gs1_flag_encodes_without_error() -> None:
    """AztecCode(gs1=True) must not raise for a valid GS1 payload."""
    payload = build_gs1_payload([GS1Element(ai="01", data="09521234543213")])
    code = AztecCode(payload, gs1=True)
    assert code is not None
    assert code.size >= 15


def test_gs1_flg0_is_first_sequence_element() -> None:
    """gs1=True prepends FLG(0) before any data characters."""
    payload = build_gs1_payload([GS1Element(ai="01", data="09521234543213")])
    seq = find_optimal_sequence(payload, gs1=True)
    # FLG(0) preamble: Shift.PUNCT, Misc.FLG, 0
    assert seq[0] is Shift.PUNCT
    assert seq[1] is Misc.FLG
    assert seq[2] == 0


def test_gs1_false_emits_no_flg0() -> None:
    """Default gs1=False must not inject any FLG character."""
    seq = find_optimal_sequence("010952123454321317261231", gs1=False)
    assert Misc.FLG not in seq


def test_gs1_flag_via_from_preset() -> None:
    """from_preset accepts and forwards gs1=True."""
    payload = build_gs1_payload([
        GS1Element(ai="01", data="09521234543213"),
        GS1Element(ai="17", data="261231"),
        GS1Element(ai="10", data="LOT001", variable_length=True),
    ])
    code = AztecCode.from_preset(payload, "gs1_label", gs1=True)
    assert code is not None
    assert code.gs1 is True
