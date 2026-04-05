# Contributing to aztec-py

Thanks for contributing.

## Development setup

```bash
git clone git@github.com:greyllmmoder/python-aztec.git
cd python-aztec
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,image,pdf]"
```

## Branching

- Create a branch from `main`.
- Use one coherent goal per branch.
- Suggested names:
  - `feat/<short-topic>`
  - `fix/<short-topic>`
  - `chore/<short-topic>`

## Before opening a PR

Run all required checks locally:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy --strict aztec_py
python -m build
```

If your change touches compatibility behavior, also run:

```bash
python scripts/decoder_matrix.py --report compat_matrix_report.md
```

## Pull request requirements

- Keep PR scope focused and reviewable.
- Add or update tests for behavior changes.
- Update docs for user-facing changes.
- Add a changelog entry when needed.
- Use the PR template and include exact validation commands.

## Commit guidance

- Prefer small logical commits.
- Use clear commit messages.
- Avoid unrelated formatting or cleanup changes.

## Reporting bugs

Please include:

- input payload (or a minimal reproducible subset)
- expected behavior
- actual behavior
- Python version and OS
- scanner/runtime details if decode-related
