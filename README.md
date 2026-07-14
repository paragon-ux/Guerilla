# Guerilla

An authoritative causal-lineage and continuity layer for heterogeneous systems.

**Current status:** Gate B in progress. Phases 1-8 are complete: contracts are
frozen, deterministic codec/config/identifier/hash primitives exist, the local
append store/replay path is implemented, DAG integrity plus a rebuildable
SQLite query index exist, and local authority/boundary registries are in place.
No adapter runtime, projection, or transport exists yet.

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
| B — Kernel Ready | 5–8 | Authoritative storage, replay, DAG integrity, index, authority, identity | Phase 8 complete; Gate B checklist next |
| C — Continuity MVP | 9–15 | Synthetic adapters, observations, safe actions, reconciliation, projections, snapshots, CLI | Blocked by Gate B |
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

- No adapter runtime, projection engine, or transport exists yet. The
  implemented runtime surface is limited to Phase 5 primitives, Phase 6 local
  append storage/replay, Phase 7 DAG/index/query behavior, and Phase 8 local
  authority/boundary registries.
- Schemas, registries, conformance fixtures, and Phase 5 primitives are frozen
  for later Gate B phases.
- No adapters, integrations, benchmarks, or empirical results are available.
- The architecture papers (v0.2.0-draft) are the current normative specification.

---

## Further Reading

- [Development setup and commands](README_DEV.md)
- [AGENTS.md](AGENTS.md) — agent control surface and invariants
- [Architecture papers](docs/architecture/) — normative concept, implementation, protocol, and snapshot specifications
- [Build workflow](docs/GUERILLA_WORKFLOW_CURRENT.md) — complete 4-stage, 22-phase build plan
- [Related work](docs/architecture/RELATED_WORK.md) — comparative positioning against provenance, workflow, and agent systems
