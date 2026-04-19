from pathlib import Path

from llm_wiki.lint import run_lint


def test_run_lint_flags_unknown_owner_and_status(tmp_path: Path) -> None:
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
        'owner: "unknown"\n'
        "owner_confidence: low\n"
        "status: unknown\n"
        "status_confidence: low\n"
        'last_ingested: "2026-04-09T10:00:00Z"\n'
        'last_reviewed: "unknown"\n'
        'canonical_snapshot: "raw/demo"\n'
        "---\n\n"
        "# Demo\n"
    )

    findings = run_lint(tmp_path / "wiki")

    assert any("unknown owner" in finding.lower() for finding in findings)
    assert any("unknown status" in finding.lower() for finding in findings)
