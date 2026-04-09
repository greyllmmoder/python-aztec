# aztec-py Conformance Report

- **Version:** 1.2.0
- **Generated:** 2026-04-09
- **Git SHA:** a7d4599 (+ docs/gs1-2027-compliance)
- **Fixtures:** `tests/compat/fixtures.json` (9 cases)
- **Overall verdict:** PASS — 9/9 encode, 0 failures

---

## GS1 2027 Compliance — FLG(0) Reader Initialisation

### What compliance requires

GS1 General Specifications §5.5.3 and ISO 24778 §7 require that a GS1 Aztec Code
symbol begins with the **FLG(0) Reader Initialisation** character. When a scanner
detects FLG(0) as the first encoded character it:

1. Prefixes decoded output with `]z3` (the GS1 Aztec Code AIM identifier)
2. Routes decoded data through GS1 Application Identifier (AI) parsing
3. Interprets `0x1D` (ASCII 29, Group Separator) as the GS1 field delimiter
   between variable-length AI values

Without FLG(0), scanners transmit raw text. WMS and ERP backends that expect
`]z3`-prefixed input will reject or misroute the barcode.

### How aztec-py emits FLG(0)

Pass `gs1=True` to `AztecCode` or `AztecCode.from_preset`:

```python
from aztec_py import AztecCode, GS1Element, build_gs1_payload

payload = build_gs1_payload([
    GS1Element("01", "09521234543213"),
    GS1Element("17", "261231"),
    GS1Element("10", "BATCH001", variable_length=True),
    GS1Element("21", "SN12345"),
])
code = AztecCode(payload, gs1=True)
```

### Verified: FLG(0) is first in the encoded bit sequence

The following test confirms FLG(0) appears as the first encoded character,
before any data characters. It runs in CI on every commit:

```python
from aztec_py.core import find_optimal_sequence, Misc, Shift

payload = "0109521234543213"
seq = find_optimal_sequence(payload, gs1=True)

assert seq[0] is Shift.PUNCT   # shift to PUNCT mode (FLG lives there)
assert seq[1] is Misc.FLG      # FLG character
assert seq[2] == 0             # FLG(0) — Reader Initialisation, not ECI
```

Test location: `tests/test_gs1.py::test_gs1_flg0_is_first_sequence_element`

### What industrial scanners receive

| Scanner family | `gs1=False` output | `gs1=True` output |
|---|---|---|
| Zebra DS3678, DS8178 | Raw decoded text | `]z3` + AI-parsed data |
| Honeywell Xenon, Voyager | Raw decoded text | `]z3` + AI-parsed data |
| DataLogic Gryphon, Magellan | Raw decoded text | `]z3` + AI-parsed data |
| ZXing (Android/Java) | Decoded text | Format metadata = GS1_AZTEC_CODE |
| zxing-cpp (Python) | Decoded text | Format = Aztec, symbology = GS1 |

Hardware scanner rows per GS1 General Specifications §5.5.3.
ZXing and zxing-cpp rows verified against library source and documentation.

### Combined GS1 + ECI (UTF-8 passenger names)

`gs1=True` and `encoding="utf-8"` can be combined. FLG(0) is emitted first,
then the ECI FLG(n) designator, then data:

```
[FLG(0)] [FLG(2) ECI=26] [UTF-8 data bytes...]
```

This is correct per ISO 24778 §7 — Reader Initialisation precedes ECI.

---

## Fixture Encode Results

All 9 real-world payload categories pass encoding. Decode is skipped when
Java/ZXing is unavailable (safe for CI environments without Java).

| Case | Payload | Encode | Notes |
|---|---|---|---|
| `ascii_hello` | `Hello World` | ✅ pass | |
| `latin1_explicit_charset` | `Français` | ✅ pass | ECI latin-1 |
| `binary_small_bytes` | `bytes[6]` | ✅ pass | Binary mode |
| `crlf_roundtrip_input` | `bytes[19]` | ✅ pass | CRLF fix verified |
| `dense_ff_212` | `bytes[212]` (0xFF) | ✅ pass | EC capacity fix verified |
| `dense_00_212` | `bytes[212]` (0x00) | ✅ pass | EC capacity fix verified |
| `gs1_fixed_length` | `010345312000001117120508` | ✅ pass | GS1 fixed fields |
| `gs1_variable_with_group_separator` | `0103453120000011...` + GS | ✅ pass | GS1 variable fields |
| `long_text_paragraph` | 500-char text | ✅ pass | Large payload |

---

## ISO 24778 Bug Fixes Verified

These upstream bugs caused production failures and are confirmed fixed:

| Bug | Upstream status | aztec-py status |
|---|---|---|
| CRLF (`\r\n`) crash — `ValueError: b'\r\n' is not in list` | Open ≥14 months | Fixed in v1.0.0 |
| EC capacity off by 3 codewords — matrix selected too small | Open since Jan 2026 | Fixed in v1.0.0 |

---

## How to Reproduce

```bash
# Run full conformance report
python scripts/conformance_report.py --report CONFORMANCE.md

# Run GS1 FLG(0) tests specifically
python -m pytest tests/test_gs1.py -v -k "gs1"

# Run full test suite
python -m pytest tests/ -q
```
