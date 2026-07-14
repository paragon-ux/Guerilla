# GLCP Core Specification

**Status:** FROZEN -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
**Protocol version:** `0.2.0`
**Controlling schema:** `schemas/protocol_envelope.schema.json`

## Purpose

GLCP is the transport-independent Guerilla Lineage and Continuity Protocol.
Phase 3 freezes message shape, identifiers, actor attribution, error objects,
extension handling, and compatibility rules. It does not implement a client,
server, transport binding, or mutation path.

## Envelope

Every request, response, and event uses `schemas/protocol_envelope.schema.json`.

Required envelope fields are:

- `protocol: "glcp"`;
- `version: "0.2.0"`;
- `message_id` with the `gmsg_` UUIDv7 prefix;
- `message_type`;
- `operation`;
- `sent_at` in canonical UTC timestamp form;
- `correlation_id`;
- `extensions`;
- `body`.

Actor fields are attribution only. Authorization comes from the effective
principal and fixed local profile defined in AD-009.

## Responses and Errors

Response bodies use `schemas/protocol_response.schema.json`. Error objects use
`schemas/error.schema.json` and `registries/error_codes.json`.

Error objects must not include unredacted payload contents or credentials.

## Compatibility

Unknown critical extension fields are rejected. Unknown optional extension
fields may be ignored only when negotiated compatibility permits and ignoring
them does not weaken authorization, integrity, canonical bytes, graph
invariants, or derived-versus-authoritative boundaries.

Protocol extensions must not create a second mutation path, redefine GLCP
semantics, grant authority from payload content, bypass graph cycle validation,
or mark derived views authoritative.

## Operation Families

Phase 3 freezes schemas for message envelopes and common response/error
objects. Operation-specific request and response bodies remain future Phase 16
transport/client work unless already represented by graph, adapter, boundary, or
derived-view schemas.

## Phase Boundary

No transport, client, server, adapter host, graph mutation, or projection
runtime is implemented by this specification.
