# Phase 5 -- Codec, Config, and Identifiers

**Status:** PASS -- Phase 5 complete
**Owner phase:** Phase 5 (Codec/Config/Identifiers)
**Gate:** B -- Kernel Ready
**Execution date:** 2026-07-14

## Objective

Implement deterministic configuration loading, read-only contract loading,
canonical JSON, timestamp handling, UUIDv7-prefixed identifiers, hash preimages,
payload primitives, immutable contract values, and protocol validation.

## Permitted Scope

- `src/guerilla/config/`
- `src/guerilla/contracts/`
- `src/guerilla/codec/`
- `src/guerilla/protocol/`
- `src/guerilla/payloads/`
- `src/guerilla/identity/`
- Unit and conformance tests for those primitives.
- Documentation updates for Phase 5 evidence.

## Prohibited Scope

- Append store, writer lock, transaction commit, graph replay, cycle engine,
  SQLite index, authority registry, external mappings, adapter runtime,
  observations, actions, reconciliation, projections, snapshots, or network
  service.

## Required Sources

1. `AGENTS.md`
2. `docs/ARCHITECTURE_DECISIONS.md`
3. `docs/contract_inventory.json`
4. `schemas/`
5. `registries/`
6. `tests/fixtures/contracts/`
7. `docs/GRAPH_RECORD_FORMAT.md`
8. `docs/GLCP_CORE_SPEC.md`
9. `docs/STATE_BOUNDARY_MODEL.md`

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Gate A vectors reproduced by production codec/hash code | PASS | `tests/unit/test_phase5_codec_config_identity.py` |
| Raw JSON and timestamp rejection implemented outside tests | PASS | `tests/unit/test_phase5_codec_config_identity.py` |
| UUIDv7 generation/validation exact and deterministic under injection | PASS | `tests/unit/test_phase5_codec_config_identity.py` |
| Configuration validates and fails closed for mutation-capable services | PASS | `tests/unit/test_phase5_codec_config_identity.py` |
| Contract loader validates with two independent implementations | PASS | `tests/unit/test_phase5_codec_config_identity.py` |
| Immutable values validate against Gate A contracts | PASS | `tests/unit/test_phase5_codec_config_identity.py` |
| No Phase 6 storage/replay code introduced | PASS | Repository audit |

## Completion Note

Phase 5 may hand off to Phase 6 after hosted CI passes the Phase 5 commit.
Phase 6 remains intentionally not started in this phase.

## Stop Conditions

Stop before Phase 6 if canonical bytes, hashes, identifiers, configuration, or
contract validation do not match Gate A, or if Phase 5 introduces graph storage,
replay, locking, indexing, adapter execution, projections, or external actions.
