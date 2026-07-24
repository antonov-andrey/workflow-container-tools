"""Shared report-contract helpers for `code-antipattern-audit` tools."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import re

ALLOWED_OVERALL_VERDICTS = {"CLEAN", "FINDINGS", "NO_AUDITABLE_SCOPE"}
CHECKER_RESULT_RE = re.compile(r"^- `(?P<checker>[^`]+)`: `(?P<status>PASS|FAIL|NOT_RUN)`$")
KEYED_BULLET_RE = re.compile(r"^- `(?P<key>[^`]+)`: (?P<value>.+)$")
KIND_TO_FILENAME_RE = {
    "instrumental": re.compile(
        r"^tmp/code-antipattern-audit-instrumental-(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\.md$"
    ),
    "semantic": re.compile(
        r"^tmp/code-antipattern-audit-semantic-(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\.md$"
    ),
}
REPORT_ROOT_OVERRIDE_ENV_NAME = "CODE_ANTIPATTERN_AUDIT_REPORT_ROOT"
PLUGIN_ROOT = Path(__file__).resolve().parents[4]
INSTRUMENTAL_TEMPLATE_PATH = PLUGIN_ROOT / "lib" / "code-antipattern-audit" / "template" / "instrumental.md"
ROOT = Path(os.environ.get(REPORT_ROOT_OVERRIDE_ENV_NAME, str(Path.cwd()))).resolve()
SEMANTIC_TEMPLATE_PATH = PLUGIN_ROOT / "lib" / "code-antipattern-audit" / "template" / "semantic.md"
KIND_TO_TEMPLATE_PATH = {
    "instrumental": INSTRUMENTAL_TEMPLATE_PATH,
    "semantic": SEMANTIC_TEMPLATE_PATH,
}


def _nonempty_bullet_list_collect(section_line_sequence: Sequence[str]) -> list[str]:
    """Return non-empty bullet lines from one section.

    Args:
        section_line_sequence: Section lines.

    Returns:
        Non-empty bullet lines.
    """

    return [line.strip() for line in section_line_sequence if line.strip()]


def confirmed_case_count(parsed: ParsedReport) -> int:
    """Count non-empty confirmed-case bullets in one parsed report.

    Args:
        parsed: Parsed report.

    Returns:
        Count of non-`None` confirmed-case bullets.
    """

    count = 0
    for line in _nonempty_bullet_list_collect(parsed.section_map.get("Confirmed anti-pattern cases", ())):
        if line == "- None":
            continue
        count += 1
    return count


def _report_kind_get(relpath: str) -> str | None:
    """Infer report kind from repository-relative path.

    Args:
        relpath: Repository-relative report path.

    Returns:
        Report kind or `None`.
    """

    for kind, pattern in KIND_TO_FILENAME_RE.items():
        if pattern.fullmatch(relpath):
            return kind
    return None


def _report_uuid_get(relpath: str) -> str | None:
    """Extract report UUID from repository-relative path.

    Args:
        relpath: Repository-relative report path.

    Returns:
        UUID string or `None`.
    """

    kind = _report_kind_get(relpath)
    if kind is None:
        return None
    match = KIND_TO_FILENAME_RE[kind].fullmatch(relpath)
    if match is None:
        return None
    return match.group("uuid")


def merged_report_relpath_build(instrumental_relpath: str, semantic_relpath: str) -> str:
    """Build deterministic merged-report path from two validated source reports.

    Args:
        instrumental_relpath: Repository-relative instrumental report path.
        semantic_relpath: Repository-relative semantic report path.

    Returns:
        Deterministic merged-report path.
    """

    instrumental_uuid = _report_uuid_get(instrumental_relpath)
    semantic_uuid = _report_uuid_get(semantic_relpath)
    if instrumental_uuid is None or semantic_uuid is None:
        raise ValueError("source report paths do not match canonical anti-pattern report families")
    return f"tmp/code-antipattern-audit-merged-{instrumental_uuid}-{semantic_uuid}.md"


def _backtick_wrapped_text_strip(value: str) -> str:
    """Strip one pair of wrapping backticks when present.

    Args:
        value: Raw keyed-bullet value text.

    Returns:
        Unwrapped value.
    """

    normalized = value.strip()
    if normalized.startswith("`") and normalized.endswith("`") and len(normalized) >= 2:
        return normalized[1:-1]
    return normalized


def _keyed_section_value_map_build(section_line_sequence: Sequence[str]) -> dict[str, str]:
    """Parse keyed bullet values from one section.

    Args:
        section_line_sequence: Lines inside one markdown section.

    Returns:
        Mapping from key name to unwrapped value.
    """

    values: dict[str, str] = {}
    for line in section_line_sequence:
        match = KEYED_BULLET_RE.match(line.strip())
        if match is None:
            continue
        values[match.group("key")] = _backtick_wrapped_text_strip(match.group("value"))
    return values


def _root_relative_get(path: Path) -> str:
    """Return repository-relative POSIX path.

    Args:
        path: Path inside repository root.

    Returns:
        Repository-relative POSIX path.
    """

    return path.resolve().relative_to(ROOT).as_posix()


def _section_parse_result_build(text: str) -> SectionParseResult:
    """Parse level-2 markdown section_map from one report or template.

    Args:
        text: Markdown text.

    Returns:
        Parsed section result.
    """

    order: list[str] = []
    section_map: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        if raw_line.startswith("## "):
            current = raw_line[3:].strip()
            order.append(current)
            section_map[current] = []
            continue
        if current is not None:
            section_map[current].append(raw_line)
    return SectionParseResult(
        section_name_list=order,
        section_line_map=section_map,
    )


def parsed_report_build(path: Path) -> ParsedReport:
    """Parse one anti-pattern report without applying the full validator.

    Args:
        path: Absolute report path.

    Returns:
        Parsed report payload.
    """

    relpath = _root_relative_get(path)
    kind = _report_kind_get(relpath)
    if kind is None:
        raise ValueError(f"path does not match a canonical anti-pattern report family: {relpath}")
    text = path.read_text(encoding="utf-8")
    parsed_sections = _section_parse_result_build(text)
    scope_values = _keyed_section_value_map_build(parsed_sections.section_line_map.get("Scope", ()))
    metadata_values = _keyed_section_value_map_build(parsed_sections.section_line_map.get("Report metadata", ()))
    verdict_values = _keyed_section_value_map_build(parsed_sections.section_line_map.get("Verdict", ()))
    return ParsedReport(
        kind=kind,
        path=path,
        relpath=relpath,
        report_uuid=metadata_values.get("report_uuid", ""),
        scope=scope_values.get("scope", ""),
        overall_verdict=verdict_values.get("overall_verdict", ""),
        section_name_list=parsed_sections.section_name_list,
        section_map=parsed_sections.section_line_map,
        text=text,
    )


def _required_checker_entry_list_collect() -> list[str]:
    """Load canonical instrumental checker inventory from the template.

    Returns:
        Ordered checker entry paths.
    """

    parsed_sections = _section_parse_result_build(INSTRUMENTAL_TEMPLATE_PATH.read_text(encoding="utf-8"))
    entries: list[str] = []
    for line in parsed_sections.section_line_map.get("Checker results", ()):
        match = KEYED_BULLET_RE.match(line.strip())
        if match is not None:
            entries.append(match.group("key"))
    return entries


def _required_section_order_get(kind: str) -> list[str]:
    """Load canonical section order from the selected template.

    Args:
        kind: Report kind.

    Returns:
        Ordered required section names.
    """

    template_path = KIND_TO_TEMPLATE_PATH[kind]
    parsed_sections = _section_parse_result_build(template_path.read_text(encoding="utf-8"))
    return list(parsed_sections.section_name_list)


def report_contract_error_list_collect(path: Path, *, expected_scope: str) -> list[str]:
    """Validate one anti-pattern source-report contract.

    Args:
        path: Absolute report path.
        expected_scope: Required normalized declared scope.

    Returns:
        Collected validation errors.
    """

    errors: list[str] = []
    if not path.is_file():
        return [f"report path does not exist: {path.as_posix()}"]

    try:
        relpath = _root_relative_get(path)
    except ValueError:
        return [f"report path is outside repository root: {path.as_posix()}"]

    kind = _report_kind_get(relpath)
    if kind is None:
        return [f"report path does not match a canonical anti-pattern report family: {relpath}"]

    parsed = parsed_report_build(path)
    if "<fill " in parsed.text:
        errors.append("report still contains unfilled template placeholders")

    expected_sections = _required_section_order_get(kind)
    if parsed.section_name_list != expected_sections:
        errors.append(
            f"section order mismatch: expected {list(expected_sections)}, got {list(parsed.section_name_list)}"
        )

    scope_values = _keyed_section_value_map_build(parsed.section_map.get("Scope", ()))
    metadata_values = _keyed_section_value_map_build(parsed.section_map.get("Report metadata", ()))
    verdict_values = _keyed_section_value_map_build(parsed.section_map.get("Verdict", ()))

    scope = scope_values.get("scope")
    if not scope:
        errors.append("missing `scope` in `## Scope`")
    elif scope != expected_scope:
        errors.append(f"`scope` mismatch: expected {expected_scope!r}, got {scope!r}")

    metadata_report_uuid = metadata_values.get("report_uuid")
    if not metadata_report_uuid:
        errors.append("missing `report_uuid` in `## Report metadata`")
    else:
        path_uuid = _report_uuid_get(relpath)
        if path_uuid is not None and metadata_report_uuid != path_uuid:
            errors.append(f"`report_uuid` mismatch: expected path UUID {path_uuid!r}, got {metadata_report_uuid!r}")

    report_path = metadata_values.get("report_path")
    if not report_path:
        errors.append("missing `report_path` in `## Report metadata`")
    elif report_path != relpath:
        errors.append(f"`report_path` mismatch: expected {relpath!r}, got {report_path!r}")

    overall_verdict = verdict_values.get("overall_verdict")
    if overall_verdict not in ALLOWED_OVERALL_VERDICTS:
        errors.append(f"`overall_verdict` must be one of {sorted(ALLOWED_OVERALL_VERDICTS)}, got {overall_verdict!r}")

    for section_name, section_lines in parsed.section_map.items():
        if section_name in {"Scope", "Report metadata", "Verdict"}:
            continue
        if not _nonempty_bullet_list_collect(section_lines):
            errors.append(f"`## {section_name}` is empty")

    if kind == "instrumental":
        checker_lines = _nonempty_bullet_list_collect(parsed.section_map.get("Checker results", ()))
        parsed_checker_entries: list[str] = []
        for line in checker_lines:
            match = CHECKER_RESULT_RE.match(line)
            if match is None:
                errors.append(f"invalid checker-result line: {line!r}")
                continue
            parsed_checker_entries.append(match.group("checker"))
        if parsed_checker_entries != _required_checker_entry_list_collect():
            errors.append(
                f"`## Checker results` inventory mismatch: expected {list(_required_checker_entry_list_collect())}, got {parsed_checker_entries}"
            )

    case_count = confirmed_case_count(parsed)
    if overall_verdict == "CLEAN" and case_count > 0:
        errors.append("`overall_verdict` CLEAN is inconsistent with non-empty `Confirmed anti-pattern cases`")
    if overall_verdict == "FINDINGS" and case_count == 0:
        errors.append("`overall_verdict` FINDINGS is inconsistent with empty `Confirmed anti-pattern cases`")
    if overall_verdict == "NO_AUDITABLE_SCOPE" and case_count > 0:
        errors.append(
            "`overall_verdict` NO_AUDITABLE_SCOPE is inconsistent with non-empty `Confirmed anti-pattern cases`"
        )

    return errors


def source_report_heading_level_demote(text: str) -> str:
    """Embed one source report under a merged report by demoting section headings.

    Args:
        text: Full source report text.

    Returns:
        Embedded markdown without the top-level report heading.
    """

    lines = text.splitlines()
    body: list[str] = []
    skipping_lead = True
    for line in lines:
        if skipping_lead and line.startswith("# "):
            continue
        if skipping_lead and line == "":
            continue
        skipping_lead = False
        if line.startswith("## "):
            body.append(f"### {line[3:]}")
            continue
        body.append(line)
    return "\n".join(body).rstrip() + "\n"


@dataclass(frozen=True)
class ParsedReport:
    """Represent one parsed anti-pattern audit report."""

    kind: str
    overall_verdict: str
    path: Path
    relpath: str
    report_uuid: str
    scope: str
    section_map: dict[str, list[str]]
    section_name_list: list[str]
    text: str


@dataclass(frozen=True)
class SectionParseResult:
    """Represent parsed level-2 markdown section_map."""

    section_line_map: dict[str, list[str]]
    section_name_list: list[str]
