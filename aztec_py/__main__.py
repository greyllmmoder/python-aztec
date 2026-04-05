"""CLI entry point for ``aztec`` and ``python -m aztec_py``."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from . import AztecCode


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(prog="aztec", description="Generate Aztec code symbols.")
    parser.add_argument("data", help="Payload to encode.")
    parser.add_argument(
        "-f",
        "--format",
        choices=("svg", "png", "terminal"),
        default="terminal",
        help="Output format (default: terminal).",
    )
    parser.add_argument(
        "-m",
        "--module-size",
        type=int,
        default=1,
        help="Module size in pixels (default: 1).",
    )
    parser.add_argument("--ec", type=int, default=23, help="Error correction percent (default: 23).")
    parser.add_argument(
        "--charset",
        default="UTF-8",
        help="Character set for string input (default: UTF-8).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path. Required for png output; optional for svg.",
    )
    return parser


def cli_main(argv: Sequence[str] | None = None) -> int:
    """Run CLI and return process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    code = AztecCode(args.data, ec_percent=args.ec, charset=args.charset)
    if args.format == "terminal":
        code.print_fancy(border=2)
        return 0

    if args.format == "png":
        if not args.output:
            parser.error("--output is required when --format png is selected")
        code.save(args.output, module_size=args.module_size, format="PNG")
        return 0

    svg = code.svg(module_size=args.module_size)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file_obj:
            file_obj.write(svg)
    else:
        sys.stdout.write(svg)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli_main())
