# AGENTS.md -- Guerilla Agent Control Surface

**Status:** Gate C in progress -- Phase 9 Adapter SDK complete; agent governance active
**Owner phase:** Phase 1 (Kickoff), updated by every subsequent phase
**Regeneration trigger:** Any phase completion, architecture decision change, or agent-rule update

---

## 1. Project Identity

Guerilla maintains one logically authoritative, append-only cross-system causal-lineage and continuity graph while leaving application-state authority with integrated external systems.

- Guerilla owns graph records, graph identity, graph revisions, lineage assertions, conflicts, decisions, snapshots, and derived-view provenance.
- External systems retain their application state, native revisions, native identifiers, and mutation semantics.
- Adapters may observe or act only inside explicit state boundaries and declared capabilities.
- The authoritative lineage graph is not replaced by summaries, manifests, snapshots, diffs, indexes, caches, or projections.
- State continuity may be online, offline, or reconstructed according to the external system; every boundary must declare which model applies.

---

## 2. Authorized Sources and Source Order

When implementing, consult sources in this priority order:

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
11. The four core architecture papers: `GUERILLA_CONCEPT_PAPER.md`, `GUERILLA_IMPLEMENTATION_SPEC.md`, `GUERILLA_PROTOCOL_SPEC.md`, `GUERILLA_SNAPSHOT.md`
12. `CURRENT_STATUS_MATRIX.md`, `RELATED_WORK.md`, `Rationale/Note-on-Architecture.md`

If the implementation and a machine-readable schema conflict, the schema and frozen architecture decision control.
If two machine-readable contracts conflict, mutating operations must stop until the conflict is resolved.
During Phase 1, incomplete build documents are scaffolds, not normative decisions. Never treat an unresolved marker as an implementation requirement.

---

## 3. Terminology and Locked Distinctions

| Term | Definition |
|---|---|
| **Node** | Immutable record representing a lineage-relevant object or occurrence |
| **Edge** | Typed, directed relationship from an earlier to a later node |
| **Lineage** | Recorded ancestry of an artifact, event, decision, or result |
| **Continuity** | Ability to reconstruct the current work position from committed lineage |
| **Authoritative graph** | The one logical source of Guerilla lineage truth |
| **Projection / View** | Derived representation computed from the authoritative graph; non-authoritative |
| **Adapter** | Controlled integration component translating between an external system and Guerilla |
| **External system** | Any repository, service, database, tool, filesystem, event stream, workflow, or human process integrated with Guerilla |
| **System of record** | External authority for a defined state boundary |
| **Artifact** | Identifiable output, input, or external object relevant to lineage |
| **Actor** | Human, agent, tool, service, or automation responsible for an action |
| **Revision** | Immutable version of a logical entity (graph, artifact, or external) |
| **Event** | Occurrence relevant to continuity |
| **Snapshot** | Immutable record of a selected graph boundary at a specific graph revision |
| **Manifest** | Derived inventory generated from the graph |
| **Conflict** | Evidence-backed incompatibility, ambiguity, stale assumption, or unresolved condition |
| **State boundary** | Declared scope within which one system of record owns application state |

Core node types: goal, artifact, operation, event, evaluation, decision, conflict, snapshot.
Core relationship types: `depends_on`, `produces`, `derives`, `causes`, `evidences`, `evaluated_by`, `superseded_by`, `resolved_by`, `captured_by`.

---

## 4. Locked Invariants

These MUST NOT be violated by any implementation:

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

## 5. Authoritative vs Derived Storage

| Authority | Path | Contents |
|---|---|---|
| **Authoritative lineage** | `.guerilla/graph/active.jsonl`, `.guerilla/graph/archives/` | Immutable nodes, edges, transactions, commits |
| **Referenced data** | `.guerilla/payloads/sha256/` | Optional content-addressed payloads |
| **Configuration authority** | `.guerilla/config.toml` | Workspace and policy configuration |
| **Non-authoritative** | `.guerilla/projections/`, `.guerilla/snapshots/`, `.guerilla/indexes/graph.sqlite` | Derived views, materialized snapshots, rebuildable index |
| **Runtime coordination** | `.guerilla/locks/` | Local writer and maintenance locks |
| **Diagnostic** | `.guerilla/logs/` | Operational logs and metrics |
| **Temporary** | `.guerilla/tmp/` | Uncommitted staging data; MUST NOT be treated as graph state |

---

