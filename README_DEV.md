# Guerilla — Development Guide

**Current status:** Architecture-complete / pre-prototype; Phase 1 closure candidate
**Phase:** 1 - Repository and Agent-Control Bootstrap; Phase 2 blocked pending Phase 1 acceptance

---

## Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Clean Setup

```bash
# Clone and enter the repository
git clone <repo-url>
cd Guerilla

# Verify the committed lockfile and install all dependencies without resolving
uv lock --check
uv sync --frozen --extra dev

# Verify installation
uv run python -c "import guerilla; print(guerilla.__version__)"
uv run guerilla --version
uv run guerilla --help
```

## Development Commands

```bash
# Formatting
uv run ruff format --check .
uv run ruff format .           # auto-fix

# Linting
uv run ruff check .
uv run ruff check --fix .      # auto-fix

# Static analysis
uv run mypy src tests

# Tests
uv run pytest                  # all tests
uv run pytest tests/unit/      # unit tests only
uv run pytest tests/repository/ # repository-contract tests
uv run pytest -v               # verbose output

# Package build
uv build                      # source distribution + wheel

# Full validation sequence
uv lock --check
uv sync --frozen --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
uv build
```

## Isolated Wheel Smoke Test

```powershell
# Build the wheel
uv build

# Install in a clean environment and verify from outside the repository
$wheel = (Get-Item dist\*.whl | Select-Object -First 1).FullName
$wheelVenv = Join-Path ([System.IO.Path]::GetTempPath()) ("guerilla-wheel-test-" + [System.Guid]::NewGuid())
uv venv $wheelVenv
uv pip install --python (Join-Path $wheelVenv "Scripts\python.exe") $wheel --no-deps
Push-Location ([System.IO.Path]::GetTempPath())
& (Join-Path $wheelVenv "Scripts\python.exe") -c "import guerilla; print(guerilla.__version__)"
& (Join-Path $wheelVenv "Scripts\guerilla.exe") --version
& (Join-Path $wheelVenv "Scripts\guerilla.exe") --help
& (Join-Path $wheelVenv "Scripts\guerilla.exe") version --json
Pop-Location

# Confirm no workspace, graph, database, cache, or external-state files are created
```

## Source Integrity Verification

```bash
# Verify architecture source digests match the manifest
uv run pytest tests/repository/test_repository_contract.py -k source_digests
```

## Phase Discipline

- **No phase or gate skipping.** Each phase must complete its exit criteria before the next begins.
- **Gate A (Contract Ready) blocks Gate B (Kernel Ready).** No runtime code before contracts freeze.
- Phase 1 is a **repository-contract phase**, not a runtime phase. Do not implement simplified Guerilla runtime.
- Completion claims require linked evidence (command output, test result, file digest, inspection result).

## Completion Evidence

Each phase completion must report:

- **Phase Result:** PASS / PARTIAL / FAIL
- **Delivered Artifacts:** grouped by category
- **Validation Evidence:** `Command | Exit code | Result | Evidence path`
- **Exit-Criteria Matrix:** every criterion with Status, Evidence, Notes
- **Scope Audit:** prohibited behavior and reserved decisions introduced (or None)
- **Blockers and Contradictions:** or None

## Phase 2 Handoff

After Phase 1 closure is accepted:

1. Confirm repository baseline passes all repository-contract tests.
2. Verify architecture sources are present, classified, and hash-verified.
3. Resolve any architecture decisions reserved for Phase 2 (none should be frozen in Phase 1).
4. Hand off to `PHASE_02_ARCHITECTURE_DECISIONS.md`.
