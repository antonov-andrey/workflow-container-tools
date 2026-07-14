"""Tests for adjacent workflow-container project discovery."""

from pathlib import Path

from workflow_container_tools.project import WorkflowContainerProjectFinder


def _project_create(root: Path, name: str) -> Path:
    """Create a minimal workflow-container project fixture.

    Args:
        root: Parent directory for the project.
        name: Project directory name.

    Returns:
        Created project path.
    """

    project_path = root / name
    project_path.mkdir()
    (project_path / "workflow.yaml").write_text("name: sample\n", encoding="utf-8")
    (project_path / "versions.yaml").write_text("project: sample\nversion: 0.1.0\n", encoding="utf-8")
    return project_path


def test_project_list_get_finds_adjacent_workflow_container(tmp_path: Path) -> None:
    """Find projects through workflow markers without hardcoded names."""

    tools_path = tmp_path / "workflow-container-tools"
    tools_path.mkdir()
    target_path = _project_create(tmp_path, "sample-container")
    (tmp_path / "ordinary-project").mkdir()

    finder = WorkflowContainerProjectFinder(tools_path=tools_path)

    assert [project.path for project in finder.project_list_get()] == [target_path]
