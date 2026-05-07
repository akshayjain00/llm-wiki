from llm_wiki.writeback import render_decisions_markdown


def test_render_decisions_markdown_has_decision_rationale_and_citations() -> None:
    rendered = render_decisions_markdown(
        title="Decisions",
        decision="Keep the workspace CLI-first.",
        rationale="It matches the current operator workflow.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )

    assert rendered.startswith("# Decisions")
    assert "## Decision" in rendered
    assert "Keep the workspace CLI-first." in rendered
    assert "## Rationale" in rendered
    assert "It matches the current operator workflow." in rendered
    assert "## Citations" in rendered
    assert "- [wiki:wiki/projects/hcv/project-card.md#Summary]" in rendered
