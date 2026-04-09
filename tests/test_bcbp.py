"""IATA BCBP payload builder tests."""

from __future__ import annotations

import dataclasses
import datetime
import warnings

import pytest

from aztec_py import AztecCode, BCBPSegment, build_bcbp_string

# ---------------------------------------------------------------------------
# Shared fixture — a valid single-segment boarding pass
# June 15 2026 is Julian day 166 (2026 is not a leap year)
# ---------------------------------------------------------------------------

VALID = BCBPSegment(
    passenger_name="SMITH/JOHN",
    pnr_code="ABC123",
    from_airport="LHR",
    to_airport="JFK",
    carrier="BA",
    flight_number="0123",
    date_of_flight=datetime.date(2026, 6, 15),
    compartment_code="Y",
    seat_number="023A",
    sequence_number=42,
    passenger_status="0",
    electronic_ticket=True,
)


# ---------------------------------------------------------------------------
# Test 1 — output is exactly 60 characters
# ---------------------------------------------------------------------------

def test_output_is_60_characters() -> None:
    result = build_bcbp_string(VALID)
    assert len(result) == 60, f"Expected 60 chars, got {len(result)}: {result!r}"


# ---------------------------------------------------------------------------
# Test 2 — format code and number-of-legs fields
# ---------------------------------------------------------------------------

def test_format_code_and_legs() -> None:
    result = build_bcbp_string(VALID)
    assert result[0] == "M", "Position 1 must be format code 'M'"
    assert result[1] == "1", "Position 2 must be number of legs '1'"


# ---------------------------------------------------------------------------
# Test 3 — passenger name is left-justified, space-padded to 20 chars
# ---------------------------------------------------------------------------

def test_passenger_name_padded() -> None:
    result = build_bcbp_string(VALID)
    name_field = result[2:22]           # positions 3–22 (0-indexed 2–21)
    assert len(name_field) == 20
    assert name_field == "SMITH/JOHN          "   # 10 chars + 10 spaces


# ---------------------------------------------------------------------------
# Test 4 — datetime.date auto-converts to correct Julian day
# ---------------------------------------------------------------------------

def test_date_auto_converts_to_julian() -> None:
    result = build_bcbp_string(VALID)
    date_field = result[44:47]          # positions 45–47 (0-indexed 44–46)
    assert date_field == "166", f"Expected Julian day '166' for 2026-06-15, got {date_field!r}"


# ---------------------------------------------------------------------------
# Test 5 — integer Julian day passes through unchanged
# ---------------------------------------------------------------------------

def test_date_int_passthrough() -> None:
    seg = dataclasses.replace(VALID, date_of_flight=166)
    result = build_bcbp_string(seg)
    assert result[44:47] == "166"


# ---------------------------------------------------------------------------
# Test 6 — from_airport wrong length raises ValueError
# ---------------------------------------------------------------------------

def test_invalid_airport_wrong_length() -> None:
    seg = dataclasses.replace(VALID, from_airport="LH")
    with pytest.raises(ValueError, match="from_airport"):
        build_bcbp_string(seg)


# ---------------------------------------------------------------------------
# Test 7 — sequence_number=0 raises ValueError
# ---------------------------------------------------------------------------

def test_sequence_number_zero_raises() -> None:
    seg = dataclasses.replace(VALID, sequence_number=0)
    with pytest.raises(ValueError, match="sequence_number"):
        build_bcbp_string(seg)


# ---------------------------------------------------------------------------
# Test 8 — passenger_status out of 0–7 range raises ValueError
# ---------------------------------------------------------------------------

def test_passenger_status_invalid_raises() -> None:
    seg = dataclasses.replace(VALID, passenger_status="8")
    with pytest.raises(ValueError, match="passenger_status"):
        build_bcbp_string(seg)


# ---------------------------------------------------------------------------
# Test 9 — full output encodes into AztecCode without error
# ---------------------------------------------------------------------------

def test_bcbp_encodes_to_aztec_no_crash() -> None:
    bcbp = build_bcbp_string(VALID)
    code = AztecCode.from_preset(bcbp, "boarding_pass")
    assert code is not None
    assert code.size >= 15


# ---------------------------------------------------------------------------
# Test 10 — passenger_name > 20 chars is truncated with UserWarning
# ---------------------------------------------------------------------------

def test_long_passenger_name_truncated_with_warning() -> None:
    long_name = "VERYLONGSURNAME/FIRSTNAME"   # 25 chars
    seg = dataclasses.replace(VALID, passenger_name=long_name)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = build_bcbp_string(seg)

    # Output is still 60 chars
    assert len(result) == 60

    # Name field is exactly 20 chars, truncated
    assert result[2:22] == "VERYLONGSURNAME/FIRS"

    # Warning was issued
    assert any(issubclass(w.category, UserWarning) for w in caught), (
        "Expected a UserWarning for name truncation"
    )
