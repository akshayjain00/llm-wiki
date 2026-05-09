from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from llm_wiki.config import WORKSPACE_SCHEMA_VERSION
from llm_wiki.state_db import index_db_path

_GRAPH_TABLES = (
    "graph_nodes",
    "graph_edges",
    "entity_aliases",
    "link_proposals",
    "graph_rebuild_runs",
)


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def run_health_checks(workspace: Path) -> list[str]:
    findings: list[str] = []
    db_path = index_db_path(workspace)
    if not db_path.exists():
        return ["retrieval database missing"]
    if not (workspace / "logs" / "query-log.md").exists():
        findings.append("query log missing")

    conn = sqlite3.connect(db_path)
    try:
        meta_row = conn.execute(
            "SELECT workspace_version, schema_version FROM workspace_meta LIMIT 1"
        ).fetchone()
        if meta_row is None:
            findings.append("workspace metadata missing")
        elif (
            meta_row[0] != WORKSPACE_SCHEMA_VERSION
            or meta_row[1] != WORKSPACE_SCHEMA_VERSION
            or meta_row[0] != meta_row[1]
        ):
            findings.append("schema version mismatch")

        chunk_count = _count_rows(conn, "chunks")
        if chunk_count == 0:
            findings.append("retrieval index has no chunks")

        if _count_rows(conn, "query_runs") == 0:
            findings.append("no query runs recorded yet")

        embedding_count = _count_rows(conn, "embeddings")
        if chunk_count > 0 and embedding_count == 0:
            findings.append("missing embedding rows")

        fts_count = _count_rows(conn, "fts_chunks")
        if fts_count != chunk_count:
            findings.append("fts index drift detected")

        # ── Phase 3: Graph health checks (FR11) ──────────────────────────────
        # Only check graph state if a wiki directory exists (graph is opt-in per workspace)
        has_wiki = (workspace / "wiki").exists()
        if not has_wiki:
            # No wiki directory → graph checks not applicable
            conn.close()
            return findings

        for tbl in _GRAPH_TABLES:
            if not _table_exists(conn, tbl):
                findings.append(f"graph table missing: {tbl} (run 'llm-wiki rebuild-graph')")

        if _table_exists(conn, "graph_nodes"):
            node_count = _count_rows(conn, "graph_nodes")
            if node_count == 0:
                findings.append("graph has no nodes (run 'llm-wiki rebuild-graph')")

        if _table_exists(conn, "graph_rebuild_runs"):
            last_run = conn.execute(
                "SELECT status FROM graph_rebuild_runs ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            if last_run is None:
                findings.append("graph never rebuilt (run 'llm-wiki rebuild-graph')")
            elif last_run[0] == "failed":
                findings.append("last graph rebuild failed")

        # Stale graph: check if any wiki page files changed since last rebuild
        if _table_exists(conn, "graph_nodes") and _table_exists(conn, "graph_rebuild_runs"):
            last_rebuild_row = conn.execute(
                "SELECT completed_at FROM graph_rebuild_runs WHERE status='success' "
                "ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            if last_rebuild_row and last_rebuild_row[0]:
                stale_count = _check_stale_pages(workspace, conn)
                if stale_count > 0:
                    findings.append(
                        f"graph may be stale: {stale_count} wiki page(s) changed since last rebuild"
                    )

        # Duplicate entity aliases
        if _table_exists(conn, "entity_aliases"):
            dup_row = conn.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT normalized_alias FROM entity_aliases "
                "  GROUP BY normalized_alias HAVING COUNT(DISTINCT node_id) > 1"
                ")"
            ).fetchone()
            if dup_row and dup_row[0] > 0:
                findings.append(
                    f"ambiguous entity aliases detected: {dup_row[0]} normalized alias(es) "
                    "resolve to multiple entities"
                )

        # Stale proposals (base_content_hash mismatch)
        if _table_exists(conn, "link_proposals"):
            stale_props = _check_stale_proposals(workspace, conn)
            if stale_props > 0:
                findings.append(
                    f"stale link proposals: {stale_props} proposal(s) have mismatched content hash"
                )

    finally:
        conn.close()
    return findings


def _check_stale_pages(workspace: Path, conn: sqlite3.Connection) -> int:
    """Return count of pages whose on-disk hash differs from graph_nodes.content_hash."""
    rows = conn.execute(
        "SELECT canonical_path, content_hash FROM graph_nodes WHERE canonical_path != ''"
    ).fetchall()
    stale = 0
    for path_str, stored_hash in rows:
        file_path = workspace / path_str
        if not file_path.is_file():
            continue
        try:
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]
            if actual_hash != stored_hash:
                stale += 1
        except OSError:
            continue
    return stale


def _check_stale_proposals(workspace: Path, conn: sqlite3.Connection) -> int:
    """Return count of pending proposals whose source file hash no longer matches."""
    rows = conn.execute(
        "SELECT source_path, base_content_hash FROM link_proposals WHERE status='pending'"
    ).fetchall()
    stale = 0
    for path_str, stored_hash in rows:
        file_path = workspace / path_str
        if not file_path.is_file():
            stale += 1
            continue
        try:
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if actual_hash != stored_hash:
                stale += 1
        except OSError:
            stale += 1
    return stale
