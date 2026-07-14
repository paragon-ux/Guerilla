# State Boundary Model

**Status:** FROZEN -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
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

## Continuity Rules

Boundaries state whether continuity is online, offline, or reconstructed. Stale
external revisions, ambiguous authority, identity reuse, and unknown external
outcomes remain explicit conflicts or reconciliation work rather than hidden
defaults.

## Phase Boundary

This model publishes contracts only. Runtime authorization, identity registry,
adapter enforcement, and reconciliation are later phases.
