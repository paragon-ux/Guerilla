"""Verify that importing guerilla succeeds without observable side effects.

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


def test_import_succeeds_without_proxy_configuration():
    """Import must succeed without proxy configuration."""
    result = subprocess.run(
        [sys.executable, "-c", "import guerilla; print(guerilla.__version__)"],
        capture_output=True,
        text=True,
        env={**os.environ, "http_proxy": "", "https_proxy": "", "no_proxy": "*"},
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"


def test_import_does_not_launch_process_or_open_network():
    """Import must not launch child processes or open network sockets."""
    code = """
import sys

forbidden_events = {
    "os.system",
    "socket.bind",
    "socket.connect",
    "socket.connect_ex",
    "socket.getaddrinfo",
    "subprocess.Popen",
}


def audit_hook(event, args):
    if event in forbidden_events:
        raise RuntimeError(f"forbidden import side effect: {event}")


sys.addaudithook(audit_hook)
import guerilla
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"Import had forbidden side effects: {result.stderr}"


def test_import_does_not_mutate_environment():
    """Import must not rewrite process environment variables."""
    code = """
import os

before = dict(os.environ)
import guerilla
after = dict(os.environ)

if before != after:
    before_keys = set(before)
    after_keys = set(after)
    added = sorted(after_keys - before_keys)
    removed = sorted(before_keys - after_keys)
    changed = sorted(key for key in before_keys & after_keys if before[key] != after[key])
    raise SystemExit(
        f"environment mutated; added={added}, removed={removed}, changed={changed}"
    )
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"Import mutated environment: {result.stderr}"


def test_cli_help_and_version_do_not_require_contract_validator_dependencies():
    """Wheel smoke help/version commands must work before validator imports are exercised."""
    code = """
import builtins
import io
import sys

blocked_roots = {"jsonschema", "jsonschema_rs", "referencing"}
real_import = builtins.__import__


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level == 0 and name.partition(".")[0] in blocked_roots:
        raise ModuleNotFoundError(f"No module named {name!r}")
    return real_import(name, globals, locals, fromlist, level)


builtins.__import__ = guarded_import

from guerilla.cli.main import main, run

for args in (["--version"], ["--help"]):
    try:
        main(args)
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise
    else:
        raise SystemExit(f"{args} did not exit after displaying output")

stdout = io.StringIO()
stderr = io.StringIO()
exit_code = run(["version", "--json"], stdout=stdout, stderr=stderr)
if exit_code != 0:
    raise SystemExit(f"version --json failed: {stderr.getvalue()}")
if '"package": "guerilla"' not in stdout.getvalue():
    raise SystemExit(stdout.getvalue())
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"CLI import used validator dependency: {result.stderr}"
