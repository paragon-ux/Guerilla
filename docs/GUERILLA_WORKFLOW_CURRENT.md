# Guerilla Workflow

**Version:** 1.0  
**Date:** 2026-07-13  
**Status:** Authoritative build workflow proposal for the supplied Guerilla architecture  
**Reference pattern:** Patch-DIFF workflow and current Patch-DIFF repository organization

---

## 1. Purpose and Source Boundary

This workflow converts the supplied Guerilla architecture into an executable build sequence.

It is based only on:

1. `GUERILLA_CONCEPT_PAPER.md`;
2. `GUERILLA_IMPLEMENTATION_SPEC.md`;
3. `GUERILLA_PROTOCOL_SPEC.md`;
4. `GUERILLA_SNAPSHOT.md`;
5. `CURRENT_STATUS_MATRIX.md`;
6. `RELATED_WORK.md`;
7. `Rationale/Note-on-Architecture.md`;
8. the supplied Patch-DIFF workflow; and
9. the current public Patch-DIFF repository overview, used only to confirm the workflow pattern and repository artifact structure.

Prior Guerilla edit ledgers, prior implementation plans, prior workflows, and unrelated architecture papers are outside this workflow's source boundary.

---

## 2. Executive Determination

Guerilla is at the **architecture-complete / pre-prototype** stage.

The supplied papers establish a coherent system identity:

> Guerilla maintains one authoritative cross-system causal-lineage and continuity graph while leaving application-state authority with the integrated external systems.

The architecture is sufficiently detailed to start implementation planning, but it is not yet safe to start unconstrained runtime coding. The first implementation dependency is a machine-readable contract freeze.

### 2.1 Substantially complete

- problem definition and research positioning;
- external-state versus lineage-authority boundary;
- one logically authoritative append-only DAG;
- immutable revision model;
- eight core node types and nine core relationship types;
- reification of symmetric, cyclic, and non-causal assertions;
- intent-before-external-action lifecycle;
- idempotency and uncertain-outcome reconciliation semantics;
- conflict and decision semantics;
- source-bound derived views;
- local single-writer MVP boundary;
- transport-independent protocol operation families;
- reference filesystem layout;
- MVP and conformance requirements.

### 2.2 Not yet complete

- frozen canonical serialization profile;
- selected identifier scheme;
- exact record and commit hash construction;
- published JSON Schemas;
- error and enum registries;
- executable graph kernel;
- transaction durability and crash recovery;
- cycle-validation implementation;
- rebuildable index;
- adapter SDK and adapter host;
- synthetic heterogeneous external systems;
- action interruption and reconciliation proof;
- projection implementation;
- protocol client/server interoperability;
- security and operational hardening;
- real integrations, benchmarks, or empirical results.

### 2.3 Build consequence

The workflow must not begin with MCP, HTTP, a hosted service, real adapters, or a UI. The architecture note requires state continuity and lineage ownership to be established before the architecture is finalized. Guerilla must therefore prove its local authoritative graph, state boundaries, replay, and reconciliation behavior before adding transports or production integrations.

---

## 3. Patch-DIFF Workflow Pattern Applied to Guerilla

Patch-DIFF used the following disciplined sequence:

```text
core papers
→ AGENTS.md
→ focused agent skills
→ regenerable build documents
→ kickoff prompt
→ ordered phase prompts
→ final checklist
→ external compatibility stage
```

Guerilla should retain that sequence but use four stages rather than treating external MCP compatibility as part of the first executable boundary.

```text
Stage 0 — Architecture and machine-contract freeze
Stage 1 — Internal local runtime MVP
Stage 2 — External protocol and adapter compatibility
Stage 3 — Heterogeneous pilots, evaluation, and release
```

The principal difference is architectural:

```text
Patch-DIFF Stage 1: internal MCP around a deterministic editing backend
Guerilla Stage 1: local graph-and-continuity kernel with no required transport
```

MCP, HTTP, or another message transport may be added in Stage 2 as a thin binding over the already-conforming runtime. No transport may become a second mutation path or redefine GLCP semantics.

---

# Stage 0 — Architecture and Machine-Contract Freeze

## 4. Current Design Papers

The supplied four-paper set already satisfies the conceptual-paper portion of the Patch-DIFF workflow:

| Current document | Role in the build |
|---|---|
| `GUERILLA_CONCEPT_PAPER.md` | Product identity, state ownership, graph thesis, use cases, evaluation questions |
| `GUERILLA_IMPLEMENTATION_SPEC.md` | Normative runtime components, storage, flows, security, testing, MVP acceptance |
| `GUERILLA_PROTOCOL_SPEC.md` | Transport-independent GLCP operations, envelopes, errors, retry and compatibility semantics |
| `GUERILLA_SNAPSHOT.md` | Current decisions, unresolved questions, milestones, readiness gates |

