"""Repository-contract tests for Phase 1 artifact boundary enforcement.

These tests verify structural properties, not runtime behavior.
"""

import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ── Top-level required files ──────────────────────────────────────────


def test_agents_md_exists():
    assert (REPO_ROOT / "AGENTS.md").is_file(), "AGENTS.md is missing"


def test_readme_exists():
    assert (REPO_ROOT / "README.md").is_file(), "README.md is missing"


def test_readme_dev_exists():
    assert (REPO_ROOT / "README_DEV.md").is_file(), "README_DEV.md is missing"


def test_pyproject_toml_exists():
    assert (REPO_ROOT / "pyproject.toml").is_file(), "pyproject.toml is missing"


def test_gitignore_exists():
    assert (REPO_ROOT / ".gitignore").is_file(), ".gitignore is missing"


def test_uv_lock_exists():
    assert (REPO_ROOT / "uv.lock").is_file(), "uv.lock is missing"


def test_uv_lock_not_ignored():
    ignored_entries = {
        line.strip()
        for line in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert "uv.lock" not in ignored_entries, "uv.lock must be committed, not ignored"


def test_editorconfig_exists():
    assert (REPO_ROOT / ".editorconfig").is_file(), ".editorconfig is missing"


def test_ci_workflow_exists():
    assert (REPO_ROOT / ".github" / "workflows" / "ci.yml").is_file(), "CI workflow is missing"


def test_ci_uses_locked_install_and_isolated_wheel_smoke():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "uv lock --check" in workflow
    assert "uv sync --frozen --extra dev" in workflow
    assert "uv run --frozen --extra dev --python ${{ matrix.python-version }}" in workflow
    assert "uv venv" in workflow
    assert "uv pip install --python" in workflow
    assert "RUNNER_TEMP" in workflow
    assert "uv run pip install" not in workflow


# ── Skills ────────────────────────────────────────────────────────────

SKILL_NAMES = [
    "guerilla-contracts-modeling",
    "guerilla-graph-kernel-storage",
    "guerilla-adapter-continuity-reconciliation",
    "guerilla-projections-snapshot-resume",
    "guerilla-testing-security-evaluation",
]

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
MANIFEST_ROW_PATTERN = re.compile(
    r"^\| `(?P<original>[^`]+)` \| `(?P<path>[^`]+)` \| "
    r"`(?P<digest>[0-9a-f]{64})` \|"
)


def _parse_skill_frontmatter(skill_path: Path) -> dict[str, str]:
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0] == "---", f"{skill_path} must start with YAML frontmatter"
    try:
        end_index = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError(f"{skill_path} frontmatter is not closed") from exc

    metadata: dict[str, str] = {}
    for line in lines[1:end_index]:
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        assert separator, f"{skill_path} frontmatter line is not key/value: {line!r}"
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def _architecture_manifest_rows() -> list[tuple[str, str]]:
    manifest = (REPO_ROOT / "docs" / "architecture" / "README.md").read_text(encoding="utf-8")
    rows: list[tuple[str, str]] = []
    for line in manifest.splitlines():
        match = MANIFEST_ROW_PATTERN.match(line)
        if match:
            rows.append((match.group("path"), match.group("digest")))
    return rows


def _read_line_normalized_bytes(path: Path) -> bytes:
    content = path.read_bytes()
    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def test_all_skills_exist():
    skills_dir = REPO_ROOT / ".agents" / "skills"
    assert skills_dir.is_dir(), ".agents/skills/ directory is missing"
    for name in SKILL_NAMES:
        skill_path = skills_dir / name / "SKILL.md"
        assert skill_path.is_file(), f"Skill {name}/SKILL.md is missing"


def test_all_skills_non_empty():
    skills_dir = REPO_ROOT / ".agents" / "skills"
    for name in SKILL_NAMES:
        skill_path = skills_dir / name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert len(content) > 500, f"Skill {name} appears too short ({len(content)} bytes)"


def test_all_skills_have_valid_frontmatter():
    skills_dir = REPO_ROOT / ".agents" / "skills"
    for name in SKILL_NAMES:
        skill_path = skills_dir / name / "SKILL.md"
        metadata = _parse_skill_frontmatter(skill_path)
        assert metadata.get("name") == name, f"Skill {name} frontmatter name mismatch"
        assert SKILL_NAME_PATTERN.match(name), f"Skill name {name} violates Agent Skills format"
        assert "--" not in name, f"Skill name {name} must not contain consecutive hyphens"
        description = metadata.get("description", "")
        assert 1 <= len(description) <= 1024, f"Skill {name} description length is invalid"


# ── Build-document skeletons ──────────────────────────────────────────

REQUIRED_SKELETONS = [
    "ARCHITECTURE_DECISIONS.md",
    "GLOSSARY.md",
    "MVP_SCOPE.md",
    "DATA_MODEL.md",
    "GRAPH_RECORD_FORMAT.md",
    "GLCP_CORE_SPEC.md",
    "ADAPTER_CONTRACT.md",
    "STATE_BOUNDARY_MODEL.md",
    "STORAGE_AND_RECOVERY.md",
    "PROJECTION_SPEC.md",
    "SECURITY_MODEL.md",
    "ERROR_REGISTRY.md",
    "TEST_MATRIX.md",
    "CODEX_BUILD_PLAN.md",
    "EVALUATION_PLAN.md",
]

