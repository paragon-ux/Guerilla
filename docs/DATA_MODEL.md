# Data Model

**Status:** PLACEHOLDER -- owned by Phase 3
**Owner phase:** Phase 3 (MACHINE_CONTRACTS)
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Sections 8-23, `GUERILLA_CONCEPT_PAPER.md` Section 5
**Regeneration trigger:** Any schema change or Phase 3 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 3 publishes machine-readable contracts.

---

## Purpose

Define the complete Guerilla data model: node types, edge types, record structures, identifier formats, and relationship semantics.

---

## Required Future Sections

1. Node record model (all eight core types + namespaced subtypes)
2. Edge record model (all nine core relationship types)
3. Identifier format and prefix rules
4. Authority envelope structure
5. State-boundary declaration structure
6. Provenance metadata
7. Payload reference model
8. External identity mapping
9. Logical entity identity and revision model
10. Timestamp and ordering conventions

---

## Unresolved Items

The data model depends on Phase 2 decisions: identifier scheme (UUIDv7/ULID), canonical JSON profile, record hash construction, and exact field specifications. See `docs/ARCHITECTURE_DECISIONS.md` (to be created in Phase 2).
