"""CLI entry point for ``aztec`` and ``python -m aztec_py``."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Literal, Sequence

from . import AztecCode, encode_batch, list_presets


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(prog="aztec", description="Generate Aztec code symbols.")
    parser.add_argument("data", nargs="?", help="Payload to encode.")
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
        default=None,
        help="Module size in pixels (default: 1 unless a preset is used).",
    )
    parser.add_argument(
        "--ec",
        type=int,
        default=None,
        help="Error correction percent (default: 23 unless a preset is used).",
    )
    parser.add_argument(
        "--charset",
        default=None,
        help="Character set for string input (default: UTF-8 unless a preset is used).",
    )
    parser.add_argument(
        "--preset",
        choices=list_presets(),
        help="Use a high-volume preset profile for defaults.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path. Required for png output; optional for svg.",
    )
    parser.add_argument(
        "--input",
        help="Bulk input path. When set, payloads are loaded from file instead of positional data.",
    )
    parser.add_argument(
        "--input-format",
        choices=("txt", "csv", "jsonl"),
        default="txt",
        help="Bulk input format for --input (default: txt).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Worker process count for bulk mode (default: 1).",
    )
    parser.add_argument(
        "--out-dir",
        help="Directory for bulk outputs. Required when --input is used.",
    )
    parser.add_argument(
        "--name-template",
        default="code_{index}",
        help="Bulk filename template using {index} (default: code_{index}).",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run a local throughput benchmark and exit.",
    )
    parser.add_argument(
        "--benchmark-count",
        type=int,
        default=1000,
        help="Number of benchmark encodes (default: 1000).",
    )
    parser.add_argument(
        "--benchmark-workers",
        type=int,
        default=1,
        help="Worker process count for benchmark mode (default: 1).",
    )
    return parser


def _load_bulk_payloads(path: Path, input_format: str) -> list[str]:
    payloads: list[str] = []
    if input_format == "txt":
        for line in path.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value:
                payloads.append(value)
        return payloads

    if input_format == "csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            for row in reader:
                if not row:
                    continue
                value = row[0].strip()
                if value:
                    payloads.append(value)
        return payloads

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            obj: Any = json.loads(line)
            if isinstance(obj, str):
                payloads.append(obj)
                continue
            if isinstance(obj, dict):
                payload = obj.get("payload")
                if isinstance(payload, str):
                    payloads.append(payload)
                    continue
            raise ValueError("Each JSONL row must be a string or an object with a string 'payload' field.")
    return payloads


def _build_code_for_payload(payload: str, args: argparse.Namespace) -> AztecCode:
    if args.preset:
        return AztecCode.from_preset(
            payload,
            args.preset,
            ec_percent=args.ec,
            charset=args.charset,
        )
    resolved_ec = 23 if args.ec is None else args.ec
    resolved_charset = "UTF-8" if args.charset is None else args.charset
    return AztecCode(payload, ec_percent=resolved_ec, charset=resolved_charset)


def _resolve_single_code(args: argparse.Namespace) -> AztecCode:
    return _build_code_for_payload(args.data, args)


def _bulk_mode(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    if args.format == "terminal":
        parser.error("--format terminal is not supported with --input; use svg or png.")
    if args.output:
        parser.error("--output is not used with --input; use --out-dir for bulk output.")
    if not args.out_dir:
        parser.error("--out-dir is required when --input is provided.")

    source_path = Path(args.input)
    if not source_path.exists():
        parser.error(f"--input path does not exist: {source_path}")

    try:
        payloads = _load_bulk_payloads(source_path, args.input_format)
    except Exception as exc:
        parser.error(f"Failed to load bulk input: {exc}")

    if not payloads:
        parser.error("Bulk input contains no payload rows.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    module_size = args.module_size
    if module_size is None and args.preset is None:
        module_size = 1
    ec_percent = args.ec
    charset = args.charset
    if args.preset is None and ec_percent is None:
        ec_percent = 23
    if args.preset is None and charset is None:
        charset = "UTF-8"

    output_kind: Literal["svg", "png_bytes"] = "svg" if args.format == "svg" else "png_bytes"
    outputs = encode_batch(
        payloads,
        output=output_kind,
        workers=args.workers,
        preset=args.preset,
        ec_percent=ec_percent,
        charset=charset,
        module_size=module_size,
    )

    extension = "svg" if args.format == "svg" else "png"
    for index, value in enumerate(outputs, start=1):
        try:
            stem = args.name_template.format(index=index)
        except Exception as exc:
            parser.error(f"Invalid --name-template: {exc}")
        if not stem or "/" in stem or "\\" in stem:
            parser.error("Invalid --name-template result; names must be non-empty without path separators.")
        target = out_dir / f"{stem}.{extension}"
        if isinstance(value, bytes):
            target.write_bytes(value)
        else:
            target.write_text(value, encoding="utf-8")
    return 0


def _benchmark_mode(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    if args.input:
        parser.error("--benchmark cannot be combined with --input.")
    if args.output or args.out_dir:
        parser.error("--benchmark does not write output files.")
    if args.benchmark_count < 1:
        parser.error("--benchmark-count must be >= 1.")
    if args.benchmark_workers < 1:
        parser.error("--benchmark-workers must be >= 1.")

    payload = args.data or "M1SMITH/JOHN           EZY74  YULYYZ 0123 100Y001A0001 14A>3180"
    module_size = args.module_size
    if module_size is None and args.preset is None:
        module_size = 1
    ec_percent = args.ec
    charset = args.charset
    if args.preset is None and ec_percent is None:
        ec_percent = 23
    if args.preset is None and charset is None:
        charset = "UTF-8"

    output_kind: Literal["matrix", "svg", "png_bytes"] = "matrix"
    if args.format == "svg":
        output_kind = "svg"
    elif args.format == "png":
        output_kind = "png_bytes"

    start = time.perf_counter()
    if args.benchmark_workers == 1:
        for _ in range(args.benchmark_count):
            code = _build_code_for_payload(payload, args)
            if output_kind == "svg":
                code.svg(module_size=module_size if module_size is not None else 1)
            elif output_kind == "png_bytes":
                code.image(module_size=module_size if module_size is not None else 1)
    else:
        encode_batch(
            [payload] * args.benchmark_count,
            output=output_kind,
            workers=args.benchmark_workers,
            preset=args.preset,
            ec_percent=ec_percent,
            charset=charset,
            module_size=module_size,
        )
    elapsed = time.perf_counter() - start
    throughput = args.benchmark_count / elapsed if elapsed > 0 else 0.0
    avg_ms = (elapsed / args.benchmark_count) * 1000
    sys.stdout.write(f"benchmark_count={args.benchmark_count}\n")
    sys.stdout.write(f"benchmark_workers={args.benchmark_workers}\n")
    sys.stdout.write(f"benchmark_format={args.format}\n")
    sys.stdout.write(f"payload_length={len(payload)}\n")
    sys.stdout.write(f"total_seconds={elapsed:.6f}\n")
    sys.stdout.write(f"avg_ms={avg_ms:.3f}\n")
    sys.stdout.write(f"throughput_per_sec={throughput:.1f}\n")
    return 0


def cli_main(argv: Sequence[str] | None = None) -> int:
    """Run CLI and return process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.benchmark:
        return _benchmark_mode(parser, args)

    if args.input and args.data:
        parser.error("Provide either positional data or --input, not both.")
    if not args.input and not args.data:
        parser.error("Positional data is required unless --input is provided.")

    if args.input:
        return _bulk_mode(parser, args)

    code = _resolve_single_code(args)
    module_size = 1 if args.module_size is None else args.module_size

    if args.format == "terminal":
        code.print_fancy(border=2)
        return 0

    if args.format == "png":
        if not args.output:
            parser.error("--output is required when --format png is selected")
        code.save(args.output, module_size=module_size, format="PNG")
        return 0

    svg = code.svg(module_size=module_size)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file_obj:
            file_obj.write(svg)
    else:
        sys.stdout.write(svg)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli_main())
