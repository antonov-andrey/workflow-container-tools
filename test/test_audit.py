"""Tests for generic workflow-container contract audits."""

from pathlib import Path

from workflow_container_developer.audit import WorkflowContainerAudit
from workflow_container_developer.project import WorkflowContainerProject

AUTHORING_DESIGN_REFERENCE = (
    "workflow-container-developer plugin reference `references/workflow-container-authoring.md`"
)
PYPROJECT_TEXT = """\
[project]
name = "target"
requires-python = ">=3.14"

[tool.black]
target-version = ["py314"]
line-length = 120
"""


def _target_create(tmp_path: Path) -> Path:
    """Create a target workflow-container fixture.

    Args:
        tmp_path: Temporary test root.

    Returns:
        Created target path.
    """

    target_path = tmp_path / "target"
    target_path.mkdir()
    (target_path / "workflow.yaml").write_text("name: target\ncommand:\n  - target-run\n", encoding="utf-8")
    (target_path / "versions.yaml").write_text("project: target\nversion: 0.1.0\n", encoding="utf-8")
    (target_path / "AGENTS.md").write_text(
        f"# Repository Guidelines\n\nSee `{AUTHORING_DESIGN_REFERENCE}`.\n", encoding="utf-8"
    )
    (target_path / "pyproject.toml").write_text(PYPROJECT_TEXT, encoding="utf-8")
    (target_path / "doc" / "design").mkdir(parents=True)
    (target_path / "doc" / "design" / "target.md").write_text(
        f"# Target\n\nShared rules: `{AUTHORING_DESIGN_REFERENCE}`.\n", encoding="utf-8"
    )
    return target_path


def _target_project_get(target_path: Path) -> WorkflowContainerProject:
    """Create project metadata for a target path.

    Args:
        target_path: Target project path.

    Returns:
        Target project metadata.
    """

    return WorkflowContainerProject(name=target_path.name, path=target_path)


def test_audit_result_fails_when_agents_missing(tmp_path: Path) -> None:
    """Report missing project-local instructions."""

    target_path = _target_create(tmp_path)
    (target_path / "AGENTS.md").unlink()

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert "Missing AGENTS.md" in result.error_list


def test_audit_result_fails_when_design_document_missing(tmp_path: Path) -> None:
    """Report missing project design documents."""

    target_path = _target_create(tmp_path)
    (target_path / "doc" / "design" / "target.md").unlink()

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert "Missing doc/design/*.md" in result.error_list


def test_audit_result_fails_when_design_reference_missing(tmp_path: Path) -> None:
    """Report design documents that do not link to the shared authoring baseline."""

    target_path = _target_create(tmp_path)
    (target_path / "doc" / "design" / "target.md").write_text("# Target\n", encoding="utf-8")

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert f"doc/design/*.md must reference {AUTHORING_DESIGN_REFERENCE}" in result.error_list


def test_audit_result_fails_when_instruction_reference_missing(tmp_path: Path) -> None:
    """Report project instructions that do not link to the shared authoring baseline."""

    target_path = _target_create(tmp_path)
    (target_path / "AGENTS.md").write_text("# Repository Guidelines\n", encoding="utf-8")

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert f"AGENTS.md must reference {AUTHORING_DESIGN_REFERENCE}" in result.error_list


def test_audit_result_fails_when_pyproject_black_config_missing(tmp_path: Path) -> None:
    """Report missing Black baseline configuration."""

    target_path = _target_create(tmp_path)
    (target_path / "pyproject.toml").write_text(
        '[project]\nname = "target"\nrequires-python = ">=3.14"\n', encoding="utf-8"
    )

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert "pyproject.toml missing [tool.black]" in result.error_list


def test_audit_result_fails_when_pyproject_python_version_differs(tmp_path: Path) -> None:
    """Report Python version drift from the shared baseline."""

    target_path = _target_create(tmp_path)
    (target_path / "pyproject.toml").write_text(
        PYPROJECT_TEXT.replace('requires-python = ">=3.14"', 'requires-python = ">=3.13"'), encoding="utf-8"
    )

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert 'pyproject.toml project.requires-python must be ">=3.14"' in result.error_list


def test_audit_result_fails_when_pyproject_black_line_length_differs(tmp_path: Path) -> None:
    """Report Black line-length drift from the shared baseline."""

    target_path = _target_create(tmp_path)
    (target_path / "pyproject.toml").write_text(
        PYPROJECT_TEXT.replace("line-length = 120", "line-length = 88"), encoding="utf-8"
    )

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert "pyproject.toml tool.black.line-length must be 120" in result.error_list


