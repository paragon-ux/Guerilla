# GUERILLA_IMPLEMENTATION_SPEC.md

# Guerilla Runtime Implementation Specification

**Document purpose:** Define an implementable architecture for Guerilla’s graph runtime, storage, adapters, ingestion, reconciliation, projections, snapshots, security, and conformance testing.

**Status:** Revised implementation design; reference runtime not yet evidenced as complete

**Version:** 0.2.0-draft

**Intended audience:** Runtime implementers, adapter developers, protocol implementers, security reviewers, test engineers, and maintainers.

**Revision provenance:** This document supersedes the supplied v0.1.0 implementation draft.

---

## 1. Normative Language

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

* **MUST** identifies behavior required for conformance.
* **MUST NOT** identifies prohibited behavior.
* **SHOULD** identifies recommended behavior that may be omitted only for a documented reason.
* **MAY** identifies optional behavior.

---

## 2. Scope

The mandatory v0.2 MVP is a local-first, single-workspace, single-writer lineage runtime.

The MVP MUST provide:

* one logically authoritative DAG;
* immutable nodes and typed acyclic edges;
* append transactions;
* graph revisions and commit hashes;
* content-addressed optional payloads;
* authority and state-boundary declarations;
* adapter capability discovery;
* observation and action recording;
* reconciliation of uncertain external outcomes;
* conflict records;
* regenerable projections;
* manifests and snapshots;
* graph verification and replay;
* a rebuildable query index;
* local access control and execution boundaries;
* a conformance test suite.

The MVP does not require:

* remote multi-writer consensus;
* cross-workspace federation;
* automatic semantic merge;
* distributed reservations;
* global identity resolution;
* fully isolated adapter execution;
* continuous event subscriptions;
* automatic recovery of external application state.

---

## 3. Required Invariants

A conforming runtime MUST preserve these invariants.

1. The committed graph is the sole Guerilla lineage authority.
2. External systems retain ownership of their declared application-state boundaries.
3. Committed nodes and edges are immutable.
4. A correction creates a new node and a supersession path.
5. Every direct authoritative edge belongs to the acyclic lineage graph.
6. Non-causal or potentially cyclic relationships are represented through reified nodes rather than cycle-producing direct edges.
7. Every externally sourced record identifies its authority, adapter, subject, and observation or event time.
8. Every graph mutation occurs within a committed append transaction.
9. Every committed transaction produces a monotonically increasing graph revision.
10. An index, cache, manifest, dashboard, or snapshot payload MUST NOT become an independent lineage authority.
11. External action transport success MUST NOT be treated as external acceptance.
12. External acceptance MUST NOT be treated as semantic correctness.
13. Replay MUST reconstruct graph state without repeating external actions.
14. Missing, stale, ambiguous, and unknown conditions MUST remain explicit.
15. Adapter payloads MUST be treated as data and MUST NOT be executed by the graph runtime.
16. An adapter MUST NOT claim an undeclared state boundary.
17. Every persisted projection MUST identify its source graph revision and transformation version.
18. An idempotency key reused with different request content MUST be rejected.

---

## 4. Runtime Components

The reference architecture contains thirteen components.

### 4.1 Configuration and Policy Loader

The loader MUST read:

* workspace identity;
* protocol version;
* storage configuration;
* adapter configuration;
* state-boundary ownership;
* payload capture and retention policy;
* redaction policy;
* freshness policy;
* authorization policy;
* projection definitions;
* archive thresholds;
* extension namespaces.

Invalid configuration MUST prevent mutating runtime operations.

### 4.2 Record Codec

The codec MUST:

* parse and serialize graph records;
* enforce canonical encoding;
* calculate record and payload hashes;
* reject unsupported record versions;
* preserve unknown extension fields only when permitted by compatibility rules.

### 4.3 Protocol Validator

The validator MUST check:

* required fields;
* identifier formats;
* timestamps;
* enums and namespaced extensions;
* authority envelopes;
* state-boundary references;
* actor provenance;
* payload references;
* relationship direction;
* graph revision guards;
* transaction boundaries;
* idempotency fields.

### 4.4 DAG Integrity Engine

The engine MUST:

* verify node and edge uniqueness;
* verify endpoint existence;
* reject self-loops;
* reject lineage cycles;
* verify permitted node and edge combinations;
* verify supersession direction;
* verify snapshot sources;
* compute graph heads;
* detect orphaned lineage where required by policy.

### 4.5 Append-Only Graph Store

The store MUST persist committed graph transactions and MUST support deterministic replay.

The default implementation SHOULD use hash-linked JSON Lines segments. An alternative backend MAY be used if it preserves the same transactional, immutability, revision, and replay semantics.

### 4.6 Payload Store

The payload store MAY retain large observations, reports, command results, manifests, and snapshot summaries by content hash.

