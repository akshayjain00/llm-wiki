from pathlib import Path
import sqlite3
import subprocess

from llm_wiki.state_db import ensure_schema


def test_approve_writeback_materializes_report_and_updates_status(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )
    db_path = workspace / "state" / "index.db"
    ensure_schema(db_path)
    target_path = "wiki/reports/2026-05-05-maturity-comparison.md"
    rendered = "# Maturity Comparison\n\n## Answer\n\nApproved content.\n"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO writeback_proposals (
            proposal_id, query_id, target_path, target_page_type, proposal_reason,
            proposal_hash, source_workspace_path, proposed_at, proposed_by, status,
            rendered_markdown
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?)
        """,
        (
            "proposal-demo",
            "query-demo",
            target_path,
            "report",
            "test approval",
            "hash-demo",
            str(workspace),
            "pytest",
            "pending",
            rendered,
        ),
    )
    conn.commit()
    conn.close()

    result = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "approve-writeback",
            "--workspace",
            str(workspace),
            "--proposal-id",
            "proposal-demo",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert (workspace / target_path).read_text() == rendered
    conn = sqlite3.connect(db_path)
    try:
        status = conn.execute(
            "SELECT status FROM writeback_proposals WHERE proposal_id = ?",
            ("proposal-demo",),
        ).fetchone()[0]
    finally:
        conn.close()
    assert status == "applied"
