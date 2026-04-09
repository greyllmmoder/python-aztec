"""Bulk and benchmark CLI tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from aztec_py.__main__ import cli_main


def test_cli_requires_data_when_not_bulk() -> None:
    with pytest.raises(SystemExit):
        cli_main([])


def test_cli_rejects_data_and_input_together(tmp_path: Path) -> None:
    payloads = tmp_path / "payloads.txt"
    payloads.write_text("A\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli_main(["A", "--input", str(payloads)])


def test_cli_bulk_txt_svg_writes_files(tmp_path: Path) -> None:
    source = tmp_path / "payloads.txt"
    source.write_text("HELLO\nWORLD\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    rc = cli_main(
        [
            "--input",
            str(source),
            "--input-format",
            "txt",
            "--format",
            "svg",
            "--out-dir",
            str(out_dir),
        ]
    )
    assert rc == 0
    assert (out_dir / "code_1.svg").exists()
    assert (out_dir / "code_2.svg").exists()
    assert "<svg" in (out_dir / "code_1.svg").read_text(encoding="utf-8")


def test_cli_bulk_csv_png_writes_files(tmp_path: Path) -> None:
    source = tmp_path / "payloads.csv"
    source.write_text("HELLO\nWORLD\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    rc = cli_main(
        [
            "--input",
            str(source),
            "--input-format",
            "csv",
            "--format",
            "png",
            "--workers",
            "2",
            "--out-dir",
            str(out_dir),
        ]
    )
    assert rc == 0
    first = out_dir / "code_1.png"
    second = out_dir / "code_2.png"
    assert first.exists()
    assert second.exists()
    assert first.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_cli_bulk_jsonl_supports_string_and_payload_object(tmp_path: Path) -> None:
    source = tmp_path / "payloads.jsonl"
    source.write_text('"HELLO"\n{"payload": "WORLD"}\n', encoding="utf-8")
    out_dir = tmp_path / "out"
    rc = cli_main(
        [
            "--input",
            str(source),
            "--input-format",
            "jsonl",
            "--format",
            "svg",
            "--name-template",
            "ticket_{index}",
            "--out-dir",
            str(out_dir),
        ]
    )
    assert rc == 0
    assert (out_dir / "ticket_1.svg").exists()
    assert (out_dir / "ticket_2.svg").exists()


def test_cli_bulk_rejects_terminal_format(tmp_path: Path) -> None:
    source = tmp_path / "payloads.txt"
    source.write_text("HELLO\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli_main(["--input", str(source), "--format", "terminal", "--out-dir", str(tmp_path / "out")])


def test_cli_bulk_requires_out_dir(tmp_path: Path) -> None:
    source = tmp_path / "payloads.txt"
    source.write_text("HELLO\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli_main(["--input", str(source), "--format", "svg"])


def test_cli_bulk_rejects_output_flag(tmp_path: Path) -> None:
    source = tmp_path / "payloads.txt"
    source.write_text("HELLO\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli_main(
            [
                "--input",
                str(source),
                "--format",
                "svg",
                "--out-dir",
                str(tmp_path / "out"),
                "--output",
                str(tmp_path / "unused.svg"),
            ]
        )


def test_cli_bulk_invalid_jsonl_row_fails(tmp_path: Path) -> None:
    source = tmp_path / "payloads.jsonl"
    source.write_text('{"invalid": 1}\n', encoding="utf-8")
    with pytest.raises(SystemExit):
        cli_main(
            [
                "--input",
                str(source),
                "--input-format",
                "jsonl",
                "--format",
                "svg",
                "--out-dir",
                str(tmp_path / "out"),
            ]
        )


def test_cli_benchmark_outputs_metrics(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli_main(["--benchmark", "--benchmark-count", "5"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "benchmark_count=5" in out
    assert "throughput_per_sec=" in out


def test_cli_benchmark_parallel_mode(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli_main(
        [
            "HELLO",
            "--benchmark",
            "--format",
            "svg",
            "--benchmark-count",
            "4",
            "--benchmark-workers",
            "2",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "benchmark_workers=2" in out
    assert "benchmark_format=svg" in out


def test_cli_benchmark_validates_arguments(tmp_path: Path) -> None:
    source = tmp_path / "payloads.txt"
    source.write_text("HELLO\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli_main(["--benchmark", "--benchmark-count", "0"])
    with pytest.raises(SystemExit):
        cli_main(["--benchmark", "--benchmark-workers", "0"])
    with pytest.raises(SystemExit):
        cli_main(["--benchmark", "--input", str(source)])
    with pytest.raises(SystemExit):
        cli_main(["--benchmark", "--output", str(tmp_path / "x.svg")])
    with pytest.raises(SystemExit):
        cli_main(["--benchmark", "--out-dir", str(tmp_path / "out")])

