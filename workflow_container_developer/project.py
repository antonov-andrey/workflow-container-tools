"""Workflow-container project discovery and command configuration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkflowContainerProject:
    """Adjacent workflow-container project metadata."""

    name: str
    path: Path


class WorkflowContainerProjectFinder:
    """Find workflow-container projects adjacent to this developer workspace."""

    def __init__(self, *, developer_path: Path) -> None:
        """Initialize the finder.

        Args:
            developer_path: Path to the workflow-container-developer checkout.
        """

        self._developer_path = developer_path.resolve()
        self._workspace_path = self._developer_path.parent

    def project_get(self, name: str) -> WorkflowContainerProject:
        """Return one adjacent workflow-container project by directory name.

        Args:
            name: Target project directory name.

        Returns:
            Matching workflow-container project.

        Raises:
            ValueError: No adjacent workflow-container project has that name.
        """

        for project in self.project_list_get():
            if project.name == name:
                return project
        raise ValueError(f"Unknown workflow-container project: {name}")

    def project_list_get(self) -> list[WorkflowContainerProject]:
        """Return adjacent workflow-container projects sorted by name.

        Returns:
            Sorted adjacent workflow-container project list.
        """

        project_list: list[WorkflowContainerProject] = []
        for path in sorted(self._workspace_path.iterdir()):
            if path == self._developer_path or not path.is_dir():
                continue
            if (path / "workflow.yaml").is_file() and (path / "versions.yaml").is_file():
                project_list.append(WorkflowContainerProject(name=path.name, path=path))
        return project_list
