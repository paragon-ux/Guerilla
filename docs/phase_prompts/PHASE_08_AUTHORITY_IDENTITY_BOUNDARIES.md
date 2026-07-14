# Phase 8 -- Authority, Identity, and Boundaries

**Status:** PASS -- Phase 8 local validation complete
**Owner phase:** Phase 8 (Authority/Identity/Boundaries)
**Gate:** B -- Kernel Ready
**Execution date:** 2026-07-14

## Objective

Implement the fixed local authorization profile, state-boundary registry,
adapter identity registration, scoped external identity lifecycle handling, and
non-escalation checks before adapter execution exists.

## Permitted Scope

- `src/guerilla/authority/`
- Storage and query hooks that enforce local graph append/read authorization.
- Security tests for authorization, boundary scope, adapter identity
  registration, external identity lifecycle, and registry replay/index
  preservation.
- Documentation updates for authority, state boundaries, test matrix, and Gate B
  handoff.

## Prohibited Scope

- Adapter invocation, observations, actions, reconciliation, projections,
  snapshots, transports, services, or real integrations.
- General programmable policy engines beyond `local-owner-v1`.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Local owner can read/append and non-owner principals are denied | PASS | `tests/security/test_phase8_authority_boundaries.py` |
| Actor fields and record authority envelopes cannot grant access | PASS | `tests/security/test_phase8_authority_boundaries.py` |
| State boundaries enforce declared operations and path/endpoint/namespace scope | PASS | `tests/security/test_phase8_authority_boundaries.py` |
| Ambiguous overlapping write authority is rejected while read overlap is allowed | PASS | `tests/security/test_phase8_authority_boundaries.py` |
| Adapter identity descriptors register capabilities without invocation | PASS | `tests/security/test_phase8_authority_boundaries.py` |
| External IDs and revisions are preserved; rename/delete/reuse/alias behavior is explicit | PASS | `tests/security/test_phase8_authority_boundaries.py` |
| Committed boundary registry metadata replays and indexes equivalently | PASS | `tests/security/test_phase8_authority_boundaries.py` |

## Stop Conditions

Stop before Gate B if authority can be expanded by actor, adapter, extension, or
payload data; boundary escape is accepted; ambiguous primary writers pass; an
external identity must be guessed; or any adapter/projection/transport behavior
is required to pass.
