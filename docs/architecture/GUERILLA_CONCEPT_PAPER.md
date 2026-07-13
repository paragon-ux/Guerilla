# GUERILLA_CONCEPT_PAPER.md

# Guerilla: An Authoritative Causal-Lineage and Continuity Layer

**Document purpose:** Define the problem, architectural rationale, boundaries, principles, use cases, and limitations of Guerilla as a standalone system.

**Status:** Revised architecture draft

**Version:** 0.2.0-draft

**Intended audience:** Systems architects, researchers, agent-platform designers, software engineers, technical reviewers, and organizations evaluating lineage-oriented orchestration.

**Revision provenance:** This document supersedes the conceptual framing of the supplied v0.1.0 draft.

---

## Abstract

Long-running technical work increasingly spans repositories, services, document systems, build tools, databases, human review processes, and autonomous or semi-autonomous agents. Each participating system may preserve its own state correctly, yet no single system necessarily records why work occurred, which observations informed it, which artifacts were produced, which evaluations followed, or which unresolved conflicts affect later work.

Guerilla addresses this gap through one logically authoritative directed acyclic graph of lineage and continuity records. The graph represents immutable artifact revisions, events, operations, evaluations, decisions, conflicts, snapshots, and their typed causal relationships. It provides a reconstructable account of how work progressed across tool and organizational boundaries.

Guerilla is not a replacement for application databases, filesystems, source-control systems, event stores, or domain-specific state models. An integrated system remains the system of record for the state it owns. Guerilla stores identifiers, provenance, observations, transitions, relationships, and graph-level continuity. Adapters translate between external state models and the Guerilla graph without transferring general ownership of the external state.

Dashboards, requirement-traceability matrices, manifests, snapshots, diffs, dependency maps, progress summaries, and resume reports are projections over the same authoritative graph. They may be persisted for performance or audit, but they remain reproducible, source-cited representations rather than competing lineage stores.

The resulting architecture separates two concerns that are often conflated: application-state continuity remains specific to each external system, while cross-system lineage continuity is represented consistently in Guerilla.

---

## 1. Problem

A technical workflow may include the following activities:

1. receiving a goal;
2. reading requirements or source records;
3. observing the current revision of one or more artifacts;
4. executing an operation through an external tool;
5. receiving an acceptance, rejection, or uncertain result;
6. evaluating the materialized result;
7. identifying conflicts or missing evidence;
8. selecting a corrective branch;
9. producing additional artifacts;
10. pausing and resuming the work later.

Individual systems often record fragments of this process. A repository records commits. A service records requests. A test runner records test outcomes. A document system records revisions. A human review system records approvals. An agent transcript records conversation.

These records do not automatically form a coherent causal history. Common gaps include:

* an action is logged without the observation that justified it;
* an artifact exists without a recorded producer;
* a test result is separated from the revision it evaluated;
* a later operation depends on an undocumented decision;
* two systems assign conflicting status to the same work;
* a summary hides abandoned or rejected branches;
* a resumed agent cannot distinguish current observations from stale ones;
* several tools maintain overlapping but inconsistent lineage models.

A linear transcript is insufficient because sequence is not equivalent to causation. Work can branch, converge, be superseded, fail after partial completion, or depend on several earlier results. Continuity therefore requires explicit identities, typed relationships, provenance, revisions, and graph invariants.

---

## 2. Core Definitions

### 2.1 Node

A **node** is an immutable record representing a lineage-relevant object or occurrence. Examples include an artifact revision, operation, event, decision, evaluation, conflict, goal, or snapshot.

A node does not change after commitment. A correction or later version is represented by another node.

### 2.2 Edge

An **edge** is a typed, directed relationship from an earlier or prerequisite node to a later or dependent node. Examples include `depends_on`, `produces`, `derives`, `evaluated_by`, `superseded_by`, and `resolved_by`.

### 2.3 Lineage

**Lineage** is the recorded ancestry of an artifact, event, decision, or result. It explains what preceded the object, which actors and operations participated, and which evidence supports the relationship.

