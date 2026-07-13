# GUERILLA_PROTOCOL_SPEC.md

# Guerilla Lineage and Continuity Protocol

**Document purpose:** Define the transport-independent contract used by clients, adapters, services, tools, and agents to communicate with a Guerilla runtime.

**Status:** Revised protocol draft; not yet declared stable

**Version:** 0.2.0-draft

**Intended audience:** Protocol implementers, adapter authors, client developers, runtime maintainers, security reviewers, and conformance-test authors.

**Revision provenance:** This document supersedes the supplied v0.1.0 protocol framing.

---

## 1. Protocol Scope

The Guerilla Lineage and Continuity Protocol, abbreviated GLCP, defines:

* message envelopes;
* version negotiation;
* capabilities;
* graph append operations;
* node and edge schemas;
* lineage queries;
* adapter operations;
* projection requests;
* manifest operations;
* snapshot operations;
* revisions;
* correlation and causation identifiers;
* idempotency;
* error and conflict responses;
* retries;
* ordering;
* pagination;
* authentication and authorization assumptions.

GLCP does not define:

* the internal persistence technology of a Guerilla runtime;
* the complete application state of an external system;
* external business rules;
* external rollback or merge algorithms;
* distributed consensus;
* automatic semantic conflict resolution;
* a universal external-action schema.

---

## 2. Transport Independence

GLCP messages MAY be carried over:

* local function calls;
* standard input and output;
* HTTP;
* message queues;
* remote procedure calls;
* tool protocols;
* local sockets;
* other transports that preserve message semantics.

A transport profile MUST define:

* serialization;
* framing;
* maximum message size;
* authentication mechanism;
* timeout behavior;
* streaming support;
* transport-level error mapping.

Transport success does not imply operation success.

---

## 3. Protocol Invariants

A conforming implementation MUST preserve these invariants.

1. Committed graph records are immutable.
2. Direct authoritative edges form a DAG.
3. Every graph mutation is transactional.
4. Every successful mutation returns a graph revision and commit identifier.
5. External observations identify authority and state boundary.
6. External mutation requests identify an adapter, action, and idempotency key.
7. Correlation does not imply causation.
8. Receipt order does not imply external event order.
9. Reusing an idempotency key with different request content is an error.
10. Views identify source graph revision and transformation version.
11. Snapshots do not freeze external systems.
12. Manifest and view responses are derived unless explicitly identified as graph records.
13. External action rejection is preserved.
14. Unknown action outcomes remain unknown until reconciled.
15. A client cannot obtain greater authority by declaring an actor or state boundary in message content.
16. Protocol payloads are data and MUST NOT be executed as adapter code.

---

## 4. Versioning and Negotiation

### 4.1 Version format

Protocol versions use `MAJOR.MINOR.PATCH`.

### 4.2 Compatibility

* A major-version change MAY introduce incompatible semantics.
* A minor-version change MAY add backward-compatible operations, fields, or enum values.
* A patch-version change MUST preserve wire compatibility.

### 4.3 Negotiation

A client SHOULD begin with `protocol.negotiate` and provide:

* supported versions;
* required operations;
* optional extensions;
* preferred transport profile.

The runtime MUST select the highest mutually supported compatible version or return `unsupported_version`.

### 4.4 Unknown fields

A receiver MAY ignore unknown optional fields only when:

* the negotiated version permits additive fields;
* the field is not marked critical;
* ignoring it does not weaken authorization, integrity, or graph invariants.

Unknown critical fields MUST cause rejection.

---

## 5. Message Envelope

Every request, response, and protocol event MUST use a common envelope.

