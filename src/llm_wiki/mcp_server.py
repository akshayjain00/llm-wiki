"""LLM Wiki Phase 3 — read-only MCP server (stdio transport).

Exposes 6 read-only tools and 4 resources over the MCP protocol.

IMPORTANT: This module must never print to stdout.  All logging goes to
stderr.  stdout is reserved exclusively for MCP JSON-RPC messages.

Tools:
  search_wiki          — search by query + optional project filter
  get_page             — retrieve page metadata + content
  get_entity           — resolve entity with aliases and backlinks
  list_backlinks       — backlinks to a page or entity
  list_proposed_edits  — list link proposals by status
  get_graph_summary    — counts and last rebuild timestamp

Resources:
  wiki://page/{page_id}
  wiki://entity/{entity_id}
  wiki://project/{slug}
  wiki://graph/summary
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# All logs to stderr — never stdout
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger("llm_wiki.mcp")


def run_mcp_server(workspace: Path) -> None:
    """Start the FastMCP stdio server.  Blocks until client disconnects."""
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[import-untyped]
    except ImportError as exc:
        logger.error("mcp package not installed: %s", exc)
        sys.exit(1)

    from llm_wiki.graph_builder import get_graph_summary
    from llm_wiki.graph_repo import (
        get_entity,
        get_page,
        list_backlinks,
        list_proposals,
        search_wiki,
    )

    mcp = FastMCP("llm-wiki")

    # ── Validate workspace is safe ────────────────────────────────────────────

    ws = workspace.resolve()

    def _safe_path(path_str: str) -> Path | None:
        """Resolve a path and reject anything outside the workspace."""
        try:
            candidate = (ws / path_str).resolve()
            candidate.relative_to(ws)  # raises ValueError if outside
            return candidate
        except (ValueError, RuntimeError):
            return None

    # ── Tools ─────────────────────────────────────────────────────────────────

    @mcp.tool()
    def search_wiki_tool(
        query: str,
        project_slugs: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """Search wiki pages, entities, and aliases by query text."""
        return search_wiki(ws, query, project_slugs=project_slugs, limit=limit)

    @mcp.tool()
    def get_page_tool(path_or_id: str) -> dict[str, object]:
        """Return page metadata and markdown content. Rejects paths outside workspace."""
        # Security: reject path traversal
        if ".." in path_or_id or path_or_id.startswith("/"):
            return {"error": "invalid_path", "detail": "path must be workspace-relative"}
        result = get_page(ws, path_or_id)
        if result is None:
            return {"error": "not_found", "path_or_id": path_or_id}
        return result

    @mcp.tool()
    def get_entity_tool(entity_id_or_name: str) -> dict[str, object]:
        """Resolve a canonical entity and return aliases, backlinks count, and edges."""
        result = get_entity(ws, entity_id_or_name)
        if result is None:
            return {"error": "not_found", "entity_id_or_name": entity_id_or_name}
        return result

    @mcp.tool()
    def list_backlinks_tool(
        page_or_entity: str,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """Return backlinks for a page or entity from the graph."""
        bls = list_backlinks(ws, page_or_entity, limit=limit)
        return [
            {
                "source_node_id": bl.source_node_id,
                "source_title": bl.source_title,
                "edge_type": bl.edge_type,
                "evidence_text": bl.evidence_text,
                "line_start": bl.source_line,
            }
            for bl in bls
        ]

    @mcp.tool()
    def list_proposed_edits_tool(
        status: str = "pending",
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """List link proposals. Does not apply or approve them."""
        props = list_proposals(ws, status=status, limit=limit)
        return [
            {
                "proposal_id": p.proposal_id,
                "source_path": p.source_path,
                "target_node_id": p.target_node_id,
                "target_title": p.target_title,
                "original_text": p.original_text,
                "replacement_markdown": p.replacement_markdown,
                "confidence": p.confidence,
                "rationale": p.rationale,
                "status": p.status,
            }
            for p in props
        ]

    @mcp.tool()
    def get_graph_summary_tool(project_slug: str | None = None) -> dict[str, object]:
        """Return graph node/edge/proposal counts and last rebuild timestamp."""
        return get_graph_summary(ws, project_slug)

    # ── Resources ─────────────────────────────────────────────────────────────

    @mcp.resource("wiki://graph/summary")
    def resource_graph_summary() -> str:
        summary = get_graph_summary(ws)
        return json.dumps(summary, indent=2)

    @mcp.resource("wiki://page/{page_id}")
    def resource_page(page_id: str) -> str:
        result = get_page(ws, page_id)
        if result is None:
            return json.dumps({"error": "not_found"})
        return json.dumps(result, indent=2)

    @mcp.resource("wiki://entity/{entity_id}")
    def resource_entity(entity_id: str) -> str:
        result = get_entity(ws, entity_id)
        if result is None:
            return json.dumps({"error": "not_found"})
        return json.dumps(result, indent=2)

    @mcp.resource("wiki://project/{slug}")
    def resource_project(slug: str) -> str:
        result = get_entity(ws, f"project:{slug}")
        if result is None:
            return json.dumps({"error": "not_found"})
        return json.dumps(result, indent=2)

    # ── Run ───────────────────────────────────────────────────────────────────

    logger.info("Starting llm-wiki MCP server for workspace: %s", ws)
    mcp.run(transport="stdio")