### 2.4 Continuity

**Continuity** is the ability to reconstruct the current work position from committed lineage. It includes current graph heads, open goals, latest known artifact revisions, unresolved conflicts, required refreshes, and eligible next operations.

### 2.5 Authoritative graph

The **authoritative graph** is the one logical source of Guerilla lineage truth. It consists of committed immutable nodes and acyclic typed edges.

The graph may be partitioned, indexed, cached, replicated, archived, filtered, or materialized, but those physical representations do not become independent lineage authorities.

### 2.6 Projection or view

A **projection**, also called a **view**, is a derived representation computed from the authoritative graph. A projection may filter, aggregate, sort, compress, or transform graph records for a defined consumer.

### 2.7 Adapter

An **adapter** is a controlled integration component that translates between an external system and Guerilla’s graph and protocol model. It declares the state boundary it observes, the actions it may invoke, and the consistency guarantees it can provide.

### 2.8 External system and system of record

An **external system** is any repository, service, database, tool, filesystem, event stream, workflow, or human process integrated with Guerilla.

A **system of record** is the external authority for a defined state boundary. It owns the application-specific rules for reading, validating, mutating, and reconstructing that state.

### 2.9 Artifact

An **artifact** is an identifiable output, input, or external object relevant to lineage. Examples include a requirement, file revision, report, build, model output, test result, dataset, deployment, or review record.

### 2.10 Actor

An **actor** is the human, agent, tool, service, or automation responsible for an action, observation, evaluation, or decision.

### 2.11 Revision

A **revision** is an immutable version of a logical entity.

Guerilla distinguishes three forms:

* **Graph revision:** a committed transaction boundary in the authoritative graph.
* **Artifact revision:** a versioned node describing a logical artifact.
* **External revision:** a version, hash, sequence, or token reported by a system of record.

### 2.12 Event

An **event** is an occurrence relevant to continuity, such as an observation, request, action result, external notification, or reconciliation outcome.

### 2.13 Snapshot

A **snapshot** is an immutable record of a selected graph boundary at a specific graph revision. It identifies graph heads, source nodes, query scope, transformation version, and optional materialized payload hash.

### 2.14 Manifest

A **manifest** is a derived inventory of selected artifacts, revisions, relationships, statuses, or external references. It is generated from the graph and can be regenerated from its declared source revision and transformation rules.

### 2.15 Status

A **status** is a typed label describing the condition of a node or projection item. Status is meaningful only with its basis, source records, policy version, and generation time.

### 2.16 Conflict

A **conflict** is an evidence-backed incompatibility, ambiguity, stale assumption, policy violation, or unresolved condition that affects continuity.

### 2.17 Provenance

**Provenance** is the combination of source identity, actor, authority, time, operation, revision, and relationships that explains how a record entered the graph.

### 2.18 Relationship type

A **relationship type** defines the semantics and permitted direction of an edge or reified relationship assertion.

### 2.19 State boundary

A **state boundary** is a declared scope within which one system of record owns application state. It identifies the external system, subject namespace, readable state, permitted actions, revision semantics, and ownership restrictions.

---

## 3. Architectural Thesis

Guerilla is based on four propositions.

### 3.1 Application-state continuity is architecture-specific

A transactional service, a filesystem workflow, an append-only event log, a source-control repository, and a manual review process provide different continuity and consistency guarantees.

A single replacement state model would either omit important semantics or impose unnecessary infrastructure. Guerilla therefore does not normalize all application state into one operational schema.

### 3.2 Cross-system lineage is a distinct concern

Although application-state mechanisms differ, cross-system work repeatedly produces the same classes of lineage:

* an operation depended on an observation;
* an actor initiated an action;
* an action produced a result;
* a result created or revised an artifact;
* an evaluator assessed that result;
* a conflict blocked a continuation;
* a decision resolved or deferred the conflict.

These relationships can be represented consistently without duplicating the external systems’ complete state.

### 3.3 One lineage authority reduces contradiction

