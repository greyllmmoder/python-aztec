# ISO/IEC 24778 Traceability Matrix

This document provides implementation traceability evidence for `aztec-py`.
It is intended for audit support and release validation workflows.

This matrix does not replace independent certification.

## Scope

- Encoder implementation: `aztec_py/core.py`
- Symbol rendering: `aztec_py/renderers/*`
- Validation fixtures and regression checks: `tests/*`, `tests/compat/fixtures.json`

## Traceability Table

| Requirement Area | Implementation Evidence | Automated Verification |
|---|---|---|
| Symbol layer/size selection and capacity fit checks | `aztec_py/core.py` (`find_suitable_matrix_size`, `_required_capacity_bits`) | `tests/test_core.py`, `tests/test_validation.py` |
| Reed-Solomon error correction generation | `aztec_py/core.py` (`reed_solomon`) | `tests/test_core.py::Test::test_reed_solomon` |
| Character mode/latch/shift sequencing | `aztec_py/core.py` (`find_optimal_sequence`, `optimal_sequence_to_bits`) | `tests/test_core.py::Test::test_find_optimal_sequence_*`, `tests/test_core.py::Test::test_optimal_sequence_to_bits` |
| Bit stuffing and codeword construction | `aztec_py/core.py` (`get_data_codewords`) | `tests/test_core.py::Test::test_get_data_codewords` |
| CRLF handling regression | `aztec_py/core.py` + fixture/test coverage | `tests/test_core.py::Test::test_crlf_encoding`, `tests/test_core.py::Test::test_crlf_roundtrip` |
| Error-correction capacity regression (worst-case bytes) | `aztec_py/core.py` capacity calculations | `tests/test_core.py::Test::test_ec_worst_case_ff_bytes`, `tests/test_core.py::Test::test_ec_worst_case_null_bytes` |
| GS1 payload composition and separators | `aztec_py/gs1.py` | `tests/test_gs1.py` |
| Rendering determinism (PNG/SVG/PDF) | `aztec_py/core.py`, `aztec_py/renderers/image.py`, `aztec_py/renderers/svg.py` | `tests/test_renderers.py`, `tests/test_api_behaviour.py` |
| CLI behavior and output contract | `aztec_py/__main__.py` | `tests/test_cli.py` |
| Compatibility fixture corpus and decode matrix | `scripts/decoder_matrix.py`, `tests/compat/fixtures.json` | `tests/test_compat_matrix.py`, `scripts/conformance_report.py` |

## Release Evidence Artifacts

The following artifacts are generated and retained by CI/release gates:

- `compat_matrix_report.md`
- `conformance_report.md`
- `conformance_report.json`

## Audit Notes

- Decode checks are runtime-dependent (`python-zxing` + Java).
- Non-strict mode allows skip-safe evidence generation when decode backend is unavailable.
- Strict mode can be enabled for environments where decode runtime is mandatory.
