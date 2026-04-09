# aztec-py — Pure-Python Aztec Code Barcode Generator

[![CI](https://github.com/greyllmmoder/python-aztec/actions/workflows/ci.yml/badge.svg)](https://github.com/greyllmmoder/python-aztec/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/aztec-py.svg)](https://pypi.org/project/aztec-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/aztec-py.svg)](https://pypi.org/project/aztec-py/)
[![Coverage](https://img.shields.io/badge/coverage-%3E=90%25-brightgreen)](https://github.com/greyllmmoder/python-aztec)
[![mypy: strict](https://img.shields.io/badge/mypy-strict-blue)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**The only pure-Python Aztec barcode library with batch encoding, a CLI, SVG/PDF/PNG output, Rune mode, and GS1 helpers — all zero mandatory dependencies.**

```bash
pip install aztec-py
```

```python
from aztec_py import AztecCode
AztecCode("Hello World").save("hello.svg")   # done.
```

---

## Why aztec-py?

Every other pure-Python Aztec generator is either abandoned, broken, or missing features developers actually need.

| Problem | What aztec-py does |
|---|---|
| CRLF inputs crash upstream | Fixed (upstream issue #5, open 14 months) |
| EC capacity off by 3 codewords | Fixed (upstream issue #7, open 3 months) |
| No SVG output | Built-in, zero extra deps |
| No CLI for automation | `aztec "payload" --format svg > code.svg` |
| No batch encoding | `encode_batch([...], workers=4)` |
| No GS1 / supply-chain helpers | `build_gs1_payload([GS1Element(...)])` |
| No Aztec Rune (0–255) | `AztecRune(42).save("rune.png")` |
| No type hints / mypy support | Full `mypy --strict` coverage |

---

## Install

**Core (zero deps):**

```bash
pip install aztec-py
```

**With extras:**

```bash
pip install "aztec-py[image]"    # PNG output via Pillow
pip install "aztec-py[svg]"      # lxml-backed SVG (optional; built-in SVG works without it)
pip install "aztec-py[pdf]"      # PDF output via fpdf2
pip install "aztec-py[decode]"   # Round-trip decode via python-zxing (requires Java)
```

---

## Quick Start

### Generate a barcode — three lines

```python
from aztec_py import AztecCode

code = AztecCode("Hello World")
code.save("hello.png", module_size=4)   # PNG
code.save("hello.svg")                   # SVG
print(code.svg())                        # SVG string
```

### Use a preset for common real-world formats

```python
from aztec_py import AztecCode

# Boarding pass (IATA BCBP format)
code = AztecCode.from_preset("M1SMITH/JOHN      EABCDEF LHRLAXBA 0172 226Y014C0057 100", "boarding_pass")
code.save("boarding.png")

# GS1 shipping label
code = AztecCode.from_preset(payload, "gs1_label")
code.save("label.png")
```

Available presets: `boarding_pass`, `transit_ticket`, `event_entry`, `gs1_label`

### Batch encode thousands of codes

```python
from aztec_py import encode_batch

svgs = encode_batch(
    ["TICKET-001", "TICKET-002", "TICKET-003"],
    output="svg",
    workers=4,
    preset="event_entry",
)
# Returns list of SVG strings in input order — safe for parallel workers
```

---

## Real-World Use Cases

These are the workloads aztec-py was built for. Copy the pattern, swap the data.

---

### Airline boarding passes — IATA BCBP at scale

Airlines and ground handlers generate tens of thousands of boarding pass barcodes per day at check-in kiosks, web check-in, and lounge printers. The `boarding_pass` preset matches IATA BCBP error correction and module density requirements out of the box.

```python
from aztec_py import AztecCode, encode_batch

# Single pass — kiosk / on-demand
bcbp = "M1SMITH/JOHN      EABCDEF LHRLAXBA 0172 226Y014C0057 100"
AztecCode.from_preset(bcbp, "boarding_pass").save("pass.svg")

# Batch — pre-generate a full flight manifest (300 passengers)
manifest = load_bcbp_strings_from_db()   # your data source
svgs = encode_batch(manifest, output="svg", workers=8, preset="boarding_pass")

# Embed in PDF tickets
from aztec_py import AztecCode
for bcbp, pdf_path in zip(manifest, pdf_paths):
    AztecCode.from_preset(bcbp, "boarding_pass").pdf(module_size=3)
```

**Throughput target:** 5,000+ codes/min on 4 workers (benchmark with `--benchmark-workers 4`).

---

### Shipping and logistics — GS1 parcel labels

Warehouses and 3PLs print GS1-compliant Aztec codes on parcel labels at conveyor speed. The GS1 helper constructs the correct group-separator-delimited payload — no hand-crafting hex strings.

```python
from aztec_py import AztecCode, GS1Element, build_gs1_payload

# One label: GTIN + expiry + batch + ship-to GLN
payload = build_gs1_payload([
    GS1Element("01", "03453120000011"),               # GTIN-14
    GS1Element("17", "260930"),                        # Expiry YYMMDD
    GS1Element("10", "BATCH-2026-04", variable_length=True),  # Lot
    GS1Element("410", "9501101020917"),                # Ship-To
])
AztecCode(payload, ec_percent=33).save("label.png", module_size=4)

# High-volume: encode a full dispatch batch from a CSV
import csv
from aztec_py import encode_batch

with open("dispatch.csv") as f:
    rows = list(csv.DictReader(f))

payloads = [
    build_gs1_payload([
        GS1Element("01", row["gtin"]),
        GS1Element("21", row["serial"], variable_length=True),
    ])
    for row in rows
]
results = encode_batch(payloads, output="png_bytes", workers=4, preset="gs1_label")
```

Or from the CLI — pipe a JSONL export directly to PNG files:

```bash
aztec --input dispatch.jsonl --input-format jsonl \
      --preset gs1_label --format png \
      --out-dir ./labels --workers 8
```

---

### Event ticketing — concerts, venues, transit

Generate unique barcodes per ticket at purchase time, or pre-generate the entire run for a sold-out show. The `event_entry` preset targets scanner read rates in variable-light environments.

```python
from aztec_py import encode_batch

ticket_ids = [f"EVT-2026-{i:06d}" for i in range(10_000)]

# Returns SVG strings in order — ready to inject into HTML/PDF templates
svgs = encode_batch(ticket_ids, output="svg", workers=4, preset="event_entry")

# Embed in HTML email template
for ticket_id, svg in zip(ticket_ids, svgs):
    html = TICKET_TEMPLATE.replace("{{BARCODE}}", svg).replace("{{ID}}", ticket_id)
    send_email(html)
```

Benchmark your hardware before sizing infrastructure:

```bash
aztec --benchmark "EVT-2026-000001" --preset event_entry \
      --format svg --benchmark-count 10000 --benchmark-workers 4
# prints: throughput, p50/p95/p99 latency, codes/sec
```

---

### Healthcare — drug serialization and patient wristbands

Aztec Code is mandated for patient wristbands in several national health systems (ISO/IEC 24778). For drug serialization, it encodes batch, serial, expiry, and GTIN in a single scannable symbol.

```python
from aztec_py import AztecCode, GS1Element, build_gs1_payload

# Drug label: GTIN + expiry + batch (GS1 Pharma)
payload = build_gs1_payload([
    GS1Element("01", "00889714000057"),               # GTIN
    GS1Element("17", "270131"),                        # Expiry
    GS1Element("10", "PB2026Q1", variable_length=True), # Batch
    GS1Element("21", "SN-00043871", variable_length=True), # Serial
])
AztecCode(payload, ec_percent=40).save("drug_label.svg")

# Patient wristband — binary payload with non-ASCII chars handled correctly
AztecCode(b"\x02MRN:4471823\x03", ec_percent=40).save("wristband.svg")
```

---

### Retail — shelf labels and price tags at scale

Shelf-edge labels are reprinted nightly across thousands of SKUs. The CLI bulk mode turns a product CSV into a directory of print-ready PNGs in one command — no Python code needed.

```bash
# products.csv: sku,price,description,...
aztec --input products.csv --input-format csv \
      --format png --module-size 3 \
      --out-dir ./shelf_labels --workers 8 \
      --name-template "label_{index}.png"
```

Or in Python when you need to merge barcodes into existing label artwork:

```python
from aztec_py import encode_batch
from PIL import Image
import io

skus = load_skus_from_erp()   # list of strings
png_bytes_list = encode_batch(skus, output="png_bytes", workers=4)

for sku, png_bytes in zip(skus, png_bytes_list):
    barcode_img = Image.open(io.BytesIO(png_bytes))
    label = render_label_template(sku, barcode_img)
    label.save(f"labels/{sku}.png")
```

---

### Django / Flask API — on-demand barcode service

Serve barcode images over HTTP with zero subprocess overhead:

```python
# Django view
from django.http import HttpResponse
from aztec_py import AztecCode

def barcode_svg(request, payload: str) -> HttpResponse:
    svg = AztecCode(payload, ec_percent=33).svg(module_size=2)
    return HttpResponse(svg, content_type="image/svg+xml")

# FastAPI endpoint
from fastapi import FastAPI
from fastapi.responses import Response
from aztec_py import AztecCode

app = FastAPI()

@app.get("/barcode/{payload}")
def barcode(payload: str) -> Response:
    svg = AztecCode(payload).svg()
    return Response(content=svg, media_type="image/svg+xml")
```

No subprocesses, no Ghostscript, no Java — pure Python, works in any WSGI/ASGI container.

---

## CLI

No Python needed after install. Drop it into shell scripts and CI pipelines:

```bash
# Single code
aztec "Hello World" --format terminal
aztec "Hello World" --format svg > code.svg
aztec "Hello World" --format png --module-size 4 --output code.png

# With preset
aztec --preset boarding_pass "M1SMITH/JOHN..." --format png --output pass.png

# Bulk encode from file (one payload per line)
aztec --input tickets.txt --format png --out-dir ./out --workers 4 --preset event_entry

# Benchmark your hardware
aztec --benchmark "M1SMITH/JOHN..." --format svg --benchmark-count 5000 --benchmark-workers 4
```

**All CLI flags:**

| Flag | Default | Description |
|---|---|---|
| `--format/-f` | `terminal` | `svg`, `png`, `terminal` |
| `--module-size/-m` | `1` (or preset) | Pixels per module |
| `--ec` | `23` (or preset) | Error correction percent (5–95) |
| `--charset` | `UTF-8` (or preset) | Character encoding / ECI hint |
| `--output/-o` | stdout | Output file path (required for PNG) |
| `--preset` | — | `boarding_pass`, `transit_ticket`, `event_entry`, `gs1_label` |
| `--input` | — | Bulk source file |
| `--input-format` | `txt` | `txt`, `csv`, `jsonl` |
| `--workers` | `1` | Process workers for bulk mode |
| `--out-dir` | — | Output directory for bulk mode |
| `--name-template` | — | Filename template with `{index}` |
| `--benchmark` | — | Run throughput benchmark |
| `--benchmark-count` | `1000` | Encode count for benchmark |
| `--benchmark-workers` | `1` | Workers for benchmark |

---

## API Reference

### `AztecCode`

```python
AztecCode(
    data: str | bytes,
    ec_percent: int = 23,          # error correction % (5–95)
    encoding: str | None = None,   # raw mode override
    charset: str | None = None,    # ECI charset hint
    size: int | None = None,       # force matrix size
    compact: bool | None = None,   # force compact/full flag
)
```

**Methods:**

| Method | Returns | Notes |
|---|---|---|
| `AztecCode.from_preset(data, preset, **overrides)` | `AztecCode` | Apply a named preset profile |
| `.image(module_size=2, border=0)` | `PIL.Image.Image` | Requires `[image]` extra |
| `.svg(module_size=1, border=1)` | `str` | Built-in, no extra deps |
| `.pdf(module_size=3, border=1)` | `bytes` | Requires `[pdf]` extra |
| `.save(path, module_size=2, border=0, format=None)` | `None` | Auto-detects `.png`/`.svg`/`.pdf` |
| `.print_out(border=0)` | `None` | ASCII terminal output |
| `.print_fancy(border=0)` | `None` | Unicode block terminal output |

### Batch encoding

```python
from aztec_py import encode_batch, list_presets, get_preset

results = encode_batch(
    payloads=["A", "B", "C"],
    output="svg",        # "matrix" | "svg" | "png_bytes"
    workers=4,           # multiprocessing workers
    preset="boarding_pass",
    ec_percent=33,       # override preset defaults
)
```

### `AztecRune`

Compact 11×11 barcode encoding a single integer 0–255. Used in mobile boarding passes.
Implements ISO 24778 Annex A. No other pure-Python library has this.

```python
from aztec_py import AztecRune

rune = AztecRune(42)
rune.save("rune.svg")
rune.save("rune.png", module_size=8)
```

### GS1 payload builder

```python
from aztec_py import AztecCode, GS1Element, build_gs1_payload

payload = build_gs1_payload([
    GS1Element("01", "03453120000011"),              # GTIN-14
    GS1Element("17", "260430"),                       # Expiry date
    GS1Element("10", "ABCD1234", variable_length=True),  # Batch/Lot
    GS1Element("410", "9501101020917"),               # Ship-To
])
AztecCode(payload, ec_percent=33).save("label.png", module_size=4)
```

**Common GS1 recipes:**

```python
# GTIN + Expiry
build_gs1_payload([GS1Element("01","03453120000011"), GS1Element("17","260430")])

# GTIN + Serial
build_gs1_payload([GS1Element("01","03453120000011"), GS1Element("21","XYZ001",variable_length=True)])

# GTIN + Weight (kg)
build_gs1_payload([GS1Element("01","03453120000011"), GS1Element("3103","001250")])
```

### Round-trip decode (testing / CI validation)

```python
from aztec_py import AztecCode, decode   # requires [decode] extra + Java

code = AztecCode("test payload")
assert decode(code.image()) == "test payload"
```

---

## Production Validation

Run the built-in compatibility matrix against real payloads:

```bash
# Generate a markdown report
python scripts/decoder_matrix.py --report compat_matrix_report.md

# Strict mode (fail if decode checks can't run)
python scripts/decoder_matrix.py --strict-decode
```

The script is skip-safe when ZXing/Java are unavailable — safe for CI environments without Java.

---

## Comparison

| | **aztec-py** | dlenski fork | delimitry original | treepoem | Aspose |
|---|:---:|:---:|:---:|:---:|:---:|
| Pure Python encode | ✅ | ✅ | ✅ | ❌ (BWIPP) | ❌ (proprietary) |
| SVG output | ✅ | PR pending | ❌ | Via backend | ✅ |
| PDF output | ✅ | ❌ | ❌ | Via backend | ✅ |
| CLI tool | ✅ | ❌ | ❌ | ❌ | N/A |
| Batch encoding API | ✅ | ❌ | ❌ | ❌ | N/A |
| Aztec Rune | ✅ | ❌ | ❌ | Backend-dependent | ✅ |
| GS1 helpers | ✅ | ❌ | ❌ | ❌ | ❌ |
| Preset profiles | ✅ | ❌ | ❌ | ❌ | ❌ |
| CRLF bug fixed | ✅ | ❌ (open) | ❌ (open) | N/A | N/A |
| EC capacity bug fixed | ✅ | ❌ (open) | ❌ (open) | N/A | N/A |
| Full type hints | ✅ | ❌ | ❌ | Partial | N/A |
| mypy strict clean | ✅ | ❌ | ❌ | N/A | N/A |
| Zero mandatory deps | ✅ | ✅ | ✅ | ❌ | ❌ |
| Active maintenance | ✅ | ❌ | ❌ | ✅ | ✅ |

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full history.

**Latest: [1.1.0]** — Batch encoding API, preset profiles, CLI bulk/benchmark mode, GS1 helpers, AztecRune improvements.

**[1.0.0]** — Production-grade fork: CRLF fix, EC capacity fix, SVG output, PDF output, AztecRune, CLI, type hints, Hypothesis property tests.

---

## Lineage and Attribution

- Forked from [`dlenski/aztec_code_generator`](https://github.com/dlenski/aztec_code_generator), itself forked from [`delimitry/aztec_code_generator`](https://github.com/delimitry/aztec_code_generator).
- SVG renderer based on upstream [PR #6](https://github.com/dlenski/aztec_code_generator/pull/6) by Zazzik1.
- License chain: MIT — see [LICENSE](LICENSE) and [LICENSE.upstream](LICENSE.upstream).
- Both upstream bugs reported back to maintainers with links to the fixes.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, [SECURITY.md](SECURITY.md) for vulnerability reporting.

```bash
pip install -e ".[dev]"
pytest                       # run tests + coverage
ruff check aztec_py/         # lint
mypy aztec_py/               # type check
python -m build              # build wheel + sdist
```
