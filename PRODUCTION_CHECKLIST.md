# Production Checklist

Use this checklist before shipping a new `aztec-py` version to production.

## 1. Pre-Release Validation

- [ ] `python -m pytest -q`
- [ ] `python -m ruff check .`
- [ ] `python -m mypy --strict aztec_py`
- [ ] `python -m build`
- [ ] `python scripts/decoder_matrix.py --report compat_matrix_report.md`
- [ ] If decode runtime is available in CI: `python scripts/decoder_matrix.py --strict-decode`

## 2. Runtime Optional Dependencies

- [ ] Verify `aztec-py[pdf]` installs and `AztecCode(...).pdf()` works.
- [ ] Verify `aztec-py[decode]` behavior:
  - [ ] successful decode path when Java + ZXing are available
  - [ ] clear error path when runtime/dependency is missing

## 3. GS1 Integration Readiness

- [ ] Build GS1 payloads using `GS1Element` + `build_gs1_payload`.
- [ ] Ensure variable-length elements are marked with `variable_length=True`.
- [ ] Confirm payloads with scanner app/hardware in target environment.

## 4. Release Hygiene

- [ ] Update `CHANGELOG.md`.
- [ ] Confirm `README.md` examples still execute.
- [ ] Verify version metadata in `pyproject.toml`.
- [ ] Build artifacts from clean working tree.

## 5. Post-Release Smoke Checks

- [ ] Install built wheel in fresh venv.
- [ ] `python -c "import aztec_py; print(aztec_py.__all__)"`
- [ ] `aztec "Hello" --format terminal`
- [ ] `aztec "Hello" --format svg > smoke.svg`
- [ ] `aztec "Hello" --format png --output smoke.png`

## 6. Incident Guardrails

- [ ] Keep compatibility fixture failures as release blockers.
- [ ] Log scanner model/runtime for each production decode issue.
- [ ] Add a regression fixture for every production bug before patching.
