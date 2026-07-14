# Schemas

**Status:** FROZEN -- Gate A entry closure complete
**Owner phase:** Phase 3 (Machine Contracts), updated by Gate A entry closure
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
| `payload_reference.schema.json` | Canonical workflow-surface wrapper for payload references |
| `provenance.schema.json` | Source, causation, observation, and external identity metadata |
| `node.schema.json` | Immutable authoritative node record |
| `conflict.schema.json` | Canonical conflict-node wrapper |
| `snapshot.schema.json` | Canonical snapshot-node wrapper |
| `edge.schema.json` | Immutable authoritative edge record |
| `transaction.schema.json` | Canonical transaction wrapper over begin, members, and commit |
| `transaction_begin.schema.json` | Transaction begin frame |
| `transaction_commit.schema.json` | Final commit-record frame and commit hash |
| `commit.schema.json` | Canonical commit wrapper over the final commit frame |
| `graph_header.schema.json` | Authoritative graph header |
| `archive_seal.schema.json` | Archive segment seal and integrity hash |
| `state_boundary.schema.json` | External state-boundary declaration |
| `capability.schema.json` | Adapter capability declaration |
| `adapter_descriptor.schema.json` | Trusted in-process MVP adapter descriptor |
| `adapter_observe.schema.json` | Typed observe-operation contract; no adapter execution |
| `adapter_act.schema.json` | Typed act-operation contract requiring committed intent; no adapter execution |
| `adapter_evaluate.schema.json` | Typed evaluate-operation contract; no adapter execution |
| `adapter_reconcile.schema.json` | Typed reconcile-operation contract; no adapter execution |
| `protocol_envelope.schema.json` | GLCP message envelope |
| `protocol_request.schema.json` | Canonical request-envelope wrapper |
| `protocol_response.schema.json` | GLCP response body |
| `error.schema.json` | Stable machine-readable error object |
| `protocol_error.schema.json` | Canonical protocol-error wrapper |
| `extension_namespace.schema.json` | Registered extension namespace metadata |
| `derived_projection.schema.json` | Non-authoritative projection descriptor |
| `projection_metadata.schema.json` | Canonical workflow-surface wrapper for projection metadata |

The workflow-surface inventory is machine-readable at
`docs/contract_inventory.json`. Tests fail if a required surface is missing,
duplicated, unowned, or lacks valid/invalid fixtures.

## Compatibility Rules

Unknown critical extension fields are rejected. Unknown optional extension fields
may be ignored only under negotiated compatibility rules and may not redefine
core semantics, grant authority, bypass DAG validation, or make derived data
authoritative.

No runtime implementation is provided by these schemas.
