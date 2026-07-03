"""Command line interface for workflow-container developer tooling."""

import argparse
from pathlib import Path

from workflow_container_developer.audit import WorkflowContainerAudit
from workflow_container_developer.project import WorkflowContainerProjectFinder


def main(argv: list[str] | None = None) -> int:
    """Run the workflow-container developer CLI.

    Args:
        argv: Optional argument list for tests.

    Returns:
        Process exit code.
    """

    parser = argparse.ArgumentParser(prog="workflow-container-dev")
    parser.add_argument("--developer-path", default=Path.cwd(), type=Path)
    parser.add_argument("--version", action="version", version="workflow-container-dev 0.1.0")
    subparser = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparser.add_parser("audit")
    audit_parser.add_argument("target")
    subparser.add_parser("list")
    args = parser.parse_args(argv)

    finder = WorkflowContainerProjectFinder(developer_path=args.developer_path)
    if args.command == "audit":
        project = finder.project_get(args.target)
        result = WorkflowContainerAudit(project=project).result_get()
        for warning in result.warning_list:
            print(f"WARNING {warning}")
        if result.is_ok:
            print(f"OK {project.name}")
            return 0
        for error in result.error_list:
            print(f"ERROR {error}")
        return 1
    if args.command == "list":
        for project in finder.project_list_get():
            print(f"{project.name}\t{project.path}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
