# State Boundary Model

**Status:** Gate B complete -- Phase 8 local enforcement implemented
**Owner phase:** Phase 3 (Machine Contracts), Phase 8 (Authority/Identity/Boundaries)
**Controlling schema:** `schemas/state_boundary.schema.json`

## Purpose

A state boundary declares where an external system remains the system of record
and how Guerilla may observe, reference, request mutation, and preserve lineage
without taking over application-state authority.

## Required Boundary Fields

Every state boundary declares:

- `state_boundary_id`;
- `system_id`;
- human-readable name;
- `system_of_record: true`;
- continuity mode: `online`, `offline`, or `reconstructed`;
- ownership: external application state or Guerilla lineage only;
- permitted operations;
- permitted roots, endpoints, or resource namespaces when applicable;
- lineage crossing behavior;
- conflict behavior;
- extensions.

## Authority Rules

Actor fields, adapter descriptors, payload content, and extension metadata do
not grant authority. Access outside a declared boundary is rejected. Recording a
reference to an external object does not transfer ownership of that object.

Phase 8 implements the fixed local `local-owner-v1` authorization profile and
state-boundary checks for permitted operations, filesystem roots, endpoints, and
resource namespaces. Overlapping read declarations are allowed; overlapping
primary write authority for the same system and resource scope is rejected as
ambiguous authority.

## Continuity Rules

Boundaries state whether continuity is online, offline, or reconstructed. Stale
external revisions, ambiguous authority, identity reuse, and unknown external
outcomes remain explicit conflicts or reconciliation work rather than hidden
defaults.

## Phase Boundary

This model now has Phase 8 local runtime enforcement for authorization,
boundaries, adapter identity registration, and external identity lifecycle
metadata. Adapter invocation, reconciliation, projection generation, transports,
and broader Phase 19 security hardening remain later phases.
