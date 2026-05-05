from __future__ import annotations

import sqlite3
from pathlib import Path

from llm_wiki.config import WORKSPACE_SCHEMA_VERSION


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS workspace_meta (
        workspace_version INTEGER NOT NULL,
        schema_version INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        migrated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS projects (
        project_slug TEXT PRIMARY KEY,
        project_name TEXT NOT NULL,
        owner TEXT NOT NULL,
        status TEXT NOT NULL,
        canonical_project_card_path TEXT NOT NULL,
        last_ingested TEXT NOT NULL,
        last_indexed TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wiki_pages (
        page_id TEXT PRIMARY KEY,
        project_slug TEXT,
        page_type TEXT NOT NULL,
        path TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        last_modified TEXT NOT NULL,
        manual_edit_detected INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS snapshots (
        snapshot_id TEXT PRIMARY KEY,
        project_slug TEXT NOT NULL,
        snapshot_path TEXT NOT NULL UNIQUE,
        ingested_at TEXT NOT NULL,
        source_root TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS snapshot_files (
        file_id TEXT PRIMARY KEY,
        snapshot_id TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        text_extract_status TEXT NOT NULL,
        text_extract_error TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        source_kind TEXT NOT NULL,
        page_id TEXT,
        file_id TEXT,
        project_slug TEXT NOT NULL,
        chunk_text TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        line_start INTEGER,
        line_end INTEGER,
        token_count INTEGER NOT NULL
    )
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
        chunk_id UNINDEXED,
        project_slug UNINDEXED,
        source_kind UNINDEXED,
        chunk_text
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS embeddings (
        chunk_id TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        vector_blob BLOB NOT NULL,
        embedded_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS query_runs (
        query_id TEXT PRIMARY KEY,
        asked_at TEXT NOT NULL,
        question_text TEXT NOT NULL,
        requested_projects TEXT NOT NULL,
        model_provider TEXT NOT NULL,
        model_name TEXT NOT NULL,
        used_snapshot_fallback INTEGER NOT NULL,
        status TEXT NOT NULL,
        token_input INTEGER NOT NULL,
        token_output INTEGER NOT NULL,
        cost_estimate REAL NOT NULL,
        latency_ms INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS query_evidence (
        query_id TEXT NOT NULL,
        chunk_id TEXT NOT NULL,
        lexical_score REAL NOT NULL,
        semantic_score REAL NOT NULL,
        fused_score REAL NOT NULL,
        rank INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS writeback_proposals (
        proposal_id TEXT PRIMARY KEY,
        query_id TEXT NOT NULL,
        target_path TEXT NOT NULL,
        target_page_type TEXT NOT NULL,
        proposal_reason TEXT NOT NULL,
        proposal_hash TEXT NOT NULL,
        source_workspace_path TEXT NOT NULL,
        proposed_at TEXT NOT NULL,
        proposed_by TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'applied', 'failed')),
        reviewed_at TEXT,
        reviewed_by TEXT,
        review_decision TEXT,
        review_reason TEXT,
        applied_at TEXT,
        target_content_hash TEXT
    )
    """,
)


def index_db_path(workspace: Path) -> Path:
    return workspace / "state" / "index.db"


def ensure_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        if conn.execute("SELECT COUNT(*) FROM workspace_meta").fetchone()[0] == 0:
            conn.execute(
                """
                INSERT INTO workspace_meta (
                    workspace_version, schema_version, created_at, migrated_at
                ) VALUES (?, ?, datetime('now'), NULL)
                """,
                (WORKSPACE_SCHEMA_VERSION, WORKSPACE_SCHEMA_VERSION),
            )
        conn.commit()
    finally:
        conn.close()