| Field                     |    Required | Meaning                                                                   |
| ------------------------- | ----------: | ------------------------------------------------------------------------- |
| `protocol`                |         Yes | `glcp`                                                                    |
| `version`                 |         Yes | Negotiated protocol version                                               |
| `message_id`              |         Yes | Unique message identifier                                                 |
| `message_type`            |         Yes | `request`, `response`, or `event`                                         |
| `operation`               |         Yes | Operation name                                                            |
| `sent_at`                 |         Yes | RFC 3339 timestamp                                                        |
| `workspace_id`            | Conditional | Required for workspace operations                                         |
| `actor`                   | Conditional | Actor attribution; server verifies authority                              |
| `correlation_id`          |         Yes | Groups related messages                                                   |
| `causation_id`            |          No | Identifier of the message or graph node that directly caused this message |
| `idempotency_key`         | Conditional | Required for retryable mutations                                          |
| `expected_graph_revision` |          No | Optimistic graph guard                                                    |
| `extensions`              |         Yes | Empty object permitted                                                    |
| `body`                    |         Yes | Operation-specific content                                                |

A message identifier MUST be unique for the sending principal within the transport retention period.

---

## 6. Actor and Authorization Context

The `actor` envelope MAY contain:

* actor identifier;
* actor kind;
* display name;
* provider;
* session identifier;
* delegated principal;
* metadata.

Allowed actor kinds include:

* `human`;
* `model`;
* `tool`;
* `service`;
* `automation`;
* `system`;
* `unknown`.

The runtime MUST derive authorization from the authenticated transport principal and server-side policy. It MUST NOT trust a client-supplied actor field as proof of authority.

A response SHOULD identify the effective actor used for authorization and lineage attribution.

---

## 7. Correlation and Causation

### 7.1 Correlation identifier

A `correlation_id` groups messages belonging to one workflow, request chain, or external action.

Messages sharing a correlation identifier are not automatically causally related.

### 7.2 Causation identifier

A `causation_id` identifies the specific earlier message or graph node that directly prompted the current message.

When causation is unknown, the field MUST be absent or explicitly marked unknown. A receiver MUST NOT infer causation from timestamps alone.

### 7.3 External correlation

Adapter responses SHOULD preserve external request, operation, event, or transaction identifiers under an authority-scoped field.

---

## 8. Request and Response Semantics

### 8.1 Request

A request asks the runtime to read, calculate, propose, commit, observe, invoke, or reconcile an operation.

### 8.2 Response

Every response MUST contain:

| Field                |    Required | Meaning                                                  |
| -------------------- | ----------: | -------------------------------------------------------- |
| `request_message_id` |         Yes | Corresponding request                                    |
| `status`             |         Yes | `success`, `accepted`, `partial`, `rejected`, or `error` |
| `graph_revision`     | Conditional | Current or committed graph revision                      |
| `commit_id`          | Conditional | Commit identifier for successful mutation                |
| `result`             | Conditional | Operation-specific result                                |
| `errors`             |         Yes | Empty array permitted                                    |
| `conflicts`          |         Yes | Empty array permitted                                    |
| `retry`              |         Yes | Retry classification                                     |
| `warnings`           |         Yes | Empty array permitted                                    |

### 8.3 Accepted versus completed

`accepted` means the runtime accepted a request for processing. It does not mean an external action completed.

A transport profile that supports asynchronous processing MUST provide a status-query operation.

### 8.4 Partial response

A `partial` response MUST identify:

* completed portions;
* omitted portions;
* continuation cursor when applicable;
* warnings;
* whether the result can safely be used.

---

## 9. Operation Families

GLCP defines these operation families.

| Family        | Purpose                                                        |
| ------------- | -------------------------------------------------------------- |
| `protocol.*`  | Negotiation, health, and capabilities                          |
| `workspace.*` | Workspace metadata and verification                            |
| `graph.*`     | Transactional node and edge appends                            |
| `node.*`      | Node retrieval                                                 |
| `edge.*`      | Edge retrieval                                                 |
| `lineage.*`   | Traversal and graph-head queries                               |
| `adapter.*`   | Description, observation, action, evaluation, reconciliation   |
| `conflict.*`  | Conflict retrieval and authorized resolution                   |
| `view.*`      | Derived projection generation                                  |
| `manifest.*`  | Inventory generation and retrieval                             |
| `snapshot.*`  | Snapshot creation, retrieval, verification, and resume context |
| `diff.*`      | Comparison of graph boundaries                                 |
| `payload.*`   | Authorized payload retrieval and verification                  |

