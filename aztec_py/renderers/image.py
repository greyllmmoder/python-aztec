"""Pillow-based image renderer."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None  # type: ignore[assignment]
    missing_pil = sys.exc_info()


def image_from_matrix(
    matrix: Sequence[Sequence[object]],
    module_size: int = 2,
    border: int = 0,
) -> Any:
    """Render matrix to a PIL monochrome image."""
    if ImageDraw is None:
        exc = missing_pil[0](missing_pil[1])
        exc.__traceback__ = missing_pil[2]
        raise exc

    size = len(matrix)
    image = Image.new('1', ((size + 2 * border) * module_size, (size + 2 * border) * module_size), 1)
    image_draw = ImageDraw.Draw(image)
    for y in range(size):
        for x in range(size):
            image_draw.rectangle(
                (
                    (x + border) * module_size,
                    (y + border) * module_size,
                    (x + border + 1) * module_size,
                    (y + border + 1) * module_size,
                ),
                fill=not matrix[y][x],
            )
    return image
