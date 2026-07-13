# Architecture Decisions

**Status:** PLACEHOLDER -- owned by Phase 2
**Owner phase:** Phase 2 (ARCHITECTURE_DECISIONS)
**Controlling source documents:** `AGENTS.md`, `GUERILLA_CONCEPT_PAPER.md`, `GUERILLA_IMPLEMENTATION_SPEC.md`, `GUERILLA_PROTOCOL_SPEC.md`, `GUERILLA_SNAPSHOT.md`
**Regeneration trigger:** Any architecture decision change or Phase 2 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 2 freezes architecture decisions.

---

## Purpose

Record and version every architecture decision affecting record identity, transaction validity, authority, replay semantics, and the machine-readable contract surface.

---

## Required Future Sections

1. Canonical JSON profile selection
2. Identifier scheme (UUIDv7 vs ULID) and prefix rules
3. Record hash and commit hash construction
4. Transaction ordering and canonical record order
5. Writer-lock mechanism
6. Atomic append, flush, and recovery behavior
7. Local/network-filesystem support boundary
8. Payload retention and redaction defaults
9. Adapter execution model for the MVP
10. Authorization profile for local operation
11. Projection policy representation
12. Archive thresholds and sealed-segment rules
13. Extension namespace governance

---

## Unresolved Items

All decisions listed above are unresolved. See `GUERILLA_SNAPSHOT.md` Section 7 for the full list of open architectural questions.
