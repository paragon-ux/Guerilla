# Guerilla Kickoff Prompt

**Phase:** 1 — Repository and Agent-Control Bootstrap  
**Gate:** A — Contract Ready (1 of 4)  
**Entry state:** Architecture-complete / pre-prototype  
**Required exit state:** Reproducible repository scaffold with no substantive runtime implementation

---

## 1. Assignment

Initialize the Guerilla reference repository and establish the controls required for every later build phase.

This phase must create:

- the repository structure;
- the authorized source hierarchy;
- a root `AGENTS.md`;
- five focused agent skills;
- regenerable build-document skeletons;
- the Python package scaffold;
- harmless library and CLI version reporting;
- development commands and a locked environment;
- CI, smoke tests, and repository-contract tests;
- the complete phase and gate inventory.

This is a repository-contract phase, not a runtime phase. Do not implement a simplified Guerilla runtime to demonstrate progress.

---

## 2. System Identity

Guerilla maintains one logically authoritative, append-only cross-system causal-lineage and continuity graph while leaving application-state authority with integrated external systems.

Preserve these distinctions from the first commit:

- Guerilla owns graph records, graph identity, graph revisions, lineage assertions, conflicts, decisions, snapshots, and derived-view provenance.
- External systems retain their application state, native revisions, native identifiers, and mutation semantics.
- Adapters may observe or act only inside explicit state boundaries and declared capabilities.
- The authoritative lineage graph is not replaced by summaries, manifests, snapshots, diffs, indexes, caches, or projections.
- State continuity may be online, offline, or reconstructed according to the external system; every boundary must declare which model applies.

---

## 3. Controlling Rationale

Treat `Rationale/Note-on-Architecture.md` as the controlling rationale for build ordering.

Apply its rules:

1. Select state continuity deliberately rather than assuming continuous state.
2. Preserve authoritative lineage as an explicit relational graph.
3. Compress lineage only in derived, source-bound views.
4. Define state continuity and lineage before transport, service, UI, or integration architecture.
5. In hybrid architectures, explicitly declare state ownership, continuity mode, state crossing, lineage recording, authoritative relationships, and conflict handling.

Do not hide unresolved state or lineage choices behind command orchestration, request routing, caches, files, databases, or transport-specific behavior.

---

## 4. Authorized Sources

Use only:

1. `GUERILLA_CONCEPT_PAPER.md`
2. `GUERILLA_IMPLEMENTATION_SPEC.md`
3. `GUERILLA_PROTOCOL_SPEC.md`
4. `GUERILLA_SNAPSHOT.md`
5. `CURRENT_STATUS_MATRIX.md`
6. `RELATED_WORK.md`
7. `Rationale/Note-on-Architecture.md`
8. `GUERILLA_WORKFLOW_CURRENT.md`
9. this kickoff prompt

Do not use previous Guerilla edit ledgers, prior implementation papers, superseded workflow drafts, or unrelated architecture documents.

Patch-DIFF is only the workflow pattern behind this phase structure. Do not import Patch-DIFF runtime semantics into Guerilla.

### Source-of-truth order to encode in `AGENTS.md`

1. `AGENTS.md`
2. `docs/ARCHITECTURE_DECISIONS.md`
3. `docs/MVP_SCOPE.md`
4. `docs/GLCP_CORE_SPEC.md`
5. `docs/DATA_MODEL.md`
6. `docs/GRAPH_RECORD_FORMAT.md`
7. `docs/ADAPTER_CONTRACT.md`
8. `docs/STATE_BOUNDARY_MODEL.md`
9. `docs/TEST_MATRIX.md`
10. `docs/CODEX_BUILD_PLAN.md`
11. the four core Guerilla architecture papers
12. status, related-work, and rationale documents

During Phase 1, incomplete build documents are scaffolds, not normative decisions. Never treat an unresolved marker as an implementation requirement.

---

## 5. Locked Invariants

All created instructions and documentation must preserve these invariants:

