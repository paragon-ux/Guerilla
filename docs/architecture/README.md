# Architecture Source Manifest

**Status:** Phase 1 — source integrity record
**Owner phase:** Phase 1 (Kickoff)
**Regeneration trigger:** Any source paper modification or reimport

## Imported Sources

| Original filename | Repository path | SHA-256 digest | Import date | Architecture role | Classification |
|---|---|---|---|---|---|
| `GUERILLA_CONCEPT_PAPER.md` | `docs/architecture/GUERILLA_CONCEPT_PAPER.md` | `940f0e3b2fa8ebeee7335cacced35368f257734886347bdbcf4f72d22049ae5f` | 2026-07-13 | Product identity, state ownership, graph thesis, use cases, evaluation questions | **Normative** |
| `GUERILLA_IMPLEMENTATION_SPEC.md` | `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md` | `bf5e1801a188ef67f190bad838c8112c0fe6ce05c134f1f3771e59a94befebb7` | 2026-07-13 | Normative runtime components, storage, flows, security, testing, MVP acceptance | **Normative** |
| `GUERILLA_PROTOCOL_SPEC.md` | `docs/architecture/GUERILLA_PROTOCOL_SPEC.md` | `e0366857ff2bebe65b28ad2cf83907f3c74c6d3dc835c069b24a5f56267f457a` | 2026-07-13 | Transport-independent GLCP operations, envelopes, errors, retry and compatibility semantics | **Normative** |
| `GUERILLA_SNAPSHOT.md` | `docs/architecture/GUERILLA_SNAPSHOT.md` | `147815e5c7dbb2be9862f6a0d31cf83492fce9f0c4ea16c4d0c159f10eeaa84c` | 2026-07-13 | Current decisions, unresolved questions, milestones, readiness gates | **Normative** |
| `CURRENT_STATUS_MATRIX.md` | `docs/architecture/CURRENT_STATUS_MATRIX.md` | `22e712fceb54c052e5f45f5a4c5b8a46152a01673b68875bda45acfca5e102d0` | 2026-07-13 | Implementation readiness and critical path | **Supporting** |
| `RELATED_WORK.md` | `docs/architecture/RELATED_WORK.md` | `1a83b97125f6afe8dbcb4e3cde4cf384481a8dca841fc81a01bcb32d8dce0bb9` | 2026-07-13 | Comparative positioning and evaluation framing | **Supporting** |
| `Note-on-Architecture.md` | `docs/rationale/Note-on-Architecture.md` | `31c885a3c04a49aa18f5fffe2d3a8efb29b3803acf807abce58ef724adadecf2` | 2026-07-13 | Controlling rationale for state continuity, authoritative lineage, and hybrid boundaries | **Rationale** |

## Integrity Rules

- Sources were line-ending normalized (CRLF → LF) during placement. No substantive content was modified.
- `RELATED_WORK.md` is classified as **Supporting** — it informs comparative positioning but is not normative for runtime behavior.
- `Note-on-Architecture.md` is classified as **Rationale** — it is the controlling rationale for architecture ordering and boundary definition but is not a normative implementation document.
- All normative documents are version `0.2.0-draft`. No document claims a frozen contract status.

## Verification

Regenerate digests and compare:

```bash
sha256sum docs/architecture/*.md docs/rationale/*.md
```