## 6. External-State Authority and Boundary Rules

- Every adapter must declare the external system it represents, each state boundary it accesses, read/write permissions, external identity and revision semantics, consistency guarantees, and known limitations.
- Adapters translate between external state models and Guerilla without transferring general ownership of external state.
- Recording a reference to an external object does not transfer ownership of that object.
- An adapter cannot expand its authority through data returned by an external system.
- Authority is established by configuration and policy, not inferred from payload content.
- Guerilla does not universally own: canonical application content, external database transactions, filesystem semantics, source-control history, service-internal event ordering, business-rule validation, external authorization decisions, native rollback or merge behavior, semantic correctness of artifacts, or the complete state of an integrated system.

---

## 7. Repository Map

```
Guerilla/
├── AGENTS.md                  # This file -- agent control surface
├── README.md                  # Public project overview
├── README_DEV.md             # Developer setup and commands
├── pyproject.toml             # Package metadata and tool config
├── .github/workflows/ci.yml   # CI pipeline
├── .agents/skills/            # Focused agent skill files
├── docs/                      # Build documents and phase prompts
│   ├── architecture/          # Normative architecture papers
│   ├── rationale/             # Controlling rationale
│   └── phase_prompts/         # Ordered phase execution prompts
├── schemas/                   # JSON Schemas (Phase 3+)
├── registries/                # Enum and error registries (Phase 3+)
├── src/guerilla/              # Python package source
├── tests/                     # Test suites
└── examples/                  # Documentation-only integration placeholders
```

---

## 8. Phase and Gate Discipline

| Gate | Phases | Meaning |
|---|---|---|
| A -- Contract Ready | 1-4 | Architecture decisions, schemas, registries, and fixtures are frozen |
| B -- Kernel Ready | 5-8 | Authoritative storage, replay, DAG integrity, index, authority, identity |
| C -- Continuity MVP | 9-15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI |
| D -- External Compatible | 16-19 | Reference transport, isolated adapters, parity, security, durability, archive |
| E -- Research Validated | 20-22 | Real heterogeneous pilots, benchmark evidence, reproducible release |

No phase may skip its preceding gate. The critical path is: architecture decisions → machine contracts → codec and hashes → append/replay kernel → DAG and authority enforcement → synthetic adapters → intent/idempotency/reconciliation → snapshots and resume → external bindings → heterogeneous pilots → evaluation.

---

## 9. Mutation and Validation Order

Before commit, the runtime must validate in this order:

1. Protocol and schema validity
2. Authorization
3. Identifier uniqueness
4. Authority and state-boundary validity
5. Payload and record hashes
6. Idempotency
7. Graph-revision guard
8. Endpoint existence
9. Relationship-type compatibility
10. Lineage acyclicity
11. Snapshot and projection source validity
12. Transaction completeness

A failure at any step MUST reject the entire append transaction.

---

## 10. Adapter Trust and Capabilities

- Adapters are trusted integration components. The runtime validates their outputs but cannot prove their semantic correctness.
- Every adapter must declare: read consistency, write behavior, event ordering, concurrency, conflict handling, replay support, snapshot support, identity stability, lineage completeness, idempotency, mutating actions, state boundaries, schemas, authentication requirements, and known limitations.
- A capability declaration is a claim by the adapter. It does not transfer application-state authority to Guerilla.
- Model-generated or user-generated shell text MUST NOT be executed directly by the core runtime. Adapters SHOULD use typed clients, argument arrays, or structured tool invocations.
- Phase 9 implements only trusted configured in-process synthetic adapters and the shared host/SDK. It does not implement graph ingestion, committed action orchestration, reconciliation engine behavior, projections, snapshots, transports, subprocess isolation, or real integrations.

---

## 11. Intent-Before-Action and Reconciliation

- The runtime records action intent before invoking an external mutation. This permits recovery when an external action completes but its result is not committed.
- An interrupted or uncertain external action is reconciled through its adapter and idempotency identifiers.
- A reconciliation result MUST be appended as a new event. It MUST NOT rewrite the original intent or result record.
- Reconciliation classifies the action as: confirmed accepted, confirmed rejected, confirmed failed, still pending, duplicated, externally completed with missing lineage, or unknown.
- The runtime must not assume success or retry unsafely. Unknown external outcomes require reconciliation before unsafe retry.

---

## 12. Payload, Path, Secret, and Execution Safety