The payload store MUST:

* verify payload hashes on read;
* enforce retention and redaction policy;
* distinguish absent payloads from hash failures;
* remain subordinate to graph references.

### 4.7 Authority and Identity Registry

The registry MUST maintain:

* external-system identifiers;
* adapter identifiers and versions;
* state-boundary declarations;
* permitted operations;
* external-to-Guerilla identity mappings;
* identity stability classification;
* revision semantics;
* ownership conflicts.

The registry is authoritative only for Guerilla integration configuration. It does not replace an external system’s identity store.

### 4.8 Adapter Host

The adapter host MUST:

* load only configured adapters;
* validate adapter descriptors;
* apply authorization and state-boundary rules;
* invoke structured adapter operations;
* validate adapter responses;
* capture correlation and idempotency data;
* enforce timeouts and resource limits;
* report unavailable or unsupported capabilities explicitly.

### 4.9 Ingestion and Orchestration Engine

The engine MUST coordinate:

* goal and operation creation;
* observations;
* external action intent;
* result recording;
* after-state observation;
* evaluation;
* conflict creation;
* decisions;
* continuation operations.

It MUST NOT bypass external validation or write directly into application state unless the configured external interface itself is the documented system-of-record interface.

### 4.10 Reconciliation Engine

The reconciliation engine MUST handle interrupted or uncertain external actions.

It MUST be able to classify an attempted action as:

* confirmed accepted;
* confirmed rejected;
* confirmed failed;
* still pending;
* duplicated;
* externally completed with missing lineage;
* unknown.

A reconciliation result MUST be appended as a new event. It MUST NOT rewrite the original intent or result record.

### 4.11 Conflict Engine

The conflict engine MUST:

* validate evidence requirements;
* classify conflicts;
* calculate unresolved-conflict projections;
* preserve resolution history;
* distinguish detected conflicts from policy-generated warnings;
* avoid automatic semantic merge unless a namespaced extension explicitly defines it.

### 4.12 Projection Engine

The projection engine MUST generate views from a declared graph revision and transformation version.

It MUST support at least:

* lineage traversal;
* dependency view;
* latest-revision manifest;
* snapshot summary;
* graph diff;
* conflict view;
* progress and resume view;
* requirement-traceability-style status view.

### 4.13 Index and Query Engine

The index MUST be rebuildable from graph and payload references.

An index mismatch MUST cause the affected index to be discarded or marked invalid. The runtime MUST NOT repair authoritative records from index contents.

---

## 5. Workspace Layout

The reference filesystem layout is:

| Path                             | Purpose                             | Authority                  |
| -------------------------------- | ----------------------------------- | -------------------------- |
| `.guerilla/config.toml`          | Workspace and policy configuration  | Configuration authority    |
| `.guerilla/graph/active.jsonl`   | Active graph segment                | Authoritative lineage      |
| `.guerilla/graph/archives/`      | Sealed hash-linked graph segments   | Authoritative lineage      |
| `.guerilla/payloads/sha256/`     | Optional content-addressed payloads | Referenced data            |
| `.guerilla/projections/`         | Persisted derived views             | Non-authoritative          |
| `.guerilla/snapshots/`           | Materialized snapshot summaries     | Non-authoritative payloads |
| `.guerilla/indexes/graph.sqlite` | Rebuildable query index             | Non-authoritative          |
| `.guerilla/locks/`               | Local writer and maintenance locks  | Runtime coordination       |
| `.guerilla/logs/`                | Operational logs and metrics        | Diagnostic                 |
| `.guerilla/tmp/`                 | Uncommitted staging data            | Non-authoritative          |

Temporary and uncommitted files MUST NOT be treated as graph state.

---

## 6. Canonical Encoding and Hashing

### 6.1 Encoding

The reference codec MUST use:

* UTF-8;
* LF newlines;
* one JSON object per stored line;
* lexicographically sorted object keys for hash input;
* no insignificant whitespace in hash input;
* array order preserved;
* RFC 3339 UTC timestamps;
* no implicit Unicode normalization.

The exact canonicalization identifier MUST be recorded in the graph header.

### 6.2 Hashes

SHA-256 is mandatory for the MVP.

The runtime MUST calculate:

* `record_hash` from the canonical record excluding `record_hash`;
* `payload_hash` from exact payload bytes;
* `transaction_hash` from ordered member record hashes;
* `commit_hash` from the previous commit hash, graph revision, and transaction hash;
* `segment_hash` from ordered commit hashes in the segment.

A hash mismatch MUST fail verification.

### 6.3 Graph revision

Every committed append transaction MUST receive:

* a monotonically increasing `graph_revision`;
* a unique `commit_id`;
* a `commit_hash`;
* the previous commit hash;
* a commitment timestamp.

A graph revision identifies a complete, stable read boundary.

---

## 7. Identifiers

