"""Thin-module re-export tests."""

from aztec_py.error_correction import polynomials, reed_solomon
from aztec_py.matrix import get_config_from_table


def test_matrix_module_reexport() -> None:
    cfg = get_config_from_table(15, True)
    assert cfg.layers == 1


def test_error_correction_module_reexport() -> None:
    data = [0, 9] + [0, 0, 0, 0, 0]
    reed_solomon(data, 2, 5, 16, polynomials[4])
    assert len(data) == 7
