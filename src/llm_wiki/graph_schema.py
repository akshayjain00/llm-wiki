"""LLM Wiki Phase 3 — graph SQL schema definitions.

Column names match server.py's actual SELECT queries.  Deviations from
the spec document are noted inline.
"""
from __future__ import annotations

GRAPH_SCHEMA_VERSION = 1

# DDL for all graph tables and their indexes.
GRAPH_SCHEMA_STATEMENTS = (
    # ── Nodes ────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS graph_nodes (
        node_id        TEXT PRIMARY KEY,
        node_type      TEXT NOT NULL,
        canonical_name TEXT NOT NULL,   -- spec calls this "title"
        canonical_path TEXT NOT NULL DEFAULT '',
        project_slug   TEXT NOT NULL DEFAULT '',
        content_hash   TEXT NOT NULL DEFAULT '',
        metadata_json  TEXT NOT NULL DEFAULT '{}',
        created_at     TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_graph_nodes_type   ON graph_nodes(node_type)",
    "CREATE INDEX IF NOT EXISTS idx_graph_nodes_proj   ON graph_nodes(project_slug)",

    # ── Edges ────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS graph_edges (
        edge_id        TEXT PRIMARY KEY,
        source_node_id TEXT NOT NULL,
        target_node_id TEXT NOT NULL,
        edge_type      TEXT NOT NULL,
        source_path    TEXT NOT NULL DEFAULT '',
        source_line    INTEGER NOT NULL DEFAULT 0,  -- spec: "line_start"
        confidence     REAL NOT NULL DEFAULT 1.0,
        evidence_text  TEXT NOT NULL DEFAULT '',
        created_at     TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_graph_edges_src    ON graph_edges(source_node_id)",
    "CREATE INDEX IF NOT EXISTS idx_graph_edges_tgt    ON graph_edges(target_node_id)",
    "CREATE INDEX IF NOT EXISTS idx_graph_edges_type   ON graph_edges(edge_type)",

    # ── Entity aliases ───────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS entity_aliases (
        alias_id         TEXT PRIMARY KEY,
        node_id          TEXT NOT NULL,  -- spec: "entity_id"
        alias            TEXT NOT NULL,  -- spec: "alias_text"
        normalized_alias TEXT NOT NULL,
        source           TEXT NOT NULL,
        confidence       REAL NOT NULL DEFAULT 1.0
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_entity_aliases_norm ON entity_aliases(normalized_alias)",
    "CREATE INDEX IF NOT EXISTS idx_entity_aliases_node ON entity_aliases(node_id)",

    # ── Link proposals ───────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS link_proposals (
        proposal_id        TEXT PRIMARY KEY,
        source_path        TEXT NOT NULL,
        target_node_id     TEXT NOT NULL,
        target_title       TEXT NOT NULL DEFAULT '',   -- extra col vs spec
        proposal_kind      TEXT NOT NULL DEFAULT 'missing_internal_link',
        original_text      TEXT NOT NULL,
        replacement_markdown TEXT NOT NULL,
        source_line        INTEGER NOT NULL DEFAULT 0,  -- spec: "line_start"
        char_start         INTEGER NOT NULL DEFAULT 0,
        char_end           INTEGER NOT NULL DEFAULT 0,
        base_content_hash  TEXT NOT NULL,
        confidence         REAL NOT NULL,
        rationale          TEXT NOT NULL,
        status             TEXT NOT NULL DEFAULT 'pending',
        created_at         TEXT NOT NULL,
        reviewed_at        TEXT NOT NULL DEFAULT ''
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_link_proposals_status ON link_proposals(status)",
    "CREATE INDEX IF NOT EXISTS idx_link_proposals_src    ON link_proposals(source_path)",

    # ── Rebuild audit log ────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS graph_rebuild_runs (
        run_id               TEXT PRIMARY KEY,
        started_at           TEXT NOT NULL,
        completed_at         TEXT NOT NULL DEFAULT '',
        status               TEXT NOT NULL,
        graph_schema_version INTEGER NOT NULL,
        pages_scanned        INTEGER NOT NULL DEFAULT 0,
        nodes_created        INTEGER NOT NULL DEFAULT 0,
        edges_created        INTEGER NOT NULL DEFAULT 0,
        aliases_created      INTEGER NOT NULL DEFAULT 0,
        proposals_created    INTEGER NOT NULL DEFAULT 0,
        warnings_json        TEXT NOT NULL DEFAULT '[]'
    )
    """,
)
