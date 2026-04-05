"""Validation tests for public AztecCode API."""

import pytest

from aztec_py import AztecCode


def test_ec_percent_lower_bound() -> None:
    with pytest.raises(ValueError, match="between 5 and 95"):
        AztecCode("data", ec_percent=4)


def test_ec_percent_upper_bound() -> None:
    with pytest.raises(ValueError, match="between 5 and 95"):
        AztecCode("data", ec_percent=96)


def test_empty_data_rejected() -> None:
    with pytest.raises(ValueError, match="data must not be empty"):
        AztecCode("")


def test_charset_encoding_mismatch_rejected() -> None:
    with pytest.raises(ValueError, match="encoding and charset must match"):
        AztecCode("hello", encoding="utf-8", charset="iso-8859-1")
