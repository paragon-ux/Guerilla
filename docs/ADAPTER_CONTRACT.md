# Adapter Contract

**Status:** PLACEHOLDER -- owned by Phase 3
**Owner phase:** Phase 3 (MACHINE_CONTRACTS)
**Controlling source documents:** `GUERILLA_CONCEPT_PAPER.md` Section 8, `GUERILLA_IMPLEMENTATION_SPEC.md` Sections 4.7-4.8, 13-16, `GUERILLA_PROTOCOL_SPEC.md` Sections 10, 13-17
**Regeneration trigger:** Any adapter contract change, Phase 3 completion, or Phase 9 (adapter SDK)

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 3.

---

## Purpose

Define the adapter descriptor, capability declaration, invocation contract, state-boundary enforcement, and conformance requirements.

---

## Required Future Sections

1. Adapter descriptor schema and required fields
2. Capability declaration (read consistency, write behavior, event ordering, concurrency, conflict handling, replay support, snapshot support, identity stability, lineage completeness, idempotency, mutating actions, state boundaries, schemas, authentication, limitations)
3. Operation contracts: `describe`, `observe`, `act`, `evaluate`, `reconcile`
4. State-boundary enforcement rules
5. Adapter host behavior (load, validate, authorize, invoke, validate response, enforce timeouts)
6. Synthetic adapter conformance requirements
7. Adapter isolation models (in-process, subprocess, container, remote)

---

## Unresolved Items

Depends on Phase 2 decisions for adapter execution model and isolation. See `docs/ARCHITECTURE_DECISIONS.md`.
