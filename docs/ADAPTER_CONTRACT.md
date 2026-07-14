# Adapter Contract

**Status:** FROZEN -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
**Controlling schema:** `schemas/adapter_descriptor.schema.json`

## Purpose

Adapters are trusted integration components that translate between external
systems and Guerilla contracts. Phase 3 freezes descriptor shape and capability
vocabulary only. Adapter interfaces and synthetic adapters are later phases.

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
requests without implementing adapter execution:

- `schemas/adapter_observe.schema.json`
- `schemas/adapter_act.schema.json`
- `schemas/adapter_evaluate.schema.json`
- `schemas/adapter_reconcile.schema.json`

`adapter_act` requires an `intent_node_id` so later runtime phases cannot model
an external mutation without a committed intent. These schemas are contract
surfaces only; loading, invoking, observing, acting, evaluating, and reconciling
remain later phases.

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

No adapter loading, invocation, subprocess/container isolation, network
transport, observation ingestion, action execution, or reconciliation runtime is
implemented in Phase 3.
