"""Tests for the workflow-container-developer CLI."""

from pathlib import Path

from workflow_container_developer.cli import main


def _target_create(tmp_path: Path) -> tuple[Path, Path]:
    """Create a developer checkout and adjacent workflow-container target.

    Args:
        tmp_path: Temporary test root.

    Returns:
        Developer path and target path.
    """

    developer_path = tmp_path / "workflow-container-developer"
    developer_path.mkdir()
    target_path = tmp_path / "sample-container"
    target_path.mkdir()
    (target_path / "workflow.yaml").write_text("name: sample\ncommand:\n  - sample-run\n", encoding="utf-8")
    (target_path / "versions.yaml").write_text("project: sample\nversion: 0.1.0\n", encoding="utf-8")
    (target_path / "AGENTS.md").write_text("# Repository Guidelines\n", encoding="utf-8")
    (target_path / "doc" / "design").mkdir(parents=True)
    (target_path / "doc" / "design" / "sample.md").write_text("# Sample\n", encoding="utf-8")
    return developer_path, target_path


def test_cli_audit_reports_errors(tmp_path: Path, capsys) -> None:
    """Return failure status and print audit errors."""

    developer_path, target_path = _target_create(tmp_path)
    (target_path / "AGENTS.md").unlink()

    assert main(["--developer-path", str(developer_path), "audit", "sample-container"]) == 1

    captured = capsys.readouterr()
    assert "ERROR Missing AGENTS.md" in captured.out


def test_cli_audit_reports_success(tmp_path: Path, capsys) -> None:
    """Audit a selected adjacent workflow-container project."""

    developer_path, _target_path = _target_create(tmp_path)

    assert main(["--developer-path", str(developer_path), "audit", "sample-container"]) == 0

    captured = capsys.readouterr()
    assert "OK sample-container" in captured.out


def test_cli_audit_reports_unknown_target(tmp_path: Path, capsys) -> None:
    """Report unknown audit targets without traceback."""

    developer_path, _target_path = _target_create(tmp_path)

    assert main(["--developer-path", str(developer_path), "audit", "missing-container"]) == 1

    captured = capsys.readouterr()
    assert "ERROR Unknown workflow-container project: missing-container" in captured.out


def test_cli_audit_reports_warnings(tmp_path: Path, capsys) -> None:
    """Print warning output from generic audit results."""

    developer_path, target_path = _target_create(tmp_path)
    prompt_path = target_path / "workflow_module" / "prompt"
    prompt_path.mkdir(parents=True)
    (prompt_path / "duplicate.md").write_text("# Duplicate\n", encoding="utf-8")
    (prompt_path / "template").mkdir()
    (prompt_path / "template" / "stage.md").write_text("# Stage\n", encoding="utf-8")

    assert main(["--developer-path", str(developer_path), "audit", "sample-container"]) == 0

    captured = capsys.readouterr()
    assert "WARNING Root-level prompt markdown file found at workflow_module/prompt/duplicate.md; use template tree" in captured.out
    assert "OK sample-container" in captured.out


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
