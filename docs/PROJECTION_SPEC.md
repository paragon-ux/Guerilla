# Projection Specification

**Status:** Gate C current -- Phase 14 snapshots and resume implemented
**Owner phase:** Phase 13 (Projections/Manifest/Diff), Phase 14 (Snapshot/Resume)
**Controlling source documents:** `GUERILLA_CONCEPT_PAPER.md` Section 9, `GUERILLA_IMPLEMENTATION_SPEC.md` Sections 4.12-4.13 and 27, `GUERILLA_PROTOCOL_SPEC.md` Sections 18-20
**Regeneration trigger:** Any projection policy change, Phase 13 completion, or Phase 14 completion

---

## Purpose

This document defines the Phase 13 projection contract. Projections are
derived, non-authoritative views over the authoritative graph. They may be
persisted for convenience, but they are disposable and must regenerate from
graph replay or a rebuilt non-authoritative index without changing lineage
truth.

Phase 13 implements lineage, dependency, conflict, manifest, diff, progress,
and requirement-traceability-style views. Phase 14 implements snapshot creation,
snapshot verification, and resume-context generation.

---

## Common Projection Envelope

Every Phase 13 projection result includes:

- `projection_id`: `prj_` plus the first 32 hex characters of the result hash.
- `view_type`: one of `lineage`, `dependency`, `conflict`, `manifest`,
  `diff`, `progress`, or `traceability`.
- `workspace_id`: source workspace identifier from replay.
- `graph_revision`: exact source graph revision.
- `commit_hash`: commit hash for `graph_revision`, or the zero hash for
  revision 0.
- `generated_at`: caller-provided timestamp; defaults to a deterministic epoch
  timestamp for tests and reproducible local generation.
- `transformation_version`: `phase13-projections-v1`.
- `policy_version`: projection policy identifier; defaults to
  `phase13-default-policy-v1`.
- `source_query`: reproducible query parameters for the view.
- `source_node_ids`: graph nodes used as projection sources.
- `freshness`: source revision and external-observation refresh warnings.
- `information_loss`: explicit lossy-summary notes.
- `persistence_mode`: generated/regenerable projection output.
- `authoritative_status`: always `derived_non_authoritative`.
- `payload`: view-specific data.
- `result_hash`: SHA-256 payload hash over canonical bytes of the stable
  envelope and payload, excluding `generated_at` and `projection_id`.

Projection hashes are deterministic for the same graph revision, query,
transformation version, policy version, source nodes, freshness declaration,
information-loss declaration, and payload.

---

## Authority and Persistence

The authoritative graph remains the only lineage source of truth. Persisted
projection files under `.guerilla/projections/<revision>/<view>/` are derived
cache artifacts. Deleting every persisted projection and deleting the SQLite
index must not remove graph facts or change regenerated projection hashes.

A persisted projection may be served only for its own `graph_revision` and
transformation/policy version. A later graph revision requires regeneration.
Projection code must not invoke adapters, perform external actions, or treat
external observations as current without refresh.

---

## Lineage View

The lineage view starts from a root node and supports:

- `ancestors`;
- `descendants`;
- `both`;
- `immediate_predecessors`;
- `immediate_successors`.

The view declares direction, depth, limit, truncation, source revision, source
nodes, summarized nodes, and summarized edges. It includes branch and
convergence structure visible through direct DAG relationships at the requested
revision. Reified non-DAG assertions remain records in the graph and are not
converted into direct cycles.

---

## Dependency View

The dependency view selects direct `depends_on` relationships visible at the
requested revision. Relationship direction remains the Gate A direction:
prerequisite to dependent. The view lists edge summaries, endpoint source nodes,
and truncation status.

---

## Conflict View

The conflict view lists conflict nodes and resolution lineage. Because conflict
records are immutable, effective conflict status is derived from graph evidence:
a conflict with visible `resolved_by` lineage is effectively resolved even if
the original conflict node record remains `open`.

