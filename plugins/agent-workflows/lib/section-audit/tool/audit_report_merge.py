#!/usr/bin/env python3
"""Merge validated section audit results into one deterministic report body."""

from __future__ import annotations

import argparse
from pathlib import Path

from lib.audit_contract import ROOT, section_result_findings_get, section_result_section_get


def _args_parse() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-name", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scope-entry", action="append", dest="scope_entry_list", required=True)
    parser.add_argument("--scope-mode", choices=("default-changed", "explicit"), required=True)
    parser.add_argument("section_result_path_list", nargs="+", type=Path)
    return parser.parse_args()


def main() -> int:
    """Merge section results in caller-supplied canonical order."""

    args = _args_parse()
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    result_path_list = [path if path.is_absolute() else ROOT / path for path in args.section_result_path_list]
    title = " ".join(word.capitalize() for word in args.audit_name.split("-"))
    line_list = [
        f"# {title} Report",
        "",
        "## Scope",
        f"- Scope mode: {args.scope_mode}",
        *[f"- Scope entry: {entry}" for entry in args.scope_entry_list],
        "",
        "## Section Results",
    ]
    has_finding = False
    for result_path in result_path_list:
        finding_line_list = section_result_findings_get(result_path)
        has_finding = has_finding or finding_line_list != ["- None"]
        line_list.extend(["", f"### {section_result_section_get(result_path)}", *finding_line_list])
    line_list.extend(["", "## Verdict", f"- Status: {'FINDINGS' if has_finding else 'CLEAN'}", ""])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(line_list), encoding="utf-8")
    print(output_path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
