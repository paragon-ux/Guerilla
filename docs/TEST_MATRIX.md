# Test Matrix

**Status:** PLACEHOLDER -- cross-phase (Phase 2 document evidence added)
**Owner phase:** Cross-phase; populated by each phase
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Section 36, `GUERILLA_PROTOCOL_SPEC.md` Section 33
**Regeneration trigger:** Any phase completion that adds or modifies tests

> **WARNING:** This document is a Phase 1 skeleton. Do not mark unimplemented tests as passing.

---

## Purpose

Track every planned test, its owning phase, current status, and evidence. Each row maps a test requirement to its implementation and pass/fail status.

---

## Required Future Sections

### Repository and Decision-Document Tests (Phase 1-2)
| Test ID | Description | Phase | Status | Evidence |
|---|---|---|---|---|
| REP-001 | Required repository scaffold exists | 1 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/repository/` |
| REP-002 | Agent skills have valid frontmatter | 1 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/repository/` |
| REP-003 | Architecture source digests match LF-normalized manifest entries | 1 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/repository/` |
| DEC-001 | Phase 2 architecture decisions are frozen and complete | 2 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/repository/` |
| DEC-002 | Glossary contains required standardized terms and core types | 2 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/repository/` |
| DEC-003 | MVP scope contains all 15 acceptance criteria and exclusions | 2 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/repository/` |
| DEC-004 | Phase 2 did not create schemas or registries | 2 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/repository/` |

### Record Tests (Phase 3-4)
| Test ID | Description | Phase | Status | Evidence |
|---|---|---|---|---|
| REC-001 | Valid node records accepted | 3 | PLANNED | -- |
| REC-002 | Invalid node records rejected | 3 | PLANNED | -- |
| REC-003 | Valid edge records accepted | 3 | PLANNED | -- |
| REC-004 | Invalid edge records rejected | 3 | PLANNED | -- |
| REC-005 | Duplicate identifiers rejected | 3 | PLANNED | -- |
| REC-006 | Hash mismatches detected | 3 | PLANNED | -- |
| REC-007 | Unsupported versions rejected | 3 | PLANNED | -- |
| REC-008 | Authority envelope validated | 3 | PLANNED | -- |

### Transaction Tests (Phase 6)
| Test ID | Description | Phase | Status | Evidence |
|---|---|---|---|---|
| TXN-001 | Atomic commit | 6 | PLANNED | -- |
| TXN-002 | Incomplete transaction ignored on replay | 6 | PLANNED | -- |
| TXN-003 | Previous-commit mismatch rejected | 6 | PLANNED | -- |
| TXN-004 | Transaction-hash mismatch rejected | 6 | PLANNED | -- |
| TXN-005 | Monotonic graph revisions | 6 | PLANNED | -- |
| TXN-006 | Concurrent append rejected | 6 | PLANNED | -- |

### DAG Tests (Phase 7)
| Test ID | Description | Phase | Status | Evidence |
|---|---|---|---|---|
| DAG-001 | Linear ancestry | 7 | PLANNED | -- |
| DAG-002 | Branching | 7 | PLANNED | -- |
| DAG-003 | Multi-parent convergence | 7 | PLANNED | -- |
| DAG-004 | Supersession | 7 | PLANNED | -- |
| DAG-005 | Direct cycle rejection | 7 | PLANNED | -- |
| DAG-006 | Self-loop rejection | 7 | PLANNED | -- |
| DAG-007 | Missing endpoints rejected | 7 | PLANNED | -- |
| DAG-008 | Reified symmetric relationships | 7 | PLANNED | -- |

### Adapter Tests (Phase 9-12)
### Action-Recovery Tests (Phase 11-12)
### Projection Tests (Phase 13-14)
### Security Tests (Phase 19)
### Performance Tests (Phase 21)

---

## Status Legend

- **PLANNED:** Test requirement exists, not yet implemented
- **IMPLEMENTED:** Test code written, not yet passing
- **PASSING:** Test passes reliably
- **FAILING:** Known failure with documented reason
- **BLOCKED:** Cannot run due to missing dependency
- **DEFERRED:** Intentionally postponed beyond current phase

---

## Unresolved Items

Runtime, schema, conformance, crash, security, and performance rows remain PLANNED until their owning phases. Phase 2 evidence is limited to repository and decision-document checks; it does not claim runtime implementation.