def test_audit_result_fails_when_pyproject_black_target_differs(tmp_path: Path) -> None:
    """Report Black target-version drift from the shared baseline."""

    target_path = _target_create(tmp_path)
    (target_path / "pyproject.toml").write_text(
        PYPROJECT_TEXT.replace('target-version = ["py314"]', 'target-version = ["py313"]'), encoding="utf-8"
    )

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert 'pyproject.toml tool.black.target-version must be ["py314"]' in result.error_list


def test_audit_result_fails_when_workflow_yaml_has_no_command(tmp_path: Path) -> None:
    """Report missing generic workflow command declaration."""

    target_path = _target_create(tmp_path)
    (target_path / "workflow.yaml").write_text("name: target\n", encoding="utf-8")

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert "workflow.yaml missing command" in result.error_list


def test_audit_result_fails_when_workflow_yaml_is_not_mapping(tmp_path: Path) -> None:
    """Report workflow YAML that does not declare a mapping."""

    target_path = _target_create(tmp_path)
    (target_path / "workflow.yaml").write_text("- target\n", encoding="utf-8")

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert not result.is_ok
    assert "workflow.yaml must be a mapping" in result.error_list


def test_audit_result_success_for_valid_project(tmp_path: Path) -> None:
    """Accept a target with required project-owned contract files."""

    target_path = _target_create(tmp_path)

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert result.is_ok
    assert result.error_list == []
    assert result.warning_list == []


def test_audit_result_ignores_transient_prompt_markdown(tmp_path: Path) -> None:
    """Ignore prompt markdown under transient and test fixture trees."""

    target_path = _target_create(tmp_path)
    ignored_name_list = [
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        ".worktrees",
        "__pycache__",
        "build",
        "dist",
        "fixture",
        "fixtures",
        "test",
        "tests",
        "tmp",
    ]
    for ignored_name in ignored_name_list:
        prompt_path = target_path / ignored_name / "workflow_module" / "prompt"
        prompt_path.mkdir(parents=True)
        (prompt_path / "duplicate.md").write_text("# Duplicate\n", encoding="utf-8")

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert result.is_ok
    assert result.error_list == []
    assert result.warning_list == []


def test_audit_result_warns_for_prompt_markdown_outside_template_tree_with_path(tmp_path: Path) -> None:
    """Warn when root prompt markdown duplicates template-owned prompts."""

    target_path = _target_create(tmp_path)
    prompt_path = target_path / "workflow_module" / "prompt"
    prompt_path.mkdir(parents=True)
    (prompt_path / "duplicate.md").write_text("# Duplicate\n", encoding="utf-8")
    (prompt_path / "template").mkdir()
    (prompt_path / "template" / "stage.md").write_text("# Stage\n", encoding="utf-8")

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert result.is_ok
    assert result.error_list == []
    assert (
        "Root-level prompt markdown file found at workflow_module/prompt/duplicate.md; use template tree"
        in result.warning_list
    )


def test_audit_result_warns_for_runtime_owned_codex_runner_copy(tmp_path: Path) -> None:
    """Warn when a workflow container owns generic Codex runner implementation."""

    target_path = _target_create(tmp_path)
    runner_path = target_path / "workflow_module" / "codex" / "runner.py"
    runner_path.parent.mkdir(parents=True)
    runner_path.write_text("class CodexStageRunner:\n    pass\n", encoding="utf-8")

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert result.is_ok
    assert result.error_list == []
    assert (
        "Runtime-owned CodexStageRunner implementation found at workflow_module/codex/runner.py; "
        "use workflow-container-runtime"
    ) in result.warning_list


def test_audit_result_warns_for_runtime_owned_prompt_partial_copy(tmp_path: Path) -> None:
    """Warn when a workflow container copies runtime-owned prompt partials."""

    target_path = _target_create(tmp_path)
    partial_path = target_path / "workflow_module" / "prompt" / "template" / "partial"
    partial_path.mkdir(parents=True)
    (partial_path / "runtime_source_access.md.j2").write_text("Use browser\n", encoding="utf-8")

    result = WorkflowContainerAudit(project=_target_project_get(target_path)).result_get()

    assert result.is_ok
    assert result.error_list == []
    assert (
        "Runtime-owned prompt partial found at "
        "workflow_module/prompt/template/partial/runtime_source_access.md.j2; use workflow-container-runtime"
    ) in result.warning_list
