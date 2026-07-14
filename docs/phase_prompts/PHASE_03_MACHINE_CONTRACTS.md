# Phase 3 -- Machine Contracts

**Status:** PASS -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
**Gate:** A -- Contract Ready
**Execution date:** 2026-07-13

## Objective

Publish the complete Draft 2020-12 schema set and registries that encode the
frozen Phase 2 decisions before any Phase 5 runtime implementation begins.

## Permitted Scope

- JSON Schemas under `schemas/`.
- Registries under `registries/`.
- Phase 3-owned contract documents.
- Repository and conformance tests for schemas, registries, and examples.
- Documentation status updates.

## Prohibited Scope

- Codec implementation.
- Identifier generator.
- Graph store, replay, transaction engine, lock manager, or archive writer.
- Adapter runtime, transport, projections, or real external integrations.

## Required Sources

1. `AGENTS.md`
2. `docs/ARCHITECTURE_DECISIONS.md`
3. `docs/MVP_SCOPE.md`
4. `docs/DATA_MODEL.md`
5. `docs/GRAPH_RECORD_FORMAT.md`
6. `docs/GLCP_CORE_SPEC.md`
7. `docs/ADAPTER_CONTRACT.md`
8. `docs/STATE_BOUNDARY_MODEL.md`
9. `docs/ERROR_REGISTRY.md`

## Delivered Contracts

- 20 JSON Schemas in `schemas/`.
- 6 registries in `registries/`.
- Phase 3 contract docs replacing placeholder documents.
- Semantic tests for schema meta-validation, reference resolution,
  registry/schema synchronization, relationship directions, UUIDv7 validation,
  authority non-escalation, timestamps, numbers, extensions, and examples.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Draft 2020-12 schemas published | PASS | `schemas/*.schema.json` |
| Required registries published | PASS | `registries/*.json` |
| Registries synchronized with schema enums | PASS | `tests/conformance/` |
| Valid and invalid schema examples covered | PASS | `tests/conformance/` |
| No runtime implementation introduced | PASS | Repository contract tests |

## Completion Note

Phase 3 may hand off to Phase 4 conformance fixtures. Phase 5 remains blocked
until Phase 4 passes and Gate A is complete.
