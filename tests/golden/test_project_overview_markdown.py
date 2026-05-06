from llm_wiki.writeback import render_project_overview_markdown


def test_render_project_overview_markdown_has_summary_and_citations() -> None:
    rendered = render_project_overview_markdown(
        title="Project Overview",
        summary="A durable overview for new contributors.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )

    assert rendered.startswith("# Project Overview")
    assert "## Summary" in rendered
    assert "A durable overview for new contributors." in rendered
    assert "## Citations" in rendered
    assert "- [wiki:wiki/projects/hcv/project-card.md#Summary]" in rendered
