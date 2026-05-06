from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from llm_wiki.config import WORKSPACE_SCHEMA_VERSION
from llm_wiki.text_extraction import IndexedChunk


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
        target_content_hash TEXT,
        rendered_markdown TEXT NOT NULL DEFAULT ''
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


def upsert_chunks(db_path: Path, chunks: list[IndexedChunk]) -> None:
    conn = sqlite3.connect(db_path)
    try:
        for chunk in chunks:
            conn.execute(
                """
                INSERT OR REPLACE INTO chunks (
                    chunk_id, source_kind, page_id, file_id, project_slug, chunk_text,
                    content_hash, line_start, line_end, token_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.chunk_id,
                    chunk.source_kind,
                    chunk.page_id,
                    chunk.file_id,
                    chunk.project_slug,
                    chunk.chunk_text,
                    chunk.content_hash,
                    chunk.line_start,
                    chunk.line_end,
                    chunk.token_count,
                ),
            )
            conn.execute("DELETE FROM fts_chunks WHERE chunk_id = ?", (chunk.chunk_id,))
            conn.execute(
                """
                INSERT INTO fts_chunks (chunk_id, project_slug, source_kind, chunk_text)
                VALUES (?, ?, ?, ?)
                """,
                (chunk.chunk_id, chunk.project_slug, chunk.source_kind, chunk.chunk_text),
            )
        conn.commit()
    finally:
        conn.close()


def search_lexical(
    db_path: Path, *, project_slugs: list[str], query_text: str, limit: int
) -> list[dict[str, Any]]:
    if not project_slugs:
        return []
    placeholders = ",".join("?" for _ in project_slugs)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT chunk_id, project_slug, source_kind, bm25(fts_chunks) AS lexical_score
            FROM fts_chunks
            WHERE fts_chunks MATCH ?
              AND project_slug IN ({placeholders})
            ORDER BY lexical_score
            LIMIT ?
            """,
            [query_text, *project_slugs, limit],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
