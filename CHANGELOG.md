# Changelog

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
