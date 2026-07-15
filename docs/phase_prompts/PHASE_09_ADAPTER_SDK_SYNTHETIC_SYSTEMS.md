# Phase 9 -- Adapter SDK and Synthetic Systems

**Status:** LOCAL PASS -- Phase 9 implementation and local validation complete; hosted CI pending
**Owner phase:** Phase 9 (Adapter SDK/Synthetic Systems)
**Gate:** C -- Continuity MVP
**Execution date:** 2026-07-14

## Objective

Implement a provider-agnostic, trusted in-process adapter SDK, a local adapter
host, and three synthetic external systems that exercise materially different
state-continuity models without adding observation ingestion, graph
orchestration, real integrations, subprocess isolation, or transport bindings.

Phase 9 proves that one typed adapter contract can describe, observe, act,
evaluate, and reconcile across heterogeneous state models. It does not commit
continuity records to the graph.

## Permitted Scope

- `src/guerilla/adapters/`
- `tests/adapters/`
- `tests/fixtures/adapters/`
- `examples/transactional_service/`
- `examples/reconstructed_filesystem/`
- `examples/asynchronous_unknown_outcome/`
- Repository-contract test updates that permit Phase 9 adapter SDK modules while
  continuing to block Phase 10+ runtime modules.
- Documentation updates for Phase 9 evidence.

## Prohibited Scope

- Real product integrations or access to user external systems.
- Subprocess, container, remote, HTTP, socket, RPC, MCP, daemon, or marketplace
  adapter execution.
- Observation ingestion into graph records.
- External action orchestration through committed graph intent.
- Graph-backed idempotency, reconciliation engine, conflict engine, decisions,
  projections, snapshots, CLI workflows, pilots, benchmarks, archive, backup, or
  production hardening.
- Graph-core branches keyed by synthetic system type.

## Required Sources

1. `AGENTS.md`
2. `docs/ARCHITECTURE_DECISIONS.md`
3. `docs/MVP_SCOPE.md`
4. `docs/DATA_MODEL.md`
5. `docs/GRAPH_RECORD_FORMAT.md`
6. `docs/GLCP_CORE_SPEC.md`
7. `docs/ADAPTER_CONTRACT.md`
8. `docs/STATE_BOUNDARY_MODEL.md`
9. `docs/STORAGE_AND_RECOVERY.md`
10. `docs/SECURITY_MODEL.md`
11. `docs/ERROR_REGISTRY.md`
12. `docs/TEST_MATRIX.md`
13. `docs/CODEX_BUILD_PLAN.md`
14. `docs/GATE_C_ENTRY_VERIFICATION_REPORT.md`
15. `schemas/adapter_descriptor.schema.json`
16. `schemas/adapter_observe.schema.json`
17. `schemas/adapter_act.schema.json`
18. `schemas/adapter_evaluate.schema.json`
19. `schemas/adapter_reconcile.schema.json`
20. `schemas/state_boundary.schema.json`
21. `schemas/capability.schema.json`
22. `registries/capabilities.json`
23. `registries/error_codes.json`
24. `registries/extension_namespaces.json`
25. `docs/architecture/GUERILLA_CONCEPT_PAPER.md` Sections 4 and 8
26. `docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md` Sections 4.7-4.11, 13,
    31, and 36.4
27. `docs/architecture/GUERILLA_PROTOCOL_SPEC.md` Sections 9, 10, 15, 22, 26,
    27, 28, and 33
28. `docs/rationale/Note-on-Architecture.md`

## Files Expected To Change

- `src/guerilla/adapters/__init__.py`
- New Phase 9 modules under `src/guerilla/adapters/`
- New tests under `tests/adapters/`
- New fixtures under `tests/fixtures/adapters/`
- New example README files under the three synthetic-system example directories
- `tests/repository/test_repository_contract.py`
- `docs/ADAPTER_CONTRACT.md`
- `docs/TEST_MATRIX.md`
- `docs/CODEX_BUILD_PLAN.md`
- `docs/phase_prompts/README.md`
- This prompt

## Invariants

- External systems retain application-state authority.
- Adapter descriptors and payloads cannot grant authority.
- Authorization and state-boundary checks occur before adapter invocation.
- Adapter outputs are validated before they can affect later phases.
- Adapter code is trusted in-process Python, never loaded from graph payloads.
- Adapter operation requests and results are typed data, not executable shell
  text.
- `act` may call a synthetic system in Phase 9, but the runtime must not claim
  committed intent-before-action until Phase 11.
- Replay remains side-effect free and imports no adapter operation.
- Synthetic systems must share one SDK and host path.

## Ordered Tasks

1. Define Phase 9 adapter errors, enums, data models, descriptor completeness
   validation, request/result validation, and extension compatibility checks.
2. Implement one local in-process adapter host that registers configured
   adapters, validates descriptors, checks principal authorization, checks state
   boundaries, invokes one typed operation, normalizes adapter failures, and
   validates typed results.
