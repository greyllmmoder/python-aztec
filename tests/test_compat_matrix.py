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


def test_load_compat_invalid_root(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="root must be an object"):
        load_compat_cases(p)


def test_load_compat_missing_cases_list(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text('{"cases": "nope"}', encoding="utf-8")
    with pytest.raises(ValueError, match="'cases' list"):
        load_compat_cases(p)


def test_load_compat_duplicate_id(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": ['
        '{"id":"x","payload":{"kind":"text","value":"a"},"tags":[]},'
        '{"id":"x","payload":{"kind":"text","value":"b"},"tags":[]}'
        "]}",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate case id"):
        load_compat_cases(p)


def test_load_compat_ec_out_of_range(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": [{"id":"y","payload":{"kind":"text","value":"a"},"ec_percent":3,"tags":[]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="ec_percent"):
        load_compat_cases(p)


def test_load_compat_bytes_hex_odd_length(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": [{"id":"z","payload":{"kind":"bytes_hex","value":"abc"},"tags":[]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="even length"):
        load_compat_cases(p)


def test_load_compat_bytes_hex_invalid(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": [{"id":"z","payload":{"kind":"bytes_hex","value":"zzzz"},"tags":[]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid"):
        load_compat_cases(p)


def test_load_compat_bytes_repeat_count_range(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": [{"id":"z","payload":{"kind":"bytes_repeat","byte":"ff","count":9999},"tags":[]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="count out of range"):
        load_compat_cases(p)


def test_load_compat_bytes_repeat_invalid_byte(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": [{"id":"z","payload":{"kind":"bytes_repeat","byte":"zz","count":5},"tags":[]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="valid hex"):
        load_compat_cases(p)


def test_load_compat_bytes_repeat_multi_byte_unit(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": [{"id":"z","payload":{"kind":"bytes_repeat","byte":"ffff","count":5},"tags":[]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exactly one byte"):
        load_compat_cases(p)


def test_load_compat_unsupported_kind(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": [{"id":"z","payload":{"kind":"unknown","value":"a"},"tags":[]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported payload kind"):
        load_compat_cases(p)


def test_load_compat_invalid_tag_type(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        '{"cases": [{"id":"z","payload":{"kind":"text","value":"a"},"tags":[123]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-empty string"):
        load_compat_cases(p)


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