When every tool owns a separate authoritative lineage graph, the same dependency or transition can be represented differently in several places. Reconciliation then requires additional translation rules and can still leave ambiguous ownership.

Guerilla instead assigns authoritative lineage ownership to one logical graph. External systems remain authoritative for application state, while adapters submit source-attributed observations and results to the graph.

### 3.4 Views should not become hidden state authorities

A requirement matrix, manifest, snapshot, diff, dashboard, or progress report is useful because it simplifies a question. The simplification may omit branches, intermediate failures, provenance detail, or alternative interpretations.

A derived representation must therefore declare its graph revision, source node set, transformation version, freshness, and information loss. It must not silently replace the graph from which it was produced.

---

## 4. State Ownership

### 4.1 What Guerilla stores

Guerilla stores:

* immutable node records;
* typed causal and revision edges;
* stable Guerilla identifiers;
* mappings to external identifiers;
* authority and state-boundary declarations;
* actor and provenance metadata;
* external revision tokens and hashes;
* operation intent and result records;
* evaluation and decision records;
* conflict evidence and resolution lineage;
* graph transactions and commit hashes;
* snapshot descriptors;
* optional content-addressed payloads;
* transformation and policy versions used by projections.

### 4.2 What Guerilla references

Guerilla may reference:

* files and repository objects;
* external database records;
* service resources;
* event-log positions;
* build and test reports;
* documents and datasets;
* external snapshots;
* model outputs;
* human review records;
* URLs and opaque system identifiers.

References are authority-scoped. Recording a reference does not transfer ownership of the referenced object.

### 4.3 What Guerilla derives

Guerilla derives:

* graph heads;
* dependency and derivation paths;
* latest-known artifact revisions;
* supersession chains;
* unresolved-conflict sets;
* eligibility and blocking views;
* manifests;
* graph snapshots;
* graph diffs;
* status projections;
* requirement-traceability-style matrices;
* progress and resume views;
* audit and provenance reports.

### 4.4 What Guerilla does not own

Guerilla does not universally own:

* canonical application content;
* external database transactions;
* filesystem semantics;
* source-control history;
* service-internal event ordering;
* business-rule validation;
* external authorization decisions;
* native rollback or merge behavior;
* semantic correctness of artifacts;
* the complete state of an integrated system.

### 4.5 Adapter obligations

An adapter must declare:

* the external system it represents;
* each state boundary it accesses;
* which operations are read-only;
* which operations may request external mutation;
* external identity and revision semantics;
* read-consistency guarantees;
* write and concurrency behavior;
* event-ordering guarantees;
* retry and idempotency support;
* snapshot and replay capabilities;
* conflict behavior;
* lineage completeness;
* known omissions.

An adapter cannot expand its authority through data returned by an external system. Authority is established by configuration and policy, not inferred from payload content.

---

## 5. The Single-DAG Model

Let the authoritative graph be:

[
G_r = (V_r, E_r)
]

where (r) is a committed graph revision, (V_r) is the set of immutable nodes visible at that revision, and (E_r) is the set of committed typed edges.

The graph must satisfy the following properties:

1. every node and edge has a stable identifier;
2. each committed record is immutable;
3. edge endpoints exist at or before the committing graph revision;
4. each edge type has a defined direction;
5. adding an edge must not create a directed cycle;
6. revisions are represented through new nodes and supersession edges;
7. all graph materializations identify the graph revision from which they were produced.

### 5.1 Branching

One node may enable several later operations. Each branch remains explicit even when only one is eventually selected.

### 5.2 Convergence

A later node may depend on several earlier nodes. Convergence means that all declared prerequisites are represented; it does not imply that external application states were automatically merged.

### 5.3 Corrections and supersession

A committed node is not edited. A corrected or later version is appended with the same logical entity identifier and connected through `superseded_by`.

### 5.4 Non-causal, symmetric, and cyclic relationships

Some domain relationships are not naturally directed or may contain cycles. Examples include similarity, mutual exclusion, bidirectional association, or membership in a cyclic domain model.