3. Implement Synthetic System A: transactional revisioned service with
   compare-and-set mutation, monotonic revisions, queryable action status,
   native idempotency, deterministic rejection, and read-after-write consistency.
4. Implement Synthetic System B: reconstructed filesystem with content-hash
   revisions, temporary-root boundaries, non-transactional multi-file actions,
   rename/deletion, partial failure, no native rollback, and emulated
   idempotency.
5. Implement Synthetic System C: asynchronous unknown-outcome service with a
   deterministic virtual clock, accepted pending operations, delayed completion,
   duplicate submission, partially queryable history, and true unknown outcomes.
6. Add cross-adapter conformance tests proving all three systems use the same
   SDK and host path.
7. Add security and failure tests for capability escalation, boundary escape,
   unsupported capability, malformed request/result, timeout, adapter exception
   normalization, payload non-execution, and deterministic synthetic replay.
8. Regenerate Phase 9 documentation and completion evidence.

## Required Tests

- Descriptor completeness and schema compatibility.
- Duplicate adapter registration rejection.
- Unsupported capability and undeclared boundary rejection.
- Unsupported critical extension rejection and optional extension compatibility.
- Authorization denial before adapter invocation.
- State-boundary denial before adapter invocation.
- Capability escalation rejection.
- Malformed request and malformed adapter result rejection.
- Timeout and adapter exception normalization.
- One SDK/host path across all three synthetic systems.
- Transactional service revision and native idempotency behavior.
- Reconstructed filesystem root escape, content-hash revision, partial failure,
  rename, deletion, and emulated idempotency behavior.
- Asynchronous service pending, completed, duplicated, and unknown outcomes
  under deterministic virtual time.
- Payload content is returned as data and never executed.
- No Phase 10 ingestion, graph action orchestration, reconciliation engine,
  projections, snapshots, transports, or real integrations exist.

## Failure and Crash Cases

- Adapter unavailable.
- Adapter raises an exception.
- Adapter operation exceeds timeout budget.
- Adapter returns a result with mismatched adapter, boundary, or capability.
- Adapter claims a capability outside its descriptor.
- Adapter attempts access outside declared roots, endpoints, or namespaces.
- Request payload contains executable-looking text; it remains inert data.
- Synthetic system state is replayed deterministically from its own test state,
  not from the Guerilla graph.

## Documentation Regeneration

Update documentation only for Phase 9 status and evidence. Do not rewrite the
imported architecture papers. Corrections to architecture decisions require
reopening the appropriate gate.

## Exit Criteria

| Criterion | Status | Evidence |
|---|---|---|
| One SDK/host supports all three synthetic systems | PASS | `tests/adapters/test_phase9_adapter_sdk.py::test_one_host_path_supports_all_synthetic_systems` |
| Contracts and capabilities validate | PASS | `tests/adapters/test_phase9_adapter_sdk.py::test_descriptor_completeness_duplicate_registration_and_critical_extensions` |
| Authorization and boundary checks precede invocation | PASS | `tests/adapters/test_phase9_adapter_sdk.py::test_authorization_and_boundary_checks_happen_before_invocation` |
| Malformed output cannot reach graph mutation | PASS | `tests/adapters/test_phase9_adapter_sdk.py::test_malformed_result_timeout_and_exception_are_normalized` |
| Systems represent materially different continuity models | PASS | `tests/fixtures/adapters/synthetic_systems.json`; `examples/transactional_service/`; `examples/reconstructed_filesystem/`; `examples/asynchronous_unknown_outcome/` |
| No real integration or transport exists | PASS | `tests/repository/test_repository_contract.py`; `src/guerilla/adapters/` inspection |
| No Phase 10 ingestion exists | PASS | `tests/repository/test_repository_contract.py`; no observation-ingestion modules or graph-backed adapter commits added |
| Full validation and hosted CI pass | LOCAL PASS / CI PENDING | `uv lock --check`; `uv sync --frozen --extra dev`; `uv run --frozen --extra dev ruff format --check .`; `uv run --frozen --extra dev ruff check .`; `uv run --frozen --extra dev mypy src tests`; `uv run --frozen --extra dev pytest`; `uv build`; isolated wheel smoke |

## Completion Report Format

The Phase 9 completion report must include:

- Phase Result
- Delivered Artifacts
- Validation Evidence: `Command | Exit code | Result | Evidence`
- Exit-Criteria Matrix
- Invariant Audit
- External-State Audit for all three synthetic systems
- Failure and Recovery Evidence
- Scope Audit
- Blockers and Contradictions
- Git Summary
- Handoff

## Stop Conditions

Stop before Phase 10 if:

- an adapter can observe or act outside its declared boundary;
- authorization happens after invocation;
- adapter output can bypass validation;
- a synthetic system requires a graph-core special case;
- a real integration, transport, subprocess, or network service is needed;
- Phase 9 introduces graph observation ingestion, committed action intent,
  reconciliation, projections, snapshots, or CLI workflows;
- replay invokes adapters or external actions;
- tests cannot distinguish adapter failure from authorization or boundary
  failure.
