"""Shared report contracts for provider-owned section audit workflows."""

from __future__ import annotations

from collections.abc import Sequence
import os
from pathlib import Path, PurePosixPath
import re
from uuid import UUID

AUDIT_ROOT_ENV_NAME = "AGENT_WORKFLOWS_AUDIT_ROOT"
ROOT = Path(os.environ.get(AUDIT_ROOT_ENV_NAME, str(Path.cwd()))).resolve()
SEVERITY_PATTERN = re.compile(r"^- (High|Medium|Low): .+$")


def _audit_title_get(audit_name: str) -> str:
    """Return one report title from a canonical audit name.

    Args:
        audit_name: Lowercase hyphenated audit identifier.

    Returns:
        Human-readable report title.
    """

    return " ".join(word.capitalize() for word in audit_name.split("-"))


def _finding_error_list_get(line_list: Sequence[str]) -> list[str]:
    """Validate canonical finding entries.

    Args:
        line_list: Nonblank lines below one Findings heading.

    Returns:
        Collected contract errors.
    """

    if not line_list:
        return ["findings section is empty"]
    if list(line_list) == ["- None"]:
        return []
    error_list: list[str] = []
    index = 0
    while index < len(line_list):
        if SEVERITY_PATTERN.fullmatch(line_list[index]) is None:
            error_list.append(f"invalid problem line: {line_list[index]!r}")
            break
        if index + 1 >= len(line_list) or not line_list[index + 1].startswith("  Fix: "):
            error_list.append("every problem must include one indented Fix line")
            break
        if index + 2 >= len(line_list) or not line_list[index + 2].startswith("  Path: "):
            error_list.append("every problem must include one indented Path line")
            break
        path_text = line_list[index + 2][8:].strip()
        path = PurePosixPath(path_text)
        if not path_text or path.is_absolute() or ".." in path.parts:
            error_list.append(f"problem Path must be repository-relative: {path_text!r}")
            break
        index += 3
    return error_list


def _metadata_value_get(line_list: Sequence[str], key: str) -> str | None:
    """Return one exact metadata bullet value.

    Args:
        line_list: Candidate report lines.
        key: Metadata label.

    Returns:
        Stripped value when present.
    """

    prefix = f"- {key}: "
    for line in line_list:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def report_error_list_get(
    report_path: Path,
    *,
    audit_name: str,
    expected_scope_entry_list: Sequence[str],
    expected_scope_mode: str,
) -> list[str]:
    """Validate one final merged audit report.

    Args:
        report_path: Absolute or target-repository-relative report path.
        audit_name: Canonical audit identifier.
        expected_scope_entry_list: Ordered declared scope entries.
        expected_scope_mode: Declared scope mode.

    Returns:
        Collected contract errors.
    """

    path = report_path if report_path.is_absolute() else ROOT / report_path
    expected_name_pattern = re.compile(
        rf"^{re.escape(audit_name)}-[0-9a-fA-F]{{8}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-"
        rf"[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{12}}\.md$"
    )
    error_list: list[str] = []
    if not path.is_relative_to(ROOT / "tmp") or not expected_name_pattern.fullmatch(path.name):
        error_list.append(f"report path must match tmp/{audit_name}-<uuid>.md")
    if not path.is_file():
        error_list.append("report file does not exist")
        return error_list
    line_list = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not line_list or line_list[0] != f"# {_audit_title_get(audit_name)} Report":
        return [*error_list, "report heading mismatch"]
    if _metadata_value_get(line_list, "Scope mode") != expected_scope_mode:
        error_list.append("scope mode mismatch")
    scope_entry_list = [
        line[len("- Scope entry: ") :].strip() for line in line_list if line.startswith("- Scope entry: ")
    ]
    if scope_entry_list != list(expected_scope_entry_list):
        error_list.append("scope entries mismatch")
    if "## Section Results" not in line_list:
        error_list.append("section results heading is missing")
    try:
        verdict_index = line_list.index("## Verdict")
    except ValueError:
        error_list.append("verdict heading is missing")
        return error_list
    status = _metadata_value_get(line_list[verdict_index + 1 :], "Status")
    if status not in {"CLEAN", "FINDINGS"}:
        error_list.append("verdict status must be CLEAN or FINDINGS")
    has_finding = any(SEVERITY_PATTERN.fullmatch(line) for line in line_list)
    if status == "CLEAN" and has_finding:
        error_list.append("CLEAN verdict conflicts with findings")
    if status == "FINDINGS" and not has_finding:
        error_list.append("FINDINGS verdict requires at least one finding")
    return error_list


def section_result_error_list_get(
    result_path: Path,
    *,
    audit_name: str,
    expected_scope: str,
    expected_section: str,
) -> list[str]:
    """Validate one section-agent result artifact.

    Args:
        result_path: Absolute or target-repository-relative result path.
        audit_name: Canonical audit identifier.
        expected_scope: Exact assigned scope.
        expected_section: Exact assigned checklist section.

    Returns:
        Collected contract errors.
    """

    path = result_path if result_path.is_absolute() else ROOT / result_path
    error_list: list[str] = []
    try:
        relative_path = path.relative_to(ROOT)
    except ValueError:
        return ["section result path is outside target repository"]
    if len(relative_path.parts) != 4 or relative_path.parts[:2] != ("tmp", audit_name):
        error_list.append(f"section result path must stay under tmp/{audit_name}/<run_uuid>/")
    elif not relative_path.name.endswith(".result.md"):
        error_list.append("section result filename must end with .result.md")
    else:
        try:
            UUID(relative_path.parts[2])
        except ValueError:
            error_list.append("section result run directory must be one UUID")
    if not path.is_file():
        error_list.append("section result file does not exist")
        return error_list
    line_list = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not line_list or line_list[0] != "# Audit Section Result":
        return [*error_list, "section result heading mismatch"]
    if _metadata_value_get(line_list, "Audit") != audit_name:
        error_list.append("audit name mismatch")
    if _metadata_value_get(line_list, "Section") != expected_section:
        error_list.append("section name mismatch")
    if _metadata_value_get(line_list, "Scope") != expected_scope:
        error_list.append("scope mismatch")
    try:
        findings_index = line_list.index("## Findings")
    except ValueError:
        error_list.append("findings heading is missing")
        return error_list
    error_list.extend(_finding_error_list_get(line_list[findings_index + 1 :]))
    return error_list


def section_result_findings_get(result_path: Path) -> list[str]:
    """Return canonical finding lines from one validated section result.

    Args:
        result_path: Absolute section result path.

    Returns:
        Finding lines below the Findings heading.
    """

    line_list = [line for line in result_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return line_list[line_list.index("## Findings") + 1 :]


def section_result_section_get(result_path: Path) -> str:
    """Return the declared section from one validated section result.

    Args:
        result_path: Absolute section result path.

    Returns:
        Declared section name.
    """

    line_list = [line for line in result_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    section = _metadata_value_get(line_list, "Section")
    if section is None:
        raise ValueError("section result has no Section metadata")
    return section
