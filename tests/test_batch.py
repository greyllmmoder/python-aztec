"""Batch API tests."""

from __future__ import annotations

import pytest

from aztec_py import encode_batch


def test_encode_batch_empty_payloads() -> None:
    assert encode_batch([]) == []


def test_encode_batch_matrix_output() -> None:
    outputs = encode_batch(["HELLO", "WORLD"], output="matrix")
    assert len(outputs) == 2
    for matrix in outputs:
        assert matrix
        assert len(matrix) == len(matrix[0])


def test_encode_batch_svg_output() -> None:
    outputs = encode_batch(["HELLO"], output="svg", preset="boarding_pass", module_size=2)
    assert len(outputs) == 1
    assert outputs[0].startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert 'stroke-width="2"' in outputs[0]


def test_encode_batch_png_bytes_output() -> None:
    outputs = encode_batch(["HELLO"], output="png_bytes")
    assert len(outputs) == 1
    assert outputs[0].startswith(b"\x89PNG\r\n\x1a\n")


def test_encode_batch_preserves_order_across_workers() -> None:
    payloads = ["HELLO", "WORLD", "AZTEC", "BATCH", "ORDER"]
    single = encode_batch(payloads, output="svg", workers=1, module_size=2, border=1)
    parallel = encode_batch(payloads, output="svg", workers=2, module_size=2, border=1)
    assert parallel == single


def test_encode_batch_validates_arguments() -> None:
    with pytest.raises(ValueError, match="workers must be >= 1"):
        encode_batch(["HELLO"], workers=0)
    with pytest.raises(ValueError, match="chunksize must be >= 1"):
        encode_batch(["HELLO"], chunksize=0)
    with pytest.raises(ValueError, match="Unsupported output"):
        encode_batch(["HELLO"], output="pdf_bytes")  # type: ignore[arg-type]

