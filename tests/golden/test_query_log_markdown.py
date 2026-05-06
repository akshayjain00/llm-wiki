from llm_wiki.wiki_writer import render_query_log_summary


def test_render_query_log_summary_reports_audit_counts() -> None:
    rendered = render_query_log_summary(total_queries=3, snapshot_fallbacks=1, writebacks=2)

    assert rendered.startswith("# Query Log Summary")
    assert "- total queries: 3" in rendered
    assert "- snapshot fallbacks: 1" in rendered
    assert "- write-backs: 2" in rendered
