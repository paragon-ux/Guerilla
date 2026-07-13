# Graph Record Format

**Status:** PLACEHOLDER -- owned by Phase 3
**Owner phase:** Phase 3 (MACHINE_CONTRACTS)
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Section 6 (Canonical Encoding and Hashing)
**Regeneration trigger:** Any hash or encoding change or Phase 3 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 3.

---

## Purpose

Define the byte-level record layout, canonical encoding rules, and exact hash construction for all Guerilla records and messages.

---

## Required Future Sections

1. Canonical encoding rules (UTF-8, LF, sorted keys, RFC 3339 timestamps)
2. Record hash construction (`record_hash` input fields)
3. Payload hash construction
4. Transaction hash construction (ordered member record hashes)
5. Commit hash construction (previous commit hash + graph revision + transaction hash)
6. Segment hash construction (ordered commit hashes)
7. Canonicalization identifier format
8. Published test vectors for every hash type

---

## Unresolved Items

Depends on Phase 2 decisions: canonical JSON profile selection and exact hash-input field ordering. See `docs/ARCHITECTURE_DECISIONS.md`.
