from pathlib import Path
import sqlite3

from llm_wiki.health import run_health_checks
from llm_wiki.state_db import ensure_schema, upsert_chunks
from llm_wiki.text_extraction import IndexedChunk


def test_run_health_checks_reports_missing_database(tmp_path: Path) -> None:
    findings = run_health_checks(tmp_path)

    assert "retrieval database missing" in findings


def test_run_health_checks_reports_missing_chunks_and_query_log(tmp_path: Path) -> None:
    ensure_schema(tmp_path / "state" / "index.db")

    findings = run_health_checks(tmp_path)

    assert "retrieval index has no chunks" in findings
    assert "query log missing" in findings
    assert "no query runs recorded yet" in findings


def test_run_health_checks_reports_schema_mismatch_missing_embeddings_and_fts_drift(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state" / "index.db"
    ensure_schema(db_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "query-log.md").write_text("# Query Log\n")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO chunks (
                chunk_id, source_kind, page_id, file_id, project_slug, chunk_text,
                content_hash, line_start, line_end, token_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("c1", "snapshot_file", None, "f1", "demo", "alpha beta", "h1", 1, 1, 2),
        )
        conn.execute("UPDATE workspace_meta SET schema_version = 999")
        conn.commit()
    finally:
        conn.close()

    findings = run_health_checks(tmp_path)

    assert "schema version mismatch" in findings
    assert "missing embedding rows" in findings
    assert "fts index drift detected" in findings


def test_run_health_checks_passes_when_retrieval_state_is_complete(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "index.db"
    ensure_schema(db_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "query-log.md").write_text("# Query Log\n")
    upsert_chunks(
        db_path,
        [
            IndexedChunk(
                chunk_id="c1",
                source_kind="snapshot_file",
                page_id=None,
                file_id="f1",
                project_slug="demo",
                chunk_text="alpha beta",
                content_hash="h1",
                line_start=1,
                line_end=1,
                token_count=2,
            )
        ],
    )
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO embeddings (
                chunk_id, provider, model, dimensions, vector_blob, embedded_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("c1", "openai", "text-embedding-3-small", 2, b"\x00\x01", "2026-05-05T00:00:00Z"),
        )
        conn.execute(
            """
            INSERT INTO query_runs (
                query_id, asked_at, question_text, requested_projects, model_provider,
                model_name, used_snapshot_fallback, status, token_input, token_output,
                cost_estimate, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "q1",
                "2026-05-05T00:00:00Z",
                "What changed?",
                '["demo"]',
                "local",
                "deterministic",
                0,
                "completed",
                0,
                0,
                0.0,
                1,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    assert run_health_checks(tmp_path) == []
