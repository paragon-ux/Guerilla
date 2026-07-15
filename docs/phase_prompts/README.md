# Phase Prompts

**Status:** Gate C in progress; Phase 11 PASS; Phase 12 pending
**Owner phase:** Cross-phase; each phase prompt is owned by its phase

---

## Purpose

This directory contains the ordered phase execution prompts that drive Guerilla's build sequence. Each prompt defines exact scope, invariants, tasks, tests, exit criteria, and evidence requirements.

---

## Rules

- **No phase or gate skipping.** Every phase must complete its exit criteria before the next phase begins.
- **Gate A (Contract Ready) must complete before Gate B (Kernel Ready).** No kernel code before contracts freeze.
- **Prompts are regenerated or updated when their owning phase changes scope.**
- **Completion claims require linked evidence.** File existence is not sufficient.

---

## Complete Prompt Inventory

| Number | Prompt file | Gate | Status |
|---|---|---|---|
| 1 | `Guerilla-Kickoff-Prompt.md` (Phase 1) | A | PASS |
| 2 | `PHASE_02_ARCHITECTURE_DECISIONS.md` | A | PASS |
| 3 | `PHASE_03_MACHINE_CONTRACTS.md` | A | PASS |
| 4 | `PHASE_04_CONFORMANCE_FIXTURES.md` | A | PASS |
| 5 | `PHASE_05_CODEC_CONFIG_IDENTIFIERS.md` | B | PASS |
| 6 | `PHASE_06_APPEND_STORE_TRANSACTIONS_REPLAY.md` | B | PASS |
| 7 | `PHASE_07_DAG_INTEGRITY_INDEX_QUERY.md` | B | PASS |
| 8 | `PHASE_08_AUTHORITY_IDENTITY_BOUNDARIES.md` | B | PASS |
| 9 | `PHASE_09_ADAPTER_SDK_SYNTHETIC_SYSTEMS.md` | C | PASS |
| 10 | `PHASE_10_OBSERVATION_INGESTION.md` | C | PASS |
| 11 | `PHASE_11_ACTION_INTENT_IDEMPOTENCY.md` | C | PASS |
| 12 | `PHASE_12_RECONCILIATION_CONFLICTS.md` | C | PENDING |
| 13 | `PHASE_13_PROJECTIONS_MANIFEST_DIFF.md` | C | PENDING |
| 14 | `PHASE_14_SNAPSHOT_RESUME.md` | C | PENDING |
| 15 | `PHASE_15_INTERNAL_CLI_E2E_SMOKE.md` | C | PENDING |
| FINAL | `FINAL_INTERNAL_MVP_CHECKLIST.md` | C | PENDING |
| 16 | `PHASE_16_GLCP_REFERENCE_CLIENT_SERVER.md` | D | PENDING |
| 17 | `PHASE_17_SUBPROCESS_ADAPTER_HOST.md` | D | PENDING |
| 18 | `PHASE_18_TRANSPORT_PARITY_ROBUSTNESS.md` | D | PENDING |
| 19 | `PHASE_19_SECURITY_DURABILITY_ARCHIVE.md` | D | PENDING |
| FINAL | `FINAL_EXTERNAL_COMPATIBILITY_CHECKLIST.md` | D | PENDING |
| 20 | `PHASE_20_HETEROGENEOUS_PILOTS.md` | E | PENDING |
| 21 | `PHASE_21_BENCHMARK_EVALUATION.md` | E | PENDING |
| 22 | `PHASE_22_RELEASE_RESEARCH_PACKAGE.md` | E | PENDING |
| FINAL | `FINAL_RELEASE_CHECKLIST.md` | E | PENDING |

---

## Required Content of Every Phase Prompt

Every phase prompt must contain:

1. Phase objective
2. Permitted scope
3. Prohibited scope
4. Required source documents
5. Files expected to change
6. Invariants that cannot change
7. Implementation tasks in dependency order
8. Required unit, integration, and conformance tests
9. Failure and crash cases
10. Documentation regeneration requirements
11. Exact exit criteria
12. Completion report format
13. Stop conditions when a prerequisite is missing or contradictory
