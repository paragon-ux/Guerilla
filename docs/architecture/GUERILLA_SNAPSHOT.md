
# GUERILLA_SNAPSHOT.md

# Guerilla Project Snapshot

**Document purpose:** Record Guerilla’s current architectural state, accepted decisions, MVP boundaries, unresolved questions, risks, and next milestones.

**Status:** Architecture-defined; implementation not evidenced as complete

**Version:** 0.2.0-draft

**Intended audience:** Project maintainers, implementers, reviewers, research collaborators, and prospective adopters.

**Revision provenance:** This snapshot replaces the supplied v0.1.0 status framing.

---

## 1. Current Architectural Definition

Guerilla is defined as a standalone lineage and continuity orchestration layer.

Its authoritative state is one logically unified directed acyclic graph containing immutable:

* goals;
* artifact revisions;
* operations;
* events;
* evaluations;
* decisions;
* conflicts;
* snapshots;
* typed relationships;
* provenance and authority metadata.

External systems retain ownership of their application state. Guerilla records authority-scoped observations, action intent, external results, revisions, evaluations, and cross-system causal relationships.

Derived representations include:

* lineage and dependency views;
* manifests;
* snapshots and resume summaries;
* graph and artifact diffs;
* conflict views;
* progress views;
* requirement-traceability-style status views.

These representations are non-authoritative unless the graph records the fact that a snapshot or derived artifact was created. Their content remains reproducible from a declared graph revision and transformation version.

---

## 2. Current Scope

The accepted v0.2 MVP scope is:

* local-first;
* one workspace;
* one serialized graph writer;
* concurrent revision-bound reads;
* append-only graph transactions;
* immutable nodes and edges;
* SHA-256 integrity;
* authority and state-boundary declarations;
* adapter capability negotiation;
* observation, action, evaluation, and reconciliation;
* idempotency;
* explicit conflicts;
* graph replay and verification;
* rebuildable indexing;
* manifests, snapshots, diffs, and core views;
* CLI, library, or local-service exposure.

The MVP does not include distributed consensus, cross-workspace federation, or automatic semantic merge.

---

## 3. Accepted Design Decisions

### 3.1 One logical authoritative DAG

Guerilla uses one lineage authority. Physical partitions, archives, indexes, caches, and materialized projections do not create additional lineage sources.

### 3.2 Strictly acyclic direct edges

All direct authoritative relationships preserve the DAG invariant.

Symmetric, cyclic, or non-causal domain relationships are represented through reified event or conflict nodes and may be rendered differently in derived views.

### 3.3 Immutable revision model

Committed records are never updated in place. Later versions use new nodes and `superseded_by` relationships.

### 3.4 Explicit state boundaries

Every adapter declares the external state it observes or may ask the external system to mutate. Application-state authority remains with the system of record.

### 3.5 Intent before external action

The runtime records action intent before invoking an external mutation. This permits recovery when an external action completes but its result is not committed.

### 3.6 Reconciliation for unknown outcomes

An interrupted or uncertain external action is reconciled through its adapter and idempotency identifiers. The runtime does not assume success or retry unsafely.

### 3.7 Derived views cite sources

A manifest, snapshot, matrix, dashboard, diff, or resume report identifies its graph revision, source records, transformation version, freshness, and information loss.

### 3.8 Separate outcome layers

The architecture distinguishes:

* transport outcome;
* external-system outcome;
* evaluation outcome;
* conflict state;
* goal-completion decision.

### 3.9 Adapter capability metadata

Adapters declare consistency, concurrency, ordering, replay, snapshot, identity, idempotency, and lineage-completeness characteristics.

### 3.10 Local single-writer MVP

Graph mutations are serialized by a workspace lock. Multi-writer coordination is deferred.

---

## 4. Current Documented Deliverables

The supplied material establishes four architecture-level drafts:

* a concept paper;
* an implementation specification;
* a protocol specification;
* a project snapshot.

The revised architecture set now defines:

* stable terminology;
* state-ownership boundaries;
* a strict single-DAG model;
* reified handling of non-DAG relationships;
* core node and relationship types;
* graph revisions and append transactions;
* adapter capabilities;
* action and reconciliation flow;
* projections, manifests, snapshots, and diffs;
* protocol messages and operations;
* MVP and deferred scope;
* conformance expectations.

---

## 5. Implementation Status

No executable Guerilla runtime, adapter SDK, conformance suite, or production deployment is evidenced by the supplied source material.

Accordingly:

