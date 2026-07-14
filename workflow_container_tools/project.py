"""Workflow-container project discovery."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkflowContainerProject:
    """Adjacent workflow-container project metadata."""

    name: str
    path: Path


class WorkflowContainerProjectFinder:
    """Find workflow-container projects adjacent to this tools workspace."""

    def __init__(self, *, tools_path: Path) -> None:
        """Initialize the finder.

        Args:
            tools_path: Path to the workflow-container-tools checkout.
        """

        self._tools_path = tools_path.resolve()
        self._workspace_path = self._tools_path.parent

    def project_list_get(self) -> list[WorkflowContainerProject]:
        """Return adjacent workflow-container projects sorted by name.

        Returns:
            Sorted adjacent workflow-container project list.
        """

        project_list: list[WorkflowContainerProject] = []
        for path in sorted(self._workspace_path.iterdir()):
            if path == self._tools_path or not path.is_dir():
                continue
            if (path / "workflow.yaml").is_file() and (path / "versions.yaml").is_file():
                project_list.append(WorkflowContainerProject(name=path.name, path=path))
        return project_list
