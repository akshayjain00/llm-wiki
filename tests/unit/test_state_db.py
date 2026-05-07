from pathlib import Path
import sqlite3

from llm_wiki.state_db import ensure_schema, search_lexical, upsert_chunks
from llm_wiki.text_extraction import IndexedChunk


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


def test_upsert_chunks_populates_fts_table(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "index.db"
    ensure_schema(db_path)

    upsert_chunks(
        db_path,
        [
            IndexedChunk(
                chunk_id="c1",
                source_kind="snapshot_file",
                page_id=None,
                file_id="f1",
                project_slug="demo",
                chunk_text="alpha beta gamma",
                content_hash="h1",
                line_start=1,
                line_end=3,
                token_count=3,
            )
        ],
    )

    rows = search_lexical(db_path, project_slugs=["demo"], query_text="alpha", limit=5)
    assert rows[0]["chunk_id"] == "c1"