FROZEN_DOCS = {
    "ARCHITECTURE_DECISIONS.md",
    "GLOSSARY.md",
    "MVP_SCOPE.md",
    "DATA_MODEL.md",
    "GRAPH_RECORD_FORMAT.md",
    "GLCP_CORE_SPEC.md",
    "ADAPTER_CONTRACT.md",
    "ERROR_REGISTRY.md",
}

GATE_STATUS_DOCS = {
    "CODEX_BUILD_PLAN.md",
    "STATE_BOUNDARY_MODEL.md",
    "STORAGE_AND_RECOVERY.md",
    "TEST_MATRIX.md",
}


def test_all_skeletons_exist():
    docs_dir = REPO_ROOT / "docs"
    for name in REQUIRED_SKELETONS:
        path = docs_dir / name
        assert path.is_file(), f"Build skeleton {name} is missing"


def test_skeletons_have_status():
    """Every skeleton must declare its status in the first 50 lines."""
    docs_dir = REPO_ROOT / "docs"
    for name in REQUIRED_SKELETONS:
        path = docs_dir / name
        content = path.read_text(encoding="utf-8")
        first_lines = "\n".join(content.splitlines()[:50])
        assert "PLACEHOLDER" in first_lines or "Status" in first_lines, (
            f"Skeleton {name} does not declare status"
        )


# ── Architecture sources ──────────────────────────────────────────────

ARCH_SOURCES = [
    "docs/architecture/GUERILLA_CONCEPT_PAPER.md",
    "docs/architecture/GUERILLA_IMPLEMENTATION_SPEC.md",
    "docs/architecture/GUERILLA_PROTOCOL_SPEC.md",
    "docs/architecture/GUERILLA_SNAPSHOT.md",
    "docs/architecture/CURRENT_STATUS_MATRIX.md",
    "docs/architecture/RELATED_WORK.md",
]


def test_architecture_sources_present():
    for rel_path in ARCH_SOURCES:
        path = REPO_ROOT / rel_path
        assert path.is_file(), f"Architecture source {rel_path} is missing"


def test_rationale_note_present():
    path = REPO_ROOT / "docs" / "rationale" / "Note-on-Architecture.md"
    assert path.is_file(), "Rationale note is missing"


def test_architecture_readme_exists():
    path = REPO_ROOT / "docs" / "architecture" / "README.md"
    assert path.is_file(), "Architecture source manifest is missing"


def test_source_digests_recorded():
    """The architecture README must contain SHA-256 digests."""
    manifest = (REPO_ROOT / "docs" / "architecture" / "README.md").read_text(encoding="utf-8")
    digests = re.findall(r"[0-9a-f]{64}", manifest)
    assert len(digests) >= 7, f"Expected at least 7 SHA-256 digests, found {len(digests)}"


def test_source_digests_match_files():
    """The manifest must match LF-normalized bytes of every listed source."""
    rows = _architecture_manifest_rows()
    assert len(rows) >= 7, f"Expected at least 7 architecture manifest rows, found {len(rows)}"
    for rel_path, expected_digest in rows:
        path = REPO_ROOT / rel_path
        assert path.is_file(), f"Manifest source path is missing: {rel_path}"
        actual_digest = hashlib.sha256(_read_line_normalized_bytes(path)).hexdigest()
        assert actual_digest == expected_digest, (
            f"SHA-256 mismatch for {rel_path}: expected {expected_digest}, got {actual_digest}"
        )


# ── Schema and registry directories ───────────────────────────────────


def test_schemas_readme_exists():
    assert (REPO_ROOT / "schemas" / "README.md").is_file(), "schemas/README.md missing"


def test_registries_readme_exists():
    assert (REPO_ROOT / "registries" / "README.md").is_file(), "registries/README.md missing"


def test_phase3_schema_inventory_is_frozen():
    """schemas/ contains exactly the frozen Gate A machine contracts."""
    schema_dir = REPO_ROOT / "schemas"
    inventory = json.loads(
        (REPO_ROOT / "docs" / "contract_inventory.json").read_text(encoding="utf-8")
    )
    expected = {
        "actor.schema.json",
        "archive_seal.schema.json",
        "capability.schema.json",
        "common.schema.json",
        "extension_namespace.schema.json",
        "external_identity.schema.json",
        "provenance.schema.json",
    }
    for surface in inventory["surfaces"]:
        expected.add(Path(surface["canonical_schema_path"]).name)
        expected.update(Path(alias).name for alias in surface["aliases"])
    json_files = {path.name for path in schema_dir.glob("*.schema.json")}
    assert json_files == expected


