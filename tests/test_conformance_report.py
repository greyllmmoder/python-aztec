"""Smoke tests for conformance report generation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_conformance_report_script_smoke(tmp_path: Path) -> None:
    report_path = tmp_path / "conformance_report.md"
    json_path = tmp_path / "conformance_report.json"
    matrix_path = tmp_path / "compat_matrix_report.md"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/conformance_report.py",
            "--report",
            str(report_path),
            "--json",
            str(json_path),
            "--matrix-report",
            str(matrix_path),
        ],
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert report_path.exists()
    assert json_path.exists()
    assert matrix_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["overall_pass"] is True
    assert payload["summary"]["total_cases"] > 0
    assert payload["traceability"]["present"] is True