---

## 10. Capability Declaration

`protocol.capabilities` and `adapter.describe` MUST return declared capabilities rather than requiring clients to infer behavior.

An adapter capability declaration MUST include:

| Capability           | Required values or description                                                         |
| -------------------- | -------------------------------------------------------------------------------------- |
| Read consistency     | Strong, bounded-stale, eventual, snapshot, reconstructed, unknown                      |
| Write behavior       | Read-only, transactional, optimistic, append-only, last-write-wins, manual, unknown    |
| Event ordering       | Total, per-subject, causal, source-sequence, unordered, unknown                        |
| Concurrency          | Single-writer, multi-writer, externally serialized, optimistic, none, unknown          |
| Conflict handling    | Reject, native merge, last-write-wins, manual, report-only, unknown                    |
| Replay support       | None, query-only, deterministic replay, external replay                                |
| Snapshot support     | None, native snapshot, point-in-time read, reconstructed snapshot                      |
| Identity stability   | Immutable, stable, renameable, recyclable, content-addressed, unknown                  |
| Lineage completeness | Complete within boundary, best effort, sampled, action-only, observation-only, unknown |
| Idempotency          | Native, adapter-emulated, unsupported, unknown                                         |
| Mutating actions     | Explicit action list                                                                   |
| State boundaries     | Explicit ownership scopes                                                              |
| Schemas              | Request and response schema identifiers                                                |
| Authentication       | Required external credentials or scopes                                                |
| Limitations          | Known omissions and unsafe assumptions                                                 |

A capability declaration is a claim by the adapter. It does not transfer application-state authority to Guerilla.

---

## 11. Graph Transaction Operations

### 11.1 `graph.append`

`graph.append` proposes one atomic graph transaction.

The request MUST include:

* transaction identifier;
* expected graph revision;
* proposed nodes;
* proposed edges;
* idempotency key;
* actor attribution;
* optional policy references.

The runtime MUST validate the complete transaction before commitment.

A successful response MUST include:

* new graph revision;
* commit identifier;
* commit hash;
* committed node identifiers;
* committed edge identifiers.

### 11.2 Immutability

GLCP does not define node update or delete operations.

A correction MUST use:

* a new node;
* the same logical entity identifier where applicable;
* a `superseded_by` edge;
* optional decision or rationale.

### 11.3 Transaction failure

Any invalid member MUST reject the entire transaction.

The runtime MUST NOT partially commit a rejected `graph.append`.

---

## 12. Node Operations

### 12.1 `node.get`

The request identifies:

* node identifier;
* optional graph revision;
* payload-inclusion policy.

The response MUST return the node as visible at the requested graph revision or `unknown_node`.

### 12.2 `node.get_by_entity`

The request identifies:

* entity identifier;
* optional state boundary;
* revision-selection policy;
* graph revision.

The response MUST distinguish:

* latest non-superseded revision;
* all revisions;
* ambiguous incomparable revisions;
* no matching node.

### 12.3 Node types

Core node types are:

* `goal`;
* `artifact`;
* `operation`;
* `event`;
* `evaluation`;
* `decision`;
* `conflict`;
* `snapshot`.

Unknown unnamespaced node types MUST be rejected.

---

## 13. Edge Operations

### 13.1 `edge.get`

The request identifies an edge and optional graph revision.

### 13.2 Direct edge semantics

Core relationship types are:

* `depends_on`;
* `produces`;
* `derives`;
* `causes`;
* `evidences`;
* `evaluated_by`;
* `superseded_by`;
* `resolved_by`;
* `captured_by`.

All direct edges MUST point from earlier or prerequisite records to later or dependent records.

