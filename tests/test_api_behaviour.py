"""Additional API behavior tests for coverage and regressions."""

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path

import pytest

from aztec_py import AztecCode
from aztec_py import core as core_module
from aztec_py.renderers import image as image_module


def test_save_svg_to_file_object() -> None:
    code = AztecCode("hello")
    stream = StringIO()
    code.save(stream, format="svg")
    assert "<svg" in stream.getvalue()


def test_save_pdf_to_file_object() -> None:
    pytest.importorskip("fpdf")
    code = AztecCode("hello")
    stream = BytesIO()
    code.save(stream, format="pdf")
    assert stream.getbuffer().nbytes > 64


def test_image_renderer_missing_pillow(monkeypatch: pytest.MonkeyPatch) -> None:
    missing = RuntimeError("Pillow missing")
    monkeypatch.setattr(image_module, "ImageDraw", None)
    monkeypatch.setattr(image_module, "missing_pil", (RuntimeError, missing, None), raising=False)
    with pytest.raises(RuntimeError, match="Pillow missing"):
        image_module.image_from_matrix([[1]])


def test_core_main_usage_message(capsys: pytest.CaptureFixture[str]) -> None:
    assert core_module.main(["aztec"]) == 1
    out = capsys.readouterr().out
    assert "usage:" in out


def test_core_main_saves_png(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "main.png"
    monkeypatch.setattr(core_module.sys, "argv", ["aztec", "hello", str(target)])
    rc = core_module.main(["aztec", "hello", str(target)])
    assert rc == 0
    assert target.exists()
