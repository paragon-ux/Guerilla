# Phase 7 -- DAG Integrity, Index, and Query

**Status:** PASS -- Phase 7 local validation complete
**Owner phase:** Phase 7 (DAG Integrity/Index/Query)
**Gate:** B -- Kernel Ready
**Execution date:** 2026-07-14

## Objective

Implement graph correctness checks, graph heads, exact-revision reads, bounded
lineage traversal, and a rebuildable non-authoritative SQLite index.

## Permitted Scope

- `src/guerilla/graph/`
- `src/guerilla/index/`
- Storage integration hooks that validate graph integrity before append and
  rebuild or mark the non-authoritative index after durable commit.
- Integration tests for DAG validity, cycles, heads, replay/index query
  equivalence, and index rebuild.
- Documentation updates for data model, graph record format, storage, and test
  evidence.

## Prohibited Scope

- Phase 8 authority registry, external identity mapping, state-boundary
  enforcement, or local authorization policy.
- Adapter invocation, observations, actions, reconciliation, projections,
  snapshots, transports, services, or real integrations.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Same-transaction endpoints validate against the full node member set | PASS | `tests/integration/test_phase7_graph_index_query.py` |
| Missing endpoints, self-loops, incompatible endpoints, and direct cycles reject without revision change | PASS | `tests/integration/test_phase7_graph_index_query.py` |
| Graph heads, exact-revision reads, commits, ancestry, descendants, and bounded traversal are deterministic | PASS | `tests/integration/test_phase7_graph_index_query.py` |
| Replay and SQLite index query results are semantically equivalent | PASS | `tests/integration/test_phase7_graph_index_query.py` |
| Deleted or corrupt indexes can be rebuilt from authoritative replay | PASS | `tests/integration/test_phase7_graph_index_query.py` |
| Property-generated DAGs remain acyclic and reject reverse cycle attempts | PASS | `tests/integration/test_phase7_graph_index_query.py` |
| SQLite remains non-authoritative and cannot repair graph records | PASS | Index status/rebuild tests and storage append ordering |

## Stop Conditions

Stop before Phase 8 if an invalid edge can commit, replay/index queries
disagree, index loss changes authoritative graph state, a cycle commits, or
Phase 7 requires authority, adapter, projection, snapshot, or transport behavior
to pass.
