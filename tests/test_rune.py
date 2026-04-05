"""Aztec Rune tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from aztec_py import AztecRune


def test_rune_bounds() -> None:
    with pytest.raises(ValueError):
        AztecRune(-1)
    with pytest.raises(ValueError):
        AztecRune(256)


def test_rune_matrix_shape() -> None:
    rune = AztecRune(42)
    assert len(rune.matrix) == 11
    assert all(len(row) == 11 for row in rune.matrix)


def test_rune_svg() -> None:
    rune = AztecRune(42)
    svg = rune.svg()
    assert "<svg" in svg


def test_rune_save_png(tmp_path: Path) -> None:
    rune = AztecRune(42)
    target = tmp_path / "rune.png"
    rune.save(target, module_size=4)
    assert target.exists()
    assert target.stat().st_size > 0


def test_rune_save_svg_file_object(tmp_path: Path) -> None:
    rune = AztecRune(7)
    target = tmp_path / "rune.svg"
    with target.open("w", encoding="utf-8") as file_obj:
        rune.save(file_obj, format="svg")
    assert "<svg" in target.read_text(encoding="utf-8")


def test_rune_save_pdf(tmp_path: Path) -> None:
    pytest.importorskip("fpdf")
    rune = AztecRune(99)
    target = tmp_path / "rune.pdf"
    rune.save(target, format="pdf")
    assert target.exists()
    assert target.stat().st_size > 64
