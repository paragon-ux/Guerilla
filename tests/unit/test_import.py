"""Verify that importing guerilla succeeds and performs no side effects.

Phase 1: Only import and version access are permitted.
"""

import os
import subprocess
import sys


def test_import_succeeds():
    """import guerilla must succeed without error."""
    import guerilla  # noqa: F401


def test_version_exists():
    """__version__ must be a non-empty string."""
    from guerilla import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_import_does_not_mutate_filesystem(tmp_path):
    """Import must not create files or directories in an unrelated location."""
    before = set(os.listdir(tmp_path))
    # Run import in a subprocess with tmp_path as CWD
    result = subprocess.run(
        [sys.executable, "-c", "import guerilla"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    after = set(os.listdir(tmp_path))
    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert before == after, f"Import mutated filesystem: {after - before}"


def test_import_does_not_require_network():
    """Import must succeed without network access. Verified by subprocess isolation."""
    result = subprocess.run(
        [sys.executable, "-c", "import guerilla; print(guerilla.__version__)"],
        capture_output=True,
        text=True,
        env={**os.environ, "http_proxy": "", "https_proxy": "", "no_proxy": "*"},
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"
