"""Test contracts for `plugins/agent-workflows/lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py`."""

from __future__ import annotations

from pathlib import Path

from lib.antipattern_check_helpers import (
    INSTRUMENTAL_REPORT_RELPATH,
    SEMANTIC_REPORT_RELPATH,
    VALID_REPORT_SCOPE,
    repo_tool_run,
    temporary_repo_file_create,
    valid_instrumental_report,
    valid_semantic_report,
)


def test_report_check_accepts_valid_source_reports(tmp_path: Path) -> None:
    """Validator must accept one valid instrumental report and one valid semantic report.

    Args:
        tmp_path: Per-test temporary report root.
    """

    with (
        temporary_repo_file_create(
            repo_root=tmp_path,
            relpath=INSTRUMENTAL_REPORT_RELPATH,
            content=valid_instrumental_report(),
        ),
        temporary_repo_file_create(
            repo_root=tmp_path,
            relpath=SEMANTIC_REPORT_RELPATH,
            content=valid_semantic_report(),
        ),
    ):
        result = repo_tool_run(
            "plugins/agent-workflows/lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py",
            "--expected-scope",
            VALID_REPORT_SCOPE,
            INSTRUMENTAL_REPORT_RELPATH,
            SEMANTIC_REPORT_RELPATH,
            report_root=tmp_path,
        )

    assert result.returncode == 0, result.stderr
    assert f"PASS: {INSTRUMENTAL_REPORT_RELPATH}" in result.stdout
    assert f"PASS: {SEMANTIC_REPORT_RELPATH}" in result.stdout


def test_report_check_accepts_instrumental_report_rendered_from_owner_template(tmp_path: Path) -> None:
    """Validator must accept an instrumental report rendered from the owner template scaffold.

    Args:
        tmp_path: Per-test temporary report root.
    """

    with temporary_repo_file_create(
        repo_root=tmp_path,
        relpath=INSTRUMENTAL_REPORT_RELPATH,
        content=valid_instrumental_report(),
    ):
        result = repo_tool_run(
            "plugins/agent-workflows/lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py",
            "--expected-scope",
            VALID_REPORT_SCOPE,
            INSTRUMENTAL_REPORT_RELPATH,
            report_root=tmp_path,
        )

    assert result.returncode == 0, result.stderr
    assert f"PASS: {INSTRUMENTAL_REPORT_RELPATH}" in result.stdout


def test_report_check_rejects_scope_mismatch(tmp_path: Path) -> None:
    """Validator must reject a source report whose scope differs from the declared scope.

    Args:
        tmp_path: Per-test temporary report root.
    """

    with temporary_repo_file_create(
        repo_root=tmp_path,
        relpath=INSTRUMENTAL_REPORT_RELPATH,
        content=valid_instrumental_report(),
    ):
        result = repo_tool_run(
            "plugins/agent-workflows/lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py",
            "--expected-scope",
            "script/other",
            INSTRUMENTAL_REPORT_RELPATH,
            report_root=tmp_path,
        )

    assert result.returncode == 1
    assert f"FAIL: {INSTRUMENTAL_REPORT_RELPATH}" in result.stderr
    assert "`scope` mismatch" in result.stderr


def test_report_check_rejects_missing_required_section(tmp_path: Path) -> None:
    """Validator must reject a malformed report that omits one required section.

    Args:
        tmp_path: Per-test temporary report root.
    """

    malformed = valid_semantic_report().replace("\n## Rejected signals\n- None\n", "\n")
    with temporary_repo_file_create(
        repo_root=tmp_path,
        relpath=SEMANTIC_REPORT_RELPATH,
        content=malformed,
    ):
        result = repo_tool_run(
            "plugins/agent-workflows/lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py",
            "--expected-scope",
            VALID_REPORT_SCOPE,
            SEMANTIC_REPORT_RELPATH,
            report_root=tmp_path,
        )

    assert result.returncode == 1
    assert f"FAIL: {SEMANTIC_REPORT_RELPATH}" in result.stderr
    assert "section order mismatch" in result.stderr


def test_report_check_rejects_clean_verdict_with_confirmed_cases(tmp_path: Path) -> None:
    """Validator must reject one clean verdict that still reports confirmed cases.

    Args:
        tmp_path: Per-test temporary report root.
    """

    malformed = valid_semantic_report().replace(
        "- `overall_verdict`: `FINDINGS`",
        "- `overall_verdict`: `CLEAN`",
    )
    with temporary_repo_file_create(
        repo_root=tmp_path,
        relpath=SEMANTIC_REPORT_RELPATH,
        content=malformed,
    ):
        result = repo_tool_run(
            "plugins/agent-workflows/lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py",
            "--expected-scope",
            VALID_REPORT_SCOPE,
            SEMANTIC_REPORT_RELPATH,
            report_root=tmp_path,
        )

    assert result.returncode == 1
    assert "`overall_verdict` CLEAN is inconsistent" in result.stderr


def test_report_check_rejects_legacy_angle_bracket_checker_statuses(tmp_path: Path) -> None:
    """Validator must reject the legacy checker-result format with angle brackets.

    Args:
        tmp_path: Per-test temporary report root.
    """

    malformed = valid_instrumental_report().replace(
        "- `project-standards:python-developer/scripts/python_proxy_method_check.py`: `PASS`",
        "- `project-standards:python-developer/scripts/python_proxy_method_check.py`: `<PASS>`",
    )
    with temporary_repo_file_create(
        repo_root=tmp_path,
        relpath=INSTRUMENTAL_REPORT_RELPATH,
        content=malformed,
    ):
        result = repo_tool_run(
            "plugins/agent-workflows/lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py",
            "--expected-scope",
            VALID_REPORT_SCOPE,
            INSTRUMENTAL_REPORT_RELPATH,
            report_root=tmp_path,
        )

    assert result.returncode == 1
    assert "invalid checker-result line" in result.stderr


def test_report_check_rejects_findings_verdict_without_confirmed_cases(tmp_path: Path) -> None:
    """Validator must reject one findings verdict without confirmed cases.

    Args:
        tmp_path: Per-test temporary report root.
    """

    malformed = valid_instrumental_report().replace(
        "- anti-pattern ids: `PRJ-10`; violated owner rule: `Main project code Rules`; file path: `script/demo.py`; line: `10`; supporting checker ids: `python_proxy_method_check`; competing cards rejected: `BOOK-06`; exception status: `rejected`; scope expansion used: `None`; remediation direction: `delete the proxy`",
        "- None",
    )
    with temporary_repo_file_create(
        repo_root=tmp_path,
        relpath=INSTRUMENTAL_REPORT_RELPATH,
        content=malformed,
    ):
        result = repo_tool_run(
            "plugins/agent-workflows/lib/code-antipattern-audit/tool/code_antipattern_audit_report_check.py",
            "--expected-scope",
            VALID_REPORT_SCOPE,
            INSTRUMENTAL_REPORT_RELPATH,
            report_root=tmp_path,
        )

    assert result.returncode == 1
    assert "`overall_verdict` FINDINGS is inconsistent" in result.stderr
