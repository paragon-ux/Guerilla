# Security Model

**Status:** PLACEHOLDER -- cross-phase (Phase 19)
**Owner phase:** Phase 19 (Security/Durability/Archive)
**Controlling source documents:** `GUERILLA_IMPLEMENTATION_SPEC.md` Section 31, `GUERILLA_PROTOCOL_SPEC.md` Sections 27-28
**Regeneration trigger:** Any security model change or Phase 19 completion

> **WARNING:** This document is a Phase 1 skeleton. Its content is non-normative until Phase 19.

---

## Gate B Local Authorization Baseline

Phase 8 implements a fixed local `local-owner-v1` profile for the Gate B kernel.
Only the configured workspace owner principal may perform graph reads and graph
appends through the implemented runtime helpers. Actor fields, record authority
envelopes, adapter descriptors, extensions, and payload content cannot grant or
expand effective permissions.

State-boundary checks reject undeclared operations, filesystem-root escape,
endpoint escape, namespace escape, and overlapping primary write authority.
Adapter identity descriptors can be registered for capability metadata only;
there is no adapter invocation path.

This Gate B baseline is complete and is not the full Phase 19 security model.

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
