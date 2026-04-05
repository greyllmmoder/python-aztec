"""Decode utility tests."""

from __future__ import annotations

import sys

import pytest

from aztec_py import decode


def test_decode_requires_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "zxing", raising=False)
    with pytest.raises(RuntimeError, match="optional dependency 'zxing'"):
        decode("missing.png")


def test_decode_success_with_mocked_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        raw = "ok"

    class Reader:
        def decode(self, _source):
            return Result()

    class ZXing:
        BarCodeReader = Reader

    monkeypatch.setitem(sys.modules, "zxing", ZXing())
    assert decode("any.png") == "ok"


def test_decode_reports_empty_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    class Reader:
        def decode(self, _source):
            return None

    class ZXing:
        BarCodeReader = Reader

    monkeypatch.setitem(sys.modules, "zxing", ZXing())
    with pytest.raises(RuntimeError, match="no payload"):
        decode("any.png")