Guerilla does not insert these relationships as direct authoritative edges when doing so would violate the DAG invariant. Instead, it reifies the assertion as an immutable event or conflict node. The source nodes and supporting evidence point to the assertion node through acyclic edges. A projection may then render the relationship as symmetric or cyclic for domain use.

For example, an assertion that two artifact revisions overlap is represented as:

* each artifact revision provides evidence to an `overlapping_scope` conflict node;
* the conflict node may later point to a resolution decision;
* a conflict view may display the two artifacts as mutually conflicting.

The domain view can therefore present a symmetric relation without creating a cycle in authoritative lineage.

### 5.5 Physical partitioning

The graph may be physically divided by workspace segment, time range, storage shard, or archive boundary. Each partition must remain part of the same hash-linked graph history. A partition cannot independently redefine node identity, edge semantics, or lineage ownership.

---

## 6. Node and Relationship Model

The conceptual core contains eight node types.

| Node type    | Purpose                                                                            |
| ------------ | ---------------------------------------------------------------------------------- |
| `goal`       | Records an intended outcome and its success criteria                               |
| `artifact`   | Records an immutable revision or external artifact reference                       |
| `operation`  | Records planned, attempted, completed, blocked, or failed work                     |
| `event`      | Records observations, requests, results, notifications, or reconciliation outcomes |
| `evaluation` | Records deterministic, external, model, or human assessment                        |
| `decision`   | Records an explicit choice, acceptance, rejection, deferment, or resolution        |
| `conflict`   | Records an evidence-backed unresolved condition                                    |
| `snapshot`   | Records a graph boundary and source-cited continuation state                       |

Core lineage relationship types include:

| Relationship    | Direction                                                      |
| --------------- | -------------------------------------------------------------- |
| `depends_on`    | prerequisite to dependent                                      |
| `produces`      | producer to produced node                                      |
| `derives`       | source to derived node                                         |
| `causes`        | causal predecessor to effect                                   |
| `evidences`     | evidence to supported claim, evaluation, conflict, or decision |
| `evaluated_by`  | evaluated subject to evaluation                                |
| `superseded_by` | older revision or plan to newer revision or plan               |
| `resolved_by`   | conflict to resolving decision or operation                    |
| `captured_by`   | included node to snapshot                                      |

Implementations may add namespaced node subtypes and relationship types, but extensions must preserve direction, authority, immutability, and acyclicity.

---

## 7. Continuity Lifecycle

A typical continuity lifecycle is:

1. **Goal registration:** Record an intended outcome and scope.
2. **Observation:** Obtain current external revisions or state summaries through declared adapters.
3. **Planning:** Record a bounded operation and its prerequisites.
4. **Intent commitment:** Commit the intended external action before invocation.
5. **Action invocation:** Ask the system of record to perform the action.
6. **Result recording:** Preserve accepted, rejected, failed, partial, or unknown outcomes.
7. **Post-action observation:** Read the resulting external revision when supported.
8. **Evaluation:** Apply a declared validator or reviewer.
9. **Conflict handling:** Record evidence-backed blocking or contradictory conditions.
10. **Decision:** Select, defer, reject, or resolve a continuation.
11. **Snapshot:** Capture graph heads, open goals, latest observations, conflicts, and refresh requirements.
12. **Resume:** Validate the graph, refresh stale observations, and continue from eligible heads.

This sequence is a default, not an assumption that every integration provides identical guarantees. An adapter may report that before-state observation, post-action observation, replay, or strong consistency is unavailable. Guerilla records the resulting assurance level explicitly.

---

## 8. Adapter Architecture

Adapters isolate external-system semantics from the graph core.

A conforming adapter exposes five conceptual operations:

* **Describe:** Declare capabilities, schemas, authority, state boundaries, and guarantees.
* **Observe:** Read external state and return an authority-scoped observation.
* **Act:** Invoke a permitted external operation through the system’s supported interface.
* **Evaluate:** Request or report a declared validation result.
* **Reconcile:** Determine the outcome of a previously attempted action whose result is incomplete or unknown.

