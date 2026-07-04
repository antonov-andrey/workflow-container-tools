"""Generic workflow-container project audit."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from workflow_container_developer.project import WorkflowContainerProject

AUTHORING_DESIGN_REFERENCE_LABEL = (
    "workflow-container-developer plugin reference `references/workflow-container-authoring.md`"
)
AUTHORING_DESIGN_REFERENCE_TOKEN_LIST = [
    "workflow-container-developer",
    "references/workflow-container-authoring.md",
]
BLACK_LINE_LENGTH = 120
BLACK_TARGET_VERSION = "py314"
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
RUNTIME_OWNED_PROMPT_PARTIAL_NAME_SET = {
    "artifact_reference_contract.md.j2",
    "runtime_source_access.md.j2",
    "stage_verification_contract.md.j2",
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
        self._required_file_check(Path("pyproject.toml"), error_list)
        self._agents_check(error_list)
        self._design_check(error_list)
        self._pyproject_check(error_list)
        self._prompt_duplicate_check(warning_list)
        self._runtime_duplicate_check(warning_list)
        self._workflow_yaml_check(error_list)
        return WorkflowContainerAuditResult(error_list=error_list, warning_list=warning_list)

    def _agents_check(self, error_list: list[str]) -> None:
        """Check workflow-container instruction linkage.

        Args:
            error_list: Audit error output list.
        """

        agents_path = self._project.path / "AGENTS.md"
        if not agents_path.is_file():
            return
        agents_text = agents_path.read_text(encoding="utf-8")
        if not all(token in agents_text for token in AUTHORING_DESIGN_REFERENCE_TOKEN_LIST):
            error_list.append(f"AGENTS.md must reference {AUTHORING_DESIGN_REFERENCE_LABEL}")

    def _design_check(self, error_list: list[str]) -> None:
        """Check for at least one project design document.

        Args:
            error_list: Audit error output list.
        """

        design_path = self._project.path / "doc" / "design"
        design_file_list = sorted(design_path.glob("*.md")) if design_path.is_dir() else []
        if not design_file_list:
            error_list.append("Missing doc/design/*.md")
            return
        for design_file_path in design_file_list:
            design_text = design_file_path.read_text(encoding="utf-8")
            if all(token in design_text for token in AUTHORING_DESIGN_REFERENCE_TOKEN_LIST):
                return
        error_list.append(f"doc/design/*.md must reference {AUTHORING_DESIGN_REFERENCE_LABEL}")

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

    def _pyproject_check(self, error_list: list[str]) -> None:
        """Check generic Python project quality baseline.

        Args:
            error_list: Audit error output list.
        """

        pyproject_path = self._project.path / "pyproject.toml"
        if not pyproject_path.is_file():
            return
        try:
            payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            error_list.append("pyproject.toml must be valid TOML")
            return
        project_payload = payload.get("project")
        if not isinstance(project_payload, dict):
            error_list.append("pyproject.toml missing [project]")
            return
        if project_payload.get("requires-python") != ">=3.14":
            error_list.append('pyproject.toml project.requires-python must be ">=3.14"')
        black_payload = payload.get("tool", {}).get("black") if isinstance(payload.get("tool"), dict) else None
        if not isinstance(black_payload, dict):
            error_list.append("pyproject.toml missing [tool.black]")
            return
        if black_payload.get("target-version") != [BLACK_TARGET_VERSION]:
            error_list.append('pyproject.toml tool.black.target-version must be ["py314"]')
        if black_payload.get("line-length") != BLACK_LINE_LENGTH:
            error_list.append("pyproject.toml tool.black.line-length must be 120")

    def _runtime_duplicate_check(self, warning_list: list[str]) -> None:
        """Warn about workflow-container runtime-owned generic local copies.

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
            for filename in sorted(filename_list):
                path = root_path / filename
                relative_path = path.relative_to(self._project.path)
                if filename in RUNTIME_OWNED_PROMPT_PARTIAL_NAME_SET:
                    warning_list.append(
                        f"Runtime-owned prompt partial found at {relative_path}; use workflow-container-runtime"
                    )
                    continue
                if filename != "runner.py":
                    continue
                try:
                    source_text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if "class CodexStageRunner" in source_text:
                    warning_list.append(
                        f"Runtime-owned CodexStageRunner implementation found at {relative_path}; "
                        "use workflow-container-runtime"
                    )

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