1. One logically authoritative Guerilla graph exists per workspace.
2. Committed graph history is append-only and immutable.
3. Direct authoritative edges form a DAG.
4. Symmetric, cyclic, non-causal, or otherwise non-DAG assertions are reified rather than inserted as direct authoritative edges.
5. External systems retain application-state authority.
6. Guerilla represents external state through bounded observations and references; it does not silently become the external system of record.
7. Every external action requires a committed intent before invocation.
8. Unknown external outcomes require reconciliation before unsafe retry.
9. Idempotency conflicts are explicit and cannot be silently overwritten.
10. Projections, manifests, snapshots, diffs, indexes, and caches are derived and non-authoritative.
11. Every index must be rebuildable from authoritative graph records.
12. Graph replay never re-executes external actions.
13. Stored payloads are data and are never executed merely because they are stored or replayed.
14. Client, adapter, actor, or payload claims cannot grant themselves authority.
15. Every hybrid boundary declares ownership, continuity mode, permitted operations, lineage crossing, and conflict behavior.
16. Transport bindings cannot create a second mutation path or redefine GLCP semantics.
17. The internal MVP remains local and single-writer unless a later approved phase changes that boundary.
18. Missing or contradictory contracts block mutation rather than trigger best-effort guessing.

---

## 6. Permitted Scope

You may implement only:

- repository directories and configuration;
- source-document placement and integrity metadata;
- project metadata, packaging, and dependency locking;
- `AGENTS.md`;
- five complete `SKILL.md` files;
- documentation skeletons;
- package import and version reporting;
- CLI help and version reporting;
- CI configuration;
- Phase 1 smoke and repository-contract tests;
- contributor and developer instructions;
- explicit placeholders owned by later phases.

Harmless Phase 1 behavior cannot create, mutate, validate, replay, query, reconcile, project, or transmit Guerilla domain records.

---

## 7. Prohibited Scope

Do not implement or expose production-shaped stubs for:

- canonical JSON encoding;
- identifier generation or validation;
- record, payload, transaction, or commit hashing;
- Guerilla JSON Schemas or registries;
- graph headers, nodes, edges, commits, or transactions;
- append-only persistence, writer locking, durability, or recovery;
- DAG validation, graph heads, traversal, or replay;
- SQLite indexing;
- authority or identity registries;
- adapters, synthetic systems, or external-system access;
- observation ingestion;
- action intent, idempotency, or external action invocation;
- reconciliation, conflicts, or decisions;
- projections, manifests, diffs, snapshots, or resume contexts;
- GLCP client/server behavior;
- JSON-RPC, HTTP, MCP, daemon, hosted service, or UI surfaces;
- subprocess or remote adapter hosts;
- benchmarks, performance claims, or research claims.

Do not freeze decisions reserved for Phases 2–4, including:

- UUIDv7 versus ULID;
- the canonical JSON profile and library;
- exact record-hash or commit-hash construction;
- transaction record ordering;
- writer-lock and atomic-append mechanisms;
- archive thresholds;
- payload retention defaults;
- transport bindings.

---

## 8. Required Repository Layout

Create or normalize this structure:

```text
Guerilla/
├── AGENTS.md
├── README.md
├── README_DEV.md
├── pyproject.toml
├── <locked-dependency-file>
├── .gitignore
├── .editorconfig
├── .python-version
├── .env.example
├── .github/workflows/ci.yml
├── .agents/skills/
│   ├── guerilla-contracts-modeling/SKILL.md
│   ├── guerilla-graph-kernel-storage/SKILL.md
│   ├── guerilla-adapter-continuity-reconciliation/SKILL.md
│   ├── guerilla-projections-snapshot-resume/SKILL.md
│   └── guerilla-testing-security-evaluation/SKILL.md
├── docs/
│   ├── ARCHITECTURE_DECISIONS.md
│   ├── GLOSSARY.md
│   ├── MVP_SCOPE.md
│   ├── DATA_MODEL.md
│   ├── GRAPH_RECORD_FORMAT.md
│   ├── GLCP_CORE_SPEC.md
│   ├── ADAPTER_CONTRACT.md
│   ├── STATE_BOUNDARY_MODEL.md
│   ├── STORAGE_AND_RECOVERY.md
│   ├── PROJECTION_SPEC.md
│   ├── SECURITY_MODEL.md
│   ├── ERROR_REGISTRY.md
│   ├── TEST_MATRIX.md
│   ├── CODEX_BUILD_PLAN.md
│   ├── EVALUATION_PLAN.md
│   ├── architecture/
│   │   ├── README.md
│   │   ├── GUERILLA_CONCEPT_PAPER.md
│   │   ├── GUERILLA_IMPLEMENTATION_SPEC.md
│   │   ├── GUERILLA_PROTOCOL_SPEC.md
│   │   ├── GUERILLA_SNAPSHOT.md
│   │   ├── CURRENT_STATUS_MATRIX.md
│   │   └── RELATED_WORK.md
│   ├── rationale/Note-on-Architecture.md
│   ├── phase_prompts/
│   │   ├── Guerilla-Kickoff-Prompt.md
│   │   └── README.md
│   └── Archive/README.md
├── schemas/README.md
├── registries/README.md
├── src/guerilla/
│   ├── __init__.py
│   ├── __main__.py
│   ├── _version.py
│   ├── py.typed
│   ├── config/__init__.py
│   ├── contracts/__init__.py
│   ├── codec/__init__.py
│   ├── protocol/__init__.py
│   ├── graph/__init__.py
│   ├── storage/__init__.py
│   ├── payloads/__init__.py
│   ├── index/__init__.py
│   ├── authority/__init__.py
│   ├── identity/__init__.py
│   ├── adapters/__init__.py
│   ├── orchestration/__init__.py
│   ├── reconciliation/__init__.py
│   ├── conflicts/__init__.py
│   ├── projections/__init__.py
│   ├── cli/__init__.py
│   ├── cli/main.py
│   └── observability/__init__.py
├── tests/
│   ├── unit/test_import.py
│   ├── unit/test_version.py
│   ├── repository/test_repository_contract.py
│   ├── integration/README.md
│   ├── conformance/README.md
│   ├── crash/README.md
│   ├── security/README.md
│   ├── performance/README.md
│   └── fixtures/README.md
└── examples/
    ├── transactional_service/README.md
    ├── reconstructed_filesystem/README.md
    └── asynchronous_unknown_outcome/README.md
```

The example directories are documentation-only placeholders. Do not add executable adapter or simulation code.

Preserve useful, non-conflicting existing content. Do not create duplicate source-of-truth paths.

---

## 9. Packaging Baseline

Configure a Python 3.11-or-later package using a `src/` layout.

Requirements:

- package name: `guerilla`, unless an authoritative existing package name is already present;
- initial development version: `0.0.0`, unless an authoritative version already exists;
- standard PEP 517 build backend;
- `pyproject.toml` and a committed locked dependency file;
- `pytest` for tests;
- `ruff` for formatting and linting;
- `mypy` for static analysis, with the selected strictness documented;
- source distribution and wheel build checks;
- `py.typed` marker;
- no runtime dependencies unless harmless Phase 1 behavior requires them;
- development dependencies separated from runtime dependencies.

Prefer `uv` and `uv.lock` for the reference scaffold. An equivalent locked workflow is acceptable only when documented and tested in CI.

Do not add a database, ORM, web framework, RPC framework, MCP SDK, queue, container requirement, or telemetry backend.

The package must expose:

```python
from guerilla import __version__
```

The only permitted CLI behavior is:

```text
guerilla --help
guerilla --version
python -m guerilla --help
python -m guerilla --version
```

An optional `guerilla version --json` may return package/build metadata only and must perform no workspace access.

---

## 10. `AGENTS.md`

Create one operational, Guerilla-specific root `AGENTS.md`, approximately 300–450 lines.

It must include:

1. project identity;
2. authorized sources and source order;
3. terminology and locked distinctions;
4. locked invariants;
5. authoritative versus derived storage;
6. external-state authority and boundary rules;
7. repository map;
8. phase and gate discipline;
9. future mutation and validation ordering;
10. adapter trust and capabilities;
11. intent-before-action and reconciliation;
12. payload, path, secret, and execution safety;
13. test taxonomy and commands;
14. documentation regeneration;
15. prohibited shortcuts;
16. stop conditions;
17. completion-report format.

Explicitly prohibit agents from:

- making a projection or index authoritative;
- directly replacing external application state;
- invoking an external action before committing intent;
- replaying external actions during graph replay;
- weakening cycle validation;
- inserting cyclic or symmetric assertions as direct authoritative edges;
- repairing the graph from SQLite;
- treating payloads as executable content;
- retrying unknown outcomes before reconciliation;
- adding real adapters before synthetic conformance;
- adding transport-specific mutation semantics;
- hiding unresolved architecture choices in defaults;
- claiming completion without linked evidence.

---

## 11. Agent Skills

