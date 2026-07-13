# Glossary

**Status:** FROZEN -- Phase 2 complete
**Owner phase:** Phase 2 (Architecture Decisions)
**Controlling source documents:** `AGENTS.md`, `GUERILLA_CONCEPT_PAPER.md`, `GUERILLA_SNAPSHOT.md`, `ARCHITECTURE_DECISIONS.md`
**Regeneration trigger:** Any terminology change or architecture decision change

---

## Purpose

This glossary is the canonical terminology reference for Guerilla documents, schemas, registries, code, tests, and completion reports.

---

## Core Terms

| Term | Definition |
|---|---|
| Node | Immutable record representing a lineage-relevant object or occurrence. A correction or later version is represented by another node. |
| Edge | Typed, directed relationship from an earlier or prerequisite node to a later or dependent node. Direct authoritative edges must preserve the DAG invariant. |
| Lineage | Recorded ancestry of an artifact, event, decision, result, or operation, including actors, operations, evidence, revisions, and causal relationships. |
| Continuity | Ability to reconstruct the current work position from committed lineage, including graph heads, open goals, latest known revisions, conflicts, refresh needs, and eligible next operations. |
| Authoritative graph | The one logical source of Guerilla lineage truth: committed immutable nodes, edges, transactions, revisions, and commits. |
| Projection / View | Derived representation computed from the authoritative graph. It may be persisted, but it remains source-cited and non-authoritative. |
| Adapter | Controlled integration component translating between an external system and Guerilla. It declares state boundaries, capabilities, and consistency limits. |
| External system | Any repository, service, database, tool, filesystem, event stream, workflow, or human process integrated with Guerilla. |
| System of record | External authority for a defined state boundary. It owns application-specific state, validation, mutation, and reconstruction semantics. |
| Artifact | Identifiable output, input, or external object relevant to lineage, such as a file revision, report, requirement, build, test result, dataset, deployment, or review. |
| Actor | Human, model, tool, service, automation, or system responsible for an action, observation, evaluation, or decision. Actor attribution does not grant authority. |
| Revision | Immutable version of a logical entity. Guerilla distinguishes graph revisions, artifact revisions, and external revisions. |
| Event | Occurrence relevant to continuity, such as an observation, request, action result, external notification, reconciliation result, or status transition. |
| Snapshot | Immutable record that a selected graph boundary was captured at a graph revision. Its materialized summary payload is derived. |
| Manifest | Derived inventory of selected artifacts, revisions, statuses, or references generated from a declared graph revision and policy. |
| Status | Typed label describing a node or projection item. It is meaningful only with basis, source records, policy version, and generation time. |
| Conflict | Evidence-backed incompatibility, ambiguity, stale assumption, policy violation, or unresolved condition affecting continuity. |
| Provenance | Source identity, actor, authority, time, operation, revision, and relationships explaining how a record entered the graph. |
| Relationship type | Registered semantic kind and permitted direction of an edge or reified relationship assertion. |
| State boundary | Declared scope within which one system of record owns application state, including subject namespace, permitted actions, revision semantics, and conflict behavior. |

---

## Revision Types

| Revision type | Owner | Meaning |
|---|---|---|
| Graph revision | Guerilla | Monotonic committed transaction boundary in the authoritative graph. |
| Artifact revision | Guerilla lineage, external content may be elsewhere | Immutable node describing one version of a logical artifact. |
| External revision | External system | Version, hash, sequence, timestamp, or opaque token reported by a system of record. |

External revision tokens are preserved exactly as reported. They may be normalized only in derived indexes.

---

## Core Node Types

| Type | Meaning |
|---|---|
| Goal | Desired outcome or work objective. |
| Artifact | Lineage-relevant input, output, or external object revision. |
| Operation | Planned, running, completed, blocked, failed, or reconciled unit of work. |
| Event | Observation, request, action result, external notification, or reconciliation occurrence. |
| Evaluation | Assessment of a subject node or artifact against criteria. |
| Decision | Explicit choice that resolves, defers, or supersedes alternatives. |
| Conflict | Evidence-backed incompatibility or unresolved condition. |
| Snapshot | Captured graph boundary and resume source at a graph revision. |

---

## Core Relationship Types

| Type | Direction |
|---|---|
| `depends_on` | dependent node to prerequisite node |
| `produces` | producer operation or event to produced artifact/result |
| `derives` | derived artifact/view to source node |
| `causes` | cause event/operation to caused event/operation |
| `evidences` | evidence node to evidenced claim/conflict/evaluation |
| `evaluated_by` | subject node to evaluation node |
| `superseded_by` | earlier revision to later revision |
| `resolved_by` | conflict or open item to resolving decision/event |
| `captured_by` | source node or boundary to snapshot node |

Symmetric, cyclic, or non-causal domain relationships are represented through reified nodes and may be rendered differently in derived views.

---

## Locked Distinctions

| Distinction | Rule |
|---|---|
| Lineage authority vs application-state authority | Guerilla owns lineage; external systems retain application-state authority. |
| Graph revision vs external revision | Graph revisions are Guerilla commit boundaries; external revisions are opaque system-of-record tokens. |
| Authoritative graph vs derived view | Projections, manifests, snapshots, indexes, caches, and dashboards are non-authoritative. |
| Actor attribution vs authorization | Actor fields record responsibility; effective authority comes from authenticated principal and policy. |
| Transport success vs external outcome | A successful transport call does not prove external acceptance or semantic correctness. |
| Stored payload vs executable behavior | Payload content is untrusted data and must not be executed, imported, or treated as policy. |

---

## Deprecated or Ambiguous Terms

Avoid using these as authoritative terms:

- "current state" without naming the system of record and revision basis;
- "snapshot" to mean a replacement graph state;
- "manifest" to mean authoritative inventory;
- "adapter authority" without a declared state boundary;
- "status" without source records and policy version.
