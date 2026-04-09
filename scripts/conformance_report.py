#!/usr/bin/env python3
"""Generate audit-ready conformance evidence for aztec-py."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import NamedTemporaryFile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aztec_py import AztecCode  # noqa: E402
from aztec_py.compat import CompatCase, load_compat_cases  # noqa: E402
from aztec_py.decode import decode as decode_symbol  # noqa: E402


DEFAULT_FIXTURES = Path("tests/compat/fixtures.json")
DEFAULT_TRACEABILITY = Path("docs/ISO_IEC_24778_TRACEABILITY.md")


@dataclass(frozen=True)
class CaseOutcome:
    """Result row for a compatibility case."""

    case: str
    payload: str
    encode: str
    decode: str
    note: str


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


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except Exception:  # pragma: no cover - best effort
        return "unknown"


def _run_case(case: CompatCase, module_size: int, strict_decode: bool) -> tuple[bool, CaseOutcome]:
    try:
        with NamedTemporaryFile(suffix=".png") as image_file:
            AztecCode(case.payload, ec_percent=case.ec_percent, charset=case.charset).save(
                image_file.name,
                module_size=module_size,
            )

            if not case.decode_expected:
                return True, CaseOutcome(
                    case=case.case_id,
                    payload=_preview(case.payload),
                    encode="pass",
                    decode="skip",
                    note="decode not required",
                )

            try:
                decoded = decode_symbol(image_file.name)
            except RuntimeError as exc:
                message = str(exc)
                if _decode_backend_unavailable(message):
                    if strict_decode:
                        return False, CaseOutcome(
                            case=case.case_id,
                            payload=_preview(case.payload),
                            encode="pass",
                            decode="fail",
                            note=f"decode backend unavailable: {message}",
                        )
                    return True, CaseOutcome(
                        case=case.case_id,
                        payload=_preview(case.payload),
                        encode="pass",
                        decode="skip",
                        note=f"decode backend unavailable: {message}",
                    )
                return False, CaseOutcome(
                    case=case.case_id,
                    payload=_preview(case.payload),
                    encode="pass",
                    decode="fail",
                    note=message,
                )

            if _matches_expected(decoded, case.payload):
                return True, CaseOutcome(
                    case=case.case_id,
                    payload=_preview(case.payload),
                    encode="pass",
                    decode="pass",
                    note="decoded payload matches",
                )

            return False, CaseOutcome(
                case=case.case_id,
                payload=_preview(case.payload),
                encode="pass",
                decode="fail",
                note=f"decode mismatch for payload type {type(case.payload).__name__}",
            )
    except Exception as exc:  # pragma: no cover - guard for script use
        return False, CaseOutcome(
            case=case.case_id,
            payload=_preview(case.payload),
            encode="fail",
            decode="skip",
            note=str(exc),
        )


def _run_decoder_matrix(
    fixtures: Path,
    module_size: int,
    strict_decode: bool,
    report_path: Path,
) -> tuple[int, str]:
    command = [
        sys.executable,
        "scripts/decoder_matrix.py",
        "--fixtures",
        str(fixtures),
        "--module-size",
        str(module_size),
        "--report",
        str(report_path),
    ]
    if strict_decode:
        command.append("--strict-decode")

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return 0, "decoder matrix generated"

    combined = (result.stdout + "\n" + result.stderr).strip().splitlines()
    tail = combined[-3:] if combined else ["decoder matrix failed with no output"]
    return result.returncode, " | ".join(tail)


def _markdown_table_row(outcome: CaseOutcome) -> str:
    return "| {case} | {payload} | {encode} | {decode} | {note} |".format(
        case=outcome.case,
        payload=outcome.payload.replace("|", "\\|"),
        encode=outcome.encode,
        decode=outcome.decode,
        note=outcome.note.replace("|", "\\|"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate conformance evidence report.")
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=DEFAULT_FIXTURES,
        help="Path to compatibility fixture JSON.",
    )
    parser.add_argument(
        "--module-size",
        type=int,
        default=5,
        help="Module size for generated symbol images.",
    )
    parser.add_argument(
        "--strict-decode",
        action="store_true",
        help="Fail when decode backend is unavailable for decode-expected cases.",
    )
    parser.add_argument(
        "--traceability",
        type=Path,
        default=DEFAULT_TRACEABILITY,
        help="Path to traceability matrix markdown.",
    )
    parser.add_argument(
        "--matrix-report",
        type=Path,
        default=Path("compat_matrix_report.md"),
        help="Output path for compatibility matrix markdown.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("conformance_report.md"),
        help="Output path for conformance markdown report.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("conformance_report.json"),
        help="Output path for machine-readable conformance JSON.",
    )
    args = parser.parse_args()

    cases = load_compat_cases(args.fixtures)
    outcomes: list[CaseOutcome] = []
    all_cases_ok = True
    for case in cases:
        case_ok, outcome = _run_case(case, module_size=args.module_size, strict_decode=args.strict_decode)
        all_cases_ok = all_cases_ok and case_ok
        outcomes.append(outcome)

    matrix_exit, matrix_note = _run_decoder_matrix(
        fixtures=args.fixtures,
        module_size=args.module_size,
        strict_decode=args.strict_decode,
        report_path=args.matrix_report,
    )
    traceability_present = args.traceability.exists()

    encode_failures = sum(1 for row in outcomes if row.encode == "fail")
    decode_failures = sum(1 for row in outcomes if row.decode == "fail")
    decode_skips = sum(1 for row in outcomes if row.decode == "skip")
    overall_ok = all_cases_ok and matrix_exit == 0 and traceability_present

    generated_at = datetime.now(timezone.utc).isoformat()
    sha = _git_sha()

    markdown_lines = [
        "# aztec-py Conformance Report",
        "",
        f"- Generated (UTC): `{generated_at}`",
        f"- Git SHA: `{sha}`",
        f"- Fixtures: `{args.fixtures}` ({len(outcomes)} cases)",
        f"- Strict decode mode: `{args.strict_decode}`",
        "",
        "## Control Status",
        "",
        f"- Traceability matrix: `{args.traceability}` ({'present' if traceability_present else 'missing'})",
        f"- Compatibility matrix: `{args.matrix_report}` (exit code `{matrix_exit}`)",
        f"- Compatibility matrix note: {matrix_note}",
        "",
        "## Summary",
        "",
        f"- Overall verdict: **{'PASS' if overall_ok else 'FAIL'}**",
        f"- Cases total: `{len(outcomes)}`",
        f"- Encode failures: `{encode_failures}`",
        f"- Decode failures: `{decode_failures}`",
        f"- Decode skips: `{decode_skips}`",
        "",
        "## Case Results",
        "",
        "| Case | Payload | Encode | Decode | Notes |",
        "|---|---|---|---|---|",
    ]
    markdown_lines.extend(_markdown_table_row(row) for row in outcomes)
    markdown_lines.append("")

    args.report.write_text("\n".join(markdown_lines), encoding="utf-8")

    json_payload = {
        "generated_at_utc": generated_at,
        "git_sha": sha,
        "strict_decode": args.strict_decode,
        "fixtures": str(args.fixtures),
        "traceability": {
            "path": str(args.traceability),
            "present": traceability_present,
        },
        "compat_matrix": {
            "path": str(args.matrix_report),
            "exit_code": matrix_exit,
            "note": matrix_note,
        },
        "summary": {
            "overall_pass": overall_ok,
            "total_cases": len(outcomes),
            "encode_failures": encode_failures,
            "decode_failures": decode_failures,
            "decode_skips": decode_skips,
        },
        "cases": [asdict(row) for row in outcomes],
    }
    args.json.write_text(json.dumps(json_payload, indent=2) + "\n", encoding="utf-8")

    print(f"Conformance report written to {args.report}")
    print(f"Conformance JSON written to {args.json}")
    print(f"Compatibility matrix written to {args.matrix_report}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
