# Registries

**Status:** FROZEN -- Phase 3 complete
**Owner phase:** Phase 3 (Machine Contracts)
**Contract version:** `0.2.0`

The registries define the stable enum surface used by the Phase 3 schemas and
Phase 4 fixtures.

## Published Registries

| Registry | Purpose |
|---|---|
| `node_types.json` | Eight core node types |
| `relationship_types.json` | Nine core relationship types and directions |
| `conflict_types.json` | Stable conflict classes |
| `capabilities.json` | Adapter and protocol capability values |
| `error_codes.json` | Stable error codes, classifications, retry behavior |
| `extension_namespaces.json` | Registered extension namespaces |

Extension registries cannot redefine core fields, relationship directions,
authority rules, payload safety, or derived-view authority.

No runtime implementation is provided by these registries.
