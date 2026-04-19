from __future__ import annotations

import argparse
from pathlib import Path

from llm_wiki.init_workspace import initialize_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-wiki")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--workspace", type=Path, required=True)

    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--workspace", type=Path, required=True)
    ingest_parser.add_argument("--target", type=Path, required=True)

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("--workspace", type=Path, required=True)
    query_parser.add_argument("--project", required=True)

    rebuild_indexes_parser = subparsers.add_parser("rebuild-indexes")
    rebuild_indexes_parser.add_argument("--workspace", type=Path, required=True)

    lint_parser = subparsers.add_parser("lint")
    lint_parser.add_argument("--workspace", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        initialize_workspace(args.workspace)
        return 0
    raise NotImplementedError(f"{args.command} is not implemented yet")


if __name__ == "__main__":
    raise SystemExit(main())
