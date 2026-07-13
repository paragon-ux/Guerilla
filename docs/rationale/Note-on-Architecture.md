# Choose State Continuity and Lineage for the Architecture

State continuity should be selected deliberately as part of the project architecture. It is not a one-size-fits-all requirement.

The choice between continuous state and agentic or manual state management depends on the architecture:

* A full **OCC/OT architecture** supporting live collaboration requires online, continuous state.
* A **binary check/diff and drift-control architecture** may require only offline or periodically reconstructed state.

When the state-continuity model does not match the architecture, the system develops hidden state-management burdens and scalability constraints.

For example:

* Command-driven or filesystem-based systems may accumulate scores of commands that implicitly reconstruct and coordinate state.
* Server-driven systems may accumulate scores of requests that perform the same hidden coordination.
* Datastores can provide efficient continuity for concurrent edits, but may become bottlenecks for read-heavy workloads.
* Filesystems can provide efficient continuity for read-heavy workflows, but may become bottlenecks when many actors edit concurrently.

The objective is therefore not to choose continuous state by default, but to choose the form of state continuity that matches the system’s concurrency, persistence, and access requirements.

## Preserve Authoritative Lineage

Lineage is less architecture-specific.

In most systems with fully expressive hierarchical relationships, lineage is best represented as a relational graph—typically a directed acyclic graph, or DAG.

Compressing authoritative lineage creates two major problems:

1. **Hidden hierarchical inference**
   Relationships that should be explicit must instead be inferred from incomplete or flattened representations.

2. **Incomplete relational state boundaries**
   The system may lose the information required for actor-agnostic behavior, conflict handling, provenance, and dependency resolution.

Lineage may be compressed in derived views that only need to show:

* current status,
* a manifest,
* a snapshot, or
* a diff.

However, those compressed views should not replace the authoritative relational state.

## Establish State and Lineage Before Finalizing the Architecture

This principle applies across projects: state continuity and lineage should be defined before the architecture is solidified.

Validation systems, regression checks, semantic checks, and external oracles can identify incorrect outputs or invalid transitions. They cannot prevent the primary architectural consequences of mismatched state or lineage:

* hidden state-management mechanisms,
* scalability limitations,
* hidden hierarchical inference, and
* incomplete relational state boundaries.

These are structural problems, not merely validation problems.

## Define Explicit Boundaries in Hybrid Architectures

Hybridization is not a way to avoid these decisions.

A project may legitimately use multiple architectural models, but those models must not overlap ambiguously. Each architectural boundary must clearly define:

* which component owns authoritative state,
* whether state continuity is online, offline, or reconstructed,
* how state crosses the boundary,
* where lineage is recorded,
* which relationships remain authoritative, and
* how conflicts are detected and resolved.

Without clear delineation, a hybrid architecture reproduces the same hidden state-management, scalability, inference, and relational-boundary problems it was intended to avoid.

The architecture should therefore be chosen around explicit state-continuity and lineage requirements—not the other way around.
