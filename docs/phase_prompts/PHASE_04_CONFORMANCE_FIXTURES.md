# Phase 4 -- Conformance Fixtures

**Status:** PASS -- Phase 4 complete
**Owner phase:** Phase 4 (Conformance Fixtures)
**Gate:** A -- Contract Ready
**Execution date:** 2026-07-13

## Objective

Publish deterministic fixture corpora for the Phase 2 decisions and Phase 3
machine contracts. Validate every schema fixture with two independent JSON
Schema validator implementations and validate canonicalization/hash vectors
without importing future Guerilla runtime modules.

## Permitted Scope

- Fixture files under `tests/fixtures/contracts/`.
- Conformance tests under `tests/conformance/`.
- Phase 4 documentation and status updates.

## Prohibited Scope

- Codec implementation.
- Identifier generator.
- Graph store, replay, transaction engine, lock manager, archive writer, or
  recovery implementation.
- Adapter runtime, transport, projections, or external integrations.

## Fixture Corpora

| Corpus | Path | Coverage |
|---|---|---|
| Valid schema examples | `tests/fixtures/contracts/valid/schema_examples.json` | Every Phase 3 schema |
| Invalid schema examples | `tests/fixtures/contracts/invalid/schema_examples.json` | Every schema plus semantic invalid cases |
| Compatibility cases | `tests/fixtures/contracts/compatibility/compatibility_cases.json` | Optional/critical extensions, version compatibility, downgrade behavior |
| Canonicalization and hashes | `tests/fixtures/contracts/canonicalization/canonical_hash_vectors.json` | Unicode, timestamps, integer forms, identifiers, record/payload/transaction/commit/segment/archive hashes, relationship directions |

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Every fixture declares contract version, expected outcome, failure reason, and governing decision | PASS | `tests/conformance/test_conformance_fixtures.py` |
| Both validators agree for every schema fixture | PASS | `tests/conformance/test_conformance_fixtures.py` |
| Canonicalization vectors reproduce exact bytes and digests | PASS | `tests/conformance/test_conformance_fixtures.py` |
| Hash vectors contain exact preimages and digests | PASS | `tests/fixtures/contracts/canonicalization/canonical_hash_vectors.json` |
| Compatibility behavior demonstrated | PASS | `tests/fixtures/contracts/compatibility/compatibility_cases.json` |
| No runtime implementation introduced | PASS | Repository contract tests |

## Completion Note

Phase 4 completes Gate A. Phase 5 remains intentionally not started in this
thread.
