"""Repository-contract tests for Phase 1 artifact boundary enforcement.

These tests verify structural properties, not runtime behavior.
"""

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


def test_editorconfig_exists():
    assert (REPO_ROOT / ".editorconfig").is_file(), ".editorconfig is missing"


# ── Skills ────────────────────────────────────────────────────────────

SKILL_NAMES = [
    "guerilla-contracts-modeling",
    "guerilla-graph-kernel-storage",
    "guerilla-adapter-continuity-reconciliation",
    "guerilla-projections-snapshot-resume",
    "guerilla-testing-security-evaluation",
]


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
    # At least one 64-char hex digest
    import re

    digests = re.findall(r"[0-9a-f]{64}", manifest)
    assert len(digests) >= 7, f"Expected at least 7 SHA-256 digests, found {len(digests)}"


# ── Schema and registry directories ───────────────────────────────────


def test_schemas_readme_exists():
    assert (REPO_ROOT / "schemas" / "README.md").is_file(), "schemas/README.md missing"


def test_registries_readme_exists():
    assert (REPO_ROOT / "registries" / "README.md").is_file(), "registries/README.md missing"


def test_no_frozen_schemas_in_phase1():
    """schemas/ must not contain frozen .schema.json files in Phase 1."""
    schema_dir = REPO_ROOT / "schemas"
    json_files = list(schema_dir.glob("*.schema.json"))
    assert len(json_files) == 0, (
        f"Phase 1 must not freeze schemas; found: {[f.name for f in json_files]}"
    )


def test_no_frozen_registries_in_phase1():
    """registries/ must not contain frozen .json files in Phase 1."""
    registry_dir = REPO_ROOT / "registries"
    json_files = list(registry_dir.glob("*.json"))
    assert len(json_files) == 0, (
        f"Phase 1 must not freeze registries; found: {[f.name for f in json_files]}"
    )


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
    """Beyond __init__.py placeholders and cli/main.py, no substantive .py files exist."""
    src = REPO_ROOT / "src" / "guerilla"
    py_files = list(src.rglob("*.py"))
    # Allowed: __init__.py files (short), cli/main.py, _version.py, __main__.py
    for py_file in py_files:
        rel = py_file.relative_to(REPO_ROOT)
        name = py_file.name
        if name == "__init__.py":
            # Must be a placeholder (short, no substantive logic beyond docstring)
            content = py_file.read_text(encoding="utf-8")
            assert len(content) < 300 or "cli" in str(rel), (
                f"__init__.py at {rel} exceeds placeholder size ({len(content)} bytes)"
            )
        elif name in ("_version.py", "__main__.py") or "cli/main.py" in str(rel).replace("\\", "/"):
            continue  # permitted
        else:
            # Any other .py file is prohibited in Phase 1
            raise AssertionError(f"Prohibited runtime module in Phase 1: {rel}")


# ── Prompt inventory ──────────────────────────────────────────────────


def test_phase_prompts_readme_exists():
    path = REPO_ROOT / "docs" / "phase_prompts" / "README.md"
    assert path.is_file(), "phase_prompts/README.md missing"


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


def test_placeholders_identify_status():
    """Document skeletons must contain a status marker."""
    docs_dir = REPO_ROOT / "docs"
    for name in REQUIRED_SKELETONS:
        path = docs_dir / name
        content = path.read_text(encoding="utf-8")
        assert "PLACEHOLDER" in content or "placeholder" in content.lower(), (
            f"{name} does not identify as placeholder"
        )
