from __future__ import annotations

import sqlite3
from pathlib import Path

from llm_wiki.config import WORKSPACE_SCHEMA_VERSION
from llm_wiki.state_db import index_db_path


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


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
    finally:
        conn.close()
    return findings
