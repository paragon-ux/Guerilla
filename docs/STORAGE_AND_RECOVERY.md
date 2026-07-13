# Storage and Recovery

**Status:** PLACEHOLDER -- cross-phase (Phase 5-6, 19)
**Owner phase:** Phase 5 (Codec/Config), Phase 6 (Append Store/Transactions), Phase 19 (Security/Durability)
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Sections 5-6, 24-28
**Regeneration trigger:** Any storage/recovery change, Phase 6 completion, or Phase 19 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 5-6.

---

## Purpose

Define the workspace layout, append-only storage format, transaction durability, crash recovery, archiving, and backup/restore procedures.

---

## Required Future Sections

1. Workspace layout (`.guerilla/` directory structure)
2. Graph segment format (active and archive)
3. Atomic append, flush, and fsync behavior
4. Writer lock mechanism
5. Crash recovery: incomplete transaction detection and ignore
6. Segment chain validation
7. Archive sealing and verification
8. Backup and restore procedures
9. Filesystem durability requirements
10. Network-filesystem behavior (supported or explicitly unsupported)

---

## Unresolved Items

Depends on Phase 2 decisions for filesystem durability, writer-lock mechanism, and archive thresholds. See `docs/ARCHITECTURE_DECISIONS.md`.
