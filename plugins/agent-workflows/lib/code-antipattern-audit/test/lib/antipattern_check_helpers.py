"""Shared helpers for anti-pattern audit checker tests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
import shutil
import subprocess
import sys
import tempfile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
PLUGIN_ROOT = Path(__file__).resolve().parents[4]
INSTRUMENTAL_TEMPLATE_PATH = PLUGIN_ROOT / "lib" / "code-antipattern-audit" / "template" / "instrumental.md"
SEMANTIC_TEMPLATE_PATH = PLUGIN_ROOT / "lib" / "code-antipattern-audit" / "template" / "semantic.md"
VALID_REPORT_SCOPE = "script/demo"
INSTRUMENTAL_REPORT_UUID = "00000000-0000-0000-0000-000000000001"
SEMANTIC_REPORT_UUID = "00000000-0000-0000-0000-000000000002"
INSTRUMENTAL_REPORT_RELPATH = f"tmp/code-antipattern-audit-instrumental-{INSTRUMENTAL_REPORT_UUID}.md"
SEMANTIC_REPORT_RELPATH = f"tmp/code-antipattern-audit-semantic-{SEMANTIC_REPORT_UUID}.md"
REPORT_ROOT_OVERRIDE_ENV_NAME = "CODE_ANTIPATTERN_AUDIT_REPORT_ROOT"


def checker_with_sample_run(
    *,
    checker_relpath: str,
    src: str,
    filename: str = "sample.py",
    extra_args: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    """Write a temporary sample file and run one checker against it.

    Args:
        checker_relpath: Repository-relative checker path.
        src: Python source code to analyze.
        filename: Sample filename to write inside the temporary scope.
        extra_args: Additional CLI arguments.

    Returns:
        Completed process result.
    """

    temp_root = Path("/tmp/pytest_antipattern_checks")
    temp_root.mkdir(parents=True, exist_ok=True)
    sample_dir = Path(tempfile.mkdtemp(prefix="sample-", dir=temp_root))
    sample = sample_dir / filename
    sample.write_text(src, encoding="utf-8")

    try:
        return subprocess.run(
            [checker_relpath, str(sample), *extra_args],
            capture_output=True,
            text=True,
            check=False,
            cwd=ROOT,
        )
    finally:
        shutil.rmtree(sample_dir, ignore_errors=True)
        try:
            temp_root.rmdir()
        except OSError:
            pass


def repo_tool_run(tool_relpath: str, *args: str, report_root: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run one project Python tool script.

    Args:
        tool_relpath: Repository-relative script path.
        args: Additional CLI arguments.
        report_root: Optional runtime root override used by report tools.

    Returns:
        Completed process result.
    """

    env = os.environ.copy()
    if report_root is not None:
        env[REPORT_ROOT_OVERRIDE_ENV_NAME] = str(report_root.resolve())
    return subprocess.run(
        [sys.executable, tool_relpath, *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
        env=env,
    )


@contextmanager
def temporary_repo_file_create(*, repo_root: Path, relpath: str, content: str) -> Iterator[Path]:
    """Create one temporary repository-root-relative file and remove it after use.

    Args:
        repo_root: Temporary runtime root that should own the created file.
        relpath: Repository-relative file path.
        content: File content to write.

    Returns:
        Iterator that yields the absolute created file path.
    """

    path = repo_root / relpath
    if path.exists():
        raise AssertionError(f"temporary_repo_file_create requires a missing path, got existing {relpath}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def valid_instrumental_report() -> str:
    """Build one valid instrumental source report.

    Returns:
        Canonical valid instrumental source-report text.
    """

    report = INSTRUMENTAL_TEMPLATE_PATH.read_text(encoding="utf-8")
    report = _keyed_bullet_value_replace(report, "scope", f"`{VALID_REPORT_SCOPE}`")
    report = _keyed_bullet_value_replace(report, "report_uuid", f"`{INSTRUMENTAL_REPORT_UUID}`")
    report = _keyed_bullet_value_replace(report, "report_path", f"`{INSTRUMENTAL_REPORT_RELPATH}`")
    report = _keyed_bullet_value_replace(
        report,
        "project-standards:python-developer/scripts/python_proxy_method_check.py",
        "`PASS`",
    )
    report = _keyed_bullet_value_replace(
        report,
        "project-standards:python-developer/scripts/python_single_use_artifact_check.py",
        "`NOT_RUN`",
    )
    report = _keyed_bullet_value_replace(
        report,
        "project-standards:python-developer/scripts/python_argument_pack_check.py",
        "`NOT_RUN`",
    )
    report = _keyed_bullet_value_replace(
        report,
        "project-standards:python-developer/scripts/python_control_flow_complexity_check.py",
        "`NOT_RUN`",
    )
    report = _keyed_bullet_value_replace(
        report,
        "project-standards:python-developer/scripts/python_dependency_fanout_check.py",
        "`NOT_RUN`",
    )
    report = _keyed_bullet_value_replace(
        report,
        "project-standards:python-developer/scripts/python_hidden_dependency_construction_check.py",
        "`NOT_RUN`",
    )
    report = _keyed_bullet_value_replace(
        report,
        "project-standards:python-developer/scripts/python_generic_bucket_module_check.py",
        "`NOT_RUN`",
    )
    report = _keyed_bullet_value_replace(report, "overall_verdict", "`FINDINGS`")
    report = _section_bullet_replace(
        report,
        "Executed commands",
        0,
        ["- `project-standards:python-developer/scripts/python_proxy_method_check.py script/demo`"],
    )
    report = _section_bullet_replace(report, "Reviewed anti-pattern cards", 0, ["- `PRJ-10`"])
    report = _section_bullet_replace(
        report,
        "Collected signals",
        0,
        [
            "- checker id: `python_proxy_method_check`; file path: `script/demo.py`; line: `10`; "
            "triggering pattern: `pass-through`; candidate anti-pattern ids: `PRJ-10`; scope expansion used: `None`"
        ],
    )
    report = _section_bullet_replace(report, "Rejected signals", 0, ["- None"])
    report = _section_bullet_replace(
        report,
        "Confirmed anti-pattern cases",
        0,
        [
            "- anti-pattern ids: `PRJ-10`; violated owner rule: `Main project code Rules`; file path: `script/demo.py`; "
            "line: `10`; supporting checker ids: `python_proxy_method_check`; competing cards rejected: `BOOK-06`; "
            "exception status: `rejected`; scope expansion used: `None`; remediation direction: `delete the proxy`"
        ],
    )
    report = _section_bullet_replace(
        report,
        "Clean cards checked",
        0,
        ["- `PRJ-11`: inspected `script/demo.py` and found no confirmed case in the declared scope"],
    )
    return report


def _keyed_bullet_value_replace(report: str, key: str, replacement_value: str) -> str:
    """Replace one keyed bullet value inside a template-derived report.

    Args:
        report: Full template report text.
        key: Literal keyed-bullet key.
        replacement_value: Replacement value text after the colon.

    Returns:
        Updated report text.
    """

    pattern = re.compile(
        rf"^(?P<prefix>- `{re.escape(key)}`: ).+$",
        flags=re.MULTILINE,
    )
    replacement = rf"\g<prefix>{replacement_value}"
    updated, count = pattern.subn(replacement, report, count=1)
    if count != 1:
        raise AssertionError(f"expected exactly one keyed bullet for {key!r} in template")
    return updated


def _section_bullet_replace(
    report: str,
    section_name: str,
    bullet_index: int,
    replacement_line_list: list[str],
) -> str:
    """Replace one bullet slot inside a named template section by bullet index.

    Args:
        report: Full template report text.
        section_name: Target section heading without leading hashes.
        bullet_index: Zero-based bullet index inside the section body.
        replacement_line_list: Final bullet lines that replace the targeted slot.

    Returns:
        Updated report text.
    """

    pattern = re.compile(
        rf"(^## {re.escape(section_name)}\n)(?P<body>.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(report)
    if match is None:
        raise AssertionError(f"expected exactly one section named {section_name!r} in template")
    body_lines = match.group("body").splitlines()
    bullet_positions = [index for index, line in enumerate(body_lines) if line.startswith("- ")]
    if bullet_index >= len(bullet_positions):
        raise AssertionError(f"expected bullet index {bullet_index} in section {section_name!r}")
    start = bullet_positions[bullet_index]
    end = bullet_positions[bullet_index + 1] if bullet_index + 1 < len(bullet_positions) else len(body_lines)
    new_body_lines = body_lines[:start] + replacement_line_list + body_lines[end:]
    replacement = match.group(1) + "\n".join(new_body_lines).rstrip() + "\n\n"
    return report[: match.start()] + replacement + report[match.end() :]


def valid_semantic_report() -> str:
    """Build one valid semantic source report.

    Returns:
        Canonical valid semantic source-report text.
    """

    report = SEMANTIC_TEMPLATE_PATH.read_text(encoding="utf-8")
    report = _keyed_bullet_value_replace(report, "scope", f"`{VALID_REPORT_SCOPE}`")
    report = _keyed_bullet_value_replace(report, "report_uuid", f"`{SEMANTIC_REPORT_UUID}`")
    report = _keyed_bullet_value_replace(report, "report_path", f"`{SEMANTIC_REPORT_RELPATH}`")
    report = _keyed_bullet_value_replace(report, "overall_verdict", "`FINDINGS`")
    report = _section_bullet_replace(report, "Reviewed anti-pattern cards", 0, ["- `PRJ-10`"])
    report = _section_bullet_replace(
        report,
        "Collected signals",
        0,
        [
            "- anti-pattern id: `PRJ-10`; file path: `script/demo.py`; line: `10`; observed signal: `pass-through method`; scope expansion used: `None`"
        ],
    )
    report = _section_bullet_replace(report, "Rejected signals", 0, ["- None"])
    report = _section_bullet_replace(
        report,
        "Confirmed anti-pattern cases",
        0,
        [
            "- anti-pattern ids: `PRJ-10`; violated owner rule: `Main project code Rules`; file path: `script/demo.py`; line: `10`; observed evidence: `direct forwarding`; competing cards rejected: `BOOK-06`; exception status: `rejected`; scope expansion used: `None`; remediation direction: `delete the proxy`"
        ],
    )
    report = _section_bullet_replace(
        report,
        "Clean cards checked",
        0,
        ["- `PRJ-11`: inspected `script/demo.py` and found no confirmed case in the declared scope"],
    )
    return report
