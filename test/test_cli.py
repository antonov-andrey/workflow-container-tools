"""Tests for the workflow-container-developer CLI."""

from pathlib import Path

from workflow_container_developer.cli import main


def test_cli_list_outputs_adjacent_project(tmp_path: Path, capsys) -> None:
    """List adjacent workflow-container projects."""

    developer_path = tmp_path / "workflow-container-developer"
    developer_path.mkdir()
    target_path = tmp_path / "sample-container"
    target_path.mkdir()
    (target_path / "workflow.yaml").write_text("name: sample\n", encoding="utf-8")
    (target_path / "versions.yaml").write_text("project: sample\nversion: 0.1.0\n", encoding="utf-8")

    assert main(["--developer-path", str(developer_path), "list"]) == 0

    captured = capsys.readouterr()
    assert "sample-container" in captured.out


def test_main_is_importable() -> None:
    """Verify the CLI entrypoint can be imported."""

    assert callable(main)
