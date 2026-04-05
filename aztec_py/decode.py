"""Optional decode utility backed by python-zxing."""

from __future__ import annotations

from typing import Any


def decode(source: Any) -> Any:
    """Decode an Aztec symbol from an image path or PIL image.

    Args:
        source: File path, file object, or PIL image supported by ``python-zxing``.

    Returns:
        Decoded payload (`str` or `bytes` depending on the decoder/runtime).

    Raises:
        RuntimeError: If optional decode dependencies are missing or decode fails.
    """
    try:
        import zxing  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Decode support requires optional dependency 'zxing' and a Java runtime."
        ) from exc

    reader = zxing.BarCodeReader()
    try:
        result = reader.decode(source)
    except Exception as exc:  # pragma: no cover - backend-specific exceptions
        raise RuntimeError(f"Failed to decode Aztec symbol: {exc}") from exc
    if result is None or result.raw is None:
        raise RuntimeError("Decoder returned no payload.")
    return result.raw
