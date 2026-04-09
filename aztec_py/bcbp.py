"""IATA BCBP (Bar Coded Boarding Pass) payload builder for Aztec Code integration.

Implements the mandatory single-segment section of IATA Resolution 792
Format Code F (Version 7, 2020).  Output is always exactly 60 characters
and is suitable for direct encoding with::

    AztecCode.from_preset(bcbp_string, "boarding_pass")
"""

from __future__ import annotations

import datetime
import re
import warnings
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class BCBPSegment:
    """Single-segment IATA BCBP Format Code F fields.

    All string fields are trimmed or padded to their IATA-specified widths
    by :func:`build_bcbp_string`.  Validation errors raise :class:`ValueError`.
    A long ``passenger_name`` is silently truncated to 20 characters with a
    :class:`UserWarning`.

    Attributes:
        passenger_name: ``"SURNAME/GIVEN"`` format, max 20 characters.
        pnr_code: Booking reference, max 7 characters.
        from_airport: IATA 3-letter origin airport code (e.g. ``"LHR"``).
        to_airport: IATA 3-letter destination airport code (e.g. ``"JFK"``).
        carrier: Operating carrier designator, 2–3 characters (e.g. ``"BA"``).
        flight_number: Flight number — digits are extracted and zero-padded to 4.
        date_of_flight: Travel date as :class:`datetime.date` (auto-converted to
            Julian day) or integer Julian day (1–366).
        compartment_code: Single cabin-class character (``"Y"``, ``"C"``, etc.).
        seat_number: Seat assignment, max 4 characters (e.g. ``"023A"``).
        sequence_number: Check-in sequence number, 1–99999.
        passenger_status: Single digit ``"0"``–``"7"`` per IATA spec.
        electronic_ticket: ``True`` encodes ``"E"`` in the e-ticket indicator field.
    """

    passenger_name: str
    pnr_code: str
    from_airport: str
    to_airport: str
    carrier: str
    flight_number: str
    date_of_flight: Union[datetime.date, int]
    compartment_code: str
    seat_number: str
    sequence_number: int
    passenger_status: str = "0"
    electronic_ticket: bool = True


def _validate_airport(code: str, field: str) -> None:
    if len(code) != 3 or not code.isalpha():
        raise ValueError(
            f"{field} must be a 3-letter IATA airport code (e.g. 'LHR'), got {code!r}"
        )


def _to_julian(date_of_flight: Union[datetime.date, int]) -> int:
    if isinstance(date_of_flight, int):
        if not 1 <= date_of_flight <= 366:
            raise ValueError(
                f"date_of_flight as int must be a Julian day 1–366, got {date_of_flight}"
            )
        return date_of_flight
    d = date_of_flight
    return (d - datetime.date(d.year, 1, 1)).days + 1


def build_bcbp_string(segment: BCBPSegment) -> str:
    """Build a single-segment IATA BCBP Format Code F string.

    Returns exactly 60 characters per IATA Resolution 792 Version 7
    mandatory section layout.  Pass the result directly to
    ``AztecCode.from_preset(bcbp, "boarding_pass")`` to produce a
    standards-compliant mobile boarding pass Aztec symbol.

    BCBP field layout (60 characters total):

    .. code-block:: text

        Pos    Width  Field
        ─────────────────────────────────────────
          1      1    Format code            → "M"
          2      1    Number of legs         → "1"
         3–22   20    Passenger name         left-justified, space-padded
         23      1    E-ticket indicator     "E" or " "
        24–30    7    PNR code               left-justified, space-padded
        31–33    3    From airport           uppercase IATA code
        34–36    3    To airport             uppercase IATA code
        37–39    3    Carrier designator     left-justified, space-padded
        40–44    5    Flight number          4 digits zero-padded + " "
        45–47    3    Date of flight         Julian day zero-padded
         48      1    Compartment code       first character
        49–52    4    Seat number            left-justified, space-padded
        53–57    5    Sequence number        zero-padded
         58      1    Passenger status       first character
        59–60    2    Conditional item size  → "00"
        ─────────────────────────────────────────
        Total:  1+1+20+1+7+3+3+3+5+3+1+4+5+1+2 = 60

    Args:
        segment: :class:`BCBPSegment` with all mandatory fields.

    Returns:
        60-character BCBP mandatory section string.

    Raises:
        ValueError: If any field fails IATA format validation.

    Warns:
        UserWarning: If ``passenger_name`` exceeds 20 characters (truncated).
    """
    # --- validate ---
    _validate_airport(segment.from_airport, "from_airport")
    _validate_airport(segment.to_airport, "to_airport")

    if not 2 <= len(segment.carrier) <= 3:
        raise ValueError(
            f"carrier must be 2–3 characters, got {segment.carrier!r}"
        )

    digits = re.sub(r"\D", "", segment.flight_number)[:4]
    if not digits:
        raise ValueError(
            f"flight_number must contain at least one digit, got {segment.flight_number!r}"
        )

    julian = _to_julian(segment.date_of_flight)

    if not segment.compartment_code:
        raise ValueError("compartment_code must not be empty")

    if not 1 <= segment.sequence_number <= 99999:
        raise ValueError(
            f"sequence_number must be 1–99999, got {segment.sequence_number}"
        )

    if (
        len(segment.passenger_status) < 1
        or segment.passenger_status[0] not in "01234567"
    ):
        raise ValueError(
            f"passenger_status must be a single digit 0–7, got {segment.passenger_status!r}"
        )

    # --- warn and truncate passenger name ---
    name = segment.passenger_name
    if len(name) > 20:
        warnings.warn(
            f"passenger_name {name!r} exceeds 20 characters and will be truncated",
            UserWarning,
            stacklevel=2,
        )
    name = name[:20].ljust(20)

    # --- assemble exactly 60 characters ---
    return "".join([
        "M",                                         # 1  — format code
        "1",                                         # 1  — number of legs
        name,                                        # 20 — passenger name
        "E" if segment.electronic_ticket else " ",  # 1  — e-ticket indicator
        segment.pnr_code[:7].ljust(7),              # 7  — PNR code
        segment.from_airport[:3].upper(),            # 3  — origin airport
        segment.to_airport[:3].upper(),              # 3  — destination airport
        segment.carrier[:3].ljust(3),               # 3  — carrier designator
        digits.zfill(4) + " ",                      # 5  — flight number
        str(julian).zfill(3),                        # 3  — Julian day
        segment.compartment_code[0],                 # 1  — compartment code
        segment.seat_number[:4].ljust(4),           # 4  — seat number
        str(segment.sequence_number).zfill(5),       # 5  — sequence number
        segment.passenger_status[0],                 # 1  — passenger status
        "00",                                         # 2  — conditional item size
    ])
