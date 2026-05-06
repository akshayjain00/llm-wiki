from pathlib import Path
import sqlite3
import subprocess


def test_rebuild_retrieval_creates_index_db_for_existing_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )

    result = subprocess.run(
        ["uv", "run", "llm-wiki", "rebuild-retrieval", "--workspace", str(workspace)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert (workspace / "state" / "index.db").exists()


def test_rebuild_retrieval_clears_dirty_flag(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )
    dirty_flag = workspace / "state" / "retrieval-dirty.flag"
    dirty_flag.write_text("dirty\n")

    result = subprocess.run(
        ["uv", "run", "llm-wiki", "rebuild-retrieval", "--workspace", str(workspace)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert not dirty_flag.exists()


def test_rebuild_retrieval_populates_chunks_for_ingested_project(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    target = tmp_path / "sample_project"
    docs = target / "docs"
    docs.mkdir(parents=True)
    (target / "README.md").write_text("# Demo\n\nOwner: Data Team\nStatus: Active\n")
    (docs / "plan.md").write_text("Next steps: ship richer retrieval indexing")

    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )
    subprocess.run(
        ["uv", "run", "llm-wiki", "ingest", "--workspace", str(workspace), "--target", str(target)],
        check=True,
        cwd=Path.cwd(),
    )

    result = subprocess.run(
        ["uv", "run", "llm-wiki", "rebuild-retrieval", "--workspace", str(workspace)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    conn = sqlite3.connect(workspace / "state" / "index.db")
    try:
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        fts_count = conn.execute("SELECT COUNT(*) FROM fts_chunks").fetchone()[0]
    finally:
        conn.close()
    assert chunk_count > 0
    assert fts_count == chunk_count
