from pathlib import Path

import yaml

from llm_wiki.lint import render_needs_review_markdown, run_lint


def _write_project_card(
    project_dir: Path,
    *,
    project_name: str = "Demo",
    slug: str = "demo",
    owner: str = "unknown",
    status: str = "unknown",
    last_ingested: str = "2026-04-09T10:00:00Z",
    next_steps: str = "- None recorded.",
) -> None:
    project_dir.mkdir(parents=True)
    (project_dir / "project-card.md").write_text(
        "---\n"
        f'project_name: "{project_name}"\n'
        f'slug: "{slug}"\n'
        'domain: "unknown"\n'
        "source_roots:\n"
        '  - "/tmp/demo"\n'
        "live_refs:\n"
        '  - "/tmp/demo"\n'
        f'owner: "{owner}"\n'
        "owner_confidence: low\n"
        f"status: {status}\n"
        "status_confidence: low\n"
        f'last_ingested: "{last_ingested}"\n'
        'last_reviewed: "unknown"\n'
        'canonical_snapshot: "raw/demo/2026-04-09T10-00-00Z"\n'
        "---\n\n"
        f"# {project_name}\n\n"
        "## Next Steps\n\n"
        f"{next_steps}\n"
    )


def test_run_lint_flags_unknown_missing_stale_and_contradictory_state(tmp_path: Path) -> None:
    project_dir = tmp_path / "wiki" / "projects" / "demo"
    _write_project_card(project_dir)
    (project_dir / "overview.md").write_text("Status: blocked\n")
    (project_dir / "status-notes.md").write_text("Status: active\n")

    (tmp_path / "refs").mkdir(parents=True)
    (tmp_path / "refs" / "demo.yaml").write_text(
        yaml.safe_dump(
            {
                "project_slug": "demo",
                "authoritative_live_paths": ["/tmp/demo"],
                "duplicate_source_notes": ["duplicate README copies detected"],
            },
            sort_keys=False,
        )
    )

    findings = run_lint(tmp_path, now_timestamp="2026-05-20T10:00:00Z")

    assert any("unknown owner" in finding.lower() for finding in findings)
    assert any("unknown status" in finding.lower() for finding in findings)
    assert any("missing next steps" in finding.lower() for finding in findings)
    assert any("stale project card" in finding.lower() for finding in findings)
    assert any("missing live path" in finding.lower() for finding in findings)
    assert any("possible duplicate" in finding.lower() for finding in findings)
    assert any("contradictory status" in finding.lower() for finding in findings)


def test_run_lint_flags_duplicate_slugs(tmp_path: Path) -> None:
    _write_project_card(
        tmp_path / "wiki" / "projects" / "demo-one", project_name="Demo One", slug="demo"
    )
    _write_project_card(
        tmp_path / "wiki" / "projects" / "demo-two", project_name="Demo Two", slug="demo"
    )

    findings = run_lint(tmp_path, now_timestamp="2026-04-20T10:00:00Z")

    assert any("duplicate slug" in finding.lower() for finding in findings)


def test_render_needs_review_markdown_is_bullet_list() -> None:
    rendered = render_needs_review_markdown(["demo: unknown owner", "demo: unknown status"])

    assert rendered.startswith("# Needs Review")
    assert "- demo: unknown owner" in rendered
    assert "- demo: unknown status" in rendered