Supporting papers and notes:

| Document | Role |
|---|---|
| `CURRENT_STATUS_MATRIX.md` | Implementation readiness and critical path |
| `RELATED_WORK.md` | Comparative positioning and evaluation framing; non-normative for runtime behavior |
| `Rationale/Note-on-Architecture.md` | Controlling rationale for state continuity, authoritative lineage, and hybrid boundaries |

### Paper handling rule

The papers are architecture inputs, not substitutes for executable contracts. Do not begin runtime phases by repeatedly rewriting the four papers. Resolve remaining choices through versioned architecture decisions and regenerate the snapshot when a stage closes.

---

## 5. Required Architecture-Freeze Documents

Create these before writing mutating runtime code:

1. `docs/ARCHITECTURE_DECISIONS.md`
2. `docs/GLOSSARY.md`
3. `docs/MVP_SCOPE.md`
4. `docs/DATA_MODEL.md`
5. `docs/GRAPH_RECORD_FORMAT.md`
6. `docs/GLCP_CORE_SPEC.md`
7. `docs/ADAPTER_CONTRACT.md`
8. `docs/STATE_BOUNDARY_MODEL.md`
9. `docs/ERROR_REGISTRY.md`
10. `docs/TEST_MATRIX.md`
11. `docs/CODEX_BUILD_PLAN.md`

### 5.1 Decisions that must be frozen

`ARCHITECTURE_DECISIONS.md` must settle:

- canonical JSON profile;
- UUIDv7 or ULID as the default identifier scheme;
- identifier prefixes and validation rules;
- record hash and commit hash inputs;
- transaction ordering and canonical record order;
- writer-lock mechanism;
- atomic append, flush, and recovery behavior;
- local/network-filesystem support boundary;
- payload retention and redaction defaults;
- adapter execution model for the MVP;
- authorization profile for local operation;
- projection policy representation;
- archive thresholds and sealed-segment rules;
- extension namespace governance.

### 5.2 Contract outputs

The machine-contract freeze must publish:

```text
schemas/
├── graph-header.schema.json
├── transaction.schema.json
├── commit.schema.json
├── node.schema.json
├── edge.schema.json
├── authority-envelope.schema.json
├── state-boundary.schema.json
├── provenance.schema.json
├── payload-reference.schema.json
├── adapter-descriptor.schema.json
├── adapter-observe.schema.json
├── adapter-act.schema.json
├── adapter-evaluate.schema.json
├── adapter-reconcile.schema.json
├── conflict.schema.json
├── snapshot.schema.json
├── projection-metadata.schema.json
├── protocol-envelope.schema.json
├── protocol-request.schema.json
├── protocol-response.schema.json
└── protocol-error.schema.json
```

Required registries:

```text
registries/
├── node-types.json
├── relationship-types.json
├── conflict-types.json
├── capability-values.json
├── error-codes.json
└── extension-namespaces.json
```

Required fixture corpus:

```text
tests/fixtures/contracts/
├── valid/
├── invalid/
├── compatibility/
└── canonicalization/
```

### Stage 0 exit gate

Stage 0 is complete only when:

1. the four design papers and all build documents use the same terms and invariants;
2. every core record and message has a versioned schema;
3. every enum and error code is registered;
4. canonicalization and hash vectors are published;
5. two independent validation paths return the same result for every fixture;
6. no unresolved architecture choice can change record identity, transaction validity, authority, or replay semantics.

---

## 6. `AGENTS.md`

Create one root `AGENTS.md`, targeted at approximately 300–450 lines. It is the coding-agent control surface, not a replacement specification.

It must contain:

- Guerilla's product identity;
- source-of-truth order;
- locked invariants;
- authoritative versus derived storage boundaries;
- workspace layout;
- mutation and transaction rules;
- graph validation order;
- adapter trust and authority rules;
- intent-before-action and reconciliation requirements;
- security rules;
- test commands and phase gates;
- prohibited shortcuts;
- phase-completion reporting format.

### 6.1 Source-of-truth order

Use this order:

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
11. current four-paper architecture set

If the implementation and a machine-readable schema conflict, the schema and frozen architecture decision control. If two machine-readable contracts conflict, mutating operations must stop until the conflict is resolved.

### 6.2 Non-negotiable instructions

`AGENTS.md` must prohibit agents from:

