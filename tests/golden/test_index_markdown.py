from llm_wiki.indexes import render_index_markdown


def test_render_index_markdown_contains_required_columns() -> None:
    markdown = render_index_markdown(
        [
            {
                "name": "Demo",
                "path": "wiki/projects/demo/project-card.md",
                "summary": "A forecast project.",
                "owner": "Data Team",
                "status": "active",
                "updated": "2026-04-09",
            }
        ]
    )
    assert "| Project | Summary | Owner | Status | Last Updated |" in markdown
    assert "[Demo](wiki/projects/demo/project-card.md)" in markdown
