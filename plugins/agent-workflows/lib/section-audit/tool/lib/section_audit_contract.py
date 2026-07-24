"""Shared contract helpers for section-based audit validators."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path, PurePosixPath
import re
from uuid import UUID

_BULLET_VALUE_RE = re.compile(r"^\s*-\s+(.*?)\s*$")
_PROBLEM_ENTRY_LINE_RE = re.compile(r"^\s*-\s+(High|Medium|Low):\s+.+$")
_PROBLEM_FIX_LINE_RE = re.compile(r"^\s*Fix:\s+.+$")


def bullet_field_value_get(line: str, *, label: str) -> str | None:
    """Return one bullet field value with tolerant spacing, or `None`.

    Args:
        line: Source markdown line.
        label: Expected field label before `:`.

    Returns:
        Stripped field value, or `None` when the line does not match.
    """

    match = re.fullmatch(rf"^\s*-\s*{re.escape(label)}\s*:\s*(.*?)\s*$", line)
    if match is None:
        return None
    return match.group(1).strip()


def bullet_header_match(line: str, *, label: str) -> bool:
    """Return whether one bullet header matches with tolerant spacing.

    Args:
        line: Source markdown line.
        label: Expected literal header text after `-`.

    Returns:
        `True` when the line matches the expected bullet header.
    """

    return re.fullmatch(rf"^\s*-\s*{re.escape(label)}\s*$", line) is not None


def bullet_value_get(line: str) -> str | None:
    """Return one bullet value with tolerant indentation, or `None`.

    Args:
        line: Source markdown line.

    Returns:
        Stripped bullet value, or `None` when the line is not one bullet.
    """

    match = _BULLET_VALUE_RE.fullmatch(line)
    if match is None:
        return None
    return match.group(1).strip()


def _line_field_value_get(line: str, *, label: str) -> str | None:
    """Return one non-bullet field value with tolerant spacing, or `None`.

    Args:
        line: Source markdown line.
        label: Expected field label before `:`.

    Returns:
        Stripped field value, or `None` when the line does not match.
    """

    match = re.fullmatch(rf"^\s*{re.escape(label)}\s*:\s*(.*?)\s*$", line)
    if match is None:
        return None
    return match.group(1).strip()


def _problem_line_error_list_collect(
    problem_line_list: Sequence[str],
    *,
    expected_item_heading: str,
    status: str,
) -> list[str]:
    """Collect contract errors from one problem-line block.

    Args:
        problem_line_list: Problem block lines after the `Problems:` header.
        expected_item_heading: Expected literal checklist item heading.
        status: Checklist result status.

    Returns:
        Collected error messages.
    """

    errors: list[str] = []
    if not problem_line_list:
        return [f"{expected_item_heading}: problems list must not be empty"]
    if status != "Problems":
        if len(problem_line_list) != 1 or bullet_value_get(problem_line_list[0]) != "None":
            errors.append(f"{expected_item_heading}: non-problem statuses must use exactly one nested `None` bullet")
        return errors

    if any(bullet_value_get(line) == "None" for line in problem_line_list):
        errors.append(f"{expected_item_heading}: problems status must not use the empty-problems marker")
        return errors

    index = 0
    while index < len(problem_line_list):
        if _PROBLEM_ENTRY_LINE_RE.fullmatch(problem_line_list[index]) is None:
            errors.append(f"{expected_item_heading}: invalid problem-entry line {problem_line_list[index]!r}")
            break
        if index + 1 >= len(problem_line_list) or _PROBLEM_FIX_LINE_RE.fullmatch(problem_line_list[index + 1]) is None:
            errors.append(f"{expected_item_heading}: problem entry must include one nested Fix line")
            break
        if index + 2 >= len(problem_line_list):
            errors.append(f"{expected_item_heading}: problem entry must include one nested Path line")
            break
        problem_path = _line_field_value_get(problem_line_list[index + 2], label="Path")
        if problem_path is None:
            errors.append(f"{expected_item_heading}: problem entry must include one nested Path line")
            break
        path_error = _repository_relative_path_error_get(problem_path)
        if path_error is not None:
            errors.append(f"{expected_item_heading}: problem Path must be repository-relative: {problem_path}")
            break

        index += 3
        while index < len(problem_line_list) and _PROBLEM_ENTRY_LINE_RE.fullmatch(problem_line_list[index]) is None:
            if not problem_line_list[index].strip():
                errors.append(f"{expected_item_heading}: continuation lines must not be empty")
                break
            index += 1
    return errors


def _repository_relative_path_error_get(path_text: str) -> str | None:
    """Return an error for one non-repository-relative path value.

    Args:
        path_text: Path text to validate.

    Returns:
        Error text, or `None` when the path is repository-relative.
    """

    path_value = path_text.strip()
    if not path_value:
        return "path must not be empty"
    if Path(path_value).is_absolute():
        return "path must not be absolute"
    path = PurePosixPath(path_value)
    if ".." in path.parts:
        return "path must not contain parent traversal"
    return None


def finding_tail_error_list_collect(
    line_list: Sequence[str],
    *,
    expected_item_heading: str,
    status_value_set: set[str],
) -> list[str]:
    """Collect contract errors from one checklist-result findings tail.

    Args:
        line_list: Checklist-result lines starting from `- Status: ...`.
        expected_item_heading: Expected literal checklist item heading.
        status_value_set: Allowed status values.

    Returns:
        Collected error messages.
    """

    errors: list[str] = []
    if len(line_list) < 4:
        return [f"{expected_item_heading}: findings block is incomplete"]
    status = bullet_field_value_get(line_list[0], label="Status")
    if status is None:
        return [f"{expected_item_heading}: status line is missing"]
    if status not in status_value_set:
        return [f"{expected_item_heading}: invalid status {status!r}"]

    applicability = bullet_field_value_get(line_list[1], label="Applicability")
    if status == "Not applicable":
        if applicability is None or not applicability.startswith("Not applicable because "):
            errors.append(f"{expected_item_heading}: not-applicable status requires an explicit reason")
    else:
        if applicability != "Applicable.":
            errors.append(f"{expected_item_heading}: applicable status requires the literal applicability line")

    check_summary = bullet_field_value_get(line_list[2], label="Check summary")
    if check_summary is None or not check_summary:
        errors.append(f"{expected_item_heading}: check summary line is missing or empty")
    if not bullet_header_match(line_list[3], label="Problems:"):
        errors.append(f"{expected_item_heading}: problems section header is invalid")
        return errors

    errors.extend(
        _problem_line_error_list_collect(line_list[4:], expected_item_heading=expected_item_heading, status=status)
    )
    return errors


def heading_text_get(line: str, *, level: int) -> str | None:
    """Return one markdown heading text for the requested level, or `None`.

    Args:
        line: Source markdown line.
        level: Exact heading level to match.

    Returns:
        Stripped heading text, or `None` when the line does not match.
    """

    heading_marker = "#" * level
    match = re.fullmatch(rf"^\s*{re.escape(heading_marker)}\s+(.*?)\s*$", line)
    if match is None:
        return None
    return match.group(1).strip()


def nonblank_line_list_get(text: str) -> list[str]:
    """Return the nonblank lines from one markdown text.

    Args:
        text: Source markdown text.

    Returns:
        Ordered nonblank lines.
    """

    return [line for line in text.splitlines() if line.strip()]


def section_block_line_list_collect(line_list: Sequence[str], *, heading_level: int) -> list[list[str]]:
    """Split one markdown line stream into heading-owned blocks.

    Args:
        line_list: Ordered markdown lines, usually already filtered to nonblank lines.
        heading_level: Heading level that starts each block.

    Returns:
        Ordered blocks whose first line is the requested heading level.
    """

    block_line_list: list[list[str]] = []
    current_block: list[str] = []
    for line in line_list:
        if heading_text_get(line, level=heading_level) is not None:
            if current_block:
                block_line_list.append(current_block)
            current_block = [line]
            continue
        if current_block:
            current_block.append(line)
    if current_block:
        block_line_list.append(current_block)
    return block_line_list


def _section_slug_get(checklist_section: str) -> str:
    """Return the stable snake_case slug for one checklist-section heading.

    Args:
        checklist_section: Literal top-level checklist-section heading.

    Returns:
        Stable snake_case slug.
    """

    return re.sub(r"_+", "_", re.sub(r"[^0-9a-z]+", "_", checklist_section.lower())).strip("_")


def task_result_path_error_list_collect(
    task_result_path: Path,
    *,
    audit_name: str,
    expected_checklist_section: str,
    root: Path,
) -> list[str]:
    """Collect path-family contract errors for one section-task result file.

    Args:
        task_result_path: Absolute or repository-relative task-result path.
        audit_name: Audit name used under `tmp/`.
        expected_checklist_section: Expected literal top-level checklist-section heading.
        root: Repository root.

    Returns:
        Collected error messages.
    """

    path = task_result_path if task_result_path.is_absolute() else root / task_result_path
    error_message = f"task-result path must match tmp/{audit_name}/<run_uuid>/<section_slug>.<agent_id>.result.md"
    try:
        relpath = path.relative_to(root)
    except ValueError:
        return [error_message]

    if len(relpath.parts) != 4 or relpath.parts[0] != "tmp" or relpath.parts[1] != audit_name:
        return [error_message]
    try:
        UUID(relpath.parts[2])
    except ValueError:
        return [error_message]

    section_slug = _section_slug_get(expected_checklist_section)
    filename = relpath.parts[3]
    prefix = f"{section_slug}."
    suffix = ".result.md"
    if not filename.startswith(prefix) or not filename.endswith(suffix):
        return [error_message]
    agent_id = filename[len(prefix) : -len(suffix)]
    try:
        UUID(agent_id)
    except ValueError:
        return [error_message]
    return []
