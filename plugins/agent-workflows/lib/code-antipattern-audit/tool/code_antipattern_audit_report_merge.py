#!/usr/bin/env python3

"""Deterministically merge validated `code-antipattern-audit` source reports."""

from __future__ import annotations
import argparse

from lib.report_contract import (
    ROOT,
    confirmed_case_count,
    merged_report_relpath_build,
    parsed_report_build,
    report_contract_error_list_collect,
    source_report_heading_level_demote,
)


def args_parse() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed arguments.
    """

    parser = argparse.ArgumentParser(description="Merge validated code-antipattern-audit source reports.")
    parser.add_argument(
        "instrumental_report",
        help="Repository-relative validated instrumental report path under tmp/.",
    )
    parser.add_argument(
        "semantic_report",
        help="Repository-relative validated semantic report path under tmp/.",
    )
    return parser.parse_args()


def _merged_overall_verdict_get(instrumental_verdict: str, semantic_verdict: str) -> str:
    """Resolve the deterministic merged overall verdict.

    Args:
        instrumental_verdict: Instrumental source verdict.
        semantic_verdict: Semantic source verdict.

    Returns:
        Merged overall verdict.
    """

    if "FINDINGS" in {instrumental_verdict, semantic_verdict}:
        return "FINDINGS"
    if instrumental_verdict == "NO_AUDITABLE_SCOPE" and semantic_verdict == "NO_AUDITABLE_SCOPE":
        return "NO_AUDITABLE_SCOPE"
    return "CLEAN"


def main() -> int:
    """Run the deterministic report merger.

    Returns:
        Process exit code.
    """

    args = args_parse()
    instrumental_path = ROOT / args.instrumental_report
    semantic_path = ROOT / args.semantic_report
    try:
        instrumental = parsed_report_build(instrumental_path)
        semantic = parsed_report_build(semantic_path)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    if instrumental.kind != "instrumental":
        raise SystemExit(f"ERROR: expected instrumental report path, got {instrumental.relpath}")
    if semantic.kind != "semantic":
        raise SystemExit(f"ERROR: expected semantic report path, got {semantic.relpath}")

    instrumental_errors = report_contract_error_list_collect(instrumental_path, expected_scope=instrumental.scope)
    if instrumental_errors:
        raise SystemExit("ERROR: invalid instrumental source report:\n- " + "\n- ".join(instrumental_errors))
    semantic_errors = report_contract_error_list_collect(semantic_path, expected_scope=semantic.scope)
    if semantic_errors:
        raise SystemExit("ERROR: invalid semantic source report:\n- " + "\n- ".join(semantic_errors))
    if instrumental.scope != semantic.scope:
        raise SystemExit(
            f"ERROR: source report scope mismatch: {instrumental.relpath} -> {instrumental.scope!r}, "
            f"{semantic.relpath} -> {semantic.scope!r}"
        )

    merged_relpath = merged_report_relpath_build(instrumental.relpath, semantic.relpath)
    merged_path = ROOT / merged_relpath
    merged_path.parent.mkdir(parents=True, exist_ok=True)

    merged_text = (
        "# `code-antipattern-audit` Report\n\n"
        "## Scope\n"
        f"- `scope`: `{instrumental.scope}`\n\n"
        "## Report metadata\n"
        f"- `report_path`: `{merged_relpath}`\n\n"
        "## Source reports\n"
        f"- `instrumental_report_path`: `{instrumental.relpath}`\n"
        f"- `semantic_report_path`: `{semantic.relpath}`\n\n"
        "## Source verdicts\n"
        f"- `instrumental_overall_verdict`: `{instrumental.overall_verdict}`\n"
        f"- `semantic_overall_verdict`: `{semantic.overall_verdict}`\n"
        f"- `instrumental_confirmed_case_count`: `{confirmed_case_count(instrumental)}`\n"
        f"- `semantic_confirmed_case_count`: `{confirmed_case_count(semantic)}`\n\n"
        "## Instrumental source report\n"
        f"{source_report_heading_level_demote(instrumental.text)}\n"
        "## Semantic source report\n"
        f"{source_report_heading_level_demote(semantic.text)}\n"
        "## Verdict\n"
        f"- `overall_verdict`: `{_merged_overall_verdict_get(instrumental.overall_verdict, semantic.overall_verdict)}`\n"
    )
    merged_path.write_text(merged_text, encoding="utf-8")
    print(merged_relpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
