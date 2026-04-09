#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
    aztec_code_generator
    ~~~~~~~~~~~~~~~~~~~~

    Aztec code generator.

    :copyright: (c) 2016-2018 by Dmitry Alimov.
    :license: The MIT License (MIT), see LICENSE for more details.
"""

import math
import numbers
import sys
import array
import codecs
from io import BytesIO
from os import PathLike
from collections import namedtuple
from enum import Enum
from typing import IO, Any, Optional, Union

from aztec_py.presets import get_preset
from aztec_py.renderers.image import image_from_matrix
from aztec_py.renderers.svg import svg_from_matrix

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

Config = namedtuple('Config', ('layers', 'codewords', 'cw_bits', 'bits'))

configs = {
    (15, True): Config(layers=1, codewords=17, cw_bits=6, bits=102),
    (19, False): Config(layers=1, codewords=21, cw_bits=6, bits=126),
    (19, True): Config(layers=2, codewords=40, cw_bits=6, bits=240),
    (23, False): Config(layers=2, codewords=48, cw_bits=6, bits=288),
    (23, True): Config(layers=3, codewords=51, cw_bits=8, bits=408),
    (27, False): Config(layers=3, codewords=60, cw_bits=8, bits=480),
    (27, True): Config(layers=4, codewords=76, cw_bits=8, bits=608),
    (31, False): Config(layers=4, codewords=88, cw_bits=8, bits=704),
    (37, False): Config(layers=5, codewords=120, cw_bits=8, bits=960),
    (41, False): Config(layers=6, codewords=156, cw_bits=8, bits=1248),
    (45, False): Config(layers=7, codewords=196, cw_bits=8, bits=1568),
    (49, False): Config(layers=8, codewords=240, cw_bits=8, bits=1920),
    (53, False): Config(layers=9, codewords=230, cw_bits=10, bits=2300),
    (57, False): Config(layers=10, codewords=272, cw_bits=10, bits=2720),
    (61, False): Config(layers=11, codewords=316, cw_bits=10, bits=3160),
    (67, False): Config(layers=12, codewords=364, cw_bits=10, bits=3640),
    (71, False): Config(layers=13, codewords=416, cw_bits=10, bits=4160),
    (75, False): Config(layers=14, codewords=470, cw_bits=10, bits=4700),
    (79, False): Config(layers=15, codewords=528, cw_bits=10, bits=5280),
    (83, False): Config(layers=16, codewords=588, cw_bits=10, bits=5880),
    (87, False): Config(layers=17, codewords=652, cw_bits=10, bits=6520),
    (91, False): Config(layers=18, codewords=720, cw_bits=10, bits=7200),
    (95, False): Config(layers=19, codewords=790, cw_bits=10, bits=7900),
    (101, False): Config(layers=20, codewords=864, cw_bits=10, bits=8640),
    (105, False): Config(layers=21, codewords=940, cw_bits=10, bits=9400),
    (109, False): Config(layers=22, codewords=1020, cw_bits=10, bits=10200),
    (113, False): Config(layers=23, codewords=920, cw_bits=12, bits=11040),
    (117, False): Config(layers=24, codewords=992, cw_bits=12, bits=11904),
    (121, False): Config(layers=25, codewords=1066, cw_bits=12, bits=12792),
    (125, False): Config(layers=26, codewords=1144, cw_bits=12, bits=13728),
    (131, False): Config(layers=27, codewords=1224, cw_bits=12, bits=14688),
    (135, False): Config(layers=28, codewords=1306, cw_bits=12, bits=15672),
    (139, False): Config(layers=29, codewords=1392, cw_bits=12, bits=16704),
    (143, False): Config(layers=30, codewords=1480, cw_bits=12, bits=17760),
    (147, False): Config(layers=31, codewords=1570, cw_bits=12, bits=18840),
    (151, False): Config(layers=32, codewords=1664, cw_bits=12, bits=19968),
}

encoding_to_eci = {
    'cp437': 0, # also 2
    'iso8859-1': 1, # (also 3) default interpretation, readers should assume if no ECI mark
    'iso8859-2': 4,
    'iso8859-3': 5,
    'iso8859-4': 6,
    'iso8859-5': 7,
    'iso8859-6': 8,
    'iso8859-7': 9,
    'iso8859-8': 10,
    'iso8859-9': 11,
    'iso8859-13': 15,
    'iso8859-14': 16,
    'iso8859-15': 17,
    'iso8859-16': 18,
    'shift_jis': 20,
    'cp1250': 21,
    'cp1251': 22,
    'cp1252': 23,
    'cp1256': 24,
    'utf-16-be': 25, # no BOM
    'utf-8': 26,
    'ascii': 27, # also 170
    'big5': 28,
    'gb18030': 29,
    'euc_kr': 30,
}

polynomials = {
    4: 19,
    6: 67,
    8: 301,
    10: 1033,
    12: 4201,
}

Side = Enum('Side', ('left', 'right', 'bottom', 'top'))

Mode = Enum('Mode', ('UPPER', 'LOWER', 'MIXED', 'PUNCT', 'DIGIT', 'BINARY'))
Latch = Enum('Latch', Mode.__members__)
Shift = Enum('Shift', Mode.__members__)
Misc = Enum('Misc', ('FLG', 'SIZE', 'RESUME'))

code_chars = {
    Mode.UPPER: [Shift.PUNCT] + list(b' ABCDEFGHIJKLMNOPQRSTUVWXYZ') + [Latch.LOWER, Latch.MIXED, Latch.DIGIT, Shift.BINARY],
    Mode.LOWER: [Shift.PUNCT] + list(b' abcdefghijklmnopqrstuvwxyz') + [Shift.UPPER, Latch.MIXED, Latch.DIGIT, Shift.BINARY],
    Mode.MIXED: [Shift.PUNCT] + list(b' \x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x1b\x1c\x1d\x1e\x1f@\\^_`|~\x7f') + [Latch.LOWER, Latch.UPPER, Latch.PUNCT, Shift.BINARY],
    Mode.PUNCT: [Misc.FLG] + list(b'\r') + [b'\r\n', b'. ', b', ', b': '] + list(b'!"#$%&\'()*+,-./:;<=>?[]{}') + [Latch.UPPER],
    Mode.DIGIT: [Shift.PUNCT] + list(b' 0123456789,.') + [Latch.UPPER, Shift.UPPER],
}

punct_2_chars = [pc for pc in code_chars[Mode.PUNCT] if isinstance(pc, bytes)]

E = 99999  # some big number

latch_len = {
    Mode.UPPER: {
        Mode.UPPER: 0, Mode.LOWER: 5, Mode.MIXED: 5, Mode.PUNCT: 10, Mode.DIGIT: 5, Mode.BINARY: 10
    },
    Mode.LOWER: {
        Mode.UPPER: 9, Mode.LOWER: 0, Mode.MIXED: 5, Mode.PUNCT: 10, Mode.DIGIT: 5, Mode.BINARY: 10
    },
    Mode.MIXED: {
        Mode.UPPER: 5, Mode.LOWER: 5, Mode.MIXED: 0, Mode.PUNCT: 5, Mode.DIGIT: 10, Mode.BINARY: 10
    },
    Mode.PUNCT: {
        Mode.UPPER: 5, Mode.LOWER: 10, Mode.MIXED: 10, Mode.PUNCT: 0, Mode.DIGIT: 10, Mode.BINARY: 15
    },
    Mode.DIGIT: {
        Mode.UPPER: 4, Mode.LOWER: 9, Mode.MIXED: 9, Mode.PUNCT: 14, Mode.DIGIT: 0, Mode.BINARY: 14
    },
    Mode.BINARY: {
        Mode.UPPER: 0, Mode.LOWER: 0, Mode.MIXED: 0, Mode.PUNCT: 0, Mode.DIGIT: 0, Mode.BINARY: 0
    },
}

shift_len = {
    (Mode.UPPER, Mode.PUNCT): 5,
    (Mode.LOWER, Mode.UPPER): 5,
    (Mode.LOWER, Mode.PUNCT): 5,
    (Mode.MIXED, Mode.PUNCT): 5,
    (Mode.DIGIT, Mode.UPPER): 4,
    (Mode.DIGIT, Mode.PUNCT): 4,
}

char_size = {
    Mode.UPPER: 5, Mode.LOWER: 5, Mode.MIXED: 5, Mode.PUNCT: 5, Mode.DIGIT: 4, Mode.BINARY: 8,
}

abbr_modes = {m.name[0]:m for m in Mode}


def prod(x: int, y: int, log: dict[int, int], alog: dict[int, int], gf: int) -> int:
    """Multiply two values in the configured Galois field."""
    if not x or not y:
        return 0
    return alog[(log[x] + log[y]) % (gf - 1)]


def reed_solomon(wd: list[int], nd: int, nc: int, gf: int, pp: int) -> None:
    """Calculate Reed-Solomon error correction codewords.

    Algorithm is based on Aztec Code bar code symbology specification from
    GOST-R-ISO-MEK-24778-2010 (Russian)
    Takes ``nd`` data codeword values in ``wd`` and adds on ``nc`` check
    codewords, all within GF(gf) where ``gf`` is a power of 2 and ``pp``
    is the value of its prime modulus polynomial.

    :param wd: data codewords (in/out param)
    :param nd: number of data codewords
    :param nc: number of error correction codewords
    :param gf: Galois Field order
    :param pp: prime modulus polynomial value
    """
    # generate log and anti log tables
    log = {0: 1 - gf}
    alog = {0: 1}
    for i in range(1, gf):
        alog[i] = alog[i - 1] * 2
        if alog[i] >= gf:
            alog[i] ^= pp
        log[alog[i]] = i
    # generate polynomial coeffs
    c = {0: 1}
    for i in range(1, nc + 1):
        c[i] = 0
    for i in range(1, nc + 1):
        c[i] = c[i - 1]
        for j in range(i - 1, 0, -1):
            c[j] = c[j - 1] ^ prod(c[j], alog[i], log, alog, gf)
        c[0] = prod(c[0], alog[i], log, alog, gf)
    # generate codewords
    for i in range(nd, nd + nc):
        wd[i] = 0
    for i in range(nd):
        assert 0 <= wd[i] < gf
        k = wd[nd] ^ wd[i]
        for j in range(nc):
            wd[nd + j] = prod(k, c[nc - j - 1], log, alog, gf)
            if j < nc - 1:
                wd[nd + j] ^= wd[nd + j + 1]


def find_optimal_sequence(data: Union[str, bytes], encoding: Optional[str] = None, gs1: bool = False) -> list[Any]:
    """Find the shortest mode/value sequence needed to encode the payload.

    :param data: string or bytes to encode
    :param encoding: see :py:class:`AztecCode`
    :param gs1: if True, prepend FLG(0) Reader Initialisation character per ISO 24778 §7
    :return: optimal sequence
    """

    # standardize encoding name, ensure that it's valid for ECI, and encode string to bytes
    if encoding:
        encoding = codecs.lookup(encoding).name
        eci = encoding_to_eci[encoding]
    else:
        encoding = 'iso8859-1'
        eci = None
    if isinstance(data, str):
        data = data.encode(encoding)

    back_to = {m: Mode.UPPER for m in Mode}
    cur_len = {m: 0 if m==Mode.UPPER else E for m in Mode}
    cur_seq = {m: [] for m in Mode}
    prev_c = None
    for c in data:
        for x in Mode:
            for y in Mode:
                if cur_len[x] + latch_len[x][y] < cur_len[y]:
                    cur_len[y] = cur_len[x] + latch_len[x][y]
                    cur_seq[y] = cur_seq[x][:]
                    back_to[y] = y
                    if y == Mode.BINARY:
                        # for binary mode use B/S instead of B/L
                        if x in (Mode.PUNCT, Mode.DIGIT):
                            # if changing from punct or digit to binary mode use U/L as intermediate mode
                            # TODO: update for digit
                            back_to[y] = Mode.UPPER
                            cur_seq[y] += [Latch.UPPER, Shift.BINARY, Misc.SIZE]
                        else:
                            back_to[y] = x
                            cur_seq[y] += [Shift.BINARY, Misc.SIZE]
                    elif cur_seq[x]:
                        # if changing from punct or digit mode - use U/L as intermediate mode
                        # TODO: update for digit
                        if x == Mode.DIGIT and y == Mode.PUNCT:
                            cur_seq[y] += [Misc.RESUME, Latch.UPPER, Latch.MIXED, Latch.PUNCT]
                        elif x in (Mode.PUNCT, Mode.DIGIT) and y != Mode.UPPER:
                            cur_seq[y] += [Misc.RESUME, Latch.UPPER, Latch[y.name]]
                        elif x == Mode.LOWER and y == Mode.UPPER:
                            cur_seq[y] += [Latch.DIGIT, Latch.UPPER]
                        elif x in (Mode.UPPER, Mode.LOWER) and y == Mode.PUNCT:
                            cur_seq[y] += [Latch.MIXED, Latch[y.name]]
                        elif x == Mode.MIXED and y != Mode.UPPER:
                            if y == Mode.PUNCT:
                                cur_seq[y] += [Latch.PUNCT]
                                back_to[y] = Mode.PUNCT
                            else:
                                cur_seq[y] += [Latch.UPPER, Latch.DIGIT]
                                back_to[y] = Mode.DIGIT
                            continue
                        elif x == Mode.BINARY:
                            # TODO: review this
                            # Reviewed by jravallec
                            if y == back_to[x]:
                                # when return from binary to previous mode, skip mode change
                                cur_seq[y] += [Misc.RESUME]
                            elif y == Mode.UPPER:
                                if back_to[x] == Mode.LOWER:
                                    cur_seq[y] += [Misc.RESUME, Latch.DIGIT, Latch.UPPER]
                                if back_to[x] == Mode.MIXED:
                                    cur_seq[y] += [Misc.RESUME, Latch.UPPER]
                            elif y == Mode.LOWER:
                                cur_seq[y] += [Misc.RESUME, Latch.LOWER]
                            elif y == Mode.MIXED:
                                cur_seq[y] += [Misc.RESUME, Latch.MIXED]
                            elif y == Mode.PUNCT:
                                if back_to[x] == Mode.MIXED:
                                    cur_seq[y] += [Misc.RESUME, Latch.PUNCT]
                                else:
                                    cur_seq[y] += [Misc.RESUME, Latch.MIXED, Latch.PUNCT]
                            elif y == Mode.DIGIT:
                                if back_to[x] == Mode.MIXED:
                                    cur_seq[y] += [Misc.RESUME, Latch.UPPER, Latch.DIGIT]
                                else:
                                    cur_seq[y] += [Misc.RESUME, Latch.DIGIT]
                        else:
                            cur_seq[y] += [Misc.RESUME, Latch[y.name]]
                    else:
                        # if changing from punct or digit mode - use U/L as intermediate mode
                        # TODO: update for digit
                        if x in (Mode.PUNCT, Mode.DIGIT):
                            cur_seq[y] = [Latch.UPPER, Latch[y.name]]
                        elif x == Mode.LOWER and y == Mode.UPPER:
                            cur_seq[y] = [Latch.DIGIT, Latch.UPPER]
                        elif x in (Mode.BINARY, Mode.UPPER, Mode.LOWER) and y == Mode.PUNCT:
                            cur_seq[y] = [Latch.MIXED, Latch[y.name]]
                        else:
                            cur_seq[y] = [Latch[y.name]]
        next_len = {m:E for m in Mode}
        next_seq = {m:[] for m in Mode}
        possible_modes = [m for m in Mode if m == Mode.BINARY or c in code_chars[m]]
        for x in possible_modes:
            # TODO: review this!
            if back_to[x] == Mode.DIGIT and x == Mode.LOWER:
                cur_seq[x] += [Latch.UPPER, Latch.LOWER]
                cur_len[x] += latch_len[back_to[x]][x]
                back_to[x] = Mode.LOWER
            # add char to current sequence
            if cur_len[x] + char_size[x] < next_len[x]:
                next_len[x] = cur_len[x] + char_size[x]
                next_seq[x] = cur_seq[x] + [c]
            for y in Mode:
                if (y, x) in shift_len and cur_len[y] + shift_len[(y, x)] + char_size[x] < next_len[y]:
                    next_len[y] = cur_len[y] + shift_len[y, x] + char_size[x]
                    next_seq[y] = cur_seq[y] + [Shift[x.name], c]
        # TODO: review this!!!
        if prev_c and bytes((prev_c, c)) in punct_2_chars:
            for x in Mode:
                # Will never StopIteration because we must have one S/L already since prev_c is PUNCT
                last_mode = next(s.value for s in reversed(cur_seq[x]) if isinstance(s, Latch) or isinstance(s, Shift))
                if last_mode == Mode.PUNCT:
                    last_c = cur_seq[x][-1]
                    if isinstance(last_c, int) and bytes((last_c, c)) in punct_2_chars:
                        if x != Mode.MIXED:  # we need to avoid this because it contains '\r', '\n' individually, but not combined
                            if cur_len[x] < next_len[x]:
                                next_len[x] = cur_len[x]
                                next_seq[x] = cur_seq[x][:-1] + [ bytes((last_c, c)) ]
        if len(next_seq[Mode.BINARY]) - 2 == 32:
            next_len[Mode.BINARY] += 11
        cur_len = next_len.copy()
        cur_seq = next_seq.copy()
        prev_c = c
    # sort in ascending order and get shortest sequence
    result_seq = []
    sorted_cur_len = sorted(cur_len, key=cur_len.__getitem__)
    if sorted_cur_len:
        min_length = sorted_cur_len[0]
        result_seq = cur_seq[min_length]
    # update binary sequences' sizes
    sizes = {}
    result_seq_len = len(result_seq)
    reset_pos = result_seq_len - 1
    for i, c in enumerate(reversed(result_seq)):
        if c == Misc.SIZE:
            sizes[i] = reset_pos - (result_seq_len - i - 1)
            reset_pos = result_seq_len - i
        elif c == Misc.RESUME:
            reset_pos = result_seq_len - i - 2
    for size_pos in sizes:
        result_seq[len(result_seq) - size_pos - 1] = sizes[size_pos]
    # remove 'resume' tokens
    result_seq = [x for x in result_seq if x != Misc.RESUME]
    # update binary sequences' extra sizes
    updated_result_seq = []
    is_binary_length = False
    for i, c in enumerate(result_seq):
        if is_binary_length:
            if c > 31:
                updated_result_seq.append(0)
                updated_result_seq.append(c - 31)
            else:
                updated_result_seq.append(c)
            is_binary_length = False
        else:
            updated_result_seq.append(c)

        if c == Shift.BINARY:
            is_binary_length = True

    if eci is not None:
        updated_result_seq = [ Shift.PUNCT, Misc.FLG, len(str(eci)), eci ] + updated_result_seq

    if gs1:
        updated_result_seq = [Shift.PUNCT, Misc.FLG, 0] + updated_result_seq

    return updated_result_seq


def optimal_sequence_to_bits(optimal_sequence: list[Any]) -> str:
    """Convert an optimal sequence to a packed bit string.

    :param optimal_sequence: input optimal sequence
    :return: string with bits
    """
    out_bits = ''
    mode = prev_mode = Mode.UPPER
    shift = False
    sequence = optimal_sequence[:]
    while sequence:
        # read one item from sequence
        ch = sequence.pop(0)
        index = code_chars[mode].index(ch)
        out_bits += bin(index)[2:].zfill(char_size[mode])
        # resume previous mode for shift
        if shift:
            mode = prev_mode
            shift = False
        # get mode from sequence character
        if isinstance(ch, Latch):
            mode = ch.value
        # handle FLG(n)
        elif ch == Misc.FLG:
            if not sequence:
                raise Exception('Expected FLG(n) value')
            flg_n = sequence.pop(0)
            if not isinstance(flg_n, numbers.Number) or not 0 <= flg_n <= 7:
                raise Exception('FLG(n) value must be a number from 0 to 7')
            if flg_n == 7:
                raise Exception('FLG(7) is reserved and currently illegal')

            out_bits += bin(flg_n)[2:].zfill(3)
            if flg_n >= 1:
                # ECI
                if not sequence:
                    raise Exception('Expected FLG({}) to be followed by ECI code'.format(flg_n))
                eci_code = sequence.pop(0)
                if not isinstance(eci_code, numbers.Number) or not 0 <= eci_code < (10**flg_n):
                    raise Exception('Expected FLG({}) ECI code to be a number from 0 to {}'.format(flg_n, (10**flg_n) - 1))
                out_digits = str(eci_code).zfill(flg_n).encode()
                for ch in out_digits:
                    index = code_chars[Mode.DIGIT].index(ch)
                    out_bits += bin(index)[2:].zfill(char_size[Mode.DIGIT])
        # handle binary run
        elif ch == Shift.BINARY:
            if not sequence:
                raise Exception('Expected binary sequence length')
            # followed by a 5 bit length
            seq_len = sequence.pop(0)
            if not isinstance(seq_len, numbers.Number):
                raise Exception('Binary sequence length must be a number')
            out_bits += bin(seq_len)[2:].zfill(5)
            # if length is zero - 11 additional length bits are used for length
            if not seq_len:
                seq_len = sequence.pop(0)
                if not isinstance(seq_len, numbers.Number):
                    raise Exception('Binary sequence length must be a number')
                out_bits += bin(seq_len)[2:].zfill(11)
                seq_len += 31
            for binary_index in range(seq_len):
                ch = sequence.pop(0)
                out_bits += bin(ch)[2:].zfill(char_size[Mode.BINARY])
        # handle other shift
        elif isinstance(ch, Shift):
            mode, prev_mode = ch.value, mode
            shift = True
    return out_bits


def get_data_codewords(bits: str, codeword_size: int) -> list[int]:
    """Get codewords stream from data bits sequence.
    Bit stuffing and padding are used to avoid all-zero and all-ones codewords

    :param bits: input data bits
    :param codeword_size: codeword size in bits
    :return: data codewords
    """
    codewords = []
    sub_bits = ''
    for bit in bits:
        sub_bits += bit
        # if first bits of sub sequence are zeros add 1 as a last bit
        if len(sub_bits) == codeword_size - 1 and sub_bits.find('1') < 0:
            sub_bits += '1'
        # if first bits of sub sequence are ones add 0 as a last bit
        if len(sub_bits) == codeword_size - 1 and sub_bits.find('0') < 0:
            sub_bits += '0'
        # convert bits to decimal int and add to result codewords
        if len(sub_bits) >= codeword_size:
            codewords.append(int(sub_bits, 2))
            sub_bits = ''
    if sub_bits:
        # update and add final bits
        sub_bits = sub_bits.ljust(codeword_size, '1')
        # change final bit to zero if all bits are ones
        if sub_bits.find('0') < 0:
            sub_bits = sub_bits[:-1] + '0'
        codewords.append(int(sub_bits, 2))
    return codewords


def _required_capacity_bits(data_codewords_count: int, codeword_size: int, ec_percent: int) -> int:
    """Calculate total symbol bits needed for stuffed data + EC overhead."""
    stuffed_data_bits = data_codewords_count * codeword_size
    overhead_bits = 3 * codeword_size
    return int(math.ceil((stuffed_data_bits + overhead_bits) * 100.0 / (100 - ec_percent)))


def get_config_from_table(size: int, compact: bool) -> Config:
    """Get config with given size and compactness flag.

    :param size: matrix size
    :param compact: compactness flag
    :return: dict with config
    """
    try:
        return configs[(size, compact)]
    except KeyError:
        raise NotImplementedError('Failed to find config with size and compactness flag')

def find_suitable_matrix_size(
    data: Union[str, bytes],
    ec_percent: int = 23,
    encoding: Optional[str] = None,
    gs1: bool = False,
) -> tuple[int, bool, list[Any]]:
    """Find suitable matrix size.
    Raise an exception if suitable size is not found

    :param data: string or bytes to encode
    :param ec_percent: percentage of symbol capacity for error correction (default 23%)
    :param encoding: see :py:class:`AztecCode`
    :param gs1: if True, account for FLG(0) preamble when sizing the matrix
    :return: (size, compact) tuple
    """
    optimal_sequence = find_optimal_sequence(data, encoding, gs1)
    out_bits = optimal_sequence_to_bits(optimal_sequence)
    for (size, compact) in sorted(configs.keys()):
        config = get_config_from_table(size, compact)
        bits = config.bits
        data_cw_count = len(get_data_codewords(out_bits, config.cw_bits))
        required_bits_count = _required_capacity_bits(data_cw_count, config.cw_bits, ec_percent)
        if required_bits_count < bits:
            return size, compact, optimal_sequence
    raise Exception('Data too big to fit in one Aztec code!')

class AztecCode(object):
    """Generate and render an Aztec Code symbol."""

    @classmethod
    def from_preset(
        cls,
        data: Union[str, bytes],
        preset: str,
        *,
        size: Optional[int] = None,
        compact: Optional[bool] = None,
        ec_percent: Optional[int] = None,
        encoding: Optional[str] = None,
        charset: Optional[str] = None,
        gs1: bool = False,
    ) -> "AztecCode":
        """Build an AztecCode using named preset defaults.

        Explicit values override preset defaults.
        """
        preset_config = get_preset(preset)
        resolved_ec = ec_percent if ec_percent is not None else preset_config.ec_percent
        resolved_encoding = encoding
        resolved_charset = charset
        if resolved_encoding is None and resolved_charset is None:
            resolved_charset = preset_config.charset

        return cls(
            data,
            size=size,
            compact=compact,
            ec_percent=resolved_ec,
            encoding=resolved_encoding,
            charset=resolved_charset,
            gs1=gs1,
        )

    def __init__(
        self,
        data: Union[str, bytes],
        size: Optional[int] = None,
        compact: Optional[bool] = None,
        ec_percent: int = 23,
        encoding: Optional[str] = None,
        charset: Optional[str] = None,
        gs1: bool = False,
    ) -> None:
        """Create Aztec code with given payload and settings.

        Args:
            data: String or bytes to encode.
            size: Fixed matrix size. If omitted, size is auto-selected.
            compact: Compactness flag for fixed-size mode.
            ec_percent: Error correction percentage, 5..95 inclusive.
            encoding: Charset used for string payloads and ECI.
            charset: Alias for ``encoding`` used by the modern API.
            gs1: If True, prepend FLG(0) Reader Initialisation character so
                industrial scanners identify this as a GS1 Aztec symbol
                (ISO 24778 §7 / GS1 General Specifications §5.5.3).

        Raises:
            ValueError: If API arguments are invalid.
            Exception: If payload does not fit in selected matrix size.
        """
        if not data:
            raise ValueError("data must not be empty")
        if not 5 <= ec_percent <= 95:
            raise ValueError(f"ec_percent must be between 5 and 95, got {ec_percent}")
        if charset is not None:
            if encoding is not None and encoding != charset:
                raise ValueError("encoding and charset must match when both are provided")
            encoding = charset
        if isinstance(data, str) and encoding == "":
            raise ValueError("charset must be specified when data is a string")

        self.data = data
        self.encoding = encoding
        self.gs1 = gs1
        self.sequence = None
        self.ec_percent = ec_percent
        if size is not None and compact is not None:
            if (size, compact) in configs:
                self.size, self.compact = size, compact
            else:
                raise Exception(
                    'Given size and compact values (%s, %s) are not found in sizes table!' % (size, compact))
        else:
            self.size, self.compact, self.sequence = find_suitable_matrix_size(self.data, ec_percent, encoding, gs1)
        self.__create_matrix()
        self.__encode_data()

    def __create_matrix(self) -> None:
        """Create an empty Aztec matrix of the selected size."""
        self.matrix = [array.array('B', (0 for jj in range(self.size))) for ii in range(self.size)]

    def save(
        self,
        filename: Union[str, PathLike[str], IO[bytes], IO[str]],
        module_size: int = 2,
        border: int = 0,
        format: Optional[str] = None,
    ) -> None:
        """Save symbol to disk in PNG/SVG/PDF formats.

        Args:
            filename: Destination path or file object.
            module_size: Module size in pixels.
            border: Border width in modules.
            format: Explicit image format override for Pillow.
        """
        target_name = str(filename).lower() if isinstance(filename, (str, PathLike)) else ""
        format_name = (format or "").lower()

        if target_name.endswith(".svg") or format_name == "svg":
            payload = self.svg(module_size=module_size, border=border)
            if hasattr(filename, "write"):
                filename.write(payload)
            else:
                with open(filename, "w", encoding="utf-8") as file_obj:
                    file_obj.write(payload)
            return

        if target_name.endswith(".pdf") or format_name == "pdf":
            payload = self.pdf(module_size=module_size, border=border)
            if hasattr(filename, "write"):
                filename.write(payload)
            else:
                with open(filename, "wb") as file_obj:
                    file_obj.write(payload)
            return

        self.image(module_size, border).save(filename, format=format)

    def image(self, module_size: int = 2, border: int = 0) -> Any:
        """Create a PIL image for this symbol."""
        return image_from_matrix(self.matrix, module_size=module_size, border=border)

    def svg(self, module_size: int = 1, border: int = 1) -> str:
        """Render symbol as SVG text."""
        return svg_from_matrix(self.matrix, module_size=module_size, border=border)

    def pdf(self, module_size: int = 3, border: int = 1) -> bytes:
        """Render symbol into a single-page PDF and return bytes."""
        try:
            from fpdf import FPDF
        except ImportError as exc:
            raise RuntimeError("PDF output requires optional dependency 'fpdf2'") from exc

        image = self.image(module_size=module_size, border=border)
        png_data = BytesIO()
        image.save(png_data, format="PNG")
        png_data.seek(0)

        pdf = FPDF(unit="pt", format=(float(image.width), float(image.height)))
        pdf.add_page()
        pdf.image(png_data, x=0, y=0, w=image.width, h=image.height)
        return bytes(pdf.output())

    def print_out(self, border: int = 0) -> None:
        """Print the Aztec matrix in ASCII."""
        print('\n'.join(' '*(2*border + self.size) for ii in range(border)))
        for line in self.matrix:
            print(' '*border + ''.join(('#' if x else ' ') for x in line) + ' '*border)
        print('\n'.join(' '*(2*border + self.size) for ii in range(border)))

    def print_fancy(self, border: int = 0) -> None:
        """Print the matrix using ANSI + Unicode block characters."""
        for y in range(-border, self.size+border, 2):
            last_half_row = (y==self.size + border - 1)
            ul = '\x1b[40;37;1m' + ('\u2580' if last_half_row else '\u2588')*border
            for x in range(0, self.size):
                a = self.matrix[y][x] if 0 <= y < self.size else None
                b = self.matrix[y+1][x] if -1 <= y < self.size-1 else last_half_row
                ul += ' ' if a and b else '\u2584' if a else '\u2580' if b else '\u2588'
            ul += ('\u2580' if last_half_row else '\u2588')*border + '\x1b[0m'
            print(ul)

    def __add_finder_pattern(self):
        """ Add bulls-eye finder pattern """
        center = self.size // 2
        ring_radius = 5 if self.compact else 7
        for x in range(-ring_radius, ring_radius):
            for y in range(-ring_radius, ring_radius):
                self.matrix[center + y][center + x] = (max(abs(x), abs(y)) + 1) % 2

    def __add_orientation_marks(self):
        """ Add orientation marks to matrix """
        center = self.size // 2
        ring_radius = 5 if self.compact else 7
        # add orientation marks
        # left-top
        self.matrix[center - ring_radius][center - ring_radius] = 1
        self.matrix[center - ring_radius + 1][center - ring_radius] = 1
        self.matrix[center - ring_radius][center - ring_radius + 1] = 1
        # right-top
        self.matrix[center - ring_radius + 0][center + ring_radius + 0] = 1
        self.matrix[center - ring_radius + 1][center + ring_radius + 0] = 1
        # right-down
        self.matrix[center + ring_radius - 1][center + ring_radius + 0] = 1

    def __add_reference_grid(self):
        """ Add reference grid to matrix """
        if self.compact:
            return
        center = self.size // 2
        ring_radius = 5 if self.compact else 7
        for x in range(-center, center + 1):
            for y in range(-center, center + 1):
                # skip finder pattern
                if -ring_radius <= x <= ring_radius and -ring_radius <= y <= ring_radius:
                    continue
                # set pixel
                if x % 16 == 0 or y % 16 == 0:
                    self.matrix[center + y][center + x] = (x + y + 1) % 2

    def __get_mode_message(self, layers_count, data_cw_count):
        """ Get mode message

        :param layers_count: number of layers
        :param data_cw_count: number of data codewords
        :return: mode message codewords
        """
        if self.compact:
            # for compact mode - 2 bits with layers count and 6 bits with data codewords count
            mode_word = '{0:02b}{1:06b}'.format(layers_count - 1, data_cw_count - 1)
            # two 4 bits initial codewords with 5 Reed-Solomon check codewords
            init_codewords = [int(mode_word[i:i + 4], 2) for i in range(0, 8, 4)]
            total_cw_count = 7
        else:
            # for full mode - 5 bits with layers count and 11 bits with data codewords count
            mode_word = '{0:05b}{1:011b}'.format(layers_count - 1, data_cw_count - 1)
            # four 4 bits initial codewords with 6 Reed-Solomon check codewords
            init_codewords = [int(mode_word[i:i + 4], 2) for i in range(0, 16, 4)]
            total_cw_count = 10
        # fill Reed-Solomon check codewords with zeros
        init_cw_count = len(init_codewords)
        codewords = (init_codewords + [0] * (total_cw_count - init_cw_count))[:total_cw_count]
        # update Reed-Solomon check codewords using GF(16)
        reed_solomon(codewords, init_cw_count, total_cw_count - init_cw_count, 16, polynomials[4])
        return codewords

    def __add_mode_info(self, data_cw_count):
        """ Add mode info to matrix

        :param data_cw_count: number of data codewords.
        """
        config = get_config_from_table(self.size, self.compact)
        layers_count = config.layers
        mode_data_values = self.__get_mode_message(layers_count, data_cw_count)
        mode_data_bits = ''.join('{0:04b}'.format(v) for v in mode_data_values)

        center = self.size // 2
        ring_radius = 5 if self.compact else 7
        side_size = 7 if self.compact else 11
        bits_stream = StringIO(mode_data_bits)
        x = 0
        y = 0
        index = 0
        while True:
            # for full mode take a reference grid into account
            if not self.compact:
                if (index % side_size) == 5:
                    index += 1
                    continue
            # read one bit
            bit = bits_stream.read(1)
            if not bit:
                break
            if 0 <= index < side_size:
                # top
                x = index + 2 - ring_radius
                y = -ring_radius
            elif side_size <= index < side_size * 2:
                # right
                x = ring_radius
                y = index % side_size + 2 - ring_radius
            elif side_size * 2 <= index < side_size * 3:
                # bottom
                x = ring_radius - index % side_size - 2
                y = ring_radius
            elif side_size * 3 <= index < side_size * 4:
                # left
                x = -ring_radius
                y = ring_radius - index % side_size - 2
            # set pixel
            self.matrix[center + y][center + x] = (bit == '1')
            index += 1

    def __add_data(self, data, encoding):
        """ Add data to encode to the matrix

        :param data: data to encode
        :param encoding: see :py:class:`AztecCode`
        :return: number of data codewords
        """
        if not self.sequence:
            self.sequence = find_optimal_sequence(data, encoding, self.gs1)
        out_bits = optimal_sequence_to_bits(self.sequence)
        config = get_config_from_table(self.size, self.compact)
        layers_count = config.layers
        cw_count = config.codewords
        cw_bits = config.cw_bits
        bits = config.bits

        data_codewords = get_data_codewords(out_bits, cw_bits)
        required_bits_count = _required_capacity_bits(len(data_codewords), cw_bits, self.ec_percent)
        if required_bits_count > bits or len(data_codewords) > cw_count:
            raise Exception('Data too big to fit in Aztec code with current size!')

        # add Reed-Solomon codewords to init data codewords
        data_cw_count = len(data_codewords)
        codewords = (data_codewords + [0] * (cw_count - data_cw_count))[:cw_count]
        reed_solomon(codewords, data_cw_count, cw_count - data_cw_count, 2 ** cw_bits, polynomials[cw_bits])

        center = self.size // 2
        ring_radius = 5 if self.compact else 7

        num = 2
        side = Side.top
        layer_index = 0
        pos_x = center - ring_radius
        pos_y = center - ring_radius - 1
        full_bits = ''.join(bin(cw)[2:].zfill(cw_bits) for cw in codewords)[::-1]
        for i in range(0, len(full_bits), 2):
            num += 1
            max_num = ring_radius * 2 + layer_index * 4 + (4 if self.compact else 3)
            bits_pair = [(bit == '1') for bit in full_bits[i:i + 2]]
            if layer_index >= layers_count:
                raise Exception('Maximum layer count for current size is exceeded!')
            if side == Side.top:
                # move right
                dy0 = 1 if not self.compact and (center - pos_y) % 16 == 0 else 0
                dy1 = 2 if not self.compact and (center - pos_y + 1) % 16 == 0 else 1
                self.matrix[pos_y - dy0][pos_x] = bits_pair[0]
                self.matrix[pos_y - dy1][pos_x] = bits_pair[1]
                pos_x += 1
                if num > max_num:
                    num = 2
                    side = Side.right
                    pos_x -= 1
                    pos_y += 1
                # skip reference grid
                if not self.compact and (center - pos_x) % 16 == 0:
                    pos_x += 1
                if not self.compact and (center - pos_y) % 16 == 0:
                    pos_y += 1
            elif side == Side.right:
                # move down
                dx0 = 1 if not self.compact and (center - pos_x) % 16 == 0 else 0
                dx1 = 2 if not self.compact and (center - pos_x + 1) % 16 == 0 else 1
                self.matrix[pos_y][pos_x - dx0] = bits_pair[1]
                self.matrix[pos_y][pos_x - dx1] = bits_pair[0]
                pos_y += 1
                if num > max_num:
                    num = 2
                    side = Side.bottom
                    pos_x -= 2
                    if not self.compact and (center - pos_x - 1) % 16 == 0:
                        pos_x -= 1
                    pos_y -= 1
                # skip reference grid
                if not self.compact and (center - pos_y) % 16 == 0:
                    pos_y += 1
                if not self.compact and (center - pos_x) % 16 == 0:
                    pos_x -= 1
            elif side == Side.bottom:
                # move left
                dy0 = 1 if not self.compact and (center - pos_y) % 16 == 0 else 0
                dy1 = 2 if not self.compact and (center - pos_y + 1) % 16 == 0 else 1
                self.matrix[pos_y - dy0][pos_x] = bits_pair[1]
                self.matrix[pos_y - dy1][pos_x] = bits_pair[0]
                pos_x -= 1
                if num > max_num:
                    num = 2
                    side = Side.left
                    pos_x += 1
                    pos_y -= 2
                    if not self.compact and (center - pos_y - 1) % 16 == 0:
                        pos_y -= 1
                # skip reference grid
                if not self.compact and (center - pos_x) % 16 == 0:
                    pos_x -= 1
                if not self.compact and (center - pos_y) % 16 == 0:
                    pos_y -= 1
            elif side == Side.left:
                # move up
                dx0 = 1 if not self.compact and (center - pos_x) % 16 == 0 else 0
                dx1 = 2 if not self.compact and (center - pos_x - 1) % 16 == 0 else 1
                self.matrix[pos_y][pos_x + dx1] = bits_pair[0]
                self.matrix[pos_y][pos_x + dx0] = bits_pair[1]
                pos_y -= 1
                if num > max_num:
                    num = 2
                    side = Side.top
                    layer_index += 1
                # skip reference grid
                if not self.compact and (center - pos_y) % 16 == 0:
                    pos_y -= 1
        return data_cw_count

    def __encode_data(self):
        """ Encode data """
        self.__add_finder_pattern()
        self.__add_orientation_marks()
        self.__add_reference_grid()
        data_cw_count = self.__add_data(self.data, self.encoding)
        self.__add_mode_info(data_cw_count)


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("usage: {} STRING_TO_ENCODE [IMAGE_FILE]".format(argv[0]))
        print("  Generate a 2D Aztec barcode and print it, or save to a file.")
        return 1
    data = argv[1]
    aztec_code = AztecCode(data)
    print('Aztec Code info: {0}x{0} {1}'.format(aztec_code.size, '(compact)' if aztec_code.compact else ''))
    if len(sys.argv) == 3:
        aztec_code.save(argv[2], module_size=5)
    else:
        aztec_code.print_fancy(border=2)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