- making a projection authoritative;
- writing external application state directly;
- recording an external action before committing its intent;
- replaying external actions during graph replay;
- weakening cycle validation for convenience;
- inserting symmetric or cyclic domain relationships as direct authoritative edges;
- repairing graph records from SQLite or another derived index;
- treating payloads as executable content;
- auto-retrying an unknown external outcome without reconciliation;
- adding a real adapter before synthetic adapter conformance passes;
- adding a transport-specific mutation path.

---

## 7. Agent Skills

Create five focused skills under `.agents/skills/`. Each skill should be approximately 200–350 lines and include purpose, activation criteria, required reading, invariants, procedure, tests, stop conditions, and completion evidence.

```text
.agents/skills/
├── guerilla-contracts-modeling/SKILL.md
├── guerilla-graph-kernel-storage/SKILL.md
├── guerilla-adapter-continuity-reconciliation/SKILL.md
├── guerilla-projections-snapshot-resume/SKILL.md
└── guerilla-testing-security-evaluation/SKILL.md
```

### 7.1 `guerilla-contracts-modeling`

Owns:

- schemas and registries;
- canonicalization fixtures;
- node and edge model consistency;
- authority envelopes;
- protocol envelopes and errors;
- compatibility review.

### 7.2 `guerilla-graph-kernel-storage`

Owns:

- append-only storage;
- transactions and commit chain;
- DAG validation;
- replay and verification;
- writer lock;
- payload references;
- SQLite index rebuild.

### 7.3 `guerilla-adapter-continuity-reconciliation`

Owns:

- adapter descriptor and host;
- observation ingestion;
- state-boundary enforcement;
- intent-before-action;
- idempotency;
- interrupted-action reconciliation;
- conflict and decision recording.

### 7.4 `guerilla-projections-snapshot-resume`

Owns:

- lineage and dependency views;
- manifests;
- conflict and progress views;
- snapshots;
- diff;
- resume context;
- deterministic regeneration.

### 7.5 `guerilla-testing-security-evaluation`

Owns:

- conformance fixtures;
- crash and corruption simulation;
- security tests;
- adapter capability escalation tests;
- performance tests;
- pilot and benchmark protocol;
- release evidence.

---

## 8. Reference Build Stack

The architecture is transport- and language-independent, but the first reference implementation needs one concrete stack.

### 8.1 Required local profile

- Python 3.11 or later;
- `pyproject.toml` package and locked dependency file;
- JSON Schema Draft 2020-12;
- deterministic canonical JSON implementation selected in Stage 0;
- SHA-256 for record, payload, and commit integrity;
- append-only JSON Lines graph segments;
- SQLite for the rebuildable non-authoritative index;
- TOML workspace configuration;
- local single-writer lock;
- CLI and Python library interfaces for Stage 1;
- `pytest` for tests;
- property-based testing for transaction, hashing, and DAG invariants;
- no required Postgres, message broker, container runtime, or network service for the internal MVP.

### 8.2 Dependency policy

- Use the standard library for hashing, SQLite, JSON parsing, path handling, and TOML reading where practical.
- Pin the canonicalization and schema-validation libraries.
- Keep record validation independent from in-memory model classes.
- Keep transport dependencies out of the graph, storage, authority, and continuity modules.
- Do not introduce an ORM for the authoritative JSONL graph.
- Do not make SQLite a write authority.

### 8.3 Adapter execution profile

- Stage 1 synthetic adapters run in-process for deterministic conformance testing.
- Stage 2 adds a subprocess adapter-host profile with structured stdin/stdout or equivalent typed invocation.
- Container or remote adapter isolation remains optional until after the subprocess profile and threat model pass.

---

## 9. Reference Repository Layout

```text
Guerilla/
├── AGENTS.md
├── README.md
├── README_DEV.md
├── pyproject.toml
├── .env.example
├── .agents/
│   └── skills/
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
│   ├── phase_prompts/
│   └── Archive/
├── schemas/
├── registries/
├── src/guerilla/
│   ├── config/
│   ├── contracts/
│   ├── codec/
│   ├── protocol/
│   ├── graph/
│   ├── storage/
│   ├── payloads/
│   ├── index/
│   ├── authority/
│   ├── identity/
│   ├── adapters/
│   ├── orchestration/
│   ├── reconciliation/
│   ├── conflicts/
│   ├── projections/
│   ├── cli/
│   └── observability/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── conformance/
│   ├── crash/
│   ├── security/
│   ├── performance/
│   └── fixtures/
└── examples/
    ├── transactional_service/
    ├── reconstructed_filesystem/
    └── asynchronous_unknown_outcome/
```

---

# Stage 1 — Internal Local Runtime MVP

