"""Tests for the workflow-container-tools CLI."""

from pathlib import Path

import pytest

from workflow_container_tools.cli import main


def _tools_path_create(tmp_path: Path) -> Path:
    """Create a tools checkout fixture.

    Args:
        tmp_path: Temporary test root.

    Returns:
        Tools path.
    """

    tools_path = tmp_path / "workflow-container-tools"
    tools_path.mkdir()
    return tools_path


def test_cli_help_lists_supported_commands(tmp_path: Path, capsys) -> None:
    """Show help text with the supported command set."""

    tools_path = _tools_path_create(tmp_path)

    with pytest.raises(SystemExit) as error:
        main(["--tools-path", str(tools_path), "--help"])

    assert error.value.code == 0

    captured = capsys.readouterr()
    assert "{list}" in captured.out
    assert "audit" not in captured.out
    assert "--version" not in captured.out


def test_cli_list_outputs_adjacent_project(tmp_path: Path, capsys) -> None:
    """List adjacent workflow-container projects."""

    tools_path = tmp_path / "workflow-container-tools"
    tools_path.mkdir()
    target_path = tmp_path / "sample-container"
    target_path.mkdir()
    (target_path / "workflow.yaml").write_text("name: sample\n", encoding="utf-8")
    (target_path / "versions.yaml").write_text("project: sample\nversion: 0.1.0\n", encoding="utf-8")

    assert main(["--tools-path", str(tools_path), "list"]) == 0

    captured = capsys.readouterr()
    assert "sample-container" in captured.out


def test_cli_rejects_removed_audit_command(tmp_path: Path, capsys) -> None:
    """Reject the removed audit subcommand."""

    tools_path = _tools_path_create(tmp_path)

    with pytest.raises(SystemExit) as error:
        main(["--tools-path", str(tools_path), "audit", "sample-container"])

    assert error.value.code == 2

    captured = capsys.readouterr()
    assert "invalid choice: 'audit'" in captured.err


def test_main_is_importable() -> None:
    """Verify the CLI entrypoint can be imported."""

    assert callable(main)