Create five complete skill files, approximately 200–350 lines each. Every skill must include purpose, activation criteria, non-activation criteria, required reading, owned artifacts, invariants, ordered procedure, tests, failure cases, stop conditions, completion evidence, and handoff.

### `guerilla-contracts-modeling`

Owns architecture decisions affecting contracts, schemas, registries, canonicalization fixtures, data-model consistency, authority envelopes, protocol envelopes, and compatibility review.

It must not implement storage or adapters.

### `guerilla-graph-kernel-storage`

Owns codec integration, append-only storage, transactions, commit chain, DAG validation, replay, verification, writer locking, payload references, and rebuildable indexing.

It must not make SQLite authoritative or invoke external actions.

### `guerilla-adapter-continuity-reconciliation`

Owns adapter descriptors and host behavior, continuity modes, observation ingestion, authority boundaries, intent-before-action, idempotency, unknown-outcome reconciliation, conflicts, and decisions.

It must not permit payload or adapter claims to grant authority.

### `guerilla-projections-snapshot-resume`

Owns lineage and dependency views, manifests, conflict and progress views, traceability views, snapshots, diffs, resume context, and deterministic regeneration.

It must treat every output as source-bound and derived.

### `guerilla-testing-security-evaluation`

Owns conformance, crash and corruption simulation, security and capability-escalation tests, performance tests, pilots, benchmark manifests, and release evidence.

It must distinguish planned validation from actual evidence.

The skill files are control documents only in Phase 1. Do not create skill-specific runtime helpers.

---

## 12. Documentation Skeletons

Every required build document must include:

- title and status;
- owner phase;
- controlling source documents;
- purpose;
- required future sections;
- explicit unresolved items;
- regeneration/update trigger;
- a warning that placeholders are non-normative.

Ownership:

- Phase 2: `ARCHITECTURE_DECISIONS.md`, `GLOSSARY.md`, `MVP_SCOPE.md`.
- Phase 3: `DATA_MODEL.md`, `GRAPH_RECORD_FORMAT.md`, `GLCP_CORE_SPEC.md`, `ADAPTER_CONTRACT.md`, `STATE_BOUNDARY_MODEL.md`, `ERROR_REGISTRY.md`.
- Cross-phase: `STORAGE_AND_RECOVERY.md`, `PROJECTION_SPEC.md`, `SECURITY_MODEL.md`, `TEST_MATRIX.md`, `CODEX_BUILD_PLAN.md`, `EVALUATION_PLAN.md`.

Additional requirements:

- `CODEX_BUILD_PLAN.md` must contain Gates A–E and all 22 phases without inventing lower-level implementation details.
- `TEST_MATRIX.md` must define planned evidence columns and must not mark unimplemented tests as passing.
- `schemas/README.md` and `registries/README.md` must list the expected Phase 3 contracts and state that none are frozen in Phase 1.
- Each test-category README must define future purpose and owning phases without fake evidence.
- `docs/phase_prompts/README.md` must list the complete prompt inventory and prohibit phase or gate skipping.

### Complete phase inventory

```text
Guerilla-Kickoff-Prompt.md
PHASE_02_ARCHITECTURE_DECISIONS.md
PHASE_03_MACHINE_CONTRACTS.md
PHASE_04_CONFORMANCE_FIXTURES.md
PHASE_05_CODEC_CONFIG_IDENTIFIERS.md
PHASE_06_APPEND_STORE_TRANSACTIONS_REPLAY.md
PHASE_07_DAG_INTEGRITY_INDEX_QUERY.md
PHASE_08_AUTHORITY_IDENTITY_BOUNDARIES.md
PHASE_09_ADAPTER_SDK_SYNTHETIC_SYSTEMS.md
PHASE_10_OBSERVATION_INGESTION.md
PHASE_11_ACTION_INTENT_IDEMPOTENCY.md
PHASE_12_RECONCILIATION_CONFLICTS.md
PHASE_13_PROJECTIONS_MANIFEST_DIFF.md
PHASE_14_SNAPSHOT_RESUME.md
PHASE_15_INTERNAL_CLI_E2E_SMOKE.md
FINAL_INTERNAL_MVP_CHECKLIST.md
PHASE_16_GLCP_REFERENCE_CLIENT_SERVER.md
PHASE_17_SUBPROCESS_ADAPTER_HOST.md
PHASE_18_TRANSPORT_PARITY_ROBUSTNESS.md
PHASE_19_SECURITY_DURABILITY_ARCHIVE.md
FINAL_EXTERNAL_COMPATIBILITY_CHECKLIST.md
PHASE_20_HETEROGENEOUS_PILOTS.md
PHASE_21_BENCHMARK_EVALUATION.md
PHASE_22_RELEASE_RESEARCH_PACKAGE.md
FINAL_RELEASE_CHECKLIST.md
```

