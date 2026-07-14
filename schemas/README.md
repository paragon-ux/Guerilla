# Schemas

**Status:** FROZEN -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
**Contract version:** `0.2.0`
**Draft:** JSON Schema Draft 2020-12

The schema set encodes the frozen Phase 2 decisions for canonical JSON,
UUIDv7-prefixed identifiers, timestamps, integer bounds, authority envelopes,
state boundaries, payload references, extension handling, graph record types,
protocol envelopes, and derived-versus-authoritative distinctions.

## Published Schemas

| Schema | Purpose |
|---|---|
| `common.schema.json` | Shared identifiers, timestamps, hashes, enums, safe JSON, extensions |
| `actor.schema.json` | Actor attribution; not an authority grant |
| `authority.schema.json` | Local authorization profile and external authority envelope |
| `external_identity.schema.json` | Authority-scoped external identity tuple |
| `payload_ref.schema.json` | Payload retention, redaction, hash, and external references |
| `provenance.schema.json` | Source, causation, observation, and external identity metadata |
| `node.schema.json` | Immutable authoritative node record |
| `edge.schema.json` | Immutable authoritative edge record |
| `transaction_begin.schema.json` | Transaction begin frame |
| `transaction_commit.schema.json` | Final commit-record frame and commit hash |
| `graph_header.schema.json` | Authoritative graph header |
| `archive_seal.schema.json` | Archive segment seal and integrity hash |
| `state_boundary.schema.json` | External state-boundary declaration |
| `capability.schema.json` | Adapter capability declaration |
| `adapter_descriptor.schema.json` | Trusted in-process MVP adapter descriptor |
| `protocol_envelope.schema.json` | GLCP message envelope |
| `protocol_response.schema.json` | GLCP response body |
| `error.schema.json` | Stable machine-readable error object |
| `extension_namespace.schema.json` | Registered extension namespace metadata |
| `derived_projection.schema.json` | Non-authoritative projection descriptor |

## Compatibility Rules

Unknown critical extension fields are rejected. Unknown optional extension fields
may be ignored only under negotiated compatibility rules and may not redefine
core semantics, grant authority, bypass DAG validation, or make derived data
authoritative.

No runtime implementation is provided by these schemas.
