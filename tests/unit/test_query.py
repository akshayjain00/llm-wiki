from pathlib import Path

from llm_wiki.query import answer_project_orientation


def test_answer_project_orientation_reads_project_card(tmp_path: Path) -> None:
    project_dir = tmp_path / "wiki" / "projects" / "demo"
    project_dir.mkdir(parents=True)
    (project_dir / "project-card.md").write_text(
        "---\n"
        'project_name: "Demo"\n'
        'slug: "demo"\n'
        'domain: "forecasting"\n'
        "source_roots:\n"
        '  - "/tmp/demo"\n'
        "live_refs:\n"
        '  - "/tmp/demo"\n'
        'owner: "Data Team"\n'
        "owner_confidence: medium\n"
        "status: active\n"
        "status_confidence: medium\n"
        'last_ingested: "2026-04-09T10:00:00Z"\n'
        'last_reviewed: "unknown"\n'
        'canonical_snapshot: "raw/demo"\n'
        "---\n\n"
        "# Demo\n\n"
        "## Summary\n\n"
        "A forecast project.\n\n"
        "## Next Steps\n\n"
        "- Ship ingest.\n"
    )

    answer = answer_project_orientation(tmp_path / "wiki", "demo")

    assert "Demo" in answer
    assert "Data Team" in answer
    assert "active" in answer.lower()
    assert "Ship ingest." in answer
