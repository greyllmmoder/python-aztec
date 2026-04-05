# aztec-py

[![CI](https://github.com/greyllmmoder/python-aztec/actions/workflows/ci.yml/badge.svg)](https://github.com/greyllmmoder/python-aztec/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/aztec-py.svg)](https://pypi.org/project/aztec-py/)
[![Coverage](https://img.shields.io/badge/coverage-%3E=90%25-brightgreen)](https://github.com/greyllmmoder/python-aztec)
[![mypy](https://img.shields.io/badge/type_checked-mypy-blue)](https://mypy-lang.org/)

Pure-Python Aztec Code 2D barcode generator.

Forked from [`dlenski/aztec_code_generator`](https://github.com/dlenski/aztec_code_generator)
with production fixes, package modernization, SVG/PDF output, CLI tooling, and active maintenance.

## What Is Aztec Code?

Aztec Code is a compact 2D barcode format standardized in ISO/IEC 24778. It can encode text or
binary payloads with configurable error correction, and it does not require a quiet zone.

## Install

```bash
pip install aztec-py
```

Optional extras:

```bash
pip install "aztec-py[pdf]"      # PDF output
pip install "aztec-py[decode]"   # Decode utility via python-zxing + Java
pip install "aztec-py[svg]"      # lxml-backed SVG workflows (optional)
```

## Quick Start

```python
from aztec_py import AztecCode

code = AztecCode("Hello World")
code.save("hello.png", module_size=4)
print(code.svg())
```

## Production Validation

Run compatibility fixtures and generate a markdown report:

```bash
python scripts/decoder_matrix.py --report compat_matrix_report.md
```

The script is skip-safe when decode runtime requirements (`zxing` + Java) are unavailable.
Use strict mode when decode checks are mandatory in CI:

```bash
python scripts/decoder_matrix.py --strict-decode
```

Fixture source: `tests/compat/fixtures.json`
Release checklist: `PRODUCTION_CHECKLIST.md`

## CLI

```bash
aztec "Hello World" --format terminal
aztec "Hello World" --format svg > code.svg
aztec "Hello World" --format png --module-size 4 --output code.png
aztec --ec 33 --charset ISO-8859-1 "Héllo" --format svg --output code.svg
```

Supported flags:

- `--format/-f`: `svg`, `png`, `terminal` (default: `terminal`)
- `--module-size/-m`: module size in pixels (default: `1`)
- `--ec`: error correction percent (default: `23`)
- `--charset`: text charset/ECI hint (default: `UTF-8`)
- `--output/-o`: output file path (required for `png`)

## API Reference

### `AztecCode`

- `AztecCode(data, ec_percent=23, encoding=None, charset=None, size=None, compact=None)`
- `image(module_size=2, border=0)`
- `svg(module_size=1, border=1) -> str`
- `pdf(module_size=3, border=1) -> bytes`
- `save(path, module_size=2, border=0, format=None)`
- `print_out(border=0)`
- `print_fancy(border=0)`

### `AztecRune`

- `AztecRune(value)` where `value` is in `0..255`
- `image()`, `svg()`, `save(...)`

### GS1 Payload Helper

- `GS1Element(ai, data, variable_length=False)`
- `build_gs1_payload([...]) -> str`
- `GROUP_SEPARATOR` (`\x1d`)

Example:

```python
from aztec_py import AztecCode, GS1Element, build_gs1_payload

payload = build_gs1_payload(
    [
        GS1Element("01", "03453120000011"),
        GS1Element("17", "120508"),
        GS1Element("10", "ABCD1234", variable_length=True),
        GS1Element("410", "9501101020917"),
    ]
)
AztecCode(payload).save("gs1.png", module_size=4)
```

### Decode Utility

```python
from aztec_py import AztecCode, decode

code = AztecCode("test data")
decoded = decode(code.image())
```

Requires `pip install "aztec-py[decode]"` and a Java runtime.

## GS1 Recipes

```python
from aztec_py import GS1Element, build_gs1_payload
```

1. GTIN + Expiry (fixed-length only)
```python
build_gs1_payload([
    GS1Element("01", "03453120000011"),
    GS1Element("17", "120508"),
])
```
2. GTIN + Batch/Lot + Ship To (variable field adds separator)
```python
build_gs1_payload([
    GS1Element("01", "03453120000011"),
    GS1Element("10", "ABCD1234", variable_length=True),
    GS1Element("410", "9501101020917"),
])
```
3. GTIN + Serial
```python
build_gs1_payload([
    GS1Element("01", "03453120000011"),
    GS1Element("21", "SERIAL0001", variable_length=True),
])
```
4. GTIN + Weight (kg)
```python
build_gs1_payload([
    GS1Element("01", "03453120000011"),
    GS1Element("3103", "000750"),
])
```
5. GTIN + Expiry + Serial + Destination
```python
build_gs1_payload([
    GS1Element("01", "03453120000011"),
    GS1Element("17", "120508"),
    GS1Element("21", "XYZ12345", variable_length=True),
    GS1Element("410", "9501101020917"),
])
```

## Comparison

| Library | Pure Python encode | SVG | CLI | Rune | PDF | Notes |
|---|---:|---:|---:|---:|---:|---|
| `aztec-py` | Yes | Yes | Yes | Yes | Yes | Active fork with bugfixes |
| `dlenski/aztec_code_generator` | Yes | PR pending | No | No | No | Upstream fork |
| `delimitry/aztec_code_generator` | Yes | No | No | No | No | Original lineage |
| `treepoem` | No (BWIPP/Ghostscript backend) | Via backend | No | Backend-dependent | Via backend | Wrapper-based |
| Aspose Barcode | No (proprietary) | Yes | N/A | Yes | Yes | Commercial SDK |

## Lineage and Attribution

- Originally written by Dmitry Alimov (delimitry); this fork's updates and bug fixes are maintained by greyllmmoder.
- Upstream fork source: https://github.com/dlenski/aztec_code_generator
- Original project: https://github.com/delimitry/aztec_code_generator
- License chain: MIT (`LICENSE` and `LICENSE.upstream`)
- SVG support based on upstream PR #6 by Zazzik1:
  https://github.com/dlenski/aztec_code_generator/pull/6

## Contributing

- Read contribution guidelines: `CONTRIBUTING.md`
- Security reporting process: `SECURITY.md`
- Production release checks: `PRODUCTION_CHECKLIST.md`
- To sync standard labels (after `gh auth login`): `./scripts/sync_labels.sh`