## 10. Stage 1 Build Rule

Stage 1 exposes Guerilla through a Python library and CLI only. A minimal local service may be added for development after the CLI is complete, but it is not an MVP dependency.

The authoritative flow is:

```text
validated request
→ staged transaction
→ invariant checks
→ atomic graph commit
→ rebuildable index update
→ derived response
```

For external actions:

```text
commit intent
→ invoke adapter
→ record result or unknown outcome
→ observe after-state
→ evaluate
→ continue or create conflict
```

---

## 11. Stage 1 Phase Prompts

Stage 1 uses the kickoff prompt as Phase 1 and continues through Phase 15.

### Phase 1 — `Guerilla-Kickoff-Prompt.md`

**Purpose:** Establish repository structure, source-of-truth rules, development commands, and phase discipline.

**Deliver:**

- repository scaffold;
- `AGENTS.md`;
- five skill directories;
- documentation skeleton;
- test directory skeleton;
- empty package modules;
- CI running formatting, static checks, and placeholder tests.

**Prohibited:** Runtime behavior beyond harmless package and CLI version reporting.

**Exit:** All source documents are discoverable and the repository can be installed and tested from a clean environment.

### Phase 2 — `PHASE_02_ARCHITECTURE_DECISIONS.md`

**Purpose:** Freeze architecture choices that affect identity, durability, authority, and compatibility.

**Deliver:**

- completed `ARCHITECTURE_DECISIONS.md`;
- completed `GLOSSARY.md`;
- completed `MVP_SCOPE.md`;
- decision tests or executable vectors for canonicalization and identifiers.

**Exit:** No unresolved decision can change a record hash, identifier, transaction validity, authority rule, or replay outcome.

### Phase 3 — `PHASE_03_MACHINE_CONTRACTS.md`

**Purpose:** Publish schemas and registries before runtime implementation.

**Deliver:**

- all Stage 0 schemas;
- enum and error registries;
- schema versioning policy;
- generated documentation examples.

**Exit:** Every example in the protocol and data model validates or fails for the intended reason.

### Phase 4 — `PHASE_04_CONFORMANCE_FIXTURES.md`

**Purpose:** Build independent valid, invalid, compatibility, and canonicalization fixtures.

**Deliver:**

- contract fixture corpus;
- independent schema validator command;
- golden canonical byte and hash vectors;
- unknown-field and version-negotiation fixtures.

**Exit:** Two validators agree across the full corpus and produce stable machine-readable errors.

### Phase 5 — `PHASE_05_CODEC_CONFIG_IDENTIFIERS.md`

**Purpose:** Implement the configuration loader, record codec, canonical encoding, identifiers, timestamps, and hashing.

**Deliver:**

- configuration and policy loader;
- canonical serializer/deserializer;
- identifier generator and parser;
- record and payload hashing;
- protocol envelope validation;
- immutable internal record representations.

**Tests:** Golden vectors, cross-process determinism, unsupported-version rejection, unknown-field compatibility, invalid-config mutation block.

**Exit:** Equal logical records produce equal canonical bytes and hashes on repeated clean runs.

### Phase 6 — `PHASE_06_APPEND_STORE_TRANSACTIONS_REPLAY.md`

**Purpose:** Implement authoritative persistence.

**Deliver:**

- workspace initialization;
- graph header;
- writer lock;
- transaction staging;
- atomic begin/commit format;
- monotonically increasing graph revision;
- hash-linked commits;
- incomplete transaction handling;
- replay and graph verification;
- content-addressed payload store with hash verification.

**Tests:** Crash before commit, crash during append, truncated tail, previous-commit mismatch, payload hash mismatch, concurrent writer rejection.

**Exit:** Replay ignores incomplete work, detects corruption, and reconstructs exactly the committed graph revision without invoking external actions.

### Phase 7 — `PHASE_07_DAG_INTEGRITY_INDEX_QUERY.md`

**Purpose:** Implement graph correctness and non-authoritative query acceleration.

**Deliver:**

- node and edge uniqueness checks;
- endpoint validation;
- self-loop and cycle rejection;
- relationship compatibility checks;
- supersession rules;
- graph-head calculation;
- reified non-DAG relationship fixtures;
- SQLite index;
- index deletion and rebuild;
- exact-revision reads and bounded lineage traversal.

**Tests:** Linear history, branching, multi-parent convergence, supersession, cycle attempts, missing endpoints, stale index, index corruption.

**Exit:** The index can be deleted and rebuilt from graph records without lineage loss or authority inversion.

### Phase 8 — `PHASE_08_AUTHORITY_IDENTITY_BOUNDARIES.md`

