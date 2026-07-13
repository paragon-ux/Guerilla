# Guerilla — Development Guide

**Current status:** Architecture-complete / pre-prototype
**Phase:** 1 — Repository and Agent-Control Bootstrap

---

## Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Clean Setup

```bash
# Clone and enter the repository
git clone <repo-url>
cd Guerilla

# Create virtual environment and install all dependencies
uv sync --extra dev

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
uv run ruff format --check . && uv run ruff check . && uv run mypy src tests && uv run pytest && uv build
```

## Isolated Wheel Smoke Test

```bash
# Build the wheel
uv build

# Install in a clean environment and verify
uv run pip install dist/*.whl --force-reinstall --no-deps
python -c "import guerilla; print(guerilla.__version__)"
guerilla --version
guerilla --help
guerilla version --json

# Confirm no workspace, graph, database, cache, or external-state files are created
```

## Source Integrity Verification

```bash
# Verify architecture source digests match the manifest
sha256sum docs/architecture/*.md docs/rationale/*.md
# Compare against docs/architecture/README.md
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

After Phase 1 completes:

1. Confirm repository baseline passes all repository-contract tests.
2. Verify architecture sources are present, classified, and hash-verified.
3. Resolve any architecture decisions reserved for Phase 2 (none should be frozen in Phase 1).
4. Hand off to `PHASE_02_ARCHITECTURE_DECISIONS.md`.
