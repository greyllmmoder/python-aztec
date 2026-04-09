"""Decode utility tests."""

from __future__ import annotations

import sys

import pytest

from aztec_py import decode


# ---------------------------------------------------------------------------
# Existing tests — zxing legacy path
# (block zxingcpp with None so import raises ImportError, fall through to zxing)
# ---------------------------------------------------------------------------

def test_decode_requires_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "zxingcpp", None)   # blocks re-import
    monkeypatch.setitem(sys.modules, "zxing", None)       # blocks re-import
    with pytest.raises(RuntimeError, match="optional backend"):
        decode("missing.png")


def test_decode_success_with_mocked_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        raw = "ok"

    class Reader:
        def decode(self, _source):
            return Result()

    class ZXing:
        BarCodeReader = Reader

    monkeypatch.setitem(sys.modules, "zxingcpp", None)   # force zxing path
    monkeypatch.setitem(sys.modules, "zxing", ZXing())
    assert decode("any.png") == "ok"


def test_decode_reports_empty_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    class Reader:
        def decode(self, _source):
            return None

    class ZXing:
        BarCodeReader = Reader

    monkeypatch.setitem(sys.modules, "zxingcpp", None)   # force zxing path
    monkeypatch.setitem(sys.modules, "zxing", ZXing())
    with pytest.raises(RuntimeError, match="no payload"):
        decode("any.png")


# ---------------------------------------------------------------------------
# New tests — zxingcpp fast path
# Pass a real in-memory PIL image so no file I/O is needed
# ---------------------------------------------------------------------------

def test_decode_zxingcpp_fast_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """zxingcpp is preferred over zxing when present; returns results[0].text."""
    from PIL import Image

    class FakeResult:
        text = "fast-result"

    class FakeZxingcpp:
        @staticmethod
        def read_barcodes(_img: object) -> list[FakeResult]:
            return [FakeResult()]

    img = Image.new("RGB", (15, 15))
    monkeypatch.setitem(sys.modules, "zxingcpp", FakeZxingcpp())
    assert decode(img) == "fast-result"


def test_decode_zxingcpp_empty_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """zxingcpp returning empty list raises RuntimeError."""
    from PIL import Image

    class FakeZxingcpp:
        @staticmethod
        def read_barcodes(_img: object) -> list[object]:
            return []

    img = Image.new("RGB", (15, 15))
    monkeypatch.setitem(sys.modules, "zxingcpp", FakeZxingcpp())
    with pytest.raises(RuntimeError, match="no payload"):
        decode(img)


def test_decode_zxingcpp_falls_back_to_zxing(monkeypatch: pytest.MonkeyPatch) -> None:
    """When zxingcpp is absent, decode falls through to python-zxing."""
    class Result:
        raw = "zxing-result"

    class Reader:
        def decode(self, _source: object) -> Result:
            return Result()

    class ZXing:
        BarCodeReader = Reader

    monkeypatch.setitem(sys.modules, "zxingcpp", None)   # block fast path
    monkeypatch.setitem(sys.modules, "zxing", ZXing())
    assert decode("any.png") == "zxing-result"
