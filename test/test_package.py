"""Tests for workflow-container-tools package metadata."""

import tomllib
from pathlib import Path

PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_package_uses_tools_identity() -> None:
    """Keep distribution and wheel package names aligned with the tools project."""

    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    assert pyproject["project"]["name"] == "workflow-container-tools"
    assert pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["workflow_container_tools"]


def test_pytest_is_test_extra_not_runtime_dependency() -> None:
    """Keep pytest out of package runtime dependencies."""

    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    assert "pytest>=8.4.0" not in pyproject["project"].get("dependencies", [])
    assert pyproject["project"]["optional-dependencies"]["test"] == ["pytest>=8.4.0"]
