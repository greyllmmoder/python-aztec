"""CLI tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from aztec_py.__main__ import cli_main


def test_cli_svg_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli_main(["Hello World", "--format", "svg"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_cli_png_requires_output() -> None:
    with pytest.raises(SystemExit):
        cli_main(["Hello World", "--format", "png"])


def test_cli_png_writes_file(tmp_path: Path) -> None:
    target = tmp_path / "code.png"
    rc = cli_main(["Hello World", "--format", "png", "--output", str(target), "--module-size", "3"])
    assert rc == 0
    assert target.exists()
    assert target.stat().st_size > 0


def test_cli_terminal_output(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli_main(["Hello World", "--format", "terminal"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out


def test_cli_svg_writes_file(tmp_path: Path) -> None:
    target = tmp_path / "code.svg"
    rc = cli_main(["Hello World", "--format", "svg", "--output", str(target)])
    assert rc == 0
    assert "<svg" in target.read_text(encoding="utf-8")