def test_phase3_registry_inventory_is_frozen():
    """registries/ contains exactly the frozen Phase 3 registries."""
    registry_dir = REPO_ROOT / "registries"
    json_files = {path.name for path in registry_dir.glob("*.json")}
    assert json_files == {
        "node_types.json",
        "relationship_types.json",
        "conflict_types.json",
        "capabilities.json",
        "error_codes.json",
        "extension_namespaces.json",
    }


# ── Package directories ───────────────────────────────────────────────

REQUIRED_PACKAGES = [
    "src/guerilla",
    "src/guerilla/config",
    "src/guerilla/contracts",
    "src/guerilla/codec",
    "src/guerilla/protocol",
    "src/guerilla/graph",
    "src/guerilla/storage",
    "src/guerilla/payloads",
    "src/guerilla/index",
    "src/guerilla/authority",
    "src/guerilla/identity",
    "src/guerilla/adapters",
    "src/guerilla/orchestration",
    "src/guerilla/reconciliation",
    "src/guerilla/conflicts",
    "src/guerilla/projections",
    "src/guerilla/cli",
    "src/guerilla/observability",
]


def test_all_package_directories_exist():
    for rel_path in REQUIRED_PACKAGES:
        path = REPO_ROOT / rel_path
        assert path.is_dir(), f"Package directory {rel_path} is missing"


def test_py_typed_marker_exists():
    assert (REPO_ROOT / "src" / "guerilla" / "py.typed").is_file(), "py.typed marker missing"


# ── Prohibited Phase 2+ scaffolds ─────────────────────────────────────

PROHIBITED_PATTERNS = [
    "src/guerilla/**/*.py",  # only __init__.py and cli/main.py permitted
]


def test_no_prohibited_runtime_modules():
    """Phase 12 permits reconciliation and conflict modules but no Phase 13+ runtime modules."""
    src = REPO_ROOT / "src" / "guerilla"
    py_files = list(src.rglob("*.py"))
    allowed_subtrees = {
        "src/guerilla/codec",
        "src/guerilla/config",
        "src/guerilla/contracts",
        "src/guerilla/protocol",
        "src/guerilla/payloads",
        "src/guerilla/identity",
        "src/guerilla/storage",
        "src/guerilla/graph",
        "src/guerilla/index",
        "src/guerilla/authority",
        "src/guerilla/adapters",
        "src/guerilla/observability",
        "src/guerilla/orchestration",
        "src/guerilla/reconciliation",
        "src/guerilla/conflicts",
    }
    for py_file in py_files:
        rel = py_file.relative_to(REPO_ROOT)
        rel_posix = rel.as_posix()
        name = py_file.name
        if any(rel_posix.startswith(subtree) for subtree in allowed_subtrees):
            continue  # permitted
        if (
            name in ("__init__.py", "_version.py", "__main__.py")
            or rel_posix == "src/guerilla/cli/main.py"
        ):
            continue
        raise AssertionError(f"Prohibited post-Phase-8 runtime module: {rel}")


# ── Prompt inventory ──────────────────────────────────────────────────


def test_phase_prompts_readme_exists():
    path = REPO_ROOT / "docs" / "phase_prompts" / "README.md"
    assert path.is_file(), "phase_prompts/README.md missing"


def test_phase_2_prompt_placeholder_exists():
    path = REPO_ROOT / "docs" / "phase_prompts" / "PHASE_02_ARCHITECTURE_DECISIONS.md"
    assert path.is_file(), "Phase 2 architecture-decisions prompt is missing"
    content = path.read_text(encoding="utf-8")
    assert "Phase 2" in content
    assert "Architecture Decisions" in content
    assert "Runtime implementation remains out of scope" in content


def test_prompt_inventory_complete():
    """The phase_prompts README must list all 22 phases and 3 final checklists."""
    readme = (REPO_ROOT / "docs" / "phase_prompts" / "README.md").read_text(encoding="utf-8")
    for n in range(1, 23):
        assert (
            f"PHASE_{n:02d}" in readme or f"Phase {n}" in readme or f"phase {n}" in readme.lower()
        ), f"Phase {n} not found in prompt inventory"
    assert "FINAL_INTERNAL_MVP_CHECKLIST" in readme or "Internal MVP Checklist" in readme
    assert (
        "FINAL_EXTERNAL_COMPATIBILITY_CHECKLIST" in readme
        or "External Compatibility Checklist" in readme
    )
    assert "FINAL_RELEASE_CHECKLIST" in readme or "Release Checklist" in readme


# ── Placeholder integrity ─────────────────────────────────────────────


def test_build_documents_identify_status():
    """Build documents must identify whether they are frozen or placeholders."""
    docs_dir = REPO_ROOT / "docs"
    for name in REQUIRED_SKELETONS:
        path = docs_dir / name
        content = path.read_text(encoding="utf-8")
        if name in FROZEN_DOCS:
            assert "**Status:** FROZEN -- Phase" in content
            assert "PLACEHOLDER" not in content
        elif name in GATE_STATUS_DOCS:
            assert "**Status:** Gate " in content
            assert "PLACEHOLDER" not in content
        else:
            assert "PLACEHOLDER" in content or "placeholder" in content.lower(), (
                f"{name} does not identify as placeholder"
            )
