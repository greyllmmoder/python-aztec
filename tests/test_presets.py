"""Preset profile tests."""

from __future__ import annotations

import pytest

from aztec_py import AztecCode, get_preset, list_presets


def test_list_presets_contains_expected_profiles() -> None:
    names = list_presets()
    assert "boarding_pass" in names
    assert "transit_ticket" in names
    assert "event_entry" in names
    assert "gs1_label" in names


def test_get_preset_unknown_name_fails() -> None:
    with pytest.raises(ValueError, match="Unknown preset"):
        get_preset("does_not_exist")


def test_from_preset_uses_defaults() -> None:
    code = AztecCode.from_preset("HELLO", "boarding_pass")
    assert code.ec_percent == 33
    assert code.encoding == "UTF-8"


def test_from_preset_allows_explicit_overrides() -> None:
    code = AztecCode.from_preset(
        "HELLO",
        "boarding_pass",
        ec_percent=23,
        charset="ISO-8859-1",
    )
    assert code.ec_percent == 23
    assert code.encoding == "ISO-8859-1"


def test_from_preset_respects_explicit_encoding() -> None:
    code = AztecCode.from_preset("HELLO", "gs1_label", encoding="utf-8")
    assert code.encoding == "utf-8"

