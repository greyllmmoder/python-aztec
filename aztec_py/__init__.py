"""Public package API for aztec-py."""

__version__ = "1.1.0"

from .batch import encode_batch
from .core import (
    AztecCode,
    Latch,
    Misc,
    Mode,
    Shift,
    encoding_to_eci,
    find_optimal_sequence,
    find_suitable_matrix_size,
    get_data_codewords,
    get_config_from_table,
    optimal_sequence_to_bits,
    reed_solomon,
)
from .decode import decode
from .gs1 import GROUP_SEPARATOR, GS1Element, build_gs1_payload
from .presets import AztecPreset, get_preset, list_presets
from .rune import AztecRune

__all__ = [
    'AztecCode',
    'encode_batch',
    'Latch',
    'Misc',
    'Mode',
    'Shift',
    'encoding_to_eci',
    'find_optimal_sequence',
    'find_suitable_matrix_size',
    'get_data_codewords',
    'get_config_from_table',
    'optimal_sequence_to_bits',
    'reed_solomon',
    'AztecRune',
    'decode',
    'GROUP_SEPARATOR',
    'GS1Element',
    'build_gs1_payload',
    'AztecPreset',
    'get_preset',
    'list_presets',
]
