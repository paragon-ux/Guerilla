# Phase 6 -- Append Store, Transactions, and Replay

**Status:** PASS -- Phase 6 local validation complete
**Owner phase:** Phase 6 (Append Store/Transactions/Replay)
**Gate:** B -- Kernel Ready
**Execution date:** 2026-07-14

## Objective

Implement local workspace initialization, the single authoritative JSONL append
path, writer locking, transaction framing, final commit-record durability,
payload persistence, replay, verification, and incomplete-tail recovery.

## Permitted Scope

- `src/guerilla/storage/`
- `src/guerilla/payloads/` payload persistence helpers
- Integration tests for initialization, append, replay, lock, payload, and
  recovery behavior.
- Documentation updates for storage and recovery.

## Prohibited Scope

- Phase 7 DAG cycle engine, SQLite index, graph queries, or graph-head query
  service.
- Phase 8 authority registry, external identity mapping registry, or state
  boundary enforcement beyond fail-closed hooks.
- Adapter invocation, observations, actions, reconciliation, projections,
  snapshots, transports, services, or real integrations.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Workspace initialization is idempotent and writes one graph header | PASS | `tests/integration/test_phase6_append_store.py` |
| Valid transactions append through one path and advance one revision | PASS | `tests/integration/test_phase6_append_store.py` |
| Invalid transactions commit nothing | PASS | `tests/integration/test_phase6_append_store.py` |
| Incomplete tails replay to the last durable commit with diagnostics | PASS | `tests/crash/test_phase6_recovery.py` |
| Commit and transaction hash-chain verification detects corruption | PASS | `tests/integration/test_phase6_append_store.py` |
| Writer lock rejects concurrent appends and never breaks stale locks silently | PASS | `tests/integration/test_phase6_append_store.py` |
| Payload store writes content-addressed bytes and distinguishes missing/mismatch | PASS | `tests/integration/test_phase6_append_store.py` |
| Replay is side-effect free and does not invoke external actions | PASS | Store tests import no adapter/action/projection modules |

## Stop Conditions

Stop before Phase 7 if replay can disagree with the durable commit boundary,
invalid transactions can advance revision, the lock is uncertain, corruption is
not detected, or Phase 6 requires DAG indexing, adapters, projections, or
authority registry behavior to pass.
