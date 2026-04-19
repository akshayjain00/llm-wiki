from llm_wiki.wiki_writer import render_ingest_log_entry


def test_render_ingest_log_entry_contains_required_fields() -> None:
    entry = render_ingest_log_entry(
        timestamp_label="2026-04-09 15:30 IST",
        project_slug="demo-project",
        ingest_target="/tmp/project",
        roots_scanned=["/tmp/project"],
        snapshot_path="raw/desktop-ai-v2/demo-project/2026-04-09T10-00-00Z",
        files_copied=2,
        refs_recorded=["refs/demo-project.yaml"],
        wiki_pages_updated=["wiki/projects/demo-project/project-card.md"],
        unresolved_gaps=["owner needs review"],
        outcome="partial",
    )

    assert "## [2026-04-09 15:30 IST] ingest | demo-project" in entry
    assert "- ingest target: `/tmp/project`" in entry
    assert "- files copied: 2" in entry
    assert "- outcome: partial" in entry
