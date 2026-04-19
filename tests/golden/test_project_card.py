from llm_wiki.models import ProjectCardData
from llm_wiki.wiki_writer import render_project_card


def test_render_project_card_contains_required_frontmatter_and_sections() -> None:
    card = ProjectCardData(
        project_name="Demo Project",
        slug="demo-project",
        owner="Data Team",
        owner_confidence="medium",
        status="active",
        status_confidence="medium",
        source_roots=["/tmp/project"],
        live_refs=["/tmp/project"],
        last_ingested="2026-04-09T10:00:00Z",
        canonical_snapshot="raw/desktop-ai-v2/demo-project/2026-04-09T10-00-00Z/",
        next_steps=["ship guided ingest"],
    )

    markdown = render_project_card(card)

    assert 'project_name: "Demo Project"' in markdown
    assert 'slug: "demo-project"' in markdown
    assert 'owner: "Data Team"' in markdown
    assert "status: active" in markdown
    assert "## Slug" in markdown
    assert "## Summary" in markdown
    assert "## Owner Confidence" in markdown
    assert "## Status Confidence" in markdown
    assert "## Next Steps" in markdown
    assert "- ship guided ingest" in markdown