| Component                    | Current status                          |
| ---------------------------- | --------------------------------------- |
| Conceptual architecture      | Defined in draft                        |
| Core terminology             | Defined in draft                        |
| State-boundary model         | Defined in draft                        |
| Implementation design        | Specified, not evidenced as implemented |
| Protocol contract            | Specified, not evidenced as implemented |
| Graph store                  | Planned                                 |
| Integrity validator          | Planned                                 |
| Adapter host and SDK         | Planned                                 |
| Reconciliation engine        | Planned                                 |
| Projection engine            | Planned                                 |
| Snapshot and manifest engine | Planned                                 |
| CLI or service interface     | Planned                                 |
| Conformance suite            | Planned                                 |
| Security review              | Planned                                 |
| Performance evaluation       | Planned                                 |
| Production readiness         | Not established                         |

The project must not describe planned runtime behavior as implemented until code, tests, and reproducible evidence exist.

---

## 6. MVP Boundary

The first implementation milestone should contain only the capabilities needed to prove the architectural model.

### Mandatory MVP

* workspace initialization;
* graph header;
* canonical record codec;
* append transactions;
* graph revision and commit chain;
* node and edge validation;
* cycle detection;
* payload hashing;
* authority and state-boundary registry;
* adapter descriptor;
* observation ingestion;
* intent-before-action flow;
* idempotency;
* action-result recording;
* unknown-outcome reconciliation;
* conflict records;
* graph replay;
* rebuildable index;
* lineage query;
* manifest generation;
* snapshot creation and verification;
* diff generation;
* progress and resume views;
* conformance tests.

### Excluded from MVP

* distributed graph storage;
* multiple concurrent writers;
* remote federation;
* automatic external-state rollback;
* semantic merge;
* global scheduling;
* adapter marketplace;
* cryptographic actor signatures;
* continuous streaming projections;
* cross-workspace identity resolution;
* policy-learning systems.

---

## 7. Unresolved Architectural Questions

### 7.1 Canonical serialization

The architecture assumes deterministic canonical JSON, but the final canonicalization profile remains to be selected and tested across implementations.

### 7.2 Identifier scheme

ULID and UUIDv7 remain viable. The project must select one default and define migration and interoperability behavior.

### 7.3 Adapter isolation

The trust model treats adapters as trusted plugins. The project has not yet selected in-process, subprocess, container, or remote isolation as the default.

### 7.4 Payload retention and redaction

The interaction among redaction, content hashes, audit requirements, deletion, and sensitive-data retention requires a concrete policy.

### 7.5 External identity lifecycle

Rename, deletion, identifier reuse, and cross-system aliasing need conformance fixtures and clear conflict policies.

### 7.6 Projection policy language

Status views require versioned transformation and policy rules. The representation and execution boundary of those rules remain open.

### 7.7 Filesystem durability

The reference local store requires tested rules for file locking, atomic append, flush, recovery, and behavior on network filesystems.

### 7.8 Performance thresholds

No accepted limits yet exist for graph size, traversal depth, archive cadence, payload size, or projection latency.

### 7.9 Authorization model

Operation-level permissions are specified conceptually, but the default role and policy model is not selected.

### 7.10 Relationship extension governance

The project must define how namespaced node and relationship extensions are reviewed, registered, and prevented from weakening the DAG invariant.

---

## 8. Known Risks

### Adapter misrepresentation

An adapter may report inaccurate authority, revision, or capability data. Conformance tests reduce but do not eliminate this risk.

### Out-of-band actions

External state can change without a corresponding Guerilla event. Reconciliation and observation detect some divergence but cannot guarantee complete lineage.

### Unknown outcomes

External actions may remain impossible to classify after interruption, particularly when an external system lacks idempotency or queryable operation history.

### Projection overconfidence

Consumers may mistake a concise status view for complete lineage. Interfaces must preserve source links and authority labels.

### Graph growth

Append-only lineage may grow rapidly. Archive, indexing, payload retention, and incremental projection require measurement.

### Identity ambiguity

Unstable external identifiers may produce accidental duplication or false supersession.

### Security exposure

Lineage can reveal sensitive paths, actors, prompts, artifacts, and operational details. Access control and redaction are necessary from the first implementation.

### Specification drift

The concept, implementation, protocol, and snapshot documents can diverge as code evolves unless conformance schemas and architecture decisions are version-controlled together.

---

## 9. Deferred Capabilities

The following capabilities are intentionally deferred:

* remote shared lineage service;
* distributed writer consensus;
* graph federation;
* multi-agent reservations and leases;
* automatic branch merge;
* semantic conflict resolution;
* portable cross-workspace snapshot bundles;
* signed commits and actor attestations;
* selective cryptographic disclosure;
* global identity registry;
* event-stream subscriptions;
* autonomous scheduling;
* cost-aware operation planning;
* policy-constrained execution;
* adapter sandbox marketplace.

