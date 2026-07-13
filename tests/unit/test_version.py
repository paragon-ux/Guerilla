"""Verify version reporting consistency across library and CLI.

Phase 1: The single canonical version source is src/guerilla/_version.py.
"""

import json
import subprocess
import sys

from guerilla import __version__
from guerilla._version import __version__ as _version_source


def test_single_canonical_version_source():
    """Library __version__ and _version.__version__ must be the same object."""
    assert __version__ is _version_source
    assert __version__ == "0.0.0"


def test_cli_version_matches_library():
    """guerilla --version output must match the library version."""
    result = subprocess.run(
        [sys.executable, "-m", "guerilla", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_cli_help():
    """guerilla --help must return success."""
    result = subprocess.run(
        [sys.executable, "-m", "guerilla", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Guerilla" in result.stdout


def test_cli_version_subcommand():
    """guerilla version must return success."""
    result = subprocess.run(
        [sys.executable, "-m", "guerilla", "version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_cli_version_json():
    """guerilla version --json must return valid JSON with version field."""
    result = subprocess.run(
        [sys.executable, "-m", "guerilla", "version", "--json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["package"] == "guerilla"
    assert data["version"] == __version__
    assert "python" in data


def test_unsupported_argument_fails():
    """Invalid arguments must fail with non-zero exit."""
    result = subprocess.run(
        [sys.executable, "-m", "guerilla", "--nonexistent"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_unknown_command_fails():
    """Unknown subcommands must fail with exit code 2."""
    result = subprocess.run(
        [sys.executable, "-m", "guerilla", "nonexistent_command"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
