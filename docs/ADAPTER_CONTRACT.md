# Adapter Contract

**Status:** FROZEN -- Phase 3 complete; Gate C Phase 9-12 adapter, observation, action, reconciliation, and conflict surfaces implemented
**Owner phase:** Phase 3 (Machine Contracts), Phase 9 (Adapter SDK/Synthetic Systems), Phase 10 (Observation Ingestion), Phase 11 (Action Intent and Idempotency), Phase 12 (Reconciliation and Conflicts)
**Controlling schema:** `schemas/adapter_descriptor.schema.json`

## Purpose

Adapters are trusted integration components that translate between external
systems and Guerilla contracts. Phase 3 froze descriptor shape and capability
vocabulary. Phase 9 implements the trusted in-process Python SDK, host, and
synthetic systems that exercise the descriptor and operation contracts without
adding graph ingestion, transports, subprocess isolation, or real integrations.
Phase 10 implements observe-only ingestion from that host into authoritative
graph records. Phase 11 implements graph-backed action intent, invocation
start, result recording, idempotency replay/conflict behavior, and optional
after-state observation. Phase 12 implements reconciliation events,
missing-lineage recovery, explicit conflict records, and append-only decisions.

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

`adapter_act` requires an `intent_node_id` so the runtime cannot model an
external mutation without a committed intent. Phase 11 provides the
graph-backed lifecycle for production action orchestration. Phase 9 direct
`act` calls remain adapter SDK conformance tests only and are not the
authoritative action path.

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

## Phase 10 Observation Ingestion

Phase 10 adds `src/guerilla/observability/ingestion.py`, an observe-only
ingestion path that:

- validates `adapter.observe` request contracts;
- uses the Phase 9 host for authorization, state-boundary checks, adapter
  invocation, and result validation;
- rejects missing provenance or missing external identity;
- normalizes operation, event, artifact/external revision, and edge records;
- preserves external system, adapter, boundary, external identity, external
  revision, effective time, receipt time, graph commit time, correlation,
  causation, authority, provenance, payload retention/redaction, freshness, and
  consistency metadata;
- appends all normalized records in one authoritative graph transaction.

Observation ingestion invokes only `observe`. It does not call `act`, create
action intent, retry, infer external acceptance, reconcile, project, snapshot,
or mutate external state.

## Phase 11 Action Orchestration

Phase 11 adds `src/guerilla/orchestration/actions.py`, an action path that:

- validates `adapter.act` request contracts, principal authority, adapter
  capability, and state-boundary scope before committing intent;
- commits operation and action-request event records before adapter invocation;
- verifies the committed intent from authoritative replay before crossing into
  `act`;
- commits invocation-start event records before adapter invocation;
- passes structured arguments, expected external revision, idempotency context,
  correlation, boundary, and authorization context to the Phase 9 host;
- commits action-result event records that preserve external classification,
  external revision or action identifiers, adapter evidence, retry
  classification, warnings, and limitations;
- reconstructs idempotency truth from graph replay rather than from SQLite,
  adapter-native state, or runtime memory;
- replays same-key/same-content requests from prior committed graph results;
- rejects same-key/different-content requests with `idempotency_conflict`;
- treats prior invocation without a committed result as `outcome_unknown` and
  does not retry blindly;
- optionally schedules after-state observation through the Phase 10 ingestor
  without fabricating external state.

Action orchestration invokes only `act` and optional bounded `observe`.
It does not call `reconcile`, resolve conflicts, project, snapshot, transport,
or mutate external systems outside declared adapter actions.

## Phase 12 Reconciliation and Conflicts

Phase 12 adds `src/guerilla/reconciliation/engine.py` and
`src/guerilla/conflicts/engine.py`.

The reconciliation engine:

- loads committed Phase 11 intent, invocation, and result evidence from
  authoritative graph replay;
- authorizes and validates `adapter.reconcile` through the same Phase 9 host;
- invokes `reconcile` only after capability and boundary checks pass;
- commits reconciliation events as new event nodes and never rewrites original
  intent, invocation, or result records;
- recovers missing action-result lineage by appending a recovered result event
  with Phase 11 idempotency metadata, without fabricating the original result
  timestamp;
- records explicit conflicts for unknown outcomes, unsupported reconciliation,
  duplicate attempts, stale external revisions, and incomplete lineage;
- optionally triggers after-state observation through the Phase 10 ingestor.

The conflict engine:

- appends conflict nodes with canonical registry `conflict_type` values and
  Phase 12-specific `conflict_reason` metadata;
- records subject, evidence, authority, severity, status, detection time,
  policy version, required resolution class, limitations, and details;
- appends decisions and `resolved_by` lineage without deleting or rewriting
  conflicts;
- optionally appends continuation operation records that depend on the
  resolution decision.

Phase 12 does not project, snapshot, transport, isolate subprocess adapters,
run real integrations, or implement Gate D behavior.

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

Implemented in Phase 9-12:

- trusted configured in-process adapter loading and invocation;
- descriptor and capability validation;
- synthetic observe, act, evaluate, and reconcile calls against three local
  synthetic systems;
- observe-only normalization into authoritative graph records through one Gate B
  append transaction;
- graph-backed intent-before-action, invocation-start, result recording,
  idempotency replay/conflict behavior, and optional after-state observation.
- reconciliation events, missing-lineage recovery, explicit conflict records,
  append-only decisions, and resolution lineage.

Still deferred:

- projections, snapshots, CLI workflows, transports, subprocess/container
  isolation, network services, real integrations, pilots, archive, backup, and
  production hardening.
