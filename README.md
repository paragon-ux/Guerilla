# Guerilla

An authoritative causal-lineage and continuity layer for heterogeneous systems.

**Current status:** Gate C in progress. Phases 1-10 are complete:
contracts are frozen, the local graph kernel is implemented, the synthetic
adapter SDK exists, and observe-only ingestion records bounded external facts
into the authoritative graph. Action intent/idempotency, reconciliation,
projections, snapshots, CLI workflows, transport, and real integrations remain
future phases.

---

## What Guerilla Is

Guerilla maintains one logically authoritative, append-only cross-system causal-lineage and continuity graph while leaving application-state authority with integrated external systems.

- **Guerilla owns:** graph records, graph identity, graph revisions, lineage assertions, conflicts, decisions, snapshots, and derived-view provenance.
- **External systems retain:** their application state, native revisions, native identifiers, and mutation semantics.
- **Adapters** translate between external state models and the Guerilla graph without transferring general ownership of external state.

---

## Authority and State-Boundary Distinction

| Guerilla owns | Guerilla references | Guerilla derives |
|---|---|---|
| Immutable nodes and edges | External database records | Graph heads and dependency paths |
| Graph revisions and commit hashes | Service resources | Manifests and snapshots |
| Authority and state-boundary declarations | Source-control history | Conflict and progress views |
| Actor and provenance metadata | Event-log positions | Diffs and status projections |
| Operation intent and result records | Build and test reports | Resume contexts |
| Conflict evidence and resolution lineage | Documents and datasets | Audit and provenance reports |

Guerilla does **not** own: canonical application content, external database transactions, filesystem semantics, source-control history, business-rule validation, external authorization decisions, or the complete state of an integrated system.

---

## Build Gates

| Gate | Phases | Meaning | Status |
|---|---|---|---|
| A — Contract Ready | 1–4 | Architecture decisions, schemas, registries, and fixtures are frozen | Complete |
| B — Kernel Ready | 5–8 | Authoritative storage, replay, DAG integrity, index, authority, identity | Complete |
| C — Continuity MVP | 9–15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI | In progress; Phase 10 complete locally |
| D — External Compatible | 16–19 | Reference transport, isolated adapters, parity, security, durability, archive | Blocked by Gate C |
| E — Research Validated | 20–22 | Real heterogeneous pilots, benchmark evidence, reproducible release | Blocked by Gate D |

---

## Quick Start

```bash
# Clone and install
git clone <repo-url> && cd Guerilla
uv lock --check
uv sync --frozen --extra dev

# Check version
uv run guerilla --version
uv run python -c "import guerilla; print(guerilla.__version__)"

# Run tests
uv run pytest
```

---

## Non-Claims

- No action orchestration, reconciliation engine, projection engine, snapshot
  runtime, production CLI workflow, or transport exists yet. The implemented
  runtime surface is limited to Gate B kernel behavior, Phase 9 trusted
  in-process synthetic adapters, and Phase 10 observe-only graph ingestion.
- Schemas, registries, conformance fixtures, Gate B kernel primitives, and
  Phase 9-10 continuity primitives are current for Phase 11 entry.
- No adapters, integrations, benchmarks, or empirical results are available.
- The architecture papers (v0.2.0-draft) are the current normative specification.

---

## Further Reading

- [Development setup and commands](README_DEV.md)
- [AGENTS.md](AGENTS.md) — agent control surface and invariants
- [Architecture papers](docs/architecture/) — normative concept, implementation, protocol, and snapshot specifications
- [Build workflow](docs/GUERILLA_WORKFLOW_CURRENT.md) — complete 4-stage, 22-phase build plan
- [Related work](docs/architecture/RELATED_WORK.md) — comparative positioning against provenance, workflow, and agent systems
