"""Generic workflow-container project audit."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from workflow_container_developer.project import WorkflowContainerProject


PROMPT_SCAN_IGNORED_DIRECTORY_NAME_SET = {
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
}


@dataclass(frozen=True)
class WorkflowContainerAuditResult:
    """Workflow-container audit result."""

    error_list: list[str] = field(default_factory=list)
    warning_list: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        """Return whether the audit has no errors.

        Returns:
            True when no errors exist.
        """

        return not self.error_list


class WorkflowContainerAudit:
    """Run generic contract checks for one workflow-container project."""

    def __init__(self, *, project: WorkflowContainerProject) -> None:
        """Initialize the audit.

        Args:
            project: Target workflow-container project.
        """

        self._project = project

    def result_get(self) -> WorkflowContainerAuditResult:
        """Run audit checks.

        Returns:
            Audit result.
        """

        error_list: list[str] = []
        warning_list: list[str] = []
        self._required_file_check(Path("workflow.yaml"), error_list)
        self._required_file_check(Path("versions.yaml"), error_list)
        self._required_file_check(Path("AGENTS.md"), error_list)
        self._design_check(error_list)
        self._prompt_duplicate_check(warning_list)
        self._workflow_yaml_check(error_list)
        return WorkflowContainerAuditResult(error_list=error_list, warning_list=warning_list)

    def _design_check(self, error_list: list[str]) -> None:
        """Check for at least one project design document.

        Args:
            error_list: Audit error output list.
        """

        design_path = self._project.path / "doc" / "design"
        if not design_path.is_dir() or not any(design_path.glob("*.md")):
            error_list.append("Missing doc/design/*.md")

    def _prompt_duplicate_check(self, warning_list: list[str]) -> None:
        """Warn about prompt markdown files outside the template tree.

        Args:
            warning_list: Audit warning output list.
        """

        for root, directory_name_list, filename_list in os.walk(self._project.path):
            directory_name_list[:] = [
                directory_name
                for directory_name in sorted(directory_name_list)
                if directory_name not in PROMPT_SCAN_IGNORED_DIRECTORY_NAME_SET
            ]
            root_path = Path(root)
            if root_path.name != "prompt":
                continue
            for filename in sorted(filename_list):
                prompt_markdown_path = root_path / filename
                if prompt_markdown_path.suffix == ".md":
                    relative_path = prompt_markdown_path.relative_to(self._project.path)
                    warning_list.append(f"Root-level prompt markdown file found at {relative_path}; use template tree")

    def _required_file_check(self, relative_path: Path, error_list: list[str]) -> None:
        """Check for one required project file.

        Args:
            relative_path: Required file path relative to the target project.
            error_list: Audit error output list.
        """

        if not (self._project.path / relative_path).is_file():
            error_list.append(f"Missing {relative_path}")

    def _workflow_yaml_check(self, error_list: list[str]) -> None:
        """Check generic workflow YAML structure.

        Args:
            error_list: Audit error output list.
        """

        workflow_path = self._project.path / "workflow.yaml"
        if not workflow_path.is_file():
            return
        try:
            payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            error_list.append("workflow.yaml must be valid YAML")
            return
        if not isinstance(payload, dict):
            error_list.append("workflow.yaml must be a mapping")
            return
        for key in ["name", "command"]:
            if key not in payload:
                error_list.append(f"workflow.yaml missing {key}")