Recommended identifiers use ULID or UUIDv7 with stable prefixes.

| Object      | Suggested prefix                                |
| ----------- | ----------------------------------------------- |
| Workspace   | `grw_`                                          |
| Node        | `grn_`                                          |
| Edge        | `gre_`                                          |
| Transaction | `grt_`                                          |
| Commit      | `grm_`                                          |
| Snapshot    | `grs_`                                          |
| Adapter     | `gra_`                                          |
| Projection  | `grp_`                                          |
| Conflict    | Node identifier; no separate namespace required |

Identifiers MUST be opaque and unique within their declared scope.

### 7.1 Logical entity identity

Every revisioned node SHOULD include an `entity_id` that remains stable across revisions.

A new revision MUST have:

* a new `node_id`;
* the same `entity_id`;
* a later graph revision;
* an incoming `superseded_by` edge from the earlier node when ordering is known.

### 7.2 External identity

An external identity MUST include:

* `system_id`;
* `state_boundary_id`;
* `external_kind`;
* `external_id`;
* optional namespace;
* optional external revision token.

External identifiers MUST NOT be assumed globally unique.

---

## 8. Common Record Model

### 8.1 Node record

Every node MUST include:

| Field               |    Required | Meaning                                      |
| ------------------- | ----------: | -------------------------------------------- |
| `record_type`       |         Yes | `node`                                       |
| `protocol_version`  |         Yes | Record contract version                      |
| `workspace_id`      |         Yes | Owning workspace                             |
| `node_id`           |         Yes | Immutable node identity                      |
| `entity_id`         |         Yes | Logical entity identity                      |
| `node_type`         |         Yes | Core or namespaced type                      |
| `node_subtype`      |          No | More specific classification                 |
| `created_at`        |         Yes | Commitment-source time                       |
| `effective_at`      |          No | External event or observation time           |
| `actor`             |         Yes | Responsible actor                            |
| `authority`         |         Yes | Guerilla or external authority               |
| `state_boundary_id` | Conditional | Required for external state                  |
| `status`            |         Yes | Node-type-specific status                    |
| `provenance`        |         Yes | Source and causation metadata                |
| `payload_ref`       |         Yes | Inline, content-addressed, external, or none |
| `metadata`          |         Yes | Empty object permitted                       |
| `record_hash`       |         Yes | Integrity hash                               |

### 8.2 Edge record

Every edge MUST include:

| Field               | Required | Meaning                          |
| ------------------- | -------: | -------------------------------- |
| `record_type`       |      Yes | `edge`                           |
| `protocol_version`  |      Yes | Record contract version          |
| `workspace_id`      |      Yes | Owning workspace                 |
| `edge_id`           |      Yes | Immutable edge identity          |
| `relationship_type` |      Yes | Core or namespaced relationship  |
| `from_node_id`      |      Yes | Prerequisite or earlier endpoint |
| `to_node_id`        |      Yes | Dependent or later endpoint      |
| `created_at`        |      Yes | Creation time                    |
| `actor`             |      Yes | Edge-attributing actor           |
| `provenance`        |      Yes | Source and causation metadata    |
| `metadata`          |      Yes | Empty object permitted           |
| `record_hash`       |      Yes | Integrity hash                   |

Direct edges MUST be acyclic. A proposed edge that would create a cycle MUST be rejected.

---

## 9. Core Node Types

### 9.1 Goal

Required payload:

* goal statement;
* scope;
* success criteria;
* constraints;
* priority when applicable.

Allowed statuses:

* `open`;
* `active`;
* `satisfied`;
* `unsatisfied`;
* `deferred`;
* `cancelled`;
* `unknown`.

A later status change MUST be represented by a new goal revision, evaluation, or decision.

### 9.2 Artifact

Required payload:

* artifact kind;
* locator or content hash;
* logical entity identity;
* revision classification;
* state-boundary reference when external.

Optional payload:

* media type;
* external revision;
* immutable content hash;
* bounded summary;
* retention classification.

An external artifact node is an authority-scoped observation or reference. It MUST NOT claim that Guerilla owns the external content.

### 9.3 Operation

Required payload:

* operation kind;
* intent;
* scope;
* expected outputs;
* preconditions;
* declared state boundaries.

Allowed statuses:

* `planned`;
* `eligible`;
* `running`;
* `completed`;
* `failed`;
* `blocked`;
* `deferred`;
* `cancelled`;
* `outcome_unknown`.

### 9.4 Event

Required payload:

* event kind;
* source;
* event time;
* correlation identifier;
* result or observation summary.

Core event subtypes include:

* `observation`;
* `action_requested`;
* `action_result`;
* `external_notification`;
* `reconciliation_result`;
* `policy_event`.

### 9.5 Evaluation

Required payload:

* evaluator kind;
* evaluator identity;
* subject node identifiers;
* result;
* evaluation time.

Evaluator kinds include:

* `deterministic`;
* `external_validator`;
* `external_oracle`;
* `model_review`;
* `human_review`.

Allowed results include:

* `pass`;
* `fail`;
* `warning`;
* `needs_review`;
* `unknown`;
* `not_applicable`.

Model evaluations that express graded judgment MUST include confidence and model provenance.

### 9.6 Decision

Required payload:

* decision kind;
* statement;
* rationale;
* authorized actor;
* input node identifiers.

Decision kinds include:

* `accept`;
* `reject`;
* `select_branch`;
* `supersede`;
* `defer`;
* `cancel`;
* `resolve_conflict`;
* `request_review`;
* `continue`.

### 9.7 Conflict

Required payload:

* conflict class;
* summary;
* evidence node identifiers;
* affected node identifiers;
* detection policy;
* created time.

Initial conflict classes include:

* `stale_observation`;
* `diverged_external_state`;
* `external_rejection`;
* `failed_evaluation`;
* `overlapping_scope`;
* `ambiguous_authority`;
* `identity_collision`;
* `missing_authority`;
* `adapter_error`;
* `lineage_incomplete`;
* `external_outcome_unknown`;
* `policy_violation`.

Allowed statuses:

* `open`;
* `acknowledged`;
* `resolved`;
* `deferred`;
* `invalidated`.

A conflict MUST cite evidence unless its class specifically concerns missing evidence or authority.

### 9.8 Snapshot

Required payload:

* snapshot identifier;
* graph revision;
* commit hash;
* graph head identifiers;
* open goals;
* unresolved conflicts;
* latest relevant artifact revisions;
* freshness requirements;
* source query or source node set;
* transformation version;
* summary hash.

A snapshot record is authoritative evidence that the boundary was captured. A human-readable or machine-readable summary payload remains derived.

---

## 10. Core Relationship Types

The runtime MUST implement:

| Relationship    | Required direction                 |
| --------------- | ---------------------------------- |
| `depends_on`    | prerequisite to dependent          |
| `produces`      | producer to product                |
| `derives`       | source to derived object           |
| `causes`        | cause to effect                    |
| `evidences`     | evidence to supported record       |
| `evaluated_by`  | subject to evaluation              |
| `superseded_by` | earlier revision to later revision |
| `resolved_by`   | conflict to resolution             |
| `captured_by`   | included node to snapshot          |

Namespaced extensions MAY add relationship types. Each extension MUST declare:

* direction;
* allowed endpoint types;
* whether the relation implies causation, derivation, revision ordering, or evidence;
* cycle behavior, which MUST remain acyclic for direct edges;
* compatibility version.

---

## 11. Reified Relationship Assertions

A symmetric, cyclic, or non-causal domain relation MUST NOT be inserted as a direct edge when it would violate or weaken the lineage DAG.

The runtime MUST support reification through an event or conflict node containing:

* relationship assertion type;
* endpoint node identifiers;
* asserting actor;
* evidence;
* effective time;
* status;
* policy or adapter source.

Incoming `evidences` or `depends_on` edges connect source records to the assertion node. Later decisions or revisions may supersede or resolve it.

A projection MAY render the assertion as an undirected or cyclic relation.

---

## 12. Authority and State Boundaries

### 12.1 State-boundary declaration

Every external adapter MUST declare one or more state boundaries containing:

* `state_boundary_id`;
* `system_id`;
* subject namespace;
* owned application-state classes;
* readable operations;
* mutating operations;
* revision model;
* identity model;
* consistency characteristics;
* conflict behavior;
* permitted roots or network endpoints;
* responsible adapter.

### 12.2 Exclusive ownership

For a given workspace, state-boundary scope, and operation class, only one configured system-of-record authority MAY be primary.

Overlapping read adapters MAY be configured, but the runtime MUST identify one as primary or mark the overlap as ambiguous.

Two adapters MUST NOT both claim authority to write the same state boundary unless an explicit arbitration extension is enabled.

### 12.3 Guerilla-owned identity

Guerilla owns:

* node identifiers;
* edge identifiers;
* graph revisions;
* commit hashes;
* graph transactions;
* snapshot identifiers;
* lineage relationship ownership.

Adapters MAY propose graph records but MUST NOT commit directly to authoritative storage.

### 12.4 External ownership

The external system owns:

* canonical application data;
* application-specific revision semantics;
* acceptance or rejection of native actions;
* business-rule validation;
* native concurrency and rollback;
* external event retention.

---

## 13. Adapter Contract

### 13.1 Descriptor

Every adapter MUST return a descriptor containing:

* adapter identifier and version;
* external system identifier;
* supported protocol versions;
* state boundaries;
* supported operations;
* request and response schemas;
* read consistency;
* write behavior;
* event ordering;
* concurrency model;
* idempotency support;
* conflict handling;
* replay support;
* snapshot support;
* identity stability;
* lineage completeness;
* authentication requirements;
* known limitations.

### 13.2 Describe

`describe` MUST be non-mutating.

### 13.3 Observe

`observe` MUST return:

* subject identity;
* external revision when available;
* observation time;
* consistency level;
* freshness or expiry information;
* bounded state summary;
* payload hash or external reference;
* warnings and omissions;
* correlation information.

An adapter MUST NOT label an observation as strongly consistent unless the external system provides that guarantee.

### 13.4 Act

`act` MUST:

* accept structured arguments;
* require an idempotency key when the external operation may be retried;
* identify the target state boundary;
* preserve external acceptance, rejection, or unknown status;
* return external correlation identifiers;
* avoid direct application-state writes outside the declared interface.

### 13.5 Evaluate

`evaluate` MUST identify:

* evaluator kind;
* evaluator version;
* inputs;
* external or graph revision evaluated;
* result;
* diagnostics;
* confidence where applicable.

### 13.6 Reconcile

`reconcile` MUST accept:

* original action-request identifier;
* idempotency key;
* external correlation identifier when available;
* expected subject and state boundary.

It MUST return the strongest supported classification and disclose when the outcome remains unknown.

---

## 14. Ingestion Flow

### 14.1 External observation ingestion

The runtime MUST:

1. authorize the request;
2. resolve the adapter and state boundary;
3. validate the adapter descriptor;
4. invoke `observe`;
5. validate the returned authority and schema;
6. resolve or allocate entity identity;
7. compare external revision with the latest known revision;
8. create an artifact or event node;
9. add required lineage edges;
10. commit the records atomically;
11. update derived indexes after commit.

### 14.2 External event ingestion

For pushed or imported events, the runtime MUST distinguish:

* source event time;
* receipt time;
* graph commitment time.

Receipt order MUST NOT be treated as causation. Causation requires an explicit identifier, adapter assertion, or configured rule.

### 14.3 Duplicate ingestion

The runtime MUST deduplicate by a declared combination of:

* state boundary;
* external event identifier;
* external revision;
* payload hash;
* idempotency key.

A duplicate with identical content MAY return the original graph revision. A duplicate identifier with different content MUST produce an identity or idempotency conflict.

---

## 15. External Action Flow

Because graph commitment and external mutation cannot generally share one atomic transaction, the runtime MUST use an intent-and-reconciliation flow.

### 15.1 Before action

The runtime MUST:

1. verify current graph revision guards;
2. verify required external observations;
3. reject stale or ambiguous state unless policy permits continuation;
4. append the operation and `action_requested` event;
5. commit the intent before invoking the external system.

### 15.2 Invocation

The adapter host MUST invoke the external action with:

* structured arguments;
* state-boundary identifier;
* idempotency key;
* correlation identifier;
* expected external revision when supported;
* timeout and authorization context.

### 15.3 After action

The runtime MUST append:

* action-result event;
* exact external outcome class;
* external identifiers;
* diagnostics;
* optional after-state observation;
* evaluation or conflict records when required.

### 15.4 Interrupted action

When execution stops after intent commitment but before result commitment, the operation status MUST become `outcome_unknown` in the derived state.

The runtime MUST invoke reconciliation before retrying a non-provably idempotent action.

---

## 16. Reconciliation Flow

Reconciliation MUST:

1. load the original intent and idempotency key;
2. query the adapter or external system for the action outcome;
3. compare external revisions and correlation identifiers;
4. identify possible out-of-band state changes;
5. append a reconciliation event;
6. append any newly observed artifact revision;
7. create a conflict when the outcome remains unknown or contradicts prior lineage;
8. update eligible-operation projections.

Reconciliation MUST NOT erase the uncertainty interval.

---

## 17. Concurrency

### 17.1 MVP writer model

The MVP MUST serialize graph commits with one workspace writer lock.

Concurrent readers MAY read a stable graph revision without acquiring the writer lock.

### 17.2 Optimistic graph guard

A mutating request SHOULD include `expected_graph_revision`.

When the current revision differs, the runtime MUST return `stale_graph_revision` unless the operation is explicitly revision-independent.

### 17.3 External concurrency

External concurrency remains governed by the external system. Adapters MUST disclose whether they support:

* revision guards;
* compare-and-set;
* serializable transactions;
* optimistic concurrency;
* last-write-wins;
* append-only writes;
* no concurrency control;
* unknown behavior.

### 17.4 Future multi-writer operation

Distributed writers, reservations, leader election, and graph merge are deferred. An implementation MUST NOT claim multi-writer safety merely because the underlying storage supports concurrent appends.

---

## 18. Idempotency

Every externally mutating action MUST have an idempotency key unless the adapter proves the action cannot be retried or duplicated.