**Purpose:** Implement the authority and identity registry before adapter mutation exists.

**Deliver:**

- external-system registry;
- adapter identity and version registry;
- state-boundary declarations;
- operation permissions;
- external-to-Guerilla identity mappings;
- identity-stability classification;
- external revision preservation;
- ownership-conflict creation.

**Tests:** Unauthorized boundary access, identity reuse, rename, deletion, alias collision, external revision preservation, actor-claim rejection.

**Exit:** A client or adapter cannot acquire authority by declaring it in payload content.

### Phase 9 — `PHASE_09_ADAPTER_SDK_SYNTHETIC_SYSTEMS.md`

**Purpose:** Implement the adapter contract and prove continuity-model neutrality.

**Deliver:**

- adapter descriptor;
- `describe`, `observe`, `act`, `evaluate`, and `reconcile` interfaces;
- adapter host;
- capability validation;
- timeout and resource-limit behavior;
- three synthetic systems:
  1. transactional revisioned service;
  2. filesystem-based reconstructed-state system;
  3. asynchronous service with unknown outcomes.

**Tests:** Descriptor completeness, unsupported capability, consistency declarations, state-boundary enforcement, identity collision, malformed adapter response.

**Exit:** All three synthetic systems run through the same graph core without graph-specific adapter exceptions.

### Phase 10 — `PHASE_10_OBSERVATION_INGESTION.md`

**Purpose:** Implement observation-first ingestion.

**Deliver:**

- goal and operation creation;
- observation ingestion;
- authority envelopes;
- external event ingestion;
- duplicate observation handling;
- external, receipt, and commit timestamps;
- correlation and causation preservation.

**Tests:** Duplicate ingestion, stale observation, out-of-order events, unknown ordering, missing provenance, unauthorized observation scope.

**Exit:** External state is represented as bounded observations without Guerilla claiming application-state ownership.

### Phase 11 — `PHASE_11_ACTION_INTENT_IDEMPOTENCY.md`

**Purpose:** Implement safe external action invocation.

**Deliver:**

- action-intent node and commit;
- graph revision guard;
- idempotency store and retention metadata;
- structured adapter invocation;
- accepted, rejected, failed, pending, and unknown result recording;
- after-state observation trigger.

**Tests:** Intent-before-call proof, same-key/same-content replay, same-key/different-content conflict, stale graph revision, external rejection preservation.

**Exit:** No external mutation can be initiated by the runtime without a committed intent and idempotency context.

### Phase 12 — `PHASE_12_RECONCILIATION_CONFLICTS.md`

**Purpose:** Implement Guerilla's distinctive uncertain-action recovery and explicit conflict handling.

**Deliver:**

- reconciliation engine;
- unknown-outcome classification;
- duplicate-action detection;
- missing-lineage recovery event;
- stale/divergent revision conflicts;
- conflict evidence model;
- decision and resolution flow;
- continuation operation creation.

**Failure simulations:**

- before intent commit;
- after intent commit, before external call;
- during external call;
- after external completion, before result commit;
- after result commit, before after-state observation;
- during reconciliation.

**Exit:** Retrying an interrupted operation cannot silently duplicate an external mutation, and the original intent/result records are never rewritten.

### Phase 13 — `PHASE_13_PROJECTIONS_MANIFEST_DIFF.md`

**Purpose:** Implement deterministic derived views.

**Deliver in order:**

1. lineage view;
2. dependency view;
3. conflict view;
4. latest-revision manifest;
5. graph diff;
6. progress view;
7. requirement-traceability-style view.

Every result must include:

- source graph revision and commit hash;
- source node set or reproducible query;
- transformation and policy versions;
- generation time;
- freshness summary;
- information-loss declaration;
- result hash.

**Exit:** Deleting all persisted projections does not remove authoritative information, and regeneration from the same revision and policy yields the same result hash.

### Phase 14 — `PHASE_14_SNAPSHOT_RESUME.md`

**Purpose:** Implement verified continuity boundaries.

**Deliver:**

- snapshot node creation;
- materialized summary payload;
- snapshot verification;
- graph heads;
- open goals and unresolved conflicts;
- latest relevant artifact revisions;
- freshness and refresh requirements;
- next eligible operations;
- resume context.

**Tests:** Tampered summary, missing source, stale external observation, index deletion, policy-version difference, replay after snapshot.

**Exit:** A clean process can resume from a verified snapshot while distinguishing immutable graph facts from external observations that need refresh.

### Phase 15 — `PHASE_15_INTERNAL_CLI_E2E_SMOKE.md`

