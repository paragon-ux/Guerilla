# Security Model

**Status:** PLACEHOLDER -- cross-phase (Phase 19)
**Owner phase:** Phase 19 (Security/Durability/Archive)
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Section 31, `GUERILLA_PROTOCOL_SPEC.md` Sections 27-28
**Regeneration trigger:** Any security model change or Phase 19 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 19.

---

## Required Future Sections

1. Adapter trust model and threat analysis
2. Least-privilege execution requirements
3. Filesystem and endpoint restrictions
4. Secret redaction policy and procedure
5. Payload retention and deletion behavior
6. Unsafe-deserialization review
7. Authorization model: graph reads, graph appends, adapter observations, external actions, conflict decisions, snapshot access, payload access, administrative configuration
8. Authentication and credential management
9. Denial-of-service limits
10. Operational security monitoring

---

## Unresolved Items

Depends on Phase 2 decisions for authorization profile and adapter isolation. See `docs/ARCHITECTURE_DECISIONS.md`.
