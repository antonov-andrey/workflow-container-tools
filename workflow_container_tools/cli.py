"""Optional local discovery CLI for adjacent workflow-container projects."""

import argparse
from pathlib import Path

from workflow_container_tools.project import WorkflowContainerProjectFinder


def main(argv: list[str] | None = None) -> int:
    """Run the optional local discovery CLI.

    Args:
        argv: Optional argument list for tests.

    Returns:
        Process exit code.
    """

    parser = argparse.ArgumentParser(prog="python -m workflow_container_tools.cli")
    parser.add_argument("--tools-path", default=Path.cwd(), type=Path)
    subparser = parser.add_subparsers(dest="command", required=True)
    subparser.add_parser("list")
    args = parser.parse_args(argv)

    finder = WorkflowContainerProjectFinder(tools_path=args.tools_path)
    if args.command == "list":
        for project in finder.project_list_get():
            print(f"{project.name}\t{project.path}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
