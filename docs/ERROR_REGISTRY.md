# Error Registry

**Status:** FROZEN -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
**Controlling registry:** `registries/error_codes.json`
**Controlling schema:** `schemas/error.schema.json`

## Purpose

Guerilla errors use stable machine-readable codes with retry classifications
and safe diagnostic fields.

## Error Object

Every error object contains:

- `code`;
- `message`;
- `retriable`;
- `details`;
- optional evidence node ids;
- optional state-boundary id;
- optional current graph revision;
- optional retry-after value;
- optional documentation reference.

Payloads, credentials, and removed secret bytes must not be copied into error
text or details.

## Registry

The normative error list is `registries/error_codes.json`. The schema enum in
`schemas/common.schema.json` must remain synchronized with that registry.

## Retry Classification

Retry values are:

- `never`;
- `after_reconcile`;
- `after_refresh`;
- `after_backoff`;
- `idempotent_replay`;
- `not_applicable`.

## Phase Boundary

This document does not implement error handling, retry behavior, logging, or
transport responses. It freezes the contract vocabulary for later phases.
