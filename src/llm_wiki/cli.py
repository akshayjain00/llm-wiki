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
from llm_wiki.server import serve
from llm_wiki.writeback import approve_writeback
from llm_wiki.graph_builder import rebuild_graph, get_graph_summary
from llm_wiki.graph_repo import list_backlinks, list_proposals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-wiki")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--workspace", type=Path, required=True)

    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the local wiki UI (add --allow-writes to enable project creation)",
    )
    serve_parser.add_argument("--workspace", type=Path, required=True)
    serve_parser.add_argument("--port", type=int, default=5173)
    serve_parser.add_argument("--no-browser", action="store_true", default=False)
    serve_parser.add_argument(
        "--allow-writes",
        action="store_true",
        default=False,
        help="Enable write endpoints (POST /api/projects). Required for the '+ new project' button.",
    )

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

    # ── Phase 3: Graph commands ──────────────────────────────────────────────
    rebuild_graph_parser = subparsers.add_parser(
        "rebuild-graph", help="Rebuild graph tables from durable wiki markdown"
    )
    rebuild_graph_parser.add_argument("--workspace", type=Path, required=True)

    graph_summary_parser = subparsers.add_parser(
        "graph-summary", help="Show graph summary counts"
    )
    graph_summary_parser.add_argument("--workspace", type=Path, required=True)
    graph_summary_parser.add_argument("--project", default=None, help="Filter by project slug")

    backlinks_parser = subparsers.add_parser(
        "backlinks", help="List backlinks to a page or entity"
    )
    backlinks_parser.add_argument("--workspace", type=Path, required=True)
    backlinks_parser.add_argument("--target", required=True, help="node_id or name")
    backlinks_parser.add_argument("--limit", type=int, default=50)

    proposed_links_parser = subparsers.add_parser(
        "proposed-links", help="List proposed cross-link edits"
    )
    proposed_links_parser.add_argument("--workspace", type=Path, required=True)
    proposed_links_parser.add_argument("--status", default="pending")
    proposed_links_parser.add_argument("--limit", type=int, default=50)

    # ── Phase 3: MCP server ──────────────────────────────────────────────────
    mcp_parser = subparsers.add_parser(
        "mcp", help="Start the read-only MCP server (stdio)"
    )
    mcp_parser.add_argument("--workspace", type=Path, required=True)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "serve":
            serve(args.workspace, port=args.port, open_browser=not args.no_browser,
                  allow_writes=args.allow_writes)
            return 0
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

        # ── Phase 3: Graph commands ──────────────────────────────────────────
        if args.command == "rebuild-graph":
            result = rebuild_graph(args.workspace)
            print(f"Graph rebuild: {result.status}")
            print(f"  Pages scanned : {result.pages_scanned}")
            print(f"  Nodes created : {result.nodes_created}")
            print(f"  Edges created : {result.edges_created}")
            print(f"  Aliases       : {result.aliases_created}")
            print(f"  Proposals     : {result.proposals_created}")
            if result.warnings:
                print("  Warnings:")
                for w in result.warnings:
                    print(f"    - {w}")
            return 0 if result.status != "failed" else 1

        if args.command == "graph-summary":
            summary = get_graph_summary(args.workspace, args.project)
            print(f"Nodes    : {summary['nodes']}")
            print(f"Edges    : {summary['edges']}")
            print(f"Pages    : {summary['pages']}")
            print(f"Entities : {summary['entities']}")
            print(f"Pending proposals : {summary['pending_link_proposals']}")
            if summary["last_rebuild_at"]:
                print(f"Last rebuild : {summary['last_rebuild_at']}")
            else:
                print("Last rebuild : never (run 'llm-wiki rebuild-graph')")
            return 0

        if args.command == "backlinks":
            links = list_backlinks(args.workspace, args.target, limit=args.limit)
            if not links:
                print(f"No backlinks found for: {args.target}")
                return 0
            print(f"Backlinks to {args.target} ({len(links)} found):\n")
            for bl in links:
                print(f"  [{bl.edge_type}] {bl.source_title}")
                print(f"    node : {bl.source_node_id}")
                if bl.source_line:
                    print(f"    line : {bl.source_line}")
                if bl.evidence_text:
                    print(f"    text : {bl.evidence_text[:80]}")
                print()
            return 0

        if args.command == "proposed-links":
            proposals = list_proposals(args.workspace, status=args.status, limit=args.limit)
            if not proposals:
                print(f"No {args.status} proposals found.")
                return 0
            print(f"{len(proposals)} {args.status} proposal(s):\n")
            for p in proposals:
                print(f"  [{p.proposal_id}]")
                print(f"    source     : {p.source_path}:{p.source_line}")
                print(f"    target     : {p.target_title} ({p.target_node_id})")
                print(f"    original   : {p.original_text!r}")
                print(f"    replacement: {p.replacement_markdown!r}")
                print(f"    confidence : {p.confidence:.2f}")
                print(f"    rationale  : {p.rationale}")
                print()
            return 0

        if args.command == "mcp":
            from llm_wiki.mcp_server import run_mcp_server
            run_mcp_server(args.workspace)
            return 0

        raise NotImplementedError(f"{args.command} is not implemented yet")
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