### 13.3 Cycle rejection

Before commitment, the runtime MUST reject a direct edge if the destination already reaches the source.

The error code MUST be `lineage_cycle`.

### 13.4 Non-causal relationships

A client requesting a symmetric, cyclic, or non-causal relationship MUST submit a reified event or conflict node rather than an incompatible direct edge.

---

## 14. Lineage Queries

### 14.1 `lineage.query`

The request MAY include:

* start node identifiers;
* traversal direction;
* relationship-type filter;
* node-type filter;
* state-boundary filter;
* actor filter;
* maximum depth;
* maximum result count;
* graph revision;
* include-payload policy;
* pagination cursor.

The response MUST include:

* graph revision;
* matching nodes;
* matching edges;
* truncation indicator;
* next cursor when applicable.

### 14.2 Direction

Allowed traversal directions are:

* `ancestors`;
* `descendants`;
* `both`;
* `immediate_predecessors`;
* `immediate_successors`.

### 14.3 Graph heads

`lineage.heads` MUST return nodes within scope that have no outgoing direct lineage edge at the requested graph revision.

A projection MAY apply additional status or policy filters, but the response MUST distinguish structural heads from policy-defined active heads.

### 14.4 Path query

`lineage.paths` MAY return one or more paths between two nodes. The runtime MUST disclose when result limits prevent exhaustive path enumeration.

---

## 15. Adapter Operations

### 15.1 `adapter.describe`

Returns descriptor and capability metadata. The operation MUST be non-mutating.

### 15.2 `adapter.observe`

The request MUST include:

* adapter identifier;
* state boundary;
* subject;
* observation kind;
* requested consistency;
* optional external revision guard.

The response MUST include:

* observed subject;
* authority;
* external revision when available;
* observation time;
* consistency achieved;
* freshness;
* state summary;
* payload reference;
* omissions and warnings.

An observation response is not a graph commit unless the request explicitly asks the runtime to ingest it.

### 15.3 `adapter.act`

The request MUST include:

* adapter identifier;
* state boundary;
* action name;
* structured arguments;
* idempotency key;
* expected external revision when supported;
* correlation identifier.

The runtime MUST commit action intent before invoking the adapter.

The response MUST distinguish:

* external acceptance;
* external rejection;
* transport failure;
* adapter failure;
* timeout;
* partial result;
* unknown outcome.

### 15.4 `adapter.evaluate`

The request identifies:

* evaluator;
* subject nodes or external revisions;
* evaluation schema;
* policy version.

The result MUST identify evaluator type, inputs, result, diagnostics, and confidence where required.

### 15.5 `adapter.reconcile`

The request identifies:

* original action-request node;
* idempotency key;
* external correlation identifier when available.

The response MUST classify the action outcome or preserve `unknown`.

---

## 16. Conflict Operations

### 16.1 `conflict.list`

The request MAY filter by:

* status;
* class;
* state boundary;
* affected entity;
* graph revision;
* actor;
* creation range.

### 16.2 `conflict.get`

Returns:

* conflict node;
* evidence nodes;
* affected nodes;
* resolution lineage;
* current derived status.

### 16.3 `conflict.resolve`

Conflict resolution requires an authorized actor.

The request MUST include:

* conflict node;
* decision kind;
* statement;
* rationale;
* supporting evidence;
* optional continuation operations.

The runtime MUST create a decision or operation node and a `resolved_by` edge. It MUST NOT mutate the conflict node.

### 16.4 Conflict response

A mutating operation blocked by an unresolved conflict SHOULD return:

* status `rejected` or `partial`;
* error or conflict code;
* conflict identifiers;
* required corrective operations;
* whether retry is permitted after refresh or resolution.

---

## 17. View Operations

### 17.1 `view.generate`

The request MUST include:

* view type;
* graph revision or `latest`;
* scope;
* transformation version;
* policy version;
* parameters;
* output format.