Not every adapter must support mutation, evaluation, snapshots, replay, or event subscription. Unsupported capabilities must be explicit.

Adapters may integrate with:

* transactional databases;
* APIs and event-driven services;
* command-line tools;
* filesystems;
* append-only logs;
* source-control histories;
* batch processors;
* manual review queues;
* agentic workflows;
* mixed architectures.

The common contract standardizes identity, provenance, operations, and guarantees. It does not standardize the external system’s business rules or persistence model.

---

## 9. Derived Views

Every view must identify:

* its purpose;
* intended consumer;
* source graph revision;
* source node set or reproducible query;
* transformation and policy version;
* generation time;
* freshness;
* known information loss;
* persistence mode;
* authoritative status.

### 9.1 Lineage and dependency view

**Purpose:** Show causal ancestry, prerequisites, producers, and downstream consumers.

**Consumer:** Engineers, reviewers, auditors, planners, and agents.

**Sources:** Nodes and lineage edges.

**Transformation:** Graph traversal with declared direction, depth, and filters.

**Freshness:** Bound to a graph revision.

**Information loss:** May omit nodes outside the query scope.

**Persistence:** Generated on demand or cached.

**Authority:** Non-authoritative representation of authoritative graph records.

### 9.2 Manifest

**Purpose:** Inventory artifacts, latest-known revisions, locations, owners, and selected relationships.

**Consumer:** Build tools, agents, reviewers, release processes, and external integrations.

**Sources:** Artifact nodes, supersession paths, authority metadata, and selected evaluations.

**Transformation:** Filter and select latest eligible revisions under a declared policy.

**Freshness:** Bound to a graph revision and external-observation freshness.

**Information loss:** Usually omits full event and decision history.

**Persistence:** May be materialized and content-addressed.

**Authority:** Derived and reproducible.

### 9.3 Snapshot

**Purpose:** Establish a continuation or audit boundary.

**Consumer:** Resume engines, reviewers, release processes, and archival systems.

**Sources:** Graph heads, open goals, conflicts, latest observations, adapter versions, and query scope.

**Transformation:** Deterministic selection at a specified graph revision.

**Freshness:** Immutable as a graph record, but external observations cited by it may later become stale.

**Information loss:** A summary payload may omit non-head history, while source identifiers preserve recoverability.

**Persistence:** Snapshot descriptor is authoritative lineage; materialized summary is derived and hash-pinned.

**Authority:** The fact that the snapshot was created is authoritative. Its summary does not replace source nodes.

### 9.4 Diff view

**Purpose:** Compare two graph revisions, snapshots, artifact revisions, or manifests.

**Consumer:** Reviewers, release processes, agents, and audit tools.

**Sources:** Two declared boundaries.

**Transformation:** Set and relationship comparison under a versioned policy.

**Freshness:** Determined by the selected boundaries.

**Information loss:** May summarize unchanged ancestry.

**Persistence:** Usually generated; may be captured as an artifact.

**Authority:** Derived.

### 9.5 Requirement-traceability-style status view

**Purpose:** Show relationships among requirement artifacts, implementation artifacts, evaluations, evidence, and blocking conflicts.

**Consumer:** Engineers, assurance teams, program managers, and reviewers.

**Sources:** Artifact revisions, derivation and evidence edges, evaluations, decisions, and conflicts.

**Transformation:** Domain-specific mapping and status policy.

**Freshness:** Bound to a graph revision and latest external observations.

**Information loss:** Compresses detailed branch and event history.

**Persistence:** Generated or cached.

**Authority:** Derived. It is one supported view, not Guerilla’s primary data model.

### 9.6 Progress and resume view

**Purpose:** Identify completed work, graph heads, blocked branches, stale observations, and eligible next operations.

**Consumer:** Humans, agents, and orchestration services.

**Sources:** Goals, operations, events, evaluations, conflicts, decisions, and snapshots.

