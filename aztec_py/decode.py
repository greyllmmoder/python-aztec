"""Optional decode utility — tries zxingcpp (no Java) then falls back to python-zxing."""

from __future__ import annotations

from typing import Any


def decode(source: Any) -> Any:
    """Decode an Aztec symbol from an image path or PIL image.

    Tries the ``zxingcpp`` backend first (pure C++, no Java runtime required).
    Falls back to ``python-zxing`` (requires a JVM) if ``zxingcpp`` is absent.
    Raises :class:`RuntimeError` with install instructions if neither is available.

    Install the fast backend::

        pip install "aztec-py[decode-fast]"   # zxingcpp — no Java needed

    Install the legacy backend::

        pip install "aztec-py[decode]"         # python-zxing — requires Java

    Args:
        source: File path (``str`` / ``pathlib.Path``) or PIL ``Image`` object.

    Returns:
        Decoded payload string.

    Raises:
        RuntimeError: If no decode backend is installed or decode fails.
    """
    # --- fast path: zxingcpp (C++, no JVM) ---
    try:
        import zxingcpp  # type: ignore[import-not-found]

        try:
            import PIL.Image as _PILImage
        except ImportError as exc:
            raise RuntimeError(
                "zxingcpp requires Pillow: pip install 'aztec-py[decode-fast]'"
            ) from exc

        img = source if isinstance(source, _PILImage.Image) else _PILImage.open(source)
        results = zxingcpp.read_barcodes(img)
        if not results:
            raise RuntimeError("Decoder returned no payload.")
        # zxingcpp renders GS1 group separator as "<GS>"; normalise to raw byte.
        return results[0].text.replace("<GS>", "\x1d")
    except ImportError:
        pass  # fall through to python-zxing

    # --- legacy path: python-zxing (requires Java) ---
    try:
        import zxing  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Decode support requires an optional backend.\n"
            "  pip install \"aztec-py[decode-fast]\"  # zxingcpp — no Java needed\n"
            "  pip install \"aztec-py[decode]\"        # python-zxing — requires Java"
        ) from exc

    reader = zxing.BarCodeReader()
    try:
        result = reader.decode(source)
    except Exception as exc:  # pragma: no cover - backend-specific exceptions
        raise RuntimeError(f"Failed to decode Aztec symbol: {exc}") from exc
    if result is None or result.raw is None:
        raise RuntimeError("Decoder returned no payload.")
    return result.raw
