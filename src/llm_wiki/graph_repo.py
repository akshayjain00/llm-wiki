"""LLM Wiki Phase 3 — SQLite graph repository.

All write operations clear-and-repopulate in a single transaction to keep
the rebuild atomic.  Read operations are used by CLI, MCP, and UI.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from llm_wiki.graph_models import (
    Backlink,
    EntityAlias,
    GraphEdge,
    GraphNode,
    GraphRebuildResult,
    GraphSummary,
    LinkProposal,
)
from llm_wiki.state_db import ensure_graph_schema, index_db_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conn(workspace: Path) -> sqlite3.Connection:
    db = index_db_path(workspace)
    ensure_graph_schema(db)
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    return c


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Write (rebuild — clears and repopulates graph tables atomically)
# ---------------------------------------------------------------------------

def clear_graph_tables(conn: sqlite3.Connection) -> None:
    """Drop all graph rows in dependency order (no FK constraints in SQLite)."""
    for tbl in ("link_proposals", "graph_edges", "entity_aliases", "graph_nodes"):
        conn.execute(f"DELETE FROM {tbl}")


def insert_nodes(conn: sqlite3.Connection, nodes: list[GraphNode]) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO graph_nodes
        (node_id, node_type, canonical_name, canonical_path, project_slug,
         content_hash, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (n.node_id, n.node_type, n.canonical_name, n.canonical_path,
             n.project_slug, n.content_hash, n.metadata_json, n.created_at)
            for n in nodes
        ],
    )


def insert_edges(conn: sqlite3.Connection, edges: list[GraphEdge]) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO graph_edges
        (edge_id, source_node_id, target_node_id, edge_type, source_path,
         source_line, confidence, evidence_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (e.edge_id, e.source_node_id, e.target_node_id, e.edge_type,
             e.source_path, e.source_line, e.confidence, e.evidence_text, e.created_at)
            for e in edges
        ],
    )


def insert_aliases(conn: sqlite3.Connection, aliases: list[EntityAlias]) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO entity_aliases
        (alias_id, node_id, alias, normalized_alias, source, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (a.alias_id, a.node_id, a.alias, a.normalized_alias, a.source, a.confidence)
            for a in aliases
        ],
    )


def insert_proposals(conn: sqlite3.Connection, proposals: list[LinkProposal]) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO link_proposals
        (proposal_id, source_path, target_node_id, target_title, proposal_kind,
         original_text, replacement_markdown, source_line, char_start, char_end,
         base_content_hash, confidence, rationale, status, created_at, reviewed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (p.proposal_id, p.source_path, p.target_node_id, p.target_title,
             p.proposal_kind, p.original_text, p.replacement_markdown,
             p.source_line, p.char_start, p.char_end, p.base_content_hash,
             p.confidence, p.rationale, p.status, p.created_at, p.reviewed_at)
            for p in proposals
        ],
    )


def record_rebuild_run(conn: sqlite3.Connection, result: GraphRebuildResult) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO graph_rebuild_runs
        (run_id, started_at, completed_at, status, graph_schema_version,
         pages_scanned, nodes_created, edges_created, aliases_created,
         proposals_created, warnings_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.run_id,
            result.started_at,
            result.completed_at,
            result.status,
            1,  # GRAPH_SCHEMA_VERSION
            result.pages_scanned,
            result.nodes_created,
            result.edges_created,
            result.aliases_created,
            result.proposals_created,
            json.dumps(result.warnings),
        ),
    )


# ---------------------------------------------------------------------------
# Read — used by CLI, MCP, and UI via server.py
# ---------------------------------------------------------------------------

def get_summary(workspace: Path, project_slug: str | None = None) -> GraphSummary:
    conn = _conn(workspace)
    try:
        if not _table_exists(conn, "graph_nodes"):
            return GraphSummary(0, 0, 0, 0, 0, "")

        if project_slug:
            nodes = conn.execute(
                "SELECT COUNT(*) FROM graph_nodes WHERE project_slug=?", (project_slug,)
            ).fetchone()[0]
            pages = conn.execute(
                "SELECT COUNT(*) FROM graph_nodes WHERE node_type='page' AND project_slug=?",
                (project_slug,),
            ).fetchone()[0]
            entities = conn.execute(
                "SELECT COUNT(*) FROM graph_nodes WHERE node_type='entity' AND project_slug=?",
                (project_slug,),
            ).fetchone()[0]
            edges = conn.execute(
                """
                SELECT COUNT(*) FROM graph_edges
                WHERE source_node_id IN (
                    SELECT node_id FROM graph_nodes WHERE project_slug=?
                )
                """,
                (project_slug,),
            ).fetchone()[0]
        else:
            nodes = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
            pages = conn.execute(
                "SELECT COUNT(*) FROM graph_nodes WHERE node_type='page'"
            ).fetchone()[0]
            entities = conn.execute(
                "SELECT COUNT(*) FROM graph_nodes WHERE node_type='entity'"
            ).fetchone()[0]
            edges = conn.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]

        pending = 0
        if _table_exists(conn, "link_proposals"):
            pending = conn.execute(
                "SELECT COUNT(*) FROM link_proposals WHERE status='pending'"
            ).fetchone()[0]

        last_rebuild = ""
        if _table_exists(conn, "graph_rebuild_runs"):
            row = conn.execute(
                "SELECT completed_at FROM graph_rebuild_runs WHERE status='success' "
                "ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            if row:
                last_rebuild = row[0] or ""

        return GraphSummary(
            nodes=nodes,
            edges=edges,
            entities=entities,
            pages=pages,
            pending_link_proposals=pending,
            last_rebuild_at=last_rebuild,
        )
    finally:
        conn.close()


def list_backlinks(workspace: Path, target: str, limit: int = 50) -> list[Backlink]:
    """Return backlinks for a given node_id or canonical_name."""
    conn = _conn(workspace)
    try:
        if not _table_exists(conn, "graph_edges"):
            return []

        # Resolve target to node_id
        node_id = target
        if not target.startswith(("page:", "project:", "entity:")):
            row = conn.execute(
                "SELECT node_id FROM graph_nodes WHERE canonical_name=? LIMIT 1",
                (target,),
            ).fetchone()
            if row:
                node_id = row[0]
            else:
                row = conn.execute(
                    "SELECT node_id FROM entity_aliases WHERE normalized_alias=? LIMIT 1",
                    (target.lower(),),
                ).fetchone()
                if row:
                    node_id = row[0]

        rows = conn.execute(
            """
            SELECT e.source_node_id, n.canonical_name, e.edge_type,
                   e.evidence_text, e.source_line
            FROM graph_edges e
            LEFT JOIN graph_nodes n ON n.node_id = e.source_node_id
            WHERE e.target_node_id = ?
            ORDER BY e.confidence DESC, e.source_line ASC
            LIMIT ?
            """,
            (node_id, limit),
        ).fetchall()

        return [
            Backlink(
                source_node_id=r[0],
                source_title=r[1] or r[0],
                edge_type=r[2],
                evidence_text=r[3] or "",
                source_line=r[4] or 0,
            )
            for r in rows
        ]
    finally:
        conn.close()


def list_proposals(
    workspace: Path, status: str = "pending", limit: int = 50
) -> list[LinkProposal]:
    conn = _conn(workspace)
    try:
        if not _table_exists(conn, "link_proposals"):
            return []
        rows = conn.execute(
            """
            SELECT proposal_id, source_path, target_node_id, target_title,
                   proposal_kind, original_text, replacement_markdown, source_line,
                   char_start, char_end, base_content_hash, confidence, rationale,
                   status, created_at, reviewed_at
            FROM link_proposals
            WHERE status=?
            ORDER BY confidence DESC
            LIMIT ?
            """,
            (status, limit),
        ).fetchall()
        return [
            LinkProposal(
                proposal_id=r[0],
                source_path=r[1],
                target_node_id=r[2],
                target_title=r[3],
                proposal_kind=r[4],
                original_text=r[5],
                replacement_markdown=r[6],
                source_line=r[7],
                char_start=r[8],
                char_end=r[9],
                base_content_hash=r[10],
                confidence=r[11],
                rationale=r[12],
                status=r[13],
                created_at=r[14],
                reviewed_at=r[15] or "",
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_page(workspace: Path, path_or_id: str) -> dict[str, object] | None:
    """Return page metadata + content for a given path or node_id."""
    conn = _conn(workspace)
    try:
        # Resolve
        node_id = path_or_id if path_or_id.startswith("page:") else f"page:{path_or_id}"
        row = conn.execute(
            "SELECT node_id, canonical_name, canonical_path, project_slug, content_hash "
            "FROM graph_nodes WHERE node_id=? AND node_type='page'",
            (node_id,),
        ).fetchone()
        if not row:
            # Try by canonical_path
            row = conn.execute(
                "SELECT node_id, canonical_name, canonical_path, project_slug, content_hash "
                "FROM graph_nodes WHERE canonical_path=? AND node_type='page'",
                (path_or_id,),
            ).fetchone()
        if not row:
            return None

        page_path = workspace / row[2]
        content = ""
        if page_path.is_file():
            content = page_path.read_text(errors="replace")

        return {
            "node_id": row[0],
            "title": row[1],
            "path": row[2],
            "project_slug": row[3],
            "content_hash": row[4],
            "content": content,
        }
    finally:
        conn.close()


def get_entity(workspace: Path, entity_id_or_name: str) -> dict[str, object] | None:
    """Return entity metadata with aliases, backlinks count, and edges."""
    conn = _conn(workspace)
    try:
        # Try direct node_id lookup
        row = conn.execute(
            "SELECT node_id, canonical_name, project_slug FROM graph_nodes WHERE node_id=?",
            (entity_id_or_name,),
        ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT node_id, canonical_name, project_slug FROM graph_nodes "
                "WHERE canonical_name=? LIMIT 1",
                (entity_id_or_name,),
            ).fetchone()
        if not row:
            # Try alias lookup
            alias_row = conn.execute(
                "SELECT node_id FROM entity_aliases WHERE normalized_alias=? LIMIT 1",
                (entity_id_or_name.lower(),),
            ).fetchone()
            if alias_row:
                row = conn.execute(
                    "SELECT node_id, canonical_name, project_slug FROM graph_nodes WHERE node_id=?",
                    (alias_row[0],),
                ).fetchone()
        if not row:
            return None

        node_id, name, project_slug = row[0], row[1], row[2]

        aliases = [
            a[0] for a in conn.execute(
                "SELECT alias FROM entity_aliases WHERE node_id=?", (node_id,)
            ).fetchall()
        ]
        backlink_count = conn.execute(
            "SELECT COUNT(*) FROM graph_edges WHERE target_node_id=?", (node_id,)
        ).fetchone()[0]

        return {
            "node_id": node_id,
            "canonical_name": name,
            "project_slug": project_slug,
            "aliases": aliases,
            "backlink_count": backlink_count,
        }
    finally:
        conn.close()


def search_wiki(
    workspace: Path,
    query: str,
    project_slugs: list[str] | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    """Simple lexical search over node canonical_names and aliases."""
    conn = _conn(workspace)
    try:
        q_lower = query.lower()
        results: list[dict[str, object]] = []

        # Search graph_nodes by canonical_name
        rows = conn.execute(
            "SELECT node_id, node_type, canonical_name, project_slug "
            "FROM graph_nodes WHERE lower(canonical_name) LIKE ? ORDER BY node_type LIMIT ?",
            (f"%{q_lower}%", limit * 2),
        ).fetchall()
        for r in rows:
            if project_slugs and r[3] not in project_slugs:
                continue
            results.append({
                "node_id": r[0],
                "node_type": r[1],
                "title": r[2],
                "project_slug": r[3],
                "match": "title",
            })

        # Search aliases
        alias_rows = conn.execute(
            "SELECT a.node_id, a.alias, n.node_type, n.canonical_name, n.project_slug "
            "FROM entity_aliases a JOIN graph_nodes n ON n.node_id=a.node_id "
            "WHERE lower(a.alias) LIKE ? LIMIT ?",
            (f"%{q_lower}%", limit * 2),
        ).fetchall()
        seen = {r["node_id"] for r in results}
        for r in alias_rows:
            if r[0] in seen:
                continue
            if project_slugs and r[4] not in project_slugs:
                continue
            results.append({
                "node_id": r[0],
                "node_type": r[2],
                "title": r[3],
                "project_slug": r[4],
                "match": f"alias:{r[1]}",
            })
            seen.add(r[0])

        return results[:limit]
    finally:
        conn.close()