The runtime MUST persist:

* key;
* workspace;
* actor;
* adapter;
* action;
* canonical request hash;
* original response;
* graph revision;
* external correlation identifiers.

Repeated use of the same key and request hash MUST return the original committed result or reconciliation state.

Repeated use of the same key with a different request hash MUST return `idempotency_conflict`.

---

## 19. Projection Generation

Every projection request MUST specify or resolve:

* view type;
* scope;
* graph revision;
* transformation version;
* policy version;
* filters;
* requested output format.

Every projection result MUST contain:

* projection identifier;
* graph revision;
* commit hash;
* generation time;
* transformation version;
* policy version;
* source-node set or reproducible source query;
* freshness summary;
* information-loss declaration;
* result hash.

Projection generation MUST be deterministic when the same graph revision, policy, transformation, and parameters are used.

A non-deterministic transformation MUST identify the non-deterministic component and MUST NOT be used for authoritative integrity checks.

---

## 20. Manifest Generation

The MVP manifest MUST support:

* filtering by artifact kind, state boundary, actor, status, or scope;
* selecting latest known non-superseded revisions;
* including content hashes and external locators;
* including source node identifiers;
* reporting stale, unknown, or ambiguous revisions;
* deterministic ordering.

A manifest MUST NOT silently select between incomparable external revisions. It MUST report ambiguity or require an explicit policy.

---

## 21. Snapshot Generation

Snapshot creation MUST:

1. resolve a committed graph revision;
2. calculate graph heads within scope;
3. collect open goals;
4. collect unresolved conflicts;
5. select latest relevant artifact observations;
6. calculate freshness requirements;
7. identify next eligible operations;
8. record adapter and transformation versions;
9. generate a deterministic summary;
10. commit a snapshot node and incoming `captured_by` edges.

A snapshot MUST NOT assert that external systems are frozen.

---

## 22. Diff Generation

The diff engine MUST support comparisons between:

* graph revisions;
* snapshots;
* manifests;
* revisions of one logical artifact;
* selected subgraph scopes.

The result MUST distinguish:

* added nodes;
* superseded revisions;
* added edges;
* newly opened conflicts;
* resolved conflicts;
* status changes caused by policy;
* changes caused only by refreshed external observations.

---

## 23. Conflict Detection

The MVP conflict engine MUST detect at least:

* action based on a stale external observation;
* incompatible external revision;
* external rejection;
* failed required evaluation;
* ambiguous state-boundary ownership;
* duplicate external identity;
* idempotency conflict;
* unsupported adapter capability;
* incomplete action outcome;
* missing required ancestry;
* invalid projection source.

Conflict resolution MUST create a decision or operation node. The conflict record MUST remain in history.

---

## 24. Validation Pipeline

Before commit, the runtime MUST validate in this order:

1. protocol and schema validity;
2. authorization;
3. identifier uniqueness;
4. authority and state-boundary validity;
5. payload and record hashes;
6. idempotency;
7. graph-revision guard;
8. endpoint existence;
9. relationship-type compatibility;
10. lineage acyclicity;
11. snapshot and projection source validity;
12. transaction completeness.

A failure MUST reject the entire append transaction.

---

## 25. Append Transactions

A transaction consists of:

* transaction-begin record;
* one or more proposed node or edge records;
* transaction-commit record.

The begin record MUST include:

* transaction identifier;
* expected previous commit hash;
* expected graph revision;
* actor;
* creation time.

The commit record MUST include:

* transaction identifier;
* committed record identifiers;
* transaction hash;
* new graph revision;
* previous commit hash;
* commit hash;
* commitment time.

Records belonging to an incomplete or invalid transaction MUST be ignored during replay and reported as recovery warnings.

---

## 26. Replay and Recovery

Replay MUST:

1. load the graph header;
2. validate protocol and canonicalization versions;
3. load archive segments in hash order;
4. validate segment and commit chains;
5. parse transactions;
6. ignore incomplete transactions;
7. verify record and transaction hashes;
8. rebuild node and edge maps;
9. validate endpoint existence and acyclicity;
10. calculate graph revisions and heads;
11. rebuild indexes;
12. leave external actions untouched.

Replay MUST fail explicitly when authoritative segments are missing, corrupt, or inconsistent.

A repair tool MAY create a new recovery workspace referencing the last valid commit. It MUST NOT silently rewrite the damaged graph.

---

## 27. Indexing and Caching

The reference SQLite index SHOULD contain:

* nodes by identifier, entity, type, authority, and status;
* edges by source, destination, and relationship type;
* graph revisions and commits;
* graph heads;
* supersession chains;
* open conflicts;
* state-boundary mappings;
* external identities;
* idempotency records;
* projection metadata;
* snapshot references;
* payload references.

Caches MUST include the source graph revision in their keys.

