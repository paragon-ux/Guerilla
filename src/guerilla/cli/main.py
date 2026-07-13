"""CLI entry point and argument dispatch.

Phase 1: Only help and version are implemented.
Later phases add workspace, graph, adapter, and view subcommands.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from guerilla import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="guerilla",
        description="Guerilla -- authoritative causal-lineage and continuity layer",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"guerilla {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=False)

    # version subcommand with optional JSON output
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument(
        "--json",
        action="store_true",
        help="Output version as JSON",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        if args.json:
            json.dump(
                {
                    "package": "guerilla",
                    "version": __version__,
                    "python": sys.version,
                },
                sys.stdout,
                indent=2,
            )
            sys.stdout.write("\n")
        else:
            print(f"guerilla {__version__}")
    elif args.command is None:
        parser.print_help()
    else:
        print(f"guerilla: unknown command '{args.command}'", file=sys.stderr)
        sys.exit(2)