The response MUST include:

* projection identifier;
* resolved graph revision;
* commit hash;
* generation time;
* transformation version;
* policy version;
* source-node set or reproducible query;
* freshness summary;
* information-loss declaration;
* result hash;
* result or payload reference.

### 17.2 Required view types

The MVP MUST support:

* `lineage`;
* `dependency`;
* `conflict`;
* `progress`;
* `resume`;
* `requirement_traceability`.

Additional views MUST use namespaced identifiers.

### 17.3 Persisted views

A persisted view MUST remain identified as derived. It MUST be invalidated or marked stale when its source revision or policy no longer matches the request.

---

## 18. Manifest Operations

### 18.1 `manifest.generate`

The request MAY select:

* artifact kinds;
* state boundaries;
* scope;
* actor;
* status;
* latest-revision policy;
* graph revision;
* fields;
* sort order.

The response MUST include:

* manifest identifier;
* source graph revision;
* transformation version;
* source query;
* entries;
* ambiguity reports;
* stale-observation reports;
* result hash.

### 18.2 `manifest.get`

Retrieves a persisted manifest by identifier and MUST report whether it is current relative to the requested graph revision.

### 18.3 Authority

A manifest is derived. An external consumer MAY treat it as an input artifact, but it does not replace source graph records.

---

## 19. Snapshot Operations

### 19.1 `snapshot.create`

The request MUST include:

* scope;
* graph revision or `latest`;
* snapshot policy version;
* summary format;
* optional freshness requirements.

The runtime MUST commit a snapshot node.

The response MUST include:

* snapshot identifier;
* graph revision;
* commit hash;
* graph heads;
* open goals;
* unresolved conflicts;
* latest relevant artifact revisions;
* refresh requirements;
* next eligible operations;
* summary hash;
* source references.

### 19.2 `snapshot.get`

Returns the snapshot node and optional materialized summary.

### 19.3 `snapshot.verify`

Verifies:

* snapshot node integrity;
* graph revision and commit;
* source-node existence;
* summary hash;
* transformation version.

Verification MUST NOT claim that cited external observations remain current.

### 19.4 `snapshot.resume_context`

Returns a derived resume view. It MUST distinguish:

* immutable graph facts;
* external observations needing refresh;
* unresolved conflicts;
* eligible operations;
* adapter compatibility warnings.

---

## 20. Diff Operations

`diff.generate` MUST support comparison of:

* graph revisions;
* snapshots;
* manifests;
* artifact revisions.

The response MUST identify:

* left and right boundaries;
* added and superseded nodes;
* added edges;
* opened and resolved conflicts;
* policy-only status changes;
* refreshed observations;
* omitted unchanged history.

---

## 21. Revision Handling

### 21.1 Graph revision

Every successful graph mutation returns a new monotonically increasing graph revision.

Read requests MAY specify:

* an exact graph revision;
* `latest`;
* a snapshot identifier that resolves to a revision.

### 21.2 Artifact revision

Artifact revisions use separate nodes connected by `superseded_by`.

A runtime MUST NOT assume one revision is newer solely because it was received later. Ordering requires an external revision token, supersession assertion, causation path, or authorized decision.

### 21.3 External revision

An adapter MUST preserve external revision tokens exactly. A runtime MAY normalize them for indexing but MUST retain the original value.

### 21.4 Stale graph guard

When `expected_graph_revision` does not match the current revision, a mutation MUST fail with `stale_graph_revision`, unless the operation explicitly declares revision independence.

---

## 22. Idempotency

### 22.1 Required scope

Idempotency keys are required for:

* graph append requests that may be retried;
* adapter actions;
* conflict resolutions;
* snapshot creation when duplicate snapshots are undesirable.

### 22.2 Same key and same content

The runtime MUST return the prior committed response or current reconciliation status.

### 22.3 Same key and different content

The runtime MUST return `idempotency_conflict`.

### 22.4 Retention

