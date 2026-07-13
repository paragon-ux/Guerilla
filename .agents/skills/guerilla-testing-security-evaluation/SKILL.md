---
name: guerilla-testing-security-evaluation
description: Guides Guerilla conformance, repository, crash, security, performance, pilot, benchmark, CI, and release-evidence validation. Use whenever tests, evaluation, or completion evidence are being created or reviewed.
---

# guerilla-testing-security-evaluation

**Skill:** Conformance testing, crash and corruption simulation, security review, capability escalation tests, performance measurement, pilots, benchmarks, and release evidence
**Owner phase:** Cross-phase (Phase 4 Fixtures, Phase 15 CLI/E2E, Phase 19 Security/Durability, Phase 21 Benchmark/Evaluation, Phase 22 Release)
**File:** `.agents/skills/guerilla-testing-security-evaluation/SKILL.md`

---

## 1. Purpose

Own the validation, security, and evaluation surface. This skill governs conformance fixtures and tests, crash and corruption simulation, security and capability-escalation tests, performance benchmarks, pilot integration validation, benchmark manifests, and release evidence. It must distinguish planned validation from actual evidence -- never mark an unimplemented test as passing.

---

## 2. Activation Criteria

Activate when the task involves:

- Writing or running any test suite (unit, integration, conformance, crash, security, performance).
- Creating test fixtures for contract conformance.
- Simulating crashes, corruption, or fault injection.
- Reviewing adapter security boundaries, payload handling, or authorization.
- Measuring performance: append latency, cycle-check cost, replay time, index rebuild time, traversal latency, projection latency, snapshot size.
- Validating pilot integrations against acceptance criteria.
- Producing benchmark manifests and evaluation artifacts.
- Preparing release checklists and release evidence.
- Running CI validation sequences.

---

## 3. Non-Activation Criteria

Do NOT activate when the task involves:

- Implementing production runtime behavior (delegate to the implementation skills).
- Defining what should be tested (derived from specifications owned by other skills).
- Making architecture decisions about test scope (owned by `guerilla-contracts-modeling`).

---

## 4. Required Reading

Before any testing or evaluation work, read in order:

1. `AGENTS.md` -- test taxonomy, prohibited shortcuts, completion-report format
2. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md` -- Section 36 (testing requirements: record, transaction, DAG, adapter, action-recovery, projection, security, performance tests), Section 37 (MVP acceptance criteria)
3. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md` -- Section 33 (conformance matrix: protocol negotiation, envelope, graph operations, adapter operations, idempotency, queries, views, security)
4. `docs/architecture/GUERILLA_SNAPSHOT.md` -- Sections 10 (next milestones), 11 (readiness gates)
5. `docs/TEST_MATRIX.md` (once created) -- planned evidence columns
6. `docs/CODEX_BUILD_PLAN.md` (once created) -- gates and phase dependencies

---

## 5. Owned Artifacts

This skill owns:

- `tests/unit/` -- isolated function and class tests
- `tests/integration/` -- component interaction tests
- `tests/conformance/` -- schema, protocol, and graph-invariant conformance tests
- `tests/crash/` -- crash simulation and recovery tests
- `tests/security/` -- authorization, payload safety, adapter escalation tests
- `tests/performance/` -- throughput, latency, and resource measurement
- `tests/fixtures/` -- test data and expected outputs
- `docs/TEST_MATRIX.md` -- planned and actual test evidence
- `docs/EVALUATION_PLAN.md` -- evaluation methodology and research questions

---

## 6. Invariants

When working on tests and evaluation, these MUST NOT be violated:

- `TEST_MATRIX.md` must define planned evidence columns and must not mark unimplemented tests as passing.
- Test-category READMEs must define future purpose and owning phases without fabricating evidence.
- No Phase 1 test may fabricate graph records or external actions.
- Repository-contract tests must verify structural properties, not implementation behavior that belongs to later phases.
- Conformance tests must validate against frozen schemas and invariants, not against provisional implementation choices.
- Crash tests must simulate realistic failure modes (disk full, process kill, partial write) and verify recovery behavior.
- Security tests must attempt actual boundary violations (path escape, unauthorized action, capability escalation) and verify rejection.
- Performance results must be reproducible from a committed benchmark manifest.
- Release evidence must link to automated test results, not manual claims.

---

## 7. Ordered Procedure

### Phase 1 -- Repository Contract Tests

