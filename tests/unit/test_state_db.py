from pathlib import Path
import sqlite3

from llm_wiki.state_db import ensure_schema


def test_ensure_schema_creates_workspace_meta_and_core_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "index.db"

    ensure_schema(db_path)

    conn = sqlite3.connect(db_path)
    try:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
        assert "workspace_meta" in names
        assert "projects" in names
        assert "wiki_pages" in names
        assert "snapshots" in names
        assert "snapshot_files" in names
        assert "chunks" in names
        assert "fts_chunks" in names
        assert "embeddings" in names
        assert "query_runs" in names
        assert "query_evidence" in names
        assert "writeback_proposals" in names
    finally:
        conn.close()
