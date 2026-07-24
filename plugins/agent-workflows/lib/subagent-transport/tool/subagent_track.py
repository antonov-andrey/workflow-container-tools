#!/usr/bin/env python3

"""Print the current tracked status for one subagent."""

from __future__ import annotations

import argparse
import sys

from lib.subagent_track import subagent_status_get


def _args_parse(argv_list: list[str]) -> argparse.Namespace:
    """Parse CLI arguments for the subagent activity tracker.

    Args:
        argv_list: Raw CLI arguments.

    Returns:
        Parsed CLI namespace.
    """

    parser = argparse.ArgumentParser(
        description="Print OK, TIMEOUT, or ERROR_AGENT_ID_NOT_FOUND for one tracked subagent."
    )
    parser.add_argument("--agent-id", required=True, help="Full subagent UUID.")
    return parser.parse_args(argv_list)


def main(argv_list: list[str]) -> int:
    """Run the subagent activity tracker CLI.

    Args:
        argv_list: Raw CLI arguments.

    Returns:
        Process exit code.
    """

    args = _args_parse(argv_list)
    print(subagent_status_get(args.agent_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
