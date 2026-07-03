"""Tests for generic workflow-container contract audits."""

from pathlib import Path

from workflow_container_developer.audit import WorkflowContainerAudit
from workflow_container_developer.project import WorkflowContainerProject


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
    (target_path / "AGENTS.md").write_text("# Repository Guidelines\n", encoding="utf-8")
    (target_path / "doc" / "design").mkdir(parents=True)
    (target_path / "doc" / "design" / "target.md").write_text("# Target\n", encoding="utf-8")
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
    assert "Root-level prompt markdown file found at workflow_module/prompt/duplicate.md; use template tree" in result.warning_list
