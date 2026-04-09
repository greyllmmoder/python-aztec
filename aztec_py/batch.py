"""Batch encoding helpers for high-volume issuance flows."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from io import BytesIO
from itertools import repeat
from typing import Any, Iterable, Literal, Union

from .core import AztecCode
from .presets import get_preset

@dataclass(frozen=True)
class _BatchOptions:
    output: Literal["matrix", "svg", "png_bytes"]
    preset: str | None
    ec_percent: int | None
    encoding: str | None
    charset: str | None
    module_size: int | None
    border: int | None


def _build_code(payload: Union[str, bytes], options: _BatchOptions) -> AztecCode:
    kwargs: dict[str, Any] = {}
    if options.ec_percent is not None:
        kwargs["ec_percent"] = options.ec_percent
    if options.encoding is not None:
        kwargs["encoding"] = options.encoding
    if options.charset is not None:
        kwargs["charset"] = options.charset

    if options.preset is not None:
        return AztecCode.from_preset(payload, options.preset, **kwargs)
    return AztecCode(payload, **kwargs)


def _render_output(code: AztecCode, options: _BatchOptions) -> Any:
    if options.output == "matrix":
        return code.matrix

    if options.output == "svg":
        module_size = 1 if options.module_size is None else options.module_size
        border = 1 if options.border is None else options.border
        return code.svg(module_size=module_size, border=border)

    module_size = 2 if options.module_size is None else options.module_size
    border = 0 if options.border is None else options.border
    image = code.image(module_size=module_size, border=border)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _encode_worker(entry: tuple[int, Union[str, bytes]], options: _BatchOptions) -> tuple[int, Any]:
    index, payload = entry
    code = _build_code(payload, options)
    return index, _render_output(code, options)


def encode_batch(
    payloads: Iterable[Union[str, bytes]],
    *,
    output: Literal["matrix", "svg", "png_bytes"] = "matrix",
    workers: int = 1,
    chunksize: int = 50,
    preset: str | None = None,
    ec_percent: int | None = None,
    encoding: str | None = None,
    charset: str | None = None,
    module_size: int | None = None,
    border: int | None = None,
) -> list[Any]:
    """Encode many payloads with stable ordering and optional multiprocessing.

    Args:
        payloads: Iterable of payloads (`str` or `bytes`).
        output: Output kind: `matrix`, `svg`, or `png_bytes`.
        workers: Number of worker processes. Use `1` for local single-process mode.
        chunksize: Chunk size used by process pool mapping.
        preset: Optional preset profile name.
        ec_percent: Optional override for error correction percentage.
        encoding: Optional explicit encoding.
        charset: Optional explicit charset alias.
        module_size: Optional renderer module size for `svg`/`png_bytes`.
        border: Optional renderer border for `svg`/`png_bytes`.

    Returns:
        Encoded outputs in the same order as input payloads.
    """
    if workers < 1:
        raise ValueError(f"workers must be >= 1, got {workers}")
    if chunksize < 1:
        raise ValueError(f"chunksize must be >= 1, got {chunksize}")
    if output not in ("matrix", "svg", "png_bytes"):
        raise ValueError(f"Unsupported output '{output}'")

    resolved_module_size = module_size
    resolved_border = border
    if preset is not None:
        preset_config = get_preset(preset)
        if resolved_module_size is None:
            resolved_module_size = preset_config.module_size
        if resolved_border is None:
            resolved_border = preset_config.border

    items = list(payloads)
    if not items:
        return []

    options = _BatchOptions(
        output=output,
        preset=preset,
        ec_percent=ec_percent,
        encoding=encoding,
        charset=charset,
        module_size=resolved_module_size,
        border=resolved_border,
    )

    if workers == 1:
        return [_encode_worker((index, payload), options)[1] for index, payload in enumerate(items)]

    ordered: list[Any] = [None] * len(items)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for index, value in pool.map(_encode_worker, enumerate(items), repeat(options), chunksize=chunksize):
            ordered[index] = value
    return ordered