**Purpose:** Complete the internal MVP surface and end-to-end proof.

**Required CLI families:**

```text
guerilla workspace init|verify
guerilla graph append|verify|replay|export|archive
guerilla node get
guerilla edge get
guerilla lineage query|heads
guerilla adapter list|describe|validate
guerilla observe
guerilla act
guerilla reconcile
guerilla goal create|get
guerilla operation create|get
guerilla evaluation record|get
guerilla conflict list|get|resolve
guerilla decision record
guerilla view generate
guerilla manifest generate|verify
guerilla snapshot create|get|verify|resume
guerilla diff generate
```

**Deliver:**

- stable exit codes;
- JSON output mode;
- human-readable output mode;
- one E2E scenario per synthetic external system;
- internal MVP documentation;
- clean-install smoke script.

**Exit:** All fifteen MVP acceptance criteria in the implementation specification are demonstrated by automated tests and preserved artifacts.

---

## 12. Stage 1 Final Checklist

Create:

```text
docs/phase_prompts/FINAL_INTERNAL_MVP_CHECKLIST.md
```

The checklist must verify:

1. workspace initialization and verification;
2. atomic valid transaction commit;
3. incomplete transaction exclusion on replay;
4. cycle rejection;
5. authority and external revision preservation;
6. committed intent before external invocation;
7. reconciliation without duplicate mutation;
8. idempotency conflict behavior;
9. explicit stale-revision conflict;
10. deterministic projection regeneration;
11. snapshot heads and freshness reporting;
12. index deletion and rebuild;
13. replay without external action;
14. payload non-execution and redaction;
15. full graph and adapter conformance pass.

A manual claim is not sufficient. Each item must link to an automated test, fixture, and machine-readable result.

---

# Stage 2 — External Protocol and Adapter Compatibility

## 13. Stage 2 Objective

Stage 2 proves that the internal runtime can be used by external clients and isolated adapters without changing the authoritative mutation semantics.

The reference external profile should support:

- one subprocess adapter binding;
- one local JSON-RPC or HTTP binding for GLCP;
- an optional MCP binding generated over the same operation contracts;
- a reference client;
- transport-parity tests.

MCP is optional. GLCP remains the semantic authority.

---

## 14. Stage 2 Regenerated Build Documents

Regenerate or add:

1. `docs/GLCP_CORE_SPEC.md`
2. `docs/ADAPTER_CONTRACT.md`
3. `docs/TRANSPORT_BINDINGS.md`
4. `docs/ADAPTER_AUTHORING_GUIDE.md`
5. `docs/SECURITY_MODEL.md`
6. `docs/TEST_MATRIX.md`
7. `docs/CODEX_BUILD_PLAN.md`
8. `README.md`
9. `README_DEV.md`
10. `README_INTERNAL_RUNTIME.md`

The generated transport schemas must derive from the Stage 0 contracts rather than being rewritten by hand.

---

## 15. Stage 2 Phase Prompts

### Phase 16 — `PHASE_16_GLCP_REFERENCE_CLIENT_SERVER.md`

**Deliver:**

- reference client and server/binding;
- protocol negotiation;
- capabilities;
- request/response envelopes;
- errors, retries, pagination, and exact-revision reads;
- authentication-principal to actor mapping.

**Exit:** Reference client and runtime interoperate against all core operations without bypassing the internal service boundary.

### Phase 17 — `PHASE_17_SUBPROCESS_ADAPTER_HOST.md`

**Deliver:**

- subprocess lifecycle;
- typed request/response channel;
- timeout, cancellation, resource, and output limits;
- credential and environment scoping;
- capability-escalation rejection;
- crash and restart behavior.

**Exit:** A subprocess adapter cannot write the graph directly, expand its declared authority, or return unvalidated records.

### Phase 18 — `PHASE_18_TRANSPORT_PARITY_ROBUSTNESS.md`

**Deliver:**

- library/CLI/reference-transport parity tests;
- malformed and partial response tests;
- unknown-field and version compatibility tests;
- cursor and pagination tests;
- retry-safety tests;
- optional MCP adapter over the same contracts.

**Exit:** Equivalent valid requests produce equivalent committed graph state across every supported transport.

### Phase 19 — `PHASE_19_SECURITY_DURABILITY_ARCHIVE.md`

**Deliver:**

- finalized local authorization profile;
- path and endpoint restrictions;
- secret redaction;
- payload retention and deletion behavior;
- unsafe-deserialization review;
- graph archive sealing and verification;
- backup and restore;
- denial-of-service limits;
- metrics and operational logs;
- corruption-recovery runbook.

