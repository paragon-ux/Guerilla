# Error Registry

**Status:** PLACEHOLDER -- owned by Phase 3
**Owner phase:** Phase 3 (MACHINE_CONTRACTS)
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Section 29, `GUERILLA_PROTOCOL_SPEC.md` Section 25
**Regeneration trigger:** Any error code change or Phase 3 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 3.

---

## Purpose

Define every stable, machine-readable error code, its classification, retry behavior, and required response fields.

---

## Required Future Sections

1. Error response structure (code, message, retriable, details, evidence_node_ids, state_boundary_id, current_graph_revision, retry_after, documentation_ref)
2. Complete error-code registry with classifications
3. Retry classification for each code
4. Error-code extension governance

---

## Unresolved Items

The error codes are defined conceptually in the implementation and protocol specifications. Final codes and classifications require Phase 3 schema publication.
