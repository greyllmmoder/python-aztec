"""Property-based tests for payload robustness."""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

from aztec_py import AztecCode


@given(st.binary(min_size=1, max_size=500))
@settings(max_examples=100)
def test_encode_arbitrary_bytes(data: bytes) -> None:
    code = AztecCode(data)
    assert code.size > 0


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1, max_size=300))
@settings(max_examples=100)
def test_encode_arbitrary_text(text: str) -> None:
    code = AztecCode(text, charset="utf-8")
    assert code.size > 0
