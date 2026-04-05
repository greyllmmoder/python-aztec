"""Renderer-level tests (image/svg/pdf)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aztec_py import AztecCode
from aztec_py.renderers import image_from_matrix, svg_from_matrix


def test_svg_renderer_emits_svg() -> None:
    matrix = [[1, 0], [0, 1]]
    svg = svg_from_matrix(matrix, module_size=2, border=1)
    assert svg.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<svg" in svg
    assert "<path" in svg


def test_image_renderer_dimensions() -> None:
    matrix = [[1, 0], [0, 1]]
    image = image_from_matrix(matrix, module_size=3, border=1)
    assert image.size == (12, 12)


def test_save_svg_file(tmp_path: Path) -> None:
    code = AztecCode("renderer-test")
    target = tmp_path / "code.svg"
    code.save(target, module_size=2)
    payload = target.read_text(encoding="utf-8")
    assert "<svg" in payload


def test_save_pdf_file(tmp_path: Path) -> None:
    fpdf = pytest.importorskip("fpdf")
    assert fpdf is not None
    code = AztecCode("pdf-test")
    target = tmp_path / "code.pdf"
    code.save(target, module_size=2)
    assert target.exists()
    assert target.stat().st_size > 64