---

## 13. Architecture Source Integrity

Place working copies of the authorized source documents under `docs/architecture/` and `docs/rationale/`.

Preserve their content except for documented line-ending normalization.

Create `docs/architecture/README.md` as a source manifest with:

- original filename;
- repository path;
- SHA-256 digest;
- import date;
- architecture role;
- classification as normative, supporting, or rationale.

Do not rewrite the architecture papers. Do not classify `RELATED_WORK.md` as normative runtime behavior. Keep the architecture note separately identifiable as the controlling rationale for architecture ordering and boundary definition.

---

## 14. README Requirements

### `README.md`

Include:

- product definition;
- current status: architecture-complete / pre-prototype;
- explicit statement that no working graph runtime exists yet;
- authority and state-boundary distinction;
- Gates A–E;
- contributor installation;
- harmless version command;
- links to architecture sources, workflow, `AGENTS.md`, and `README_DEV.md`;
- explicit non-claims.

### `README_DEV.md`

Include copy-pasteable commands for:

- prerequisites and clean setup;
- locked dependency installation;
- formatting and linting;
- static analysis;
- tests;
- package build;
- clean-wheel installation smoke test;
- source-integrity verification;
- phase discipline;
- completion evidence;
- Phase 2 handoff.

CI must use the same essential commands.

---

## 15. CI and Local Commands

Create CI that runs from a clean environment and performs:

1. checkout;
2. Python setup for 3.11 and at least one newer supported version;
3. locked dependency installation;
4. formatting check;
5. lint check;
6. static analysis;
7. tests;
8. source distribution and wheel build;
9. wheel installation into a fresh environment;
10. import and CLI help/version smoke checks.

CI must require no secrets, database, service, container, or external system.