**Transformation:** Topological and policy-based classification.

**Freshness:** Bound to a graph revision; external observations may require refresh.

**Information loss:** May omit non-blocking historical detail.

**Persistence:** Generated or included in a snapshot payload.

**Authority:** Derived.

---

## 10. Primary Use Cases

### 10.1 Long-running agentic workflows

An agent can resume work from explicit graph heads and freshness requirements rather than relying on a compressed conversation transcript.

### 10.2 Cross-tool provenance

A reviewer can trace an artifact revision through the observation, operation, actor, external result, evaluation, and decision that produced it.

### 10.3 Requirement and evidence continuity

A traceability projection can connect requirement revisions, implementation artifacts, test evidence, review decisions, and unresolved conflicts without turning the matrix into a separate source of truth.

### 10.4 Multi-stage production pipelines

Batch jobs, services, human approvals, and deployment processes can share one lineage model while retaining their native execution and persistence mechanisms.

### 10.5 Conflict visibility

Stale observations, incompatible revisions, external rejections, failed evaluations, incomplete lineage, and ambiguous authority can be preserved as explicit nodes.

### 10.6 Audit and incident reconstruction

A graph revision can show which inputs, actors, decisions, and operations preceded a result or failure.

### 10.7 Reproducible manifests and snapshots

Consumers can regenerate a manifest or snapshot from its graph revision, source query, and transformation version.

---

## 11. Architectural Principles

1. **One logical lineage authority:** No projection, adapter cache, index, or external tool becomes a second Guerilla lineage source.
2. **External state remains external:** Systems of record retain application-state ownership.
3. **Immutable history:** Corrections and revisions are appended rather than overwritten.
4. **Acyclic authoritative relationships:** Direct edges preserve causal and revision ordering.
5. **Reified non-DAG relationships:** Symmetric or cyclic domain associations are represented through assertion or conflict nodes.
6. **Explicit provenance:** Actor, authority, source, time, revision, and causation are recorded when known.
7. **Observation before assumption:** Current external state is observed when available; unknown or stale state remains explicit.
8. **Native validation remains decisive:** Transport success does not imply external acceptance or semantic correctness.
9. **Views are source-cited:** Every materialized representation identifies its graph basis.
10. **Capabilities are negotiated:** Integrations do not claim guarantees they cannot provide.
11. **Failure is lineage:** Rejections, partial results, and uncertain outcomes remain visible.
12. **No hidden semantic inference:** Derived status is associated with a declared policy and evidence.

---

## 12. Benefits and Tradeoffs

### 12.1 Benefits

**Continuity beyond conversation state.** Work can be resumed from explicit graph records rather than informal summaries.

**Cross-system provenance.** Inputs, actions, revisions, evaluations, conflicts, and decisions can be traversed as one causal history.

**Boundary preservation.** External systems can retain architecture-specific databases, logs, files, and concurrency controls.

**Reduced lineage duplication.** Relationship ownership and graph invariants are defined once.

**Branch preservation.** Rejected, abandoned, superseded, and convergent paths remain reviewable.

**Regenerable views.** Manifests, snapshots, diffs, and status reports can be reproduced from declared sources.

**Explicit uncertainty.** Unknown outcomes and stale observations are represented rather than silently interpreted.

### 12.2 Tradeoffs

**Additional integration work.** Useful lineage depends on adapters, identity mapping, and authority declarations.

**Storage growth.** Append-only records, payloads, and provenance increase storage and indexing requirements.

**Operational complexity.** Action intent, external execution, graph commitment, and reconciliation cannot generally be made one atomic transaction.

**Policy dependence.** Status and conflict projections require versioned rules and may vary across organizations.

**Partial visibility.** Guerilla cannot record facts that external systems do not expose and actors do not declare.

**Graph discipline.** Strict acyclicity requires revisions and non-causal relationships to be represented carefully.

---

## 13. Risks and Limitations

### 13.1 Adapter trust

An incorrect or compromised adapter can misattribute observations, omit relevant state, or invoke an unintended action. Schema validation cannot prove the adapter’s semantic correctness.

