# Data Model

**Status:** FROZEN -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
**Contract version:** `0.2.0`
**Controlling sources:** `ARCHITECTURE_DECISIONS.md`, `MVP_SCOPE.md`, `schemas/*.schema.json`, `registries/*.json`
**Regeneration trigger:** Schema, registry, or frozen architecture-decision change

## Purpose

The Guerilla data model is the machine-checkable surface for authoritative
graph records, external authority references, payload references, extensions,
and derived-view descriptors.

The schemas under `schemas/` are normative for field shape. The registries under
`registries/` are normative for enum values, relationship directions, extension
namespaces, and error/capability names.

## Authoritative Record Types

| Record | Schema | Authority |
|---|---|---|
| Graph header | `schemas/graph_header.schema.json` | Authoritative graph metadata |
| Node | `schemas/node.schema.json` | Authoritative graph record |
| Edge | `schemas/edge.schema.json` | Authoritative graph record |
| Transaction | `schemas/transaction.schema.json` | Canonical transaction wrapper |
| Transaction begin | `schemas/transaction_begin.schema.json` | Transaction frame |
| Transaction commit | `schemas/transaction_commit.schema.json` | Final commit boundary |
| Commit | `schemas/commit.schema.json` | Canonical final commit surface |
| Archive seal | `schemas/archive_seal.schema.json` | Authoritative segment integrity record |

Gate A entry closure publishes `docs/contract_inventory.json`, which maps every
workflow surface to its canonical schema, aliases, owning phase, and fixture
coverage. Thin composed wrappers such as `commit.schema.json`,
`authority_envelope.schema.json`, `payload_reference.schema.json`,
`conflict.schema.json`, `snapshot.schema.json`, and
`projection_metadata.schema.json` do not create additional authority; they make
the workflow vocabulary machine-checkable.

## Core Node Types

The core node types are `goal`, `artifact`, `operation`, `event`,
`evaluation`, `decision`, `conflict`, and `snapshot`. The normative registry is
`registries/node_types.json`.

Namespaced node types are permitted only through registered extensions and must
not redefine core semantics.

## Core Relationship Directions

The normative registry is `registries/relationship_types.json`.

| Relationship | Direction |
|---|---|
| `depends_on` | prerequisite -> dependent |
| `produces` | producer -> product |
| `derives` | source -> derived |
| `causes` | cause -> effect |
| `evidences` | evidence -> supported record |
| `evaluated_by` | subject -> evaluation |
| `superseded_by` | earlier -> later |
| `resolved_by` | unresolved item -> resolution |
| `captured_by` | included source -> snapshot |

Edge endpoints must be node identifiers. Same-transaction endpoints are valid
only when the referenced node member is part of the same canonical transaction
member set. Self-loops, missing endpoints, incompatible endpoint types, and
cycle-producing direct edges are rejected by later runtime validation phases.
Phase 7 enforces these rules before staging a transaction. Endpoint compatibility
is read from `registries/relationship_types.json`; missing compatibility data
blocks mutation.

## Identifiers and Revisions

Guerilla identifiers are UUIDv7 with registered lowercase prefixes. Field
schemas select the required prefix family. Graph revisions are non-negative
JSON-safe integers and are authoritative for committed graph order.

## Authority, State Boundaries, and Payloads

Authority is represented by `schemas/authority.schema.json` and
`schemas/state_boundary.schema.json`. Actor fields remain attribution and never
grant authority. External identifiers remain authority-scoped tuples described
by `schemas/external_identity.schema.json`.

Payload references are described by `schemas/payload_ref.schema.json`. The
default is metadata-first retention. Retained payload hashes cover retained
post-redaction bytes only.

## Derived Data

`schemas/derived_projection.schema.json` requires `authoritative: false` and
`authority_class: derived_non_authoritative`. Projections, manifests, snapshots,
indexes, and caches never replace authoritative graph records.

The Phase 7 SQLite index is explicitly rebuildable from authoritative replay. It
may serve queries only when its source graph revision and commit hash match the
durable graph.

## Phase Boundary

This document publishes contracts and current phase boundaries. Runtime graph
storage, DAG validation, indexing, and local authority/boundary enforcement are
implemented by Phases 6-8; adapters, transports, projections, and Phase 9+
continuity behavior remain outside this document.
