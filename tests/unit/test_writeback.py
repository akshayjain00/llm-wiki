from pathlib import Path

import pytest

from llm_wiki.writeback import (
    apply_approved_writeback,
    choose_writeback_target,
    render_decisions_markdown,
    render_project_overview_markdown,
    render_report_markdown,
)


def test_choose_writeback_target_uses_reports_for_cross_project_outputs() -> None:
    target = choose_writeback_target(
        project_slugs=["hcv", "notion-sync"],
        topic_slug="maturity-comparison",
        page_type="report",
    )

    assert target.startswith("wiki/reports/")
    assert target.endswith("-maturity-comparison.md")


def test_choose_writeback_target_uses_project_overview_for_single_project_pages() -> None:
    target = choose_writeback_target(
        project_slugs=["hcv"],
        topic_slug="project-overview",
        page_type="overview",
    )

    assert target == "wiki/projects/hcv/overview.md"


def test_choose_writeback_target_rejects_invalid_page_project_combinations() -> None:
    with pytest.raises(ValueError, match="overview requires exactly one project"):
        choose_writeback_target(
            project_slugs=["hcv", "notion-sync"],
            topic_slug="bad-overview",
            page_type="overview",
        )
    with pytest.raises(ValueError, match="at least two projects"):
        choose_writeback_target(project_slugs=["hcv"], topic_slug="bad-report", page_type="report")
    with pytest.raises(ValueError, match="unknown page type"):
        choose_writeback_target(
            project_slugs=["hcv"], topic_slug="bad-route", page_type="unexpected"
        )


def test_apply_writeback_refuses_to_overwrite_manual_overview(tmp_path: Path) -> None:
    page = tmp_path / "wiki" / "projects" / "hcv" / "overview.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("# Overview\n\nHuman curated section.\n")

    with pytest.raises(ValueError, match="manual review required"):
        apply_approved_writeback(page, "# Overview\n\nMachine rewrite.\n", allow_replace=False)


def test_renderers_include_expected_sections() -> None:
    report = render_report_markdown(
        title="Cross-Project Report",
        question="Compare project maturity.",
        answer="The report synthesizes evidence.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )
    overview = render_project_overview_markdown(
        title="Project Overview",
        summary="A durable overview.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )
    decisions = render_decisions_markdown(
        title="Decisions",
        decision="Keep CLI-first.",
        rationale="It matches the workflow.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )

    assert "## Question" in report
    assert "## Summary" in overview
    assert "## Decision" in decisions
    assert "## Citations" in report
    assert "## Citations" in overview
    assert "## Citations" in decisions