### 13.2 Incomplete lineage

External actions may occur outside Guerilla. Reconciliation can detect some divergence, but it cannot guarantee complete lineage without cooperation from the systems and actors involved.

### 13.3 Stale observations

An observation is not a lock. Work based on a previously current revision may become invalid before the next action.

### 13.4 Identity ambiguity

External systems may rename, duplicate, delete, or recycle identifiers. Adapters must declare identity stability and mapping behavior.

### 13.5 Semantic uncertainty

The graph can preserve evaluations and decisions, but it cannot independently prove that a requirement is correct, a design is appropriate, or a test suite is sufficient.

### 13.6 Projection drift

A persisted view may become stale or may use an obsolete transformation policy. Every view therefore requires a source revision and transformation version.

### 13.7 Scale

Large graphs require indexing, archive segments, incremental projection, and bounded traversal. These mechanisms must remain rebuildable from authoritative records.

### 13.8 Privacy and disclosure

Lineage may reveal sensitive inputs, actors, locations, or operational details. Payload capture, redaction, access control, and selective disclosure require explicit policy.

---

## 14. Non-Goals

Guerilla does not attempt to:

* replace every application database or event store;
* define universal CRUD semantics for external systems;
* provide automatic semantic merge across unrelated state models;
* guarantee the correctness of external tools or adapters;
* infer causation solely from temporal proximity;
* treat all references as causal edges;
* make derived dashboards authoritative;
* reproduce private model reasoning;
* execute arbitrary payload content;
* provide distributed consensus in the initial local-first scope;
* guarantee complete lineage when relevant actions occur outside observed boundaries;
* collapse native action outcome, evaluation outcome, and goal completion into one status.

---

## 15. Evaluation Questions

The architecture should be evaluated against measurable questions.

### 15.1 Resume accuracy

Can a new actor resume a paused workflow and correctly identify graph heads, stale observations, unresolved conflicts, and eligible operations?

### 15.2 Lineage completeness

What proportion of material artifact revisions can be traced to a producer, actor, source observation, and external result?

### 15.3 Boundary preservation

Do adapters invoke only declared external interfaces and avoid creating replacement application-state stores?

### 15.4 Projection reproducibility

Can each manifest, snapshot, diff, and status view be regenerated from its graph revision and transformation version?

### 15.5 Conflict detection

How reliably does the system identify stale revisions, external rejections, failed evaluations, ambiguous authority, and incomplete ancestry?

### 15.6 Storage and query cost

How do append volume, payload retention, index size, projection latency, and resume-context size evolve over long workflows?

### 15.7 Recovery behavior

After interruption between action intent and result recording, can reconciliation determine whether the external operation succeeded, failed, or remains unknown?

---

## 16. Conclusion

Guerilla establishes an explicit architectural layer for causal lineage and workflow continuity. Its authoritative state is one immutable, revisioned DAG of artifacts, operations, events, evaluations, decisions, conflicts, snapshots, and typed relationships.

The system does not require integrated tools to share one database, execution model, concurrency mechanism, or persistence methodology. Each external system retains ownership of its application state. Guerilla owns the graph-level account of how observations, actions, revisions, and decisions relate across those boundaries.

This separation permits heterogeneous systems to participate in one reconstructable history while preventing manifests, matrices, dashboards, and summaries from becoming competing sources of lineage truth.

---

## References

Bernstein, P. A., and Goodman, N. (1981). Concurrency control in distributed database systems. *ACM Computing Surveys*, 13(2), 185–221.

Chacon, S., and Straub, B. (2014). *Pro Git*. Apress.

Fowler, M. (2005). “Event Sourcing.” martinfowler.com.

Lamport, L. (1978). “Time, Clocks, and the Ordering of Events in a Distributed System.” *Communications of the ACM*, 21(7), 558–565.

Moreau, L., and Missier, P., eds. (2013). *PROV-DM: The PROV Data Model*. W3C Recommendation.
