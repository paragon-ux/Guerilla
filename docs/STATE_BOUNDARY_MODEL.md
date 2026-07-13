# State Boundary Model

**Status:** PLACEHOLDER -- owned by Phase 3
**Owner phase:** Phase 3 (MACHINE_CONTRACTS)
**Controlling source documents:** `GUERILLA_CONCEPT_PAPER.md` Sections 4, 8, `GUERILLA_IMPLEMENTATION_SPEC.md` Sections 4.7, 13-16
**Regeneration trigger:** Any state-boundary change or Phase 3 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 3.

---

## Purpose

Define the state-boundary model: what Guerilla owns, what external systems own, how boundaries are declared, and how authority crossing is governed.

---

## Required Future Sections

1. State-boundary declaration structure
2. What Guerilla stores (graph records, identifiers, mappings, authority declarations, provenance, payloads)
3. What Guerilla references (external objects without ownership transfer)
4. What Guerilla derives (projections, manifests, snapshots)
5. What Guerilla does not own
6. Adapter obligations at each boundary
7. Continuity modes: online, offline, reconstructed
8. Authority crossing rules
9. Conflict detection at boundaries

---

## Unresolved Items

Depends on Phase 2 decisions for authorization profile and identity lifecycle. See `docs/ARCHITECTURE_DECISIONS.md`.
