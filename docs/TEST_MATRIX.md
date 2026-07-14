# Test Matrix

**Status:** Gate A evidence current -- Phases 1-4 and entry closure PASS
**Owner phase:** Cross-phase; populated by each phase
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Section 36, `GUERILLA_PROTOCOL_SPEC.md` Section 33
**Regeneration trigger:** Any phase completion that adds or modifies tests

> **WARNING:** Phase 5 primitive runtime tests are passing. Append storage,
> replay, crash, security, performance, adapter, projection, and transport tests
> remain planned until their owning phases.

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
| DEC-004 | Phase 2 decision vectors semantically validate canonical JSON, identifiers, hashes, ordering, durability, and authorization | 2 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/repository/` |

### Machine Contract Tests (Phase 3)
| Test ID | Description | Phase | Status | Evidence |
|---|---|---|---|---|
| SCH-001 | All Gate A Draft 2020-12 schemas are present and meta-valid | 3 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| SCH-002 | Schema references resolve in both validators | 3 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| SCH-003 | Registries synchronize with schema enums | 3 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| SCH-004 | Relationship directions match Phase 2 decisions | 3 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| SCH-005 | UUIDv7, timestamp, numeric, authority, extension, and derived-authority schema cases validate | 3 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| SCH-006 | Contract inventory maps every workflow surface to a canonical schema and fixtures | Gate A closure | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |

### Conformance Fixture Tests (Phase 4)
| Test ID | Description | Phase | Status | Evidence |
|---|---|---|---|---|
| FIX-001 | Every fixture declares contract version, expected outcome, failure reason, and governing decision | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| FIX-002 | Valid fixtures cover every schema and pass both validators | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| FIX-003 | Invalid fixtures cover every schema and fail deterministically | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| FIX-004 | Compatibility fixtures demonstrate optional/critical extension and version behavior | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| FIX-005 | Canonicalization, Unicode, timestamp, integer, identifier, and hash vectors reproduce exact expected bytes/digests | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| FIX-006 | Raw JSON lexical fixtures reject prohibited numeric spellings, duplicate keys, invalid UTF-8, and isolated surrogates through two paths | Gate A closure | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| FIX-007 | Timestamp fixtures check calendar validity, leap days, normalized fractions, and stored UTC grammar through two paths | Gate A closure | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |

### Record Tests (Phase 3-4)
| Test ID | Description | Phase | Status | Evidence |
|---|---|---|---|---|
| REC-001 | Valid node records accepted by schema fixtures | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| REC-002 | Invalid node records rejected by schema fixtures | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| REC-003 | Valid edge records accepted by schema fixtures | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| REC-004 | Invalid edge endpoint shape rejected by schema fixtures | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| REC-005 | Duplicate committed identifiers rejected by runtime validator | 6 | PLANNED | -- |
| REC-006 | Hash mismatches detected by runtime verifier | 6 | PLANNED | -- |
| REC-007 | Unsupported versions rejected by schema fixtures | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |
| REC-008 | Authority envelope validated by schema fixtures | 4 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/conformance/` |

### Codec, Config, Identifier Tests (Phase 5)
| Test ID | Description | Phase | Status | Evidence |
|---|---|---|---|---|
| CCI-001 | Production canonical JSON reproduces Gate A vectors and JSONL newline behavior | 5 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/unit/test_phase5_codec_config_identity.py` |
| CCI-002 | Raw JSON byte validation rejects duplicate keys, invalid UTF-8, isolated surrogates, and prohibited numeric spellings | 5 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/unit/test_phase5_codec_config_identity.py` |
| CCI-003 | Timestamp normalization validates calendar dates, leap days, UTC storage grammar, and offset normalization | 5 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/unit/test_phase5_codec_config_identity.py` |
| CCI-004 | UUIDv7-prefixed identifiers validate every family and generate monotonic same-millisecond IDs | 5 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/unit/test_phase5_codec_config_identity.py` |
| CCI-005 | Record, payload, transaction, commit, segment, and archive-seal hashes reproduce Gate A vectors | 5 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/unit/test_phase5_codec_config_identity.py` |
| CCI-006 | Contract loader validates schemas with two independent implementations and immutable values cannot mutate | 5 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/unit/test_phase5_codec_config_identity.py` |
| CCI-007 | Workspace config loads explicit supported profiles and fails closed for unsupported mutation-capable settings | 5 | PASSING | `uv run --frozen --extra dev --python 3.11 pytest tests/unit/test_phase5_codec_config_identity.py` |

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

Runtime crash, security, performance, adapter, projection, and storage rows remain PLANNED until their owning phases. Gate A evidence does not claim codec, graph store, adapter, transport, projection, or replay implementation.