**Exit:** Security, crash, corruption, archive, backup, and restore tests pass in a clean environment.

---

## 16. Stage 2 Final Checklist

Create:

```text
docs/phase_prompts/FINAL_EXTERNAL_COMPATIBILITY_CHECKLIST.md
```

It must prove:

- client/server schema interoperability;
- protocol negotiation and compatibility;
- identical internal and external mutation semantics;
- adapter subprocess isolation boundaries;
- authority enforcement from authenticated principals;
- unknown-outcome reconciliation through the external binding;
- deterministic snapshot and manifest regeneration;
- transport-independent error and retry behavior;
- archive, restore, and corruption recovery;
- optional MCP parity, when MCP is included.

---

# Stage 3 — Heterogeneous Pilots, Evaluation, and Release

## 17. Stage 3 Objective

Stage 3 converts the architecture into an empirical systems contribution. Basic append-only DAG storage is not the research result. The contribution must be demonstrated around:

- one lineage authority across heterogeneous systems;
- preservation of external application-state authority;
- explicit state boundaries;
- intent-before-action provenance;
- recovery from uncertain external outcomes;
- deterministic, source-bound continuity views.

---

## 18. Stage 3 Phase Prompts

### Phase 20 — `PHASE_20_HETEROGENEOUS_PILOTS.md`

Integrate at least three materially different systems:

1. a transactional revisioned system;
2. a filesystem or reconstructed-state system;
3. an asynchronous, batch, or event-oriented system.

At least two must have substantially different consistency and ownership models.

**Deliver:**

- adapters;
- boundary declarations;
- capability descriptors;
- conformance results;
- action interruption demonstrations;
- snapshot/resume demonstrations;
- documented authority maps.

**Exit:** No pilot requires Guerilla to become the application's state owner or to weaken graph invariants.

### Phase 21 — `PHASE_21_BENCHMARK_EVALUATION.md`

Evaluate:

| Research question | Required measurement |
|---|---|
| Resume accuracy | Correct heads, stale observations, conflicts, refresh requirements, and next operations |
| Lineage completeness | Artifact revisions linked to producer, observation, actor, result, and evaluation |
| Authority preservation | Direct or replacement application-state writes performed by Guerilla; target zero |
| Projection reproducibility | Result-hash equality for same graph revision, query, transformation, and policy |
| Uncertain-action safety | Duplicate external mutations and unresolved classifications after fault injection |
| Runtime cost | Append latency, cycle-check time, replay, index rebuild, traversal, projections, snapshot size |
| Storage cost | Graph growth, payload deduplication, index size, archive ratio |

Comparators should include, where practical:

- summary-only or conversation continuity;
- conventional logs;
- workflow history;
- provenance-only recording;
- Guerilla's full intent-result-reconciliation graph.

**Exit:** Results and limitations are reproducible from a committed benchmark manifest.

### Phase 22 — `PHASE_22_RELEASE_RESEARCH_PACKAGE.md`

**Deliver:**

- versioned release;
- migration and compatibility notes;
- complete examples;
- conformance suite;
- benchmark fixtures and results;
- security review;
- operations guide;
- architecture snapshot regenerated from implemented reality;
- paper-ready evaluation tables and limitations;
- release checklist.

**Exit:** A third party can install the project, run the conformance suite, reproduce the pilots, and verify the published benchmark artifacts.

---

## 19. Final Release Checklist

Create:

```text
docs/phase_prompts/FINAL_RELEASE_CHECKLIST.md
```

The release is blocked unless:

- all core schemas are frozen and versioned;
- canonical hashing has published vectors;
- graph replay is deterministic;
- cycle rejection is complete;
- index rebuild is lossless;
- adapter capabilities are machine-readable;
- state-boundary enforcement is tested;
- idempotency and reconciliation are demonstrated;
- projections cite source revisions and policies;
- payload retention and redaction are approved;
- authorization is enforced;
- crash and corruption recovery pass;
- performance limits are measured;
- at least two materially different state models are integrated without authority overlap;
- the benchmark package is reproducible;
- the snapshot accurately distinguishes implemented, tested, deferred, and proposed capabilities.

---

## 20. Complete Phase-Prompt Inventory