The runtime capability response MUST declare idempotency-key retention duration. A client MUST NOT assume keys remain recognized indefinitely.

---

## 23. Ordering Guarantees

### 23.1 Graph commits

The local single-writer profile provides a total order of committed graph revisions within one workspace.

### 23.2 Records within a transaction

Records are ordered for hashing, but semantic causation is determined by edges and identifiers, not line position.

### 23.3 External events

An adapter MUST declare its external ordering guarantee.

The runtime MUST preserve:

* external event time;
* receipt time;
* graph commitment time;
* external sequence or causation token when provided.

### 23.4 Cross-workspace order

GLCP v0.2 does not define a total order across workspaces.

---

## 24. Pagination

List and traversal operations MAY paginate.

A pagination cursor MUST be:

* opaque to the client;
* bound to the original query;
* bound to a graph revision;
* integrity-protected;
* invalidated when its required state is unavailable.

Using a cursor with altered query parameters MUST return `invalid_cursor`.

Pagination MUST NOT silently move from one graph revision to another.

---

## 25. Error Model

Each error MUST contain:

| Field                    | Required | Meaning                      |
| ------------------------ | -------: | ---------------------------- |
| `code`                   |      Yes | Stable machine-readable code |
| `message`                |      Yes | Human-readable summary       |
| `retriable`              |      Yes | Retry classification         |
| `details`                |      Yes | Empty object permitted       |
| `evidence_node_ids`      |       No | Related graph records        |
| `state_boundary_id`      |       No | Affected external boundary   |
| `current_graph_revision` |       No | Current revision             |
| `retry_after`            |       No | Time or duration             |
| `documentation_ref`      |       No | Stable reference             |

Required codes include:

* `invalid_message`;
* `unsupported_version`;
* `unsupported_operation`;
* `schema_violation`;
* `authentication_required`;
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
* `adapter_unavailable`;
* `adapter_error`;
* `external_rejection`;
* `external_outcome_unknown`;
* `conflict_open`;
* `invalid_cursor`;
* `rate_limited`;
* `internal_error`.

---

## 26. Retry Behavior

A client MAY retry only when:

* the response marks the error retriable;
* the same idempotency key is retained;
* request content is unchanged;
* any required delay is observed.

A client MUST NOT automatically retry:

* schema violations;
* authorization failures;
* external rejection;
* lineage cycles;
* ambiguous authority;
* idempotency conflicts;
* stale graph revisions without refreshing;
* non-idempotent actions with unknown outcomes.

An unknown external outcome MUST be reconciled before an unsafe retry.

---

## 27. Authentication and Authorization

GLCP assumes the transport authenticates the principal or provides a verifiable authentication context.

The runtime MUST authorize each operation by:

* workspace;
* state boundary;
* action;
* graph read scope;
* payload classification;
* actor delegation;
* conflict-decision authority.

Protocol messages MUST NOT carry plaintext reusable credentials unless a transport profile explicitly protects and permits them.

External-system credentials SHOULD remain in adapter or secret-store configuration and SHOULD NOT be persisted in graph payloads.

---

## 28. Payload Security

A payload reference MAY be:

* inline;
* content-addressed;
* external;
* absent.

The runtime MUST validate payload media type and size.

Payload content MUST NOT be:

* executed;
* imported as adapter code;
* interpreted as authorization policy;
* trusted as a graph record without validation.

A redacted payload MUST identify the redaction-policy version.

---

## 29. Neutral Example: Observing an Artifact

A client asks an adapter to observe a document managed by an external content service.

The request identifies:

* the adapter;
* content-service state boundary;
* document external identifier;
* requested consistency;
* workflow correlation identifier.

The adapter reports:

* external revision `17`;
* content hash;
* observation time;
* snapshot consistency;
* a bounded title and size summary.

The runtime creates an artifact node attributed to that external authority. The node records what was observed; it does not make Guerilla the content owner.

---

## 30. Neutral Example: External Action and Evaluation

