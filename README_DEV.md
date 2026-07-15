# Guerilla — Development Guide

**Current status:** Gate C in progress; Phases 1-11 complete
**Phase:** Phase 12 pending

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

## Codex / Windows Local Validation

Use the local wrapper when running validation from Codex or another restricted
Windows workspace. It keeps `uv` cache writes under the repository-local
`.uv-cache/` directory, keeps test temporary files under `.tmp/`, and runs the
isolated wheel smoke test without `uv` or user-profile package caches.

```powershell
.\scripts\validate-local.ps1
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
uv run pytest tests/conformance/ # schema and fixture conformance tests
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
$env:UV_CACHE_DIR = Join-Path (Get-Location) ".uv-cache"
$env:TEMP = Join-Path (Get-Location) ".tmp"
$env:TMP = $env:TEMP
$env:TMPDIR = $env:TEMP
$env:PIP_CACHE_DIR = Join-Path $env:TEMP "pip-cache"
uv build

# Install in a clean environment and verify from a non-source work directory
$wheel = (Get-Item dist\*.whl | Select-Object -First 1).FullName
$wheelVenv = Join-Path $env:TEMP ("guerilla-wheel-test-" + [System.Guid]::NewGuid())
python -m venv $wheelVenv
$wheelPython = Join-Path $wheelVenv "Scripts\python.exe"
$wheelCli = Join-Path $wheelVenv "Scripts\guerilla.exe"
& $wheelPython -m pip install --no-deps $wheel
$smokeWorkDir = Join-Path $env:TEMP "wheel-smoke-workdir"
New-Item -ItemType Directory -Force -Path $smokeWorkDir | Out-Null
Push-Location $smokeWorkDir
& $wheelPython -c "import guerilla; print(guerilla.__version__)"
& $wheelCli --version
& $wheelCli --help
& $wheelCli version --json
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
- **Gate A (Contract Ready) is complete.** Phase 5 implemented deterministic
  codec/config/identifier/hash primitives.
- Phase 6 implemented local append storage, payload persistence, writer locking,
  replay, and incomplete-tail recovery.
- Phase 7 implemented DAG integrity, graph heads, exact-revision query helpers,
  and a rebuildable non-authoritative SQLite index.
- Phase 8 implemented fixed local authorization, state-boundary checks, adapter
  identity registration without invocation, and scoped external identity
  lifecycle handling. Do not implement adapters, projections, or transports
  before their owning phases.
- Phase 9 implemented the trusted in-process adapter SDK, one validating host
  path, descriptor completeness checks, and transactional, reconstructed
  filesystem, and asynchronous synthetic systems. It did not add graph
  observation ingestion, graph-backed action orchestration, reconciliation,
  projections, snapshots, transports, subprocess isolation, or real
  integrations.
- Phase 10 implemented observe-only ingestion from the Phase 9 adapter host into
  the authoritative graph through one validated flow and one append transaction.
  It preserves external identity, revisions, provenance, payload retention, and
  duplicate/conflict classifications without invoking `act` or mutating
  external state.
- Phase 11 implemented graph-backed action intent, invocation-start records,
  adapter `act` invocation only after durable intent verification, explicit
  action-result records, idempotency replay/conflict behavior, restart handling,
  and optional after-state observation through the Phase 10 ingestor. It did
  not add reconciliation, conflict decisions, projections, snapshots,
  transports, subprocess isolation, real integrations, or Gate D behavior.
- Gate B is complete. Gate C is in progress; the current boundary is limited to
  contracts, kernel behavior, local authority/identity/boundaries, Phase 9
  synthetic adapter SDK behavior, Phase 10 observation ingestion, and Phase 11
  action intent/idempotency orchestration.
- Completion claims require linked evidence (command output, test result, file digest, inspection result).

## Completion Evidence

Each phase completion must report:

- **Phase Result:** PASS / PARTIAL / FAIL
- **Delivered Artifacts:** grouped by category
- **Validation Evidence:** `Command | Exit code | Result | Evidence path`
- **Exit-Criteria Matrix:** every criterion with Status, Evidence, Notes
- **Scope Audit:** prohibited behavior and reserved decisions introduced (or None)
- **Blockers and Contradictions:** or None

## Gate C Handoff

After Gate B completion and Phase 11 local completion:

1. Confirm repository, conformance, Phase 5 unit, Phase 6 storage/recovery, Phase 7 graph/index, Phase 8 security, and Gate B checklist tests pass.
2. Use `ARCHITECTURE_DECISIONS.md`, `docs/contract_inventory.json`, `schemas/`, `registries/`, `tests/fixtures/contracts/`, and Phase 5-8 primitives as frozen Gate B outputs.
3. Do not change canonical bytes, identifiers, hashes, relationship directions, or authorization rules without reopening Gate A.
4. Use `docs/phase_prompts/PHASE_09_ADAPTER_SDK_SYNTHETIC_SYSTEMS.md`, `src/guerilla/adapters/`, `tests/adapters/`, and `tests/fixtures/adapters/` as Phase 9 evidence.
5. Use `docs/phase_prompts/PHASE_10_OBSERVATION_INGESTION.md`, `src/guerilla/observability/`, and `tests/integration/test_phase10_observation_ingestion.py` as Phase 10 evidence.
6. Use `docs/phase_prompts/PHASE_11_ACTION_INTENT_IDEMPOTENCY.md`, `src/guerilla/orchestration/`, and `tests/integration/test_phase11_action_intent_idempotency.py` as Phase 11 local evidence.
7. Begin Phase 12 only from the Phase 11 commit with clean full local validation and hosted CI.
