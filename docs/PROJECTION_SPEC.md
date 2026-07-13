# Projection Specification

**Status:** PLACEHOLDER -- cross-phase (Phase 13-14)
**Owner phase:** Phase 13 (Projections/Manifest/Diff), Phase 14 (Snapshot/Resume)
**Controlling source documents:** `GUERILLA_CONCEPT_PAPER.md` Section 9, `GUERILLA_IMPLEMENTATION_SPEC.md` Section 4.12
**Regeneration trigger:** Any projection policy change, Phase 13 completion, or Phase 14 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 13-14.

---

## Purpose

Define every projection type, its metadata requirements, generation policies, and deterministic regeneration guarantees.

---

## Required Future Sections

1. Projection metadata requirements (purpose, consumer, source graph revision, source nodes, transformation version, generation time, freshness, information loss, persistence mode, authoritative status)
2. Lineage and dependency view specification
3. Manifest specification (generation, verification, retrieval)
4. Snapshot specification (creation, retrieval, verification, resume context)
5. Diff specification (graph revisions, snapshots, manifests, artifacts)
6. Conflict view specification
7. Progress and resume view specification
8. Requirement-traceability-style status view specification
9. Projection policy representation
10. Deterministic regeneration requirements

---

## Unresolved Items

Depends on Phase 2 decisions for projection policy representation. See `docs/ARCHITECTURE_DECISIONS.md`.
