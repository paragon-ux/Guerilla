# guerilla-projections-snapshot-resume

**Skill:** Derived views, manifests, snapshots, diffs, resume context, and deterministic regeneration
**Owner phase:** Phase 13 (Projections/Manifest/Diff), Phase 14 (Snapshot/Resume)
**File:** `.agents/skills/guerilla-projections-snapshot-resume/SKILL.md`

---

## 1. Purpose

Own every derived representation of the authoritative graph. This skill governs lineage and dependency views, manifests, conflict and progress views, traceability views, snapshots, graph diffs, resume context, and the guarantee that every output is source-bound, reproducible, and non-authoritative.

---

## 2. Activation Criteria

Activate when the task involves:

- Generating any derived view from the authoritative graph.
- Implementing manifest generation, verification, and retrieval.
- Implementing snapshot creation, retrieval, verification, and resume-context generation.
- Implementing graph and artifact diff generation.
- Implementing conflict views, progress views, and requirement-traceability-style status views.
- Ensuring every projection cites its source graph revision, transformation version, and information loss.
- Implementing deterministic projection regeneration.
- Persisting or caching derived views.

---

## 3. Non-Activation Criteria

Do NOT activate when the task involves:

- Mutating the authoritative graph (delegate to `guerilla-graph-kernel-storage`).
- Implementing adapter observation or action flows (delegate to `guerilla-adapter-continuity-reconciliation`).
- Defining projection schemas (delegate to `guerilla-contracts-modeling`).
- Writing performance or security tests (delegate to `guerilla-testing-security-evaluation`).

---

## 4. Required Reading

Before any projection work, read in order:

1. `AGENTS.md` -- authoritative vs derived storage, locked invariants (projections are non-authoritative)
2. `docs/architecture/GUERILLA_CONCEPT_PAPER.md` -- Section 9 (derived views: lineage, manifest, snapshot, diff, status, progress/resume)
3. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md` -- Sections 4.6 (payload store), 4.12-4.13 (projection engine, index and query engine), Section 27 (indexing and caching)
4. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md` -- Sections 18-20 (manifest, snapshot, diff operations)
5. `docs/architecture/GUERILLA_SNAPSHOT.md` -- Sections 3.7 (derived views cite sources), 9 (deferred capabilities)
6. `docs/PROJECTION_SPEC.md` (once created)

---

## 5. Owned Artifacts

This skill owns:

- `src/guerilla/projections/` -- all derived view generation
- `docs/PROJECTION_SPEC.md` -- projection metadata, policies, and regeneration specification
- Persisted projections under `.guerilla/projections/` (non-authoritative, rebuildable)
- Materialized snapshot summaries under `.guerilla/snapshots/` (non-authoritative payloads)

---

## 6. Invariants

When working on projections, these MUST NOT be violated:

- Every projection must identify: purpose, intended consumer, source graph revision, source node set or reproducible query, transformation and policy version, generation time, freshness, known information loss, persistence mode, and authoritative status (always "derived, non-authoritative").
- A persisted view may become stale or use an obsolete transformation policy. Every view therefore requires a source revision and transformation version.
- A cache entry from an earlier graph revision MAY be served only when the client explicitly requests that earlier revision.
- Caches must include the source graph revision in their keys.
- Deleting every persisted projection and index must not lose authoritative lineage. All views must regenerate deterministically.
- The fact that a snapshot was created is authoritative lineage. Its materialized summary is derived and hash-pinned; it does not replace source nodes.
- A manifest is derived. An external consumer MAY treat it as an input artifact, but it does not replace source graph records.
- Snapshot verification MUST NOT claim that cited external observations remain current.

---

## 7. Ordered Procedure

### Phase 13 -- Projections, Manifest, Diff

1. Implement lineage and dependency view: graph traversal with declared direction, depth, and filters.
2. Implement manifest generation: filter and select latest eligible revisions under declared policy; include source graph revision, transformation version, entries, ambiguity reports, stale-observation reports, result hash.
3. Implement conflict view: unresolved conflicts with evidence, affected artifacts, blocking status.
4. Implement progress and resume view: graph heads, blocked branches, stale observations, eligible next operations.
5. Implement requirement-traceability-style status view: relationships among requirements, implementations, evaluations, evidence, and blocking conflicts.
6. Implement graph diff: compare two graph revisions, snapshots, manifests, or artifact revisions; report added/superseded nodes, added edges, opened/resolved conflicts, refreshed observations.
7. Write `docs/PROJECTION_SPEC.md`.

### Phase 14 -- Snapshot, Resume

1. Implement snapshot creation: commit a snapshot node with scope, graph revision, policy version, graph heads, open goals, unresolved conflicts, latest artifact revisions, refresh requirements, next eligible operations, summary hash, source references.
2. Implement snapshot retrieval and verification: verify node integrity, graph revision, commit, source-node existence, summary hash, transformation version.
3. Implement resume-context generation: distinguish immutable graph facts, external observations needing refresh, unresolved conflicts, eligible operations, adapter compatibility warnings.
4. Implement deterministic regeneration of all projection types from declared sources.

---

## 8. Tests

Projection tests must verify:

- Deterministic output for same graph revision, query, and policy.
- Source revision citation in every generated view.
- Source-node citation in every generated view.
- Information-loss declaration present in every generated view.
- Stale external observation reporting in manifests and resume views.
- Regeneration after index deletion produces identical results.
- Manifest ambiguity handling.
- Snapshot verification: integrity, source-node existence, summary hash match.
- Diff correctness: added, superseded, unchanged classifications.
- Cache invalidation when graph revision changes.

Test commands: `uv run pytest tests/unit/ tests/integration/ tests/conformance/ -k "projection or manifest or snapshot or diff or view or resume"`.

---

## 9. Failure Cases

Design projections to handle:

- Missing source nodes referenced by a snapshot -- snapshot verification fails.
- Requested graph revision no longer available -- projection generation fails with explicit error.
- Transformation policy version mismatch -- projection regenerated with current policy, discrepancy reported.
- External observations are stale at generation time -- reported in freshness field, not silently treated as current.
- Cached projection from wrong graph revision -- cache miss, regeneration triggered.
- Snapshot summary hash mismatch on verification -- verification fails, source references remain valid.

---

## 10. Stop Conditions

Stop projection work and report the blocker if:

- A projection is treated as authoritative instead of derived.
- Regeneration from the same inputs produces different outputs.
- A snapshot omits its source graph revision or transformation version.
- A view silently treats a stale external observation as current.
- Cache invalidation fails and serves data from a wrong graph revision.

---

## 11. Completion Evidence

Projection completion requires:

- All eight view types generating correct output.
- Deterministic regeneration demonstrated.
- Source revision and transformation version cited in every output.
- Index deletion and projection regeneration passing.
- Snapshot creation, verification, and resume-context generation passing.
- Diff correctness demonstrated.
- All projection tests passing.

---

## 12. Handoff

After completing projection work, hand off to:

- `guerilla-testing-security-evaluation` -- for projection performance measurement, snapshot-size benchmarks, and evaluation.
