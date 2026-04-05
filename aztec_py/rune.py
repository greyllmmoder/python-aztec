"""Aztec Rune support."""

from __future__ import annotations

from io import BytesIO
from os import PathLike
from typing import Any

from aztec_py.renderers.image import image_from_matrix
from aztec_py.renderers.svg import svg_from_matrix


def _crc5(value: int) -> int:
    """Compute a small checksum for rune payload placement."""
    poly = 0b100101
    reg = value << 5
    for bit in range(7, -1, -1):
        if reg & (1 << (bit + 5)):
            reg ^= poly << bit
    return reg & 0b11111


class AztecRune:
    """Generate an 11x11 Aztec Rune for integer values 0..255."""

    size = 11

    def __init__(self, value: int) -> None:
        if not 0 <= value <= 255:
            raise ValueError(f"AztecRune value must be between 0 and 255, got {value}")
        self.value = value
        self.matrix = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self._build()

    def _build(self) -> None:
        center = self.size // 2
        # Compact finder pattern rings.
        for y in range(self.size):
            for x in range(self.size):
                ring = max(abs(x - center), abs(y - center))
                if ring in (0, 1, 3, 5):
                    self.matrix[y][x] = 1

        # Orientation marks (same positions as compact Aztec markers where possible).
        self.matrix[0][0] = 1
        self.matrix[1][0] = 1
        self.matrix[0][1] = 1
        self.matrix[0][10] = 1
        self.matrix[1][10] = 1
        self.matrix[9][10] = 1

        payload = f"{self.value:08b}"
        check = f"{_crc5(self.value):05b}"
        bits = payload + check + payload[::-1] + check[::-1]

        perimeter: list[tuple[int, int]] = []
        perimeter.extend((x, 1) for x in range(1, 10))
        perimeter.extend((9, y) for y in range(2, 10))
        perimeter.extend((x, 9) for x in range(8, 0, -1))
        perimeter.extend((1, y) for y in range(8, 1, -1))

        for bit, (x, y) in zip(bits, perimeter):
            self.matrix[y][x] = 1 if bit == "1" else 0

    def image(self, module_size: int = 2, border: int = 1) -> Any:
        """Render the rune as a PIL image."""
        return image_from_matrix(self.matrix, module_size=module_size, border=border)

    def svg(self, module_size: int = 1, border: int = 1) -> str:
        """Render the rune as SVG text."""
        return svg_from_matrix(self.matrix, module_size=module_size, border=border)

    def save(
        self,
        filename: Any,
        module_size: int = 2,
        border: int = 1,
        format: str | None = None,
    ) -> None:
        """Save rune as PNG, SVG, or PDF based on extension/format."""
        target_name = str(filename).lower() if isinstance(filename, (str, PathLike)) else ""
        format_name = (format or "").lower()

        if target_name.endswith(".svg") or format_name == "svg":
            svg_payload = self.svg(module_size=module_size, border=border)
            if isinstance(filename, (str, PathLike)):
                with open(filename, "w", encoding="utf-8") as file_obj:
                    file_obj.write(svg_payload)
            else:
                filename.write(svg_payload)
            return

        if target_name.endswith(".pdf") or format_name == "pdf":
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
            pdf_payload = bytes(pdf.output())
            if isinstance(filename, (str, PathLike)):
                with open(filename, "wb") as file_obj:
                    file_obj.write(pdf_payload)
            else:
                filename.write(pdf_payload)
            return

        self.image(module_size=module_size, border=border).save(filename, format=format)
