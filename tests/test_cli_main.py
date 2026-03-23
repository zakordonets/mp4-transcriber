"""
CLI smoke tests (no Whisper model load).
"""

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import cli


def test_transcribe_help_includes_diarize():
    runner = CliRunner()
    result = runner.invoke(cli, ["transcribe", "--help"])
    assert result.exit_code == 0
    assert "--diarize" in result.output
    assert "--diarization-backend" in result.output


def test_batch_help_includes_diarize():
    runner = CliRunner()
    result = runner.invoke(cli, ["batch", "--help"])
    assert result.exit_code == 0
    assert "--diarize" in result.output


def test_check_runs_and_lists_diarization():
    runner = CliRunner()
    result = runner.invoke(cli, ["check"])
    assert result.exit_code == 0
    assert "Diarization" in result.output or "diarization" in result.output.lower()


def test_check_includes_backend_noop():
    runner = CliRunner()
    result = runner.invoke(cli, ["check"])
    assert result.exit_code == 0
    assert "noop" in result.output


def test_diarization_smoke_runs_with_mocked_backend(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(cli, ["diarization-smoke", "--backend", "noop"])

    assert result.exit_code == 0
    assert "Diarization smoke test passed" in result.output
