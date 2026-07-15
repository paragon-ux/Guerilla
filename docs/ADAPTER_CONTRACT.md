# Adapter Contract

**Status:** FROZEN -- Phase 3 complete; Gate C Phase 9 adapter SDK implemented
**Owner phase:** Phase 3 (Machine Contracts), Phase 9 (Adapter SDK/Synthetic Systems)
**Controlling schema:** `schemas/adapter_descriptor.schema.json`

## Purpose

Adapters are trusted integration components that translate between external
systems and Guerilla contracts. Phase 3 froze descriptor shape and capability
vocabulary. Phase 9 implements the trusted in-process Python SDK, host, and
synthetic systems that exercise the descriptor and operation contracts without
adding graph ingestion, transports, subprocess isolation, or real integrations.

## Descriptor

Adapter descriptors must declare:

- adapter id and external system id;
- semantic version;
- MVP trust model `trusted_in_process_python`;
- state boundaries;
- capabilities;
- authentication requirements;
- limitations;
- extensions.

The descriptor cannot expand authority. Authority comes from configuration,
state-boundary declarations, and the local authorization profile.

## Operation Contracts

Gate A entry closure freezes typed data contracts for adapter operation
requests:

- `schemas/adapter_observe.schema.json`
- `schemas/adapter_act.schema.json`
- `schemas/adapter_evaluate.schema.json`
- `schemas/adapter_reconcile.schema.json`

`adapter_act` requires an `intent_node_id` so later runtime phases cannot model
an external mutation without a committed intent. Phase 9 does not yet provide
the Phase 11 graph-backed intent lifecycle; Phase 9 `act` calls are limited to
trusted synthetic systems and are not recorded as authoritative graph
transactions.

## Phase 9 Runtime Surface

Phase 9 adds:

- `src/guerilla/adapters/types.py` typed request, result, idempotency context,
  and adapter protocol objects;
- `src/guerilla/adapters/host.py` local in-process host registration,
  descriptor validation, authorization checks, state-boundary checks,
  timeout checks, result validation, and adapter exception normalization;
- `src/guerilla/adapters/synthetic.py` three synthetic systems:
  transactional revisioned service, reconstructed filesystem, and asynchronous
  unknown-outcome service.

Every Phase 9 operation request carries workspace, adapter, external-system,
state-boundary, operation, principal, actor, authority, contract-version,
deadline/timeout, capability, and typed request data. Mutating requests carry an
idempotency context. Every result carries adapter, boundary, classification,
external revision or identity when available, evidence, retry classification,
warnings, limitations, payload metadata, and typed data.

The host validates the frozen descriptor schema before registration. Runtime
descriptor completeness additionally requires declared read consistency, write
behavior, event ordering, concurrency, conflict handling, replay support,
snapshot support, identity stability, lineage completeness, idempotency,
schemas, limitations, and mutating actions where applicable.

The host checks authorization and state boundaries before invocation. Adapter
outputs are validated after invocation and before they can be used by later
phases. Phase 9 returns typed results only; it does not commit graph records.

## Capabilities

Capability values are registered in `registries/capabilities.json` and encoded
by `schemas/capability.schema.json`. Mutating capability `act` is allowed only
inside declared state boundaries and later runtime phases must record intent
before invocation.

## State Boundaries

Each descriptor embeds or references state-boundary declarations governed by
`schemas/state_boundary.schema.json`. External systems retain application-state
authority for those boundaries.

## Phase Boundary

Implemented in Phase 9:

- trusted configured in-process adapter loading and invocation;
- descriptor and capability validation;
- synthetic observe, act, evaluate, and reconcile calls against three local
  synthetic systems.

Still deferred:

- observation ingestion into authoritative graph records;
- graph-backed intent-before-action and idempotency;
- reconciliation engine, conflict engine, and decisions;
- projections, snapshots, CLI workflows, transports, subprocess/container
  isolation, network services, real integrations, pilots, archive, backup, and
  production hardening.