Deferred capabilities must preserve the established authority and graph invariants when reconsidered.

---

## 10. Next Milestones

### Milestone 1: Freeze core schemas

Deliver:

* canonical serialization decision;
* identifier decision;
* JSON schemas for records and protocol envelopes;
* core enum registry;
* error-code registry;
* state-boundary schema.

### Milestone 2: Implement graph core

Deliver:

* append-only store;
* transaction engine;
* graph revisions;
* hash chain;
* node and edge validator;
* cycle detector;
* replay and verification;
* writer lock.

### Milestone 3: Implement adapter SDK

Deliver:

* descriptor model;
* observation interface;
* action interface;
* evaluation interface;
* reconciliation interface;
* generic mock external systems;
* capability conformance tests.

### Milestone 4: Implement continuity flows

Deliver:

* intent-before-action orchestration;
* idempotency store;
* unknown-outcome recovery;
* conflict engine;
* revision and identity reconciliation.

### Milestone 5: Implement projections

Deliver:

* lineage query;
* dependency view;
* manifest;
* snapshot;
* diff;
* conflict view;
* progress and resume view;
* requirement-traceability-style projection.

### Milestone 6: Security and reliability review

Deliver:

* authorization profile;
* path and endpoint restrictions;
* payload redaction;
* unsafe-deserialization review;
* adapter trust analysis;
* crash and corruption testing.

### Milestone 7: Pilot evaluation

Demonstrate:

* one transactional external system;
* one filesystem or reconstructed-state system;
* one event-oriented or batch system;
* action interruption and reconciliation;
* deterministic projection regeneration;
* index deletion and rebuild;
* resume from a verified snapshot.

---

## 11. Readiness Gates

The project is not implementation-ready until:

* core schemas are frozen;
* canonical hashing is interoperable;
* graph replay is deterministic;
* cycle detection is tested;
* adapter capabilities are machine-readable;
* idempotency and reconciliation are demonstrated;
* projections identify source revisions;
* security boundaries are reviewed.

The project is not production-ready until:

* conformance tests pass;
* crash recovery is demonstrated;
* payload retention and redaction are approved;
* authorization is enforced;
* performance limits are measured;
* operational monitoring exists;
* at least two materially different state models have been integrated without authority overlap.

---

## 12. Cross-Document Consistency Report

### Terminology standardized

The four documents now use consistent definitions for:

* node;
* edge;
* lineage;
* continuity;
* authoritative graph;
* projection or view;
* adapter;
* external system;
* system of record;
* artifact;
* actor;
* revision;
* event;
* snapshot;
* manifest;
* status;
* conflict;
* provenance;
* relationship type;
* state boundary.

Core node types are consistently defined as:

* goal;
* artifact;
* operation;
* event;
* evaluation;
* decision;
* conflict;
* snapshot.

Core direct relationship types are consistently defined as:

* `depends_on`;
* `produces`;
* `derives`;
* `causes`;
* `evidences`;
* `evaluated_by`;
* `superseded_by`;
* `resolved_by`;
* `captured_by`.

### External references removed

Named project comparisons, project-specific commands, inherited schemas, and examples dependent on other architectures have been removed. Examples now use generic requirements, artifacts, repositories, services, tools, evaluators, and external systems.

### Contradictions resolved

The revisions resolve the following earlier ambiguities:

* Guerilla now has one strict authoritative DAG rather than an authoritative DAG plus potentially cyclic authoritative edge classes.
* Symmetric and cyclic domain relationships are handled through reified nodes.
* Manifests and status matrices are explicitly derived views.
* Snapshot records are distinguished from their derived summary payloads.
* Actor correlation is distinguished from causation.
* Graph revision, artifact revision, and external revision are separate concepts.
* The adapter contract includes reconciliation for uncertain actions.
* The implementation and protocol use the same node types, relationship types, capability metadata, error classes, and MVP boundary.
* The project snapshot no longer implies that specified components are implemented.

### Remaining architectural questions

Open questions remain around:

* canonical JSON;
* default identifier scheme;
* adapter isolation;
* redaction and payload retention;
* policy representation;
* external identity lifecycle;
* local-store durability;
* performance thresholds;
* authorization profiles;
* extension governance.

### Assumptions requiring confirmation

The architecture currently assumes:

* a local single-writer MVP;
* SHA-256 integrity;
* append-only graph records;
* intent commitment before external action;
* adapter-level reconciliation;
* rebuildable non-authoritative indexes;
* deterministic projection generation where practical;
* trusted but schema-validated adapters;
* no automatic semantic merge;
* no distributed consensus in v0.2.

This revision follows the supplied standalone-project requirements and final-deliverable criteria.