A cache entry from an earlier graph revision MAY be served only when the client explicitly requests that earlier revision.

---

## 28. Archiving

The runtime MAY seal old graph segments.

An archive seal MUST include:

* archive identifier;
* first and last graph revisions;
* previous segment hash;
* segment hash;
* record count;
* commit count;
* creation time.

Archived records remain authoritative. Summary compaction MAY reduce active model or user context but MUST NOT delete required lineage.

---

## 29. Error Handling

The runtime MUST use stable machine-readable error codes.

Required codes include:

* `invalid_message`;
* `unsupported_version`;
* `schema_violation`;
* `unauthorized`;
* `forbidden`;
* `unknown_workspace`;
* `unknown_node`;
* `unknown_adapter`;
* `unsupported_capability`;
* `duplicate_id`;
* `identity_collision`;
* `idempotency_conflict`;
* `stale_graph_revision`;
* `stale_external_revision`;
* `ambiguous_authority`;
* `state_boundary_violation`;
* `lineage_cycle`;
* `missing_endpoint`;
* `record_hash_mismatch`;
* `payload_hash_mismatch`;
* `transaction_incomplete`;
* `adapter_unavailable`;
* `adapter_error`;
* `external_rejection`;
* `external_outcome_unknown`;
* `projection_invalid`;
* `rate_limited`;
* `internal_error`.

Errors SHOULD include:

* request and correlation identifiers;
* retry classification;
* affected state boundary;
* graph revision;
* diagnostic summary;
* evidence node identifiers when available.

Sensitive payloads MUST NOT be copied into error text without redaction.

---

## 30. Observability

The runtime MUST emit operational metrics for:

* append latency;
* commit failures;
* cycle rejections;
* graph size;
* payload size;
* index rebuild time;
* adapter calls and latency;
* action outcomes;
* reconciliation attempts;
* unknown outcomes;
* open conflicts;
* projection generation latency;
* snapshot generation latency;
* redaction events;
* authorization failures.

Operational logs MUST distinguish:

* protocol request;
* graph transaction;
* adapter invocation;
* external result;
* projection generation.

Logs MUST NOT become the authoritative lineage store.

---

## 31. Security Boundaries

### 31.1 Adapter trust

Adapters are trusted integration components. The runtime MUST validate their outputs but cannot prove their semantic correctness.

Adapters SHOULD run with the least operating-system, filesystem, network, and external-system privileges required.

### 31.2 Structured invocation

Model-generated or user-generated shell text MUST NOT be executed directly by the core runtime.

Adapters SHOULD use typed clients, argument arrays, or structured tool invocations.

### 31.3 Root and endpoint restrictions

Each state boundary MUST declare permitted filesystem roots, network endpoints, or resource namespaces.

An access outside that declaration MUST be rejected.

### 31.4 Payload handling

Payloads MUST be treated as untrusted data.

The runtime MUST NOT:

* execute payload content;
* import executable adapter behavior from payloads;
* deserialize unsafe object formats;
* expose secrets without authorization.

### 31.5 Redaction

Redaction MUST occur before payload persistence.

The graph SHOULD record that redaction occurred, the redaction-policy version, and the hash of the retained payload. It MUST NOT retain the removed secret merely to preserve a pre-redaction hash.

### 31.6 Authorization

The runtime MUST authorize:

* graph reads;
* graph appends;
* adapter observations;
* external actions;
* conflict decisions;
* snapshot access;
* payload access;
* administrative configuration.

A model actor MUST NOT receive broader authority than the principal or policy under which it operates.

---

## 32. Reference Command and API Surface

A minimal command surface SHOULD provide:

| Command family | Required capability                      |
| -------------- | ---------------------------------------- |
| `workspace`    | initialize and verify                    |
| `adapter`      | list, describe, validate                 |
| `observe`      | request and ingest observations          |
| `act`          | record intent and invoke external action |
| `reconcile`    | resolve uncertain outcomes               |
| `goal`         | create and inspect goals                 |
| `operation`    | create and inspect operations            |
| `evaluation`   | record or request evaluations            |
| `conflict`     | list, inspect, acknowledge, resolve      |
| `decision`     | record explicit decisions                |
| `lineage`      | query ancestry and descendants           |
| `view`         | generate projections                     |
| `manifest`     | generate and verify manifests            |
| `snapshot`     | create, inspect, verify, resume          |
| `graph`        | verify, replay, export, archive          |

The implementation MAY expose CLI, local HTTP, library, or message-based interfaces. Protocol semantics MUST remain consistent.

---

## 33. MVP Requirements

A conforming MVP MUST implement:

