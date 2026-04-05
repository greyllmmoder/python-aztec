"""Production compatibility fixture tests."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from aztec_py import AztecCode
from aztec_py.compat import CompatCase, load_compat_cases


FIXTURE_PATH = Path(__file__).parent / "compat" / "fixtures.json"


def _load_cases() -> list[CompatCase]:
    return load_compat_cases(FIXTURE_PATH)


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: case.case_id)
def test_all_compat_fixtures_encode_to_matrix(case: CompatCase) -> None:
    code = AztecCode(case.payload, ec_percent=case.ec_percent, charset=case.charset)
    matrix = code.matrix
    assert matrix
    assert len(matrix) > 0
    assert all(len(row) == len(matrix) for row in matrix)


def test_compat_fixture_set_has_gs1_group_separator_case() -> None:
    gs1_cases = [case for case in _load_cases() if "gs1" in case.tags]
    assert gs1_cases, "expected GS1 fixtures"
    assert any(
        isinstance(case.payload, str) and "\x1d" in case.payload for case in gs1_cases
    ), "expected at least one GS1 fixture with group separator"


def test_decoder_matrix_script_smoke(tmp_path: Path) -> None:
    report_path = tmp_path / "compat_matrix.md"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/decoder_matrix.py",
            "--fixtures",
            str(FIXTURE_PATH),
            "--report",
            str(report_path),
        ],
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Decoder Compatibility Matrix" in content
    assert "ascii_hello" in content
