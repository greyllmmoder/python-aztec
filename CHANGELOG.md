# Changelog

## [1.2.0] - 2026-04-09

### Added
- `AztecCode(data, gs1=True)` emits FLG(0) Reader Initialisation as the first
  encoded character, per ISO 24778 §7 and GS1 General Specifications §5.5.3.
  Industrial scanners (Zebra, Honeywell, DataLogic) prefix decoded output with
  `]z3` when FLG(0) is present, enabling GS1 AI routing in WMS/ERP systems.
- `AztecCode.from_preset(data, preset, gs1=True)` forwards the GS1 flag.
- `find_optimal_sequence(data, gs1=True)` and `find_suitable_matrix_size(data, gs1=True)`
  expose the flag for advanced users.
- `CONFORMANCE.md` — evidence report documenting GS1 2027 compliance and fixture results.

## [1.1.0] - 2026-04-09

### Added
- Batch encoding API: `encode_batch(payloads, output, workers, preset)` with ordered results and multiprocessing support.
- Preset profiles: `boarding_pass`, `transit_ticket`, `event_entry`, `gs1_label` via `AztecCode.from_preset(...)`.
- CLI bulk mode: `--input`, `--input-format`, `--workers`, `--out-dir`, `--name-template`, `--preset`.
- CLI benchmark mode: `--benchmark`, `--benchmark-count`, `--benchmark-workers` with throughput metrics.
- GS1 payload builder: `GS1Element`, `build_gs1_payload`, `GROUP_SEPARATOR`.
- Production compatibility matrix script (`scripts/decoder_matrix.py`) with markdown report output.
- Compatibility fixture tests against real-world payloads.

### Changed
- Development Status classifier promoted to `5 - Production/Stable`.
- PyPI keywords and classifiers expanded for discoverability.

## [1.0.0] - 2026-04-05

### Fixed
- CRLF encoding coverage and regressions aligned with upstream issue #5.
- Error-correction capacity sizing bug fixed for worst-case stuffing payloads (upstream issue #7).

### Added
- Package split into `aztec_py` with modern `pyproject.toml` packaging.
- SVG output support based on upstream PR #6 by Zazzik1.
- CLI entry point (`aztec`) and `python -m aztec_py` runner.
- PDF output (`AztecCode.pdf()` and extension-aware `save()` behavior).
- `AztecRune` support for 0..255 values.
- Optional decode helper (`aztec_py.decode`) backed by `python-zxing`.
- Property-based tests with Hypothesis.
- Input validation for public API boundaries.

### Changed
- Project metadata updated for fork lineage visibility.
- Added explicit attribution artifacts: `LICENSE.upstream` and `CONTRIBUTORS.md`.