Prefer this local sequence:

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
uv build
```

Document the isolated built-wheel test separately.

CI must fail on lock drift, formatting drift, lint/type/test failures, missing required repository artifacts, build failure, installed-wheel import failure, or CLI version failure.

---

## 16. Required Tests

### Unit tests

`tests/unit/test_import.py` must verify:

- `import guerilla` succeeds;
- `__version__` exists;
- import performs no filesystem mutation, network call, process launch, or environment rewrite.

`tests/unit/test_version.py` must verify:

- the library version has one canonical source;
- executable and module CLI versions agree with the library version;
- output is deterministic;
- help/version return success;
- unsupported arguments fail without side effects.

### Repository-contract tests

`tests/repository/test_repository_contract.py` must verify:

- required top-level files exist;
- all five skills exist and are non-empty;
- required build-document skeletons exist;
- architecture sources and the rationale note are present;
- source digests are recorded;
- schema and registry directories contain no falsely frozen domain contracts;
- required package directories exist;
- no prohibited service/integration scaffold exists;
- the prompt inventory contains Phases 1–22 and all three final checklists;
- placeholder documents identify status and owner phase without claiming completion.

Avoid exact-prose tests unless the prose encodes a locked invariant.

### Clean-install smoke test

Prove that a fresh environment can:

1. install the built wheel rather than the source tree;
2. import `guerilla`;
3. read the version;
4. run CLI help and version;
5. confirm that no workspace, graph, database, cache, or external-state files are created.

No Phase 1 test may fabricate graph records or external actions.

---

## 17. Implementation Order

Execute in this order:

1. Inventory the repository and authorized sources.
2. Detect and preserve non-conflicting existing content.
3. Create the target structure.
4. Place, classify, and hash architecture sources.
5. Configure package metadata and the locked environment.
6. Implement package import and one version source.
7. Implement CLI help/version only.
8. Create `AGENTS.md`.
9. Create all five skills.
10. Create build-document skeletons and phase inventory.
11. Create README files.
12. Create tests.
13. Configure CI from the documented local commands.
14. Build source distribution and wheel.
15. Install the wheel in a clean environment and run smoke checks.
16. Run the complete validation sequence.
17. Audit the diff against prohibited scope and reserved decisions.
18. Produce the completion report and Phase 2 handoff.

Do not allow generated documentation to overwrite architecture sources.

---

## 18. Required Failure Checks

Test or inspect:

- package import outside the repository working directory;
- CLI version from an installed wheel;
- import/version from a read-only current directory;
- missing `.env` and optional environment values;
- malformed CLI arguments;
- a machine with no database, service, or container runtime;
- architecture-source checksum mismatch;
- accidental Phase 2+ domain contracts under `schemas/` or `registries/`;
- placeholder documents without status or owner phase;
- accidental modification of source papers.

Where automation would require out-of-scope runtime behavior, record precise inspection evidence instead.

---

## 19. Stop Conditions

Stop work on the affected area and report the blocker if:

- an authorized source is missing or unreadable;
- controlling sources conflict in a way that changes Phase 1 scope;
- pre-existing runtime code has uncertain authority or provenance;
- package naming conflicts with an authoritative existing decision;
- a tooling choice would settle a decision reserved for Phase 2;
- the scaffold would create a second source of truth;
- wheel testing cannot be isolated from the source checkout;
- a required test would need prohibited runtime behavior;
- a source paper would require substantive modification to fit the repository.

Continue unaffected Phase 1 work. Do not hide a blocker behind a stub that appears complete.

---

## 20. Exit Criteria

Phase 1 is complete only when:

1. The repository matches the required structure or documents justified equivalents.
2. Authorized sources are present, classified, and recorded with SHA-256 digests.
3. Source papers are unchanged in substance.
4. `AGENTS.md` is complete and Guerilla-specific.
5. All five skills are complete and have distinct ownership boundaries.
6. Every required build document exists with status and owner-phase metadata.
7. The 22 phases and three final checklists are discoverable.
8. The package installs from a clean checkout using a locked workflow.
9. The built wheel installs and imports in a fresh environment.
10. Library and CLI versions agree.
11. Help/version commands create no workspace or data files.
12. Formatting, linting, static analysis, tests, and package build pass.
13. CI executes the same essential checks.
14. Repository-contract tests enforce the Phase 1 artifact boundary.
15. No substantive Guerilla runtime behavior exists.
16. No Phase 2+ architecture decision has been frozen accidentally.
17. README files accurately state architecture-complete / pre-prototype status.
18. Every completion claim links to a command, test, file, digest, or inspection result.

File existence alone is not sufficient evidence.

---

## 21. Completion Report

Return these sections:

### Phase Result

Use exactly one:

- `PASS — Phase 1 complete`
- `PARTIAL — unaffected scaffold complete; blockers remain`
- `FAIL — Phase 1 exit criteria not met`

### Delivered Artifacts

Group files by repository controls, agent instructions/skills, documentation, package scaffold, tests, CI/build configuration, and source manifest.

### Validation Evidence

For formatting, linting, static analysis, tests, build, wheel install, import, CLI help, and CLI version, provide:

```text
Command | Exit code | Result | Evidence path
```

### Exit-Criteria Matrix

Report all 18 criteria as:

```text
Criterion | Status | Evidence | Notes
```

### Source Integrity

List imported sources, SHA-256 digests, any line-ending normalization, and confirmation that no substantive source content changed.

### Scope Audit

State whether prohibited runtime behavior or reserved architecture decisions were introduced. List every exception.

### Blockers and Contradictions

List blockers and source conflicts, or `None`.

### Phase 2 Handoff

List only:

- confirmed repository baseline;
- unresolved architecture decisions;
- source conflicts requiring adjudication;
- placeholders for canonicalization and identifier decision tests;
- no recommendations outside Phase 2 scope.

### Git Summary

List changed files, untracked files, generated files, and files intentionally not modified.

Do not claim Phase 2 readiness when source integrity, reproducibility, or scope-boundary criteria fail.

---

## 22. Final Instruction

Build only the repository and control foundation.

Do not demonstrate Guerilla by implementing a small graph store, mock adapter, MCP server, provisional schema, or simplified action flow. Those shortcuts would embed state, lineage, authority, or transport assumptions before the contract freeze.

The correct result is:

> A clean, installable, testable, agent-governed repository in which every later implementation phase has an explicit source, owner, boundary, test category, and exit gate—and in which no hidden runtime architecture has been introduced.
