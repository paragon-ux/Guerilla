# Architecture Source Manifest

**Status:** Phase 1 — source integrity record
**Owner phase:** Phase 1 (Kickoff)
**Regeneration trigger:** Any source paper modification or reimport

## Imported Sources

| Original filename | Repository path | SHA-256 digest | Import date | Architecture role | Classification |
|---|---|---|---|---|---|
| `GUERILLA_CONCEPT_PAPER.md` | `docs/architecture/GUERILLA_CONCEPT_PAPER.md` | `c7fc3cd5acac20a1798bb323030c6b926b61d31ede09918af63878f360613470` | 2026-07-13 | Product identity, state ownership, graph thesis, use cases, evaluation questions | **Normative** |
| `GUERILLA_IMPLEMENTATION_SPEC.md` | `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md` | `2eef1b6c4aef1e49d2bad54e3416e8d30dd2b2da5dee74c52fc3bf602446aca7` | 2026-07-13 | Normative runtime components, storage, flows, security, testing, MVP acceptance | **Normative** |
| `GUERILLA_PROTOCOL_SPEC.md` | `docs/architecture/GUERILLA_PROTOCOL_SPEC.md` | `0bddc9eb917356b288b04cb06ee43257068fbf515f8245e1bb24a302b88c389c` | 2026-07-13 | Transport-independent GLCP operations, envelopes, errors, retry and compatibility semantics | **Normative** |
| `GUERILLA_SNAPSHOT.md` | `docs/architecture/GUERILLA_SNAPSHOT.md` | `a2af47a0a89ab5b6a2588c0d2d6682a01d9ef255b013264908a7250f24c16c25` | 2026-07-13 | Current decisions, unresolved questions, milestones, readiness gates | **Normative** |
| `CURRENT_STATUS_MATRIX.md` | `docs/architecture/CURRENT_STATUS_MATRIX.md` | `201632497791dbdedd3885525eea43e690069305c7083ffd6e4d366eb48aec0d` | 2026-07-14 | Implementation readiness and critical path after Gate B and Phase 13 validation | **Supporting** |
| `RELATED_WORK.md` | `docs/architecture/RELATED_WORK.md` | `80537903154e51c683c45a9ae55a1822efbfefd4001667f58ca19ec608568eb3` | 2026-07-13 | Comparative positioning and evaluation framing | **Supporting** |
| `Note-on-Architecture.md` | `docs/rationale/Note-on-Architecture.md` | `9b8ff35a5a4f10dfe9cb21955fb114d7a82125fd26c9609503c0e85153be763f` | 2026-07-13 | Controlling rationale for state continuity, authoritative lineage, and hybrid boundaries | **Rationale** |

## Integrity Rules

- Digests are computed over LF-normalized bytes (CRLF to LF). The four normative architecture papers remain imported sources; `CURRENT_STATUS_MATRIX.md` is a supporting status surface that is refreshed as phase evidence changes.
- `RELATED_WORK.md` is classified as **Supporting** — it informs comparative positioning but is not normative for runtime behavior.
- `Note-on-Architecture.md` is classified as **Rationale** — it is the controlling rationale for architecture ordering and boundary definition but is not a normative implementation document.
- All normative documents are version `0.2.0-draft`. No document claims a frozen contract status.

## Verification

Run the repository-contract digest check:

```bash
uv run pytest tests/repository/test_repository_contract.py -k source_digests
```
