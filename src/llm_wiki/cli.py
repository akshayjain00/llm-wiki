from __future__ import annotations

import argparse
from pathlib import Path

from llm_wiki.ingest import run_ingest
from llm_wiki.init_workspace import initialize_workspace
from llm_wiki.indexes import write_indexes
from llm_wiki.lint import run_lint, write_lint_outputs
from llm_wiki.query import answer_project_orientation


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
    if args.command == "ingest":
        run_ingest(args.workspace, args.target)
        return 0
    if args.command == "rebuild-indexes":
        write_indexes(args.workspace)
        return 0
    if args.command == "query":
        print(answer_project_orientation(args.workspace / "wiki", args.project), end="")
        return 0
    if args.command == "lint":
        findings = run_lint(args.workspace / "wiki")
        write_lint_outputs(args.workspace, findings)
        if findings:
            print("\n".join(findings))
        return 0
    raise NotImplementedError(f"{args.command} is not implemented yet")


if __name__ == "__main__":
    raise SystemExit(main())
