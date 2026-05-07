from llm_wiki.writeback import render_report_markdown


def test_render_report_markdown_has_question_answer_and_citations() -> None:
    rendered = render_report_markdown(
        title="Cross-Project Report",
        question="Compare project maturity.",
        answer="The report synthesizes evidence across both projects.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )

    assert rendered.startswith("# Cross-Project Report")
    assert "## Question" in rendered
    assert "## Answer" in rendered
    assert "## Citations" in rendered
