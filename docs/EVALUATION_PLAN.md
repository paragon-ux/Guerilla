# Evaluation Plan

**Status:** PLACEHOLDER -- cross-phase (Phase 21)
**Owner phase:** Phase 21 (Benchmark/Evaluation)
**Controlling source documents:** `GUERILLA_CONCEPT_PAPER.md` Section 15, `RELATED_WORK.md`
**Regeneration trigger:** Phase 21 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 21.

---

## Purpose

Define the evaluation methodology, research questions, measurements, comparators, and evidence requirements for Guerilla's empirical contribution.

---

## Required Future Sections

### Research Questions

1. **Resume accuracy:** Correct identification of graph heads, stale observations, conflicts, and next operations
2. **Lineage completeness:** Percentage of artifact revisions traceable to producer, observation, actor, result, and evaluation
3. **Boundary preservation:** Number of direct or replacement external-state writes; target zero
4. **Projection reproducibility:** Hash equality after regeneration from same revision and policy
5. **Conflict detection:** Reliability of stale revision, external rejection, failed evaluation, ambiguous authority, and incomplete ancestry detection
6. **Storage and query cost:** Append volume, payload retention, index size, projection latency, snapshot size
7. **Recovery behavior:** Correct classification after interruption between intent and result recording

### Comparators

- Conversation or summary-only continuity
- Conventional logs
- Workflow-engine histories
- Provenance-only recording
- Guerilla full intent-result-reconciliation graph

---

## Unresolved Items

All evaluation questions are unresolved. No benchmarks, pilots, or comparative results exist.