An operation intends to generate an implementation artifact from a requirement revision.

The runtime:

1. commits the operation and action-request event;
2. invokes a configured build adapter with an idempotency key;
3. records the external result;
4. observes the produced artifact revision;
5. creates a `produces` edge from the operation to the artifact;
6. requests a deterministic evaluation;
7. records either a passing evaluation or a `failed_evaluation` conflict.

External action outcome and evaluation outcome remain separate.

---

## 31. Neutral Example: Reified Conflict

Two artifact revisions appear to claim the same output scope.

The runtime does not add a bidirectional `conflicts_with` edge. It creates an `overlapping_scope` conflict node. Each artifact provides evidence to the conflict. A later decision resolves the conflict and is connected through `resolved_by`.

A conflict projection may display the two artifacts as mutually incompatible without violating the authoritative DAG.

---

## 32. Neutral Example: Interrupted Action

An action-request event is committed, and the external system receives the request. The runtime stops before recording the result.

After restart:

1. the operation appears as `outcome_unknown`;
2. the runtime calls `adapter.reconcile` using the original idempotency and correlation identifiers;
3. the adapter confirms that the external action completed;
4. the runtime appends a reconciliation event and resulting artifact observation;
5. the original intent remains unchanged.

---

## 33. Conformance Matrix

A conforming implementation MUST pass tests covering:

### Protocol negotiation

* common version selected;
* incompatible major version rejected;
* unknown critical field rejected;
* additive optional field tolerated when permitted.

### Envelope

* required identifiers validated;
* invalid timestamps rejected;
* causation distinguished from correlation;
* unauthorized actor claims ignored.

### Graph operations

* atomic append;
* duplicate identifiers rejected;
* stale graph guard rejected;
* immutable correction through supersession;
* cycle rejection;
* missing endpoints rejected.

### Adapter operations

* descriptor completeness;
* state-boundary enforcement;
* external revision preservation;
* rejection preservation;
* unknown-outcome reconciliation;
* unsupported capability reporting.

### Idempotency

* same key and same request returns prior result;
* same key and different request fails;
* unsafe retry after unknown outcome rejected.

### Queries and pagination

* exact revision reads;
* stable opaque cursor;
* query-altering cursor reuse rejected;
* traversal limits reported.

### Views, manifests, and snapshots

* graph revision cited;
* transformation version cited;
* source references present;
* deterministic regeneration;
* stale external observations reported;
* snapshot does not claim external immutability.

### Security

* unauthorized state-boundary access rejected;
* payload never executed;
* secrets redacted;
* adapter capability escalation rejected.

---

## 34. Compatibility Rules

A client using only operations and fields defined in a negotiated minor version SHOULD remain compatible with later patch versions.

A server introducing a new enum value MUST either:

* negotiate a version that permits it;
* place it in a namespaced extension;
* provide a safe fallback.

A protocol extension MUST NOT:

* redefine a core relationship direction;
* permit mutation of committed records;
* bypass graph cycle validation;
* transfer external state authority implicitly;
* mark a derived view as authoritative lineage.

---

## 35. Deferred Protocol Capabilities

The following are deferred beyond the local single-writer profile:

* remote writer consensus;
* graph merge;
* cross-workspace identity federation;
* multi-agent reservations;
* distributed leases;
* streaming lineage subscriptions;
* selective cryptographic disclosure;
* signed actor attestations;
* automatic semantic conflict resolution;
* portable federated snapshots.

---

## 36. Protocol Stability Conditions

GLCP 0.2 SHOULD NOT be declared stable until:

1. schemas are published for all core messages and records;
2. canonical serialization is finalized;
3. reference client and server implementations interoperate;
4. the graph and adapter conformance suites pass;
5. error codes and retry semantics are validated;
6. snapshot and manifest regeneration is demonstrated;
7. action interruption and reconciliation are tested;
8. security review covers adapter trust, payload handling, and authorization.

