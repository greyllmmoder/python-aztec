#!/usr/bin/env python3
"""Run compatibility fixtures across encode/decode matrix checks."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aztec_py import AztecCode  # noqa: E402
from aztec_py.compat import CompatCase, load_compat_cases  # noqa: E402
from aztec_py.decode import decode as decode_symbol  # noqa: E402


def _preview(payload: str | bytes) -> str:
    if isinstance(payload, bytes):
        return f"bytes[{len(payload)}]"
    preview = payload.replace("\x1d", "<GS>")
    if len(preview) > 48:
        preview = f"{preview[:45]}..."
    return preview


def _decode_backend_unavailable(message: str) -> bool:
    lower = message.lower()
    return (
        "optional dependency 'zxing'" in lower
        or "java runtime" in lower
        or "java" in lower and "failed to decode" in lower
        or "optional backend" in lower  # zxingcpp-first fallback message
    )


def _matches_expected(decoded: object, expected: str | bytes) -> bool:
    if decoded == expected:
        return True

    if isinstance(expected, str) and isinstance(decoded, bytes):
        try:
            return decoded.decode("utf-8") == expected
        except UnicodeDecodeError:
            return False

    if isinstance(expected, bytes) and isinstance(decoded, str):
        try:
            return decoded.encode("iso-8859-1") == expected
        except UnicodeEncodeError:
            return False

    return False


def _evaluate_case(case: CompatCase, module_size: int, strict_decode: bool) -> tuple[bool, str, str, str]:
    try:
        with NamedTemporaryFile(suffix=".png") as image_file:
            aztec = AztecCode(case.payload, ec_percent=case.ec_percent, charset=case.charset)
            aztec.save(image_file.name, module_size=module_size)

            decode_state = "skip"
            note = "decode not required"
            if case.decode_expected:
                try:
                    decoded = decode_symbol(image_file.name)
                except RuntimeError as exc:
                    message = str(exc)
                    if _decode_backend_unavailable(message):
                        if strict_decode:
                            return False, "pass", "fail", f"decode backend unavailable: {message}"
                        return True, "pass", "skip", f"decode backend unavailable: {message}"
                    return False, "pass", "fail", message

                if _matches_expected(decoded, case.payload):
                    decode_state = "pass"
                    note = "decoded payload matches"
                else:
                    return (
                        False,
                        "pass",
                        "fail",
                        f"decode mismatch for payload type {type(case.payload).__name__}",
                    )

            return True, "pass", decode_state, note
    except Exception as exc:  # pragma: no cover - guard for script use
        return False, "fail", "skip", str(exc)


def _render_markdown(results: list[dict[str, str]]) -> str:
    lines = [
        "# Decoder Compatibility Matrix",
        "",
        "| Case | Payload | Encode | Decode | Notes |",
        "|---|---|---|---|---|",
    ]
    for row in results:
        lines.append(
            "| {case} | {payload} | {encode} | {decode} | {note} |".format(
                case=row["case"],
                payload=row["payload"],
                encode=row["encode"],
                decode=row["decode"],
                note=row["note"].replace("|", "\\|"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run production compatibility fixtures.")
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("tests/compat/fixtures.json"),
        help="Path to compatibility fixture file.",
    )
    parser.add_argument(
        "--module-size",
        type=int,
        default=5,
        help="Module size used for generated PNG files.",
    )
    parser.add_argument(
        "--strict-decode",
        action="store_true",
        help="Fail when decode backend is unavailable for decode-expected cases.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("compat_matrix_report.md"),
        help="Output path for markdown report.",
    )
    args = parser.parse_args()

    cases = load_compat_cases(args.fixtures)

    success = True
    rows: list[dict[str, str]] = []
    for case in cases:
        case_ok, encode_state, decode_state, note = _evaluate_case(
            case,
            module_size=args.module_size,
            strict_decode=args.strict_decode,
        )
        success = success and case_ok
        rows.append(
            {
                "case": case.case_id,
                "payload": _preview(case.payload),
                "encode": encode_state,
                "decode": decode_state,
                "note": note,
            }
        )

    report = _render_markdown(rows)
    args.report.write_text(report, encoding="utf-8")
    print(report)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