1. Write `tests/unit/test_import.py`: verify import succeeds, `__version__` exists, import performs no filesystem mutation, network call, process launch, or environment rewrite.
2. Write `tests/unit/test_version.py`: verify single canonical version source, CLI and library versions agree, output is deterministic, help/version return success, unsupported arguments fail without side effects.
3. Write `tests/repository/test_repository_contract.py`: verify required files exist, skills exist and are non-empty, build-document skeletons exist, architecture sources and rationale are present, source digests recorded, schema/registry directories contain no falsely frozen contracts, required package directories exist, no prohibited service/integration scaffold, prompt inventory complete, placeholder documents identify status and owner phase.

### Phase 4 -- Conformance Fixtures

1. Create valid fixtures for every record type and message envelope.
2. Create invalid fixtures for every required validation rule.
3. Create compatibility fixtures for version negotiation and unknown fields.
4. Create canonicalization fixtures with published hash vectors.
5. Verify two independent validation paths produce identical results.

### Phase 15 -- CLI, E2E, Smoke

1. Implement E2E scenarios for each synthetic external system.
2. Implement clean-install smoke test.
3. Verify stable exit codes and JSON output mode.

### Phase 19 -- Security, Durability, Archive

1. Write crash simulation tests: kill process during transaction, verify incomplete transaction ignored on replay.
2. Write corruption tests: flip bytes in graph segment, verify hash mismatch detection.
3. Write security tests: path/endpoint escape, unauthorized graph access, unauthorized external action, secret redaction, payload non-execution, unsafe serialization rejection, adapter capability escalation, idempotency-key abuse.
4. Write archive tests: seal, verify, restore.
5. Write backup and restore tests.

### Phase 21 -- Benchmark, Evaluation

1. Write performance benchmarks: append throughput, cycle-check cost, replay time, index rebuild time, traversal latency, projection latency, snapshot size.
2. Write evaluation scripts measuring resume accuracy, lineage completeness, boundary preservation, projection reproducibility, conflict detection, storage and query cost.
3. Produce benchmark manifests with committed graph revision and transformation version.

### Phase 22 -- Release

1. Verify all core schemas frozen and versioned.
2. Verify canonical hashing vectors published.
3. Verify deterministic replay.
4. Verify cycle rejection complete.
5. Verify index rebuild lossless.
6. Verify state-boundary enforcement tested.
7. Verify idempotency and reconciliation demonstrated.
8. Verify projections cite source revisions.
9. Verify payload retention and redaction approved.
10. Verify authorization enforced.
11. Verify crash and corruption recovery pass.
12. Verify at least two materially different state models integrated without authority overlap.
13. Produce release evidence package.

---

## 8. Test Commands

```bash
# Full validation sequence
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest

# Targeted suites
uv run pytest tests/unit/
uv run pytest tests/repository/
uv run pytest tests/integration/
uv run pytest tests/conformance/
uv run pytest tests/crash/
uv run pytest tests/security/
uv run pytest tests/performance/

# Build and smoke
uv build
uv run pip install dist/*.whl --force-reinstall --no-deps
python -c "import guerilla; print(guerilla.__version__)"
guerilla --version
guerilla --help
```

---

## 9. Failure Cases

Tests must verify correct handling of:

- Missing required repository artifacts -- repository-contract test fails.
- Architecture-source checksum mismatch -- source-integrity test fails.
- Accidental Phase 2+ domain contracts under schemas/ or registries/ -- repository-contract test fails.
- Placeholder documents without status or owner phase -- repository-contract test fails.
- Package import outside repository working directory -- import test succeeds.
- CLI version from installed wheel -- version test succeeds.
- Missing .env and optional environment values -- no crash, no side effects.
- Malformed CLI arguments -- non-zero exit, no side effects.
- Machine with no database, service, or container runtime -- all tests pass.

---

## 10. Stop Conditions

Stop testing or evaluation work and report the blocker if:

- A test fabricates graph records or external actions in Phase 1.
- A test marks an unimplemented feature as passing.
- A crash test cannot be reliably reproduced.
- A security test cannot distinguish authorization failure from implementation error.
- A performance measurement is not reproducible from its benchmark manifest.
- A release claim lacks linked evidence.

---

## 11. Completion Evidence

Testing and evaluation completion requires:

- All test suites passing with no skipped tests unless documented.
- `TEST_MATRIX.md` updated with actual evidence for every planned test.
- Crash recovery demonstrated and passing.
- Security boundaries verified and passing.
- Performance benchmarks measured and reproducible.
- Release checklist fully signed off with linked evidence.
- No test claims completion of unimplemented runtime behavior.

---

## 12. Handoff

After completing testing and evaluation, hand off to:

- Release process for versioning, packaging, and distribution.
- Research publication for evaluation results and comparative analysis.