* local workspace initialization;
* one writer lock;
* graph header and append transactions;
* canonical JSON and SHA-256;
* graph revisions and commit chain;
* eight core node types;
* nine core relationship types;
* cycle rejection;
* external authority envelopes;
* state-boundary registry;
* adapter `describe`, `observe`, `act`, `evaluate`, and `reconcile`;
* intent-before-action recording;
* idempotency;
* unknown-outcome reconciliation;
* conflict records;
* graph verification and replay;
* SQLite or equivalent rebuildable index;
* lineage, manifest, snapshot, diff, conflict, and resume projections;
* payload hashing and redaction;
* protocol and graph conformance tests.

---

## 34. Optional and Deferred Capabilities

The following MAY be implemented after the MVP:

* remote graph service;
* multiple concurrent writers;
* distributed locking or consensus;
* event-stream subscriptions;
* adapter process sandboxing;
* signed commits and payload attestations;
* cross-workspace federation;
* selective lineage disclosure;
* portable snapshot bundles;
* incremental streaming projections;
* policy engines;
* scheduling and reservations;
* cost-aware planning;
* domain-specific semantic merge;
* global external-identity resolution.

Optional capabilities MUST preserve the core authority and DAG invariants.

---

## 35. Extension Points

Extensions MAY define:

* namespaced node subtypes;
* namespaced relationship types;
* adapter capability fields;
* projection types;
* conflict classes;
* authentication profiles;
* payload media types;
* policy languages.

An extension MUST declare:

* namespace owner;
* version;
* compatibility range;
* schemas;
* invariants;
* downgrade behavior;
* security implications.

An extension MUST NOT redefine the meaning of a core field or relationship type.

---

## 36. Testing Requirements

### 36.1 Record tests

The conformance suite MUST test:

* valid and invalid node records;
* valid and invalid edge records;
* duplicate identifiers;
* hash mismatches;
* unsupported versions;
* authority-envelope requirements.

### 36.2 Transaction tests

The suite MUST test:

* atomic commit;
* incomplete transaction recovery;
* previous-commit mismatch;
* transaction-hash mismatch;
* monotonic graph revisions;
* concurrent append rejection under the writer lock.

### 36.3 DAG tests

The suite MUST test:

* linear ancestry;
* branching;
* multi-parent convergence;
* supersession;
* direct cycle rejection;
* self-loop rejection;
* missing endpoints;
* reified symmetric relationships.

### 36.4 Adapter tests

The suite MUST test:

* descriptor validity;
* state-boundary enforcement;
* read-only observation;
* structured action arguments;
* external rejection preservation;
* unsupported capability responses;
* reconciliation;
* identity collision handling;
* declared consistency guarantees.

### 36.5 Action-recovery tests

The suite MUST simulate failure:

* before intent commit;
* after intent commit but before external call;
* after external completion but before result commit;
* after result commit but before after-state observation;
* during reconciliation.

### 36.6 Projection tests

The suite MUST test:

* deterministic output;
* source revision citation;
* source-node citation;
* information-loss declaration;
* stale external observation reporting;
* regeneration after index deletion;
* manifest ambiguity handling;
* snapshot verification;
* diff correctness.

### 36.7 Security tests

The suite MUST test:

* path and endpoint escape;
* unauthorized graph access;
* unauthorized external action;
* secret redaction;
* payload non-execution;
* unsafe serialization rejection;
* adapter capability escalation;
* idempotency-key abuse.

### 36.8 Performance tests

The reference implementation SHOULD measure:

* append throughput;
* cycle-check cost;
* replay time;
* index rebuild time;
* traversal latency;
* projection latency;
* snapshot size;
* payload deduplication;
* archive performance.

---

## 37. MVP Acceptance Criteria

The MVP is accepted when all of the following are demonstrated:

1. A workspace can be initialized and verified.
2. Valid transactions commit atomically.
3. Incomplete transactions are ignored on replay.
4. A proposed lineage cycle is rejected.
5. External observations preserve authority and revision metadata.
6. An external action is preceded by committed intent.
7. An interrupted external action can be reconciled without duplicate mutation.
8. Reused idempotency keys return the original result or a conflict.
9. A stale external revision creates an explicit conflict.
10. A projection can be regenerated from its graph revision.
11. A snapshot identifies graph heads and freshness requirements.
12. The index can be deleted and rebuilt without lineage loss.
13. Replay does not invoke external actions.
14. Payload content is never executed.
15. No executable runtime component claims implementation completion without passing the conformance suite.

---

## 38. Implementation Assumptions Requiring Confirmation

The following choices remain architecture assumptions rather than completed implementation facts:

* canonical JSON profile;
* ULID versus UUIDv7 identifiers;
* filesystem durability and lock implementation;
* default payload-retention period;
* default redaction policy;
* exact adapter isolation model;
* default projection policy language;
* archive thresholds;
* remote API transport;
* cryptographic signature support.

These choices MAY change before the protocol is declared stable, provided the cross-document invariants remain unchanged.