```text
docs/phase_prompts/
├── Guerilla-Kickoff-Prompt.md
├── PHASE_02_ARCHITECTURE_DECISIONS.md
├── PHASE_03_MACHINE_CONTRACTS.md
├── PHASE_04_CONFORMANCE_FIXTURES.md
├── PHASE_05_CODEC_CONFIG_IDENTIFIERS.md
├── PHASE_06_APPEND_STORE_TRANSACTIONS_REPLAY.md
├── PHASE_07_DAG_INTEGRITY_INDEX_QUERY.md
├── PHASE_08_AUTHORITY_IDENTITY_BOUNDARIES.md
├── PHASE_09_ADAPTER_SDK_SYNTHETIC_SYSTEMS.md
├── PHASE_10_OBSERVATION_INGESTION.md
├── PHASE_11_ACTION_INTENT_IDEMPOTENCY.md
├── PHASE_12_RECONCILIATION_CONFLICTS.md
├── PHASE_13_PROJECTIONS_MANIFEST_DIFF.md
├── PHASE_14_SNAPSHOT_RESUME.md
├── PHASE_15_INTERNAL_CLI_E2E_SMOKE.md
├── FINAL_INTERNAL_MVP_CHECKLIST.md
├── PHASE_16_GLCP_REFERENCE_CLIENT_SERVER.md
├── PHASE_17_SUBPROCESS_ADAPTER_HOST.md
├── PHASE_18_TRANSPORT_PARITY_ROBUSTNESS.md
├── PHASE_19_SECURITY_DURABILITY_ARCHIVE.md
├── FINAL_EXTERNAL_COMPATIBILITY_CHECKLIST.md
├── PHASE_20_HETEROGENEOUS_PILOTS.md
├── PHASE_21_BENCHMARK_EVALUATION.md
├── PHASE_22_RELEASE_RESEARCH_PACKAGE.md
└── FINAL_RELEASE_CHECKLIST.md
```

---

## 21. Required Content of Every Phase Prompt

Every phase prompt must contain:

1. phase objective;
2. permitted scope;
3. prohibited scope;
4. required source documents;
5. files expected to change;
6. invariants that cannot change;
7. implementation tasks in dependency order;
8. required unit, integration, and conformance tests;
9. failure and crash cases;
10. documentation regeneration requirements;
11. exact exit criteria;
12. completion report format;
13. stop conditions when a prerequisite is missing or contradictory.

The agent must not mark a phase complete merely because code exists. Completion requires passing evidence tied to the exit criteria.

---

## 22. Build Gates and Dependency Order

| Gate | Phases | Meaning |
|---|---:|---|
| A — Contract Ready | 1–4 | Architecture decisions, schemas, registries, and fixtures are frozen |
| B — Kernel Ready | 5–8 | Authoritative storage, replay, DAG integrity, index, authority, and identity work |
| C — Continuity MVP | 9–15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI |
| D — External Compatible | 16–19 | Reference transport, isolated adapters, parity, security, durability, archive |
| E — Research Validated | 20–22 | Real heterogeneous pilots, benchmark evidence, reproducible release |

No phase may skip its preceding gate.

The critical path is:

```text
architecture decisions
→ machine contracts
→ codec and hashes
→ append/replay kernel
→ DAG and authority enforcement
→ synthetic adapters
→ intent/idempotency/reconciliation
→ snapshots and resume
→ external bindings
→ heterogeneous pilots
→ evaluation
```

---

## 23. Deferred Until After the MVP

Do not add these during Stages 0–1:

- distributed graph storage;
- multiple concurrent writers;
- consensus or remote locking;
- graph federation;
- automatic graph merge;
- semantic conflict resolution;
- autonomous scheduling;
- multi-agent reservations or leases;
- adapter marketplace;
- cross-workspace identity resolution;
- signed actor attestations;
- selective cryptographic disclosure;
- continuous streaming projections;
- production UI;
- automatic external-state rollback.

Any later addition must preserve immutability, direct-edge acyclicity, external state authority, explicit boundaries, and derived-view non-authority.

---

## 24. Final Build Necessities Summary

Before the first runtime phase, Guerilla needs:

- one frozen architecture decision record;
- one glossary and MVP scope;
- one root `AGENTS.md`;
- five focused agent skills;
- eleven core regenerable build documents;
- versioned JSON Schemas for all records and protocol messages;
- versioned registries for enums, capabilities, extensions, and errors;
- canonicalization and hash test vectors;
- contract conformance fixtures;
- a Python package and clean-install test environment;
- a local JSONL + SQLite workspace profile;
- unit, integration, conformance, crash, security, and performance test suites;
- twenty-two ordered phase prompts;
- three stage checklists;
- three synthetic state models before any real integration;
- at least three heterogeneous pilots before a research or production-readiness claim.

The shortest credible MVP is not “build a graph database.” It is:

> Prove that a local authoritative lineage graph can coordinate heterogeneous external systems, preserve their state authority, safely recover uncertain actions, and regenerate trustworthy continuity views without hidden state ownership.
