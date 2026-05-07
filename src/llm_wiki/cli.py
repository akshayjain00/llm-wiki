from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llm_wiki.ingest import run_ingest
from llm_wiki.health import run_health_checks
from llm_wiki.init_workspace import initialize_workspace
from llm_wiki.indexes import write_indexes
from llm_wiki.lint import run_lint, write_lint_outputs
from llm_wiki.migration import migrate_workspace_to_v2
from llm_wiki.query import answer_multi_project_query, answer_project_orientation
from llm_wiki.retrieval_index import rebuild_retrieval_index
from llm_wiki.writeback import approve_writeback


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
    query_parser.add_argument("--project", action="append", required=True)
    query_parser.add_argument("--question")

    rebuild_indexes_parser = subparsers.add_parser("rebuild-indexes")
    rebuild_indexes_parser.add_argument("--workspace", type=Path, required=True)

    rebuild_retrieval_parser = subparsers.add_parser("rebuild-retrieval")
    rebuild_retrieval_parser.add_argument("--workspace", type=Path, required=True)

    health_parser = subparsers.add_parser("health")
    health_parser.add_argument("--workspace", type=Path, required=True)

    migrate_parser = subparsers.add_parser("migrate-workspace")
    migrate_parser.add_argument("--workspace", type=Path, required=True)
    migrate_parser.add_argument("--target-version", type=int, required=True)

    approve_writeback_parser = subparsers.add_parser("approve-writeback")
    approve_writeback_parser.add_argument("--workspace", type=Path, required=True)
    approve_writeback_parser.add_argument("--proposal-id", required=True)

    lint_parser = subparsers.add_parser("lint")
    lint_parser.add_argument("--workspace", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "init":
            initialize_workspace(args.workspace)
            return 0
        if args.command == "ingest":
            run_ingest(args.workspace, args.target)
            return 0
        if args.command == "rebuild-indexes":
            write_indexes(args.workspace)
            return 0
        if args.command == "rebuild-retrieval":
            rebuild_retrieval_index(args.workspace)
            dirty_flag = args.workspace / "state" / "retrieval-dirty.flag"
            if dirty_flag.exists():
                dirty_flag.unlink()
            return 0
        if args.command == "query":
            if args.question is not None:
                print(
                    answer_multi_project_query(args.workspace, args.project, args.question),
                    end="",
                )
                return 0
            if len(args.project) != 1:
                raise ValueError(
                    "Orientation query requires exactly one project when --question is omitted"
                )
            print(answer_project_orientation(args.workspace, args.project[0]), end="")
            return 0
        if args.command == "lint":
            findings = run_lint(args.workspace)
            write_lint_outputs(args.workspace, findings)
            if findings:
                print("\n".join(findings))
            return 0
        if args.command == "health":
            findings = run_health_checks(args.workspace)
            if findings:
                print("\n".join(findings))
            return 0
        if args.command == "migrate-workspace":
            if args.target_version != 2:
                raise ValueError("Only target-version 2 is supported")
            migrated = migrate_workspace_to_v2(args.workspace)
            print(f"Migrated workspace to {migrated}")
            return 0
        if args.command == "approve-writeback":
            target_path = approve_writeback(args.workspace, args.proposal_id)
            print(f"Approved write-back proposal {args.proposal_id}: {target_path}")
            return 0
        raise NotImplementedError(f"{args.command} is not implemented yet")
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
