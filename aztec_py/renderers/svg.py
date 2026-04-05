"""SVG renderer adapted from upstream PR #6."""

from __future__ import annotations

from collections.abc import Callable, Sequence


class SvgFactory:
    """Build and save an SVG representation of an Aztec matrix."""

    def __init__(self, data: str) -> None:
        self.svg_str = data

    @staticmethod
    def create_svg(
        matrix: Sequence[Sequence[object]],
        border: int = 1,
        module_size: int = 1,
        matching_fn: Callable[[object], bool] = bool,
    ) -> "SvgFactory":
        """Create SVG for a matrix.

        Args:
            matrix: Two-dimensional matrix where truthy values are dark modules.
            border: Border in modules.
            module_size: Pixel size per module.
            matching_fn: Predicate used to detect dark modules.

        Returns:
            SvgFactory containing SVG content.
        """
        path_data: list[str] = []
        for y, line in enumerate(matrix):
            run_length = 0
            run_start: int | None = None
            for x, cell in enumerate(line):
                if matching_fn(cell):
                    run_length += 1
                    if run_start is None:
                        run_start = x
                next_is_dark = x + 1 < len(line) and matching_fn(line[x + 1])
                if run_start is not None and not next_is_dark:
                    x0 = (run_start + border) * module_size
                    y0 = (y + border) * module_size
                    width = run_length * module_size
                    path_data.append(f"M{x0} {y0} h{width}")
                    run_length = 0
                    run_start = None

        size = (len(matrix[0]) + (2 * border)) * module_size
        data = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<rect x="0" y="0" width="{size}" height="{size}" fill="white"/>'
            f'<path d="{" ".join(path_data)} Z" stroke="black" stroke-width="{module_size}" '
            'style="transform:translateY(0.5px);" />'
            "</svg>"
        )
        return SvgFactory(data)

    def save(self, filename: str) -> None:
        """Save SVG output to disk."""
        with open(filename, "w", encoding="utf-8") as file_obj:
            file_obj.write(self.svg_str)


def svg_from_matrix(
    matrix: Sequence[Sequence[object]],
    module_size: int = 1,
    border: int = 1,
) -> str:
    """Render matrix to SVG text.

    Args:
        matrix: Two-dimensional matrix where truthy values are dark modules.
        module_size: Pixel size per module.
        border: Border in modules.

    Returns:
        SVG payload as UTF-8 text.
    """
    return SvgFactory.create_svg(matrix, border=border, module_size=module_size).svg_str
