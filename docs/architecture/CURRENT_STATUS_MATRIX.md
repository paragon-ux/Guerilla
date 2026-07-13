## Current maturity

Guerilla is **architecturally well developed but not yet implemented or empirically validated**.

My estimated maturity, based on the supplied specifications and ledger, is:

| Area                              | Estimated maturity | Assessment                                                                 |
| --------------------------------- | -----------------: | -------------------------------------------------------------------------- |
| Problem definition and motivation |                85% | Clear and defensible                                                       |
| Architectural boundaries          |                85% | External systems retain application-state authority; Guerilla owns lineage |
| Conceptual data model             |                75% | Core records and relationships are defined, but schemas are not frozen     |
| Protocol design                   |                65% | Operations and invariants are specified, but interoperability is untested  |
| Implementation design             |                60% | Major components and flows are described                                   |
| Reference implementation          |              0–10% | No executable runtime is evidenced                                         |
| Adapter SDK and integrations      |              0–10% | Proposed, not demonstrated                                                 |
| Conformance testing               |               0–5% | Test requirements exist, but no test suite is evidenced                    |
| Empirical evaluation              |                 0% | No benchmarks, pilots, or comparative results                              |
| Production readiness              |                 0% | Security, durability, operations, and scale remain untested                |

Overall, Guerilla is approximately at the **architecture-complete / pre-prototype stage**. It is beyond an initial concept, but it has not yet crossed the boundary into a validated system.

The implementation specification already identifies the intended runtime components, including a parser, protocol validator, DAG validator, append-only graph store, payload store, adapter registry, orchestration engine, conflict engine, view engine, and checkpoint/resume engine.  However, the current edit ledger labels every P0 and P1 item as **proposed**, including the graph schema, adapter contract, ingestion store, views, conflicts, adapters, and checkpoint/resume functionality. 

## What is substantially complete

### Architectural identity

Guerilla now has a coherent standalone purpose:

> Maintain authoritative cross-system causal lineage and continuity without becoming the application-state owner for integrated systems.

The distinction between external state authority, Guerilla lineage authority, and derived views is well established. 

### Core architectural mechanisms

The documents define:

* immutable lineage records;
* typed relationships;
* authority-scoped observations;
* external action results;
* evaluations;
* conflicts and decisions;
* checkpoints and resume behavior;
* append-only storage;
* rebuildable indexes;
* adapters;
* source-cited derived views.

The observation-first lifecycle is also clear: observe external state, record a bounded operation, invoke an external action, record its result, observe the resulting state, evaluate it, and create either a continuation or conflict. 

### Failure and continuity semantics

Guerilla already separates:

* transport success;
* external-system acceptance;
* evaluation outcome;
* conflict state;
* continuation decisions.

It also specifies that replay reconstructs lineage without repeating external actions, which is an important and defensible architectural boundary. 

### Intended implementation surface

The specifications are detailed enough to begin implementation. They already describe a local append-only graph, optional content-addressed payload storage, a derived SQLite index, a CLI surface, archive behavior, and checkpoint/resume flows.  

## What remains incomplete

### The schemas are not frozen

The project still needs final machine-readable definitions for:

* graph header;
* transactions and commits;
* nodes;
* edges;
* authority envelopes;
* state boundaries;
* provenance;
* payload references;
* adapter capabilities;
* conflicts;
* snapshots;
* projection metadata;
* protocol messages and errors.

Until these are frozen, separate implementations could interpret the specifications differently.

### Some design choices remain unresolved

The revised architecture still needs final decisions concerning:

* canonical JSON format;
* ULID versus UUIDv7;
* exact commit-hash construction;
* filesystem locking and durability;
* adapter isolation;
* payload retention;
* redaction behavior;
* authorization;
* extension governance;
* projection-policy representation;
* archive thresholds.

### There is no demonstrated graph runtime

No evidence currently shows that Guerilla can:

* initialize a workspace;
* append a transaction atomically;
* reject a cycle;
* detect an incomplete transaction;
* replay a graph deterministically;
* rebuild an index;
* reconcile an interrupted action;
* regenerate a snapshot;
* resume a workflow.

### There are no generic adapter fixtures

The ledger proposes an adapter contract and says fake native tools should be tested before real integrations.  That is the correct approach, but the fake systems and tests are not yet evidenced.

### There is no empirical contribution yet

For publication at a systems or middleware venue, the project still needs evidence that Guerilla provides a material advantage over combinations of provenance stores, workflow histories, traces, and application logs.

That requires benchmarks and realistic case studies, not only architecture documents.

## Important immediate correction

The newly supplied edit ledger should be treated as **outdated relative to the revised standalone architecture**.

It still:

* frames Guerilla around named external projects;
* says Guerilla does not yet exist as a formal architecture;
* uses an older set of node and edge concepts;
* permits separate non-lineage edge classes that may be cyclic;
* centers RTM and edit-session views tied to particular integrations.

The revised standalone architecture has already moved beyond that framing. It uses a stricter single-DAG model and handles symmetric or cyclic domain relationships through reified nodes and derived views.

Therefore, the first task should not be implementing the ledger literally. The ledger should first be rewritten to align with the updated architecture.

## Recommended next steps

### Phase 0 — Freeze the architecture baseline

Create one authoritative architecture baseline and remove obsolete alternatives.

The immediate outputs should be:

1. `ARCHITECTURE_DECISIONS.md`
2. `GLOSSARY.md`
3. `MVP_SCOPE.md`
4. revised standalone implementation ledger
5. cross-document terminology matrix

Decisions to freeze include:

* eight core node types;
* core relationship types;
* strict acyclicity of direct authoritative edges;
* reification of symmetric and cyclic relationships;
* graph, artifact, and external revision distinctions;
* authority and state-boundary rules;
* intent-before-action behavior;
* reconciliation semantics;
* projection authority rules.

**Exit criterion:** The concept paper, implementation specification, protocol specification, snapshot, schemas, and ledger use the same terms and invariants.

### Phase 1 — Publish machine-readable contracts

Implement the specification before implementing runtime behavior.

Produce:

* node JSON Schema;
* edge JSON Schema;
* transaction schemas;
* graph-header schema;
* authority and state-boundary schemas;
* adapter-descriptor schema;
* protocol request and response schemas;
* error-code registry;
* valid and invalid conformance fixtures.

Also finalize canonical JSON, identifier format, and hash semantics.

**Exit criterion:** Two independent validators produce the same result for every fixture.

### Phase 2 — Build the graph kernel

Implement only the authoritative graph core:

* workspace initialization;
* append-only JSONL storage;
* writer lock;
* transaction begin and commit;
* graph revisions;
* record and commit hashing;
* node and edge validation;
* endpoint checks;
* cycle detection;
* replay;
* graph verification;
* graph-head calculation;
* rebuildable SQLite index.

Do not build real adapters yet.

**Exit criterion:** The graph survives crash simulation, detects corruption, rejects cycles, ignores incomplete transactions, and rebuilds its index entirely from authoritative records.

### Phase 3 — Build the adapter SDK with synthetic systems

Implement:

* adapter descriptor;
* `describe`;
* `observe`;
* `act`;
* `evaluate`;
* `reconcile`;
* authority enforcement;
* state-boundary enforcement;
* consistency and capability metadata;
* structured request and result envelopes.

Use at least three fake external systems:

1. a transactional revisioned service;
2. a filesystem-based reconstructed-state system;
3. an asynchronous service capable of returning an unknown action outcome.

This is more valuable than immediately coupling the prototype to existing products.

**Exit criterion:** The same Guerilla runtime handles all three continuity models without changing its graph core.

### Phase 4 — Implement action safety and reconciliation

Build the most distinctive operational mechanism:

* commit action intent;
* invoke the external action;
* record result;
* observe after-state;
* handle interruption;
* reconcile unknown outcome;
* enforce idempotency;
* record stale or divergent external revisions.

Test interruption:

* before intent commit;
* after intent commit;
* during the external call;
* after external completion but before result commit;
* before after-state observation.

**Exit criterion:** Retrying an interrupted operation cannot silently duplicate an external mutation.

### Phase 5 — Implement projections

In recommended order:

1. lineage and dependency view;
2. conflict view;
3. latest-revision manifest;
4. snapshot;
5. graph diff;
6. progress view;
7. resume view;
8. requirement-traceability-style view.

Every projection must include:

* source graph revision;
* source query or source nodes;
* transformation version;
* generation time;
* freshness;
* information-loss statement;
* result hash.

**Exit criterion:** Deleting every persisted projection and index does not lose authoritative lineage, and the views regenerate deterministically.

### Phase 6 — Run heterogeneous pilot integrations

After the generic adapter model passes conformance, integrate materially different systems, such as:

* a Git repository;
* a test runner;
* a document or issue-tracking service;
* a batch data pipeline;
* a manual review queue.

The objective is not merely to show that adapters can be written. It is to demonstrate that Guerilla preserves distinct consistency and ownership models.

**Exit criterion:** At least two integrations with substantially different state models operate without overlapping state authority.

### Phase 7 — Evaluate the research claims

The evaluation should test five questions.

| Research question                      | Suggested measurement                                                                              |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Does Guerilla improve resume accuracy? | Correct identification of current heads, stale observations, conflicts, and next operations        |
| Does it improve lineage completeness?  | Percentage of artifact revisions traceable to producer, observation, actor, result, and evaluation |
| Does it preserve external authority?   | Number of direct or replacement external-state writes performed by the runtime; target is zero     |
| Are projections reproducible?          | Hash equality after regeneration from the same revision and policy                                 |
| What is the runtime cost?              | Append latency, cycle-check time, replay time, index size, traversal latency, snapshot size        |

The comparison should include, where practical:

* conversation or summary-only continuity;
* conventional logs;
* workflow-engine histories;
* provenance-only recording;
* Guerilla’s full intent–result–reconciliation graph.

### Phase 8 — Security and operational hardening

Before any production claim, complete:

* adapter threat model;
* least-privilege execution;
* filesystem and endpoint restrictions;
* secret redaction;
* payload-retention policy;
* authorization rules;
* corruption recovery;
* archive verification;
* denial-of-service limits;
* operational metrics;
* backup and restore testing.

## The critical path

The shortest credible route to a publishable prototype is:

> Architecture freeze → schemas → graph kernel → synthetic adapters → intent and reconciliation → snapshots and resume → heterogeneous pilots → evaluation.

The real technical contribution should be demonstrated around **authority-preserving continuity and uncertain-action reconciliation**, rather than around basic graph storage. Append-only DAG storage by itself is established technology. Guerilla becomes research-worthy when it shows that one lineage authority can coordinate heterogeneous systems without taking over their application state.

## Practical status statement

A defensible project-status statement today would be:

> Guerilla has a coherent standalone architecture, an implementation-level design, and a draft protocol. Its core runtime, adapter SDK, conformance suite, integrations, and empirical evaluation remain to be implemented. The next milestone is a minimal graph kernel and synthetic adapter testbed capable of demonstrating authority boundaries, observation-first ingestion, idempotent external action, uncertain-outcome reconciliation, and deterministic snapshot regeneration.