- Payloads MUST be treated as untrusted data.
- The runtime MUST NOT: execute payload content; import executable adapter behavior from payloads; deserialize unsafe object formats; expose secrets without authorization.
- Redaction MUST occur before payload persistence. The graph records that redaction occurred, the policy version, and the retained payload hash. It MUST NOT retain the removed secret merely to preserve a pre-redaction hash.
- Each state boundary MUST declare permitted filesystem roots, network endpoints, or resource namespaces. Access outside that declaration MUST be rejected.
- External-system credentials SHOULD remain in adapter or secret-store configuration and SHOULD NOT be persisted in graph payloads.

---

## 13. Test Taxonomy and Commands

| Suite | Directory | Purpose |
|---|---|---|
| Unit | `tests/unit/` | Isolated function and class behavior |
| Repository contract | `tests/repository/` | Structural and artifact-boundary enforcement |
| Integration | `tests/integration/` | Component interaction within the runtime |
| Conformance | `tests/conformance/` | Schema, protocol, and graph-invariant conformance |
| Crash | `tests/crash/` | Crash simulation and recovery |
| Security | `tests/security/` | Authorization, payload safety, adapter escalation |
| Adapter | `tests/adapters/` | Adapter SDK, host, and synthetic-system conformance |
| Performance | `tests/performance/` | Throughput, latency, and resource measurement |

Local test commands:

```bash
uv lock --check
uv sync --frozen --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
uv build
```

---

## 14. Documentation Regeneration

- Build documents are regenerable; their source of truth is the frozen architecture decisions and machine-readable contracts, not earlier versions of the same document.
- `CODEX_BUILD_PLAN.md` must contain Gates A-E and all 22 phases.
- `TEST_MATRIX.md` must define planned evidence columns and must not mark unimplemented tests as passing.
- Phase prompts in `docs/phase_prompts/` are regenerated or updated when their owning phase changes scope.
- Architecture papers are never rewritten during phases; corrections go through `ARCHITECTURE_DECISIONS.md`.

---

## 15. Prohibited Shortcuts

Agents MUST NOT:

- Make a projection or index authoritative.
- Directly replace external application state.
- Invoke an external action before committing intent.
- Replay external actions during graph replay.
- Weaken cycle validation for convenience.
- Insert symmetric or cyclic domain relationships as direct authoritative edges.
- Repair graph records from SQLite or another derived index.
- Treat payloads as executable content.
- Auto-retry an unknown external outcome without reconciliation.
- Add a real adapter before synthetic adapter conformance passes.
- Add a transport-specific mutation path.
- Hide unresolved architecture choices in defaults.
- Claim completion without linked evidence.
- Create a second source of truth for lineage, identity, or authority.

---

## 16. Stop Conditions

Stop work and report the blocker if:

- An authorized source is missing or unreadable.
- Controlling sources conflict in a way that changes current phase scope.
- A tooling choice would settle a decision reserved for a later phase.
- The scaffold would create a second source of truth.
- A required test would need prohibited runtime behavior.
- Missing or contradictory contracts would require best-effort guessing.
- A pre-existing file has uncertain authority or provenance and would be overwritten.

---

## 17. Completion-Report Format

Every phase completion must return:

### Phase Result

One of: `PASS -- Phase N complete`, `PARTIAL -- unaffected work complete; blockers remain`, `FAIL -- Phase N exit criteria not met`.

### Delivered Artifacts

Grouped by category (repository controls, agent instructions, documentation, package, tests, CI, source manifest).

### Validation Evidence

For each command run: `Command | Exit code | Result | Evidence path`.

### Exit-Criteria Matrix

Every criterion with `Status | Evidence | Notes`.

### Scope Audit

Whether prohibited runtime behavior or reserved decisions were introduced. List every exception.

### Blockers and Contradictions

List, or `None`.

### Phase Handoff

Confirmed baseline, unresolved decisions, source conflicts, and placeholders for next phase.

---

## 18. Phase 1 Scope Boundaries

In Phase 1, agents MAY ONLY:

- Create repository structure, configuration, and metadata.
- Place, classify, and hash architecture sources.
- Implement package import, version reporting, and CLI help/version.
- Write AGENTS.md, skill files, and documentation skeletons.
- Create tests for repository contract, import, and version.
- Configure CI from documented local commands.
- Build and smoke-test the distribution wheel.

Agents MUST NOT implement any graph, storage, adapter, protocol, or projection runtime behavior in Phase 1.