The default conflict view returns effectively open conflicts. A caller may pass
`status=None` to include all conflicts with their record status, effective
status, conflict type, Phase 12 conflict metadata, authority envelope, state
boundary, and resolution decision node IDs.

---

## Manifest View

The manifest view selects the latest non-superseded eligible artifact nodes
under the current policy. Entries preserve:

- graph node and entity identifiers;
- graph revision for each entry;
- node type and status;
- state boundary;
- external identity and external revision when present;
- content hash when present;
- authority envelope.

Manifest ambiguity reports identify multiple non-superseded entries for the
same external identity with incomparable external revisions. Stale-observation
reports mark every external observation as requiring refresh before external
mutation. The manifest does not transfer application-state authority from the
external system to Guerilla.

---

## Diff View

The graph diff compares two graph revisions. Immutable records are never marked
as modified. The diff reports:

- added node records;
- added edge records;
- newly visible `superseded_by` relationships;
- newly opened conflicts using effective conflict status;
- newly visible `resolved_by` conflict resolutions;
- refreshed observations represented by newly added observation-backed nodes;
- omitted unchanged history.

The right revision is the projection source revision and must be greater than
or equal to the left revision.

---

## Progress View

The progress view reports structural heads, effectively open conflicts,
blocked/unblocked status, non-completed operations eligible for attention, and
stale external observations from the manifest. It is a work-position summary,
not an authoritative scheduler.

---

## Traceability View

The traceability view summarizes relationships among goals, artifacts,
operations, events, evaluations, evidence, decisions, and conflicts using
`depends_on`, `produces`, `derives`, `evidences`, `evaluated_by`, and
`resolved_by` edges. It also lists blocking conflicts visible at the requested
revision.

---

## Regeneration Requirements

Projection generation must satisfy all of these properties:

1. Replay-backed and index-backed generation produce identical result hashes.
2. Deleting `.guerilla/projections/` and regenerating produces the same hash.
3. Deleting `.guerilla/indexes/graph.sqlite` causes index rebuild from
   authoritative replay before serving an indexed projection.
4. Later commits do not change projections explicitly requested for an earlier
   graph revision.
5. Projection code never invokes adapters or external actions.
6. Every view cites source graph revision, source query, source nodes,
   transformation version, policy version, freshness, information loss, and
   derived authority.

---

## Snapshot Records

A snapshot node is authoritative evidence that a selected graph boundary was
captured at a source graph revision. The materialized summary is derived and
non-authoritative.

Snapshot metadata includes:

- snapshot node identifier;
- source graph revision and source commit hash;
- source query and included source node identifiers;
- transformation version `phase14-snapshot-v1`;
- projection transformation version;
- policy version;
- summary hash;
- information-loss declaration;
- freshness requirements;
- materialized summary path;
- actor, authority, and created time through the node envelope.

Snapshot capture appends `captured_by` edges from every included non-snapshot
source node to the snapshot node, preserving the Gate A direction: included
source to snapshot.

---

## Materialized Summary

The materialized summary is stored under `.guerilla/snapshots/` when requested.
It is a canonical JSON file plus trailing newline and may be deleted or
corrupted without destroying authoritative continuity. Verification regenerates
the expected summary from graph replay and compares the summary hash pinned in
the snapshot node.

Missing or corrupt materialized summaries produce warnings, not a loss of
authoritative snapshot evidence.

---

## Resume Context

Resume context generation verifies the snapshot first and then produces a
bounded derived context that separates:

- authoritative facts;
- derived summaries;
- stale observations;
- unknown outcomes;
- open goals;
- eligible operations;
- blocked operations;
- unresolved conflicts;
- pending reconciliation;
- required refresh observations;
- relevant artifact revisions;
- omitted information.

Resume context generation never executes an operation, observes external state,
reconciles an action, retries an unknown outcome, or invokes adapters.

---

## Phase 15 Reserved Scope

Phase 14 does not implement CLI workflows, transports, subprocess isolation,
real integrations, archive rotation, backup/restore, performance benchmarks, or
empirical pilots.
