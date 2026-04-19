from pathlib import Path

from llm_wiki.indexes import sort_index_rows, write_indexes


def test_sort_index_rows_orders_by_status_priority_then_recency() -> None:
    rows = [
        {"name": "Blocked", "status": "blocked", "updated": "2026-04-08"},
        {"name": "Active New", "status": "active", "updated": "2026-04-10"},
        {"name": "Active Old", "status": "active", "updated": "2026-04-07"},
    ]

    sorted_rows = sort_index_rows(rows)

    assert [row["name"] for row in sorted_rows] == ["Active New", "Active Old", "Blocked"]


def test_write_indexes_does_not_touch_needs_review_surface(tmp_path: Path) -> None:
    project_dir = tmp_path / "wiki" / "projects" / "demo"
    project_dir.mkdir(parents=True)
    (project_dir / "project-card.md").write_text(
        "---\n"
        'project_name: "Demo"\n'
        'slug: "demo"\n'
        'domain: "unknown"\n'
        "source_roots:\n"
        '  - "/tmp/demo"\n'
        "live_refs:\n"
        '  - "/tmp/demo"\n'
        'owner: "Data Team"\n'
        "owner_confidence: medium\n"
        "status: active\n"
        "status_confidence: medium\n"
        'last_ingested: "2026-04-20T10:00:00Z"\n'
        'last_reviewed: "unknown"\n'
        'canonical_snapshot: "raw/demo/2026-04-20T10-00-00Z"\n'
        "---\n\n"
        "# Demo\n\n"
        "## Summary\n\n"
        "A demo project.\n\n"
        "## Next Steps\n\n"
        "- Ship ingest.\n"
    )
    indexes_root = tmp_path / "wiki" / "indexes"
    indexes_root.mkdir(parents=True)
    original = "# Needs Review\n\n- existing finding\n"
    (indexes_root / "needs-review.md").write_text(original)

    write_indexes(tmp_path)

    assert (indexes_root / "needs-review.md").read_text() == original
