from pathlib import Path
import subprocess

import yaml


def test_ingest_command_creates_snapshot_card_and_index(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    target = tmp_path / "sample_project"
    docs = target / "docs"
    docs.mkdir(parents=True)
    (target / "README.md").write_text("# Demo\n\nOwner: Data Team\nStatus: Active\n")
    (docs / "plan.md").write_text("Next steps: ship guided ingest")

    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )
    subprocess.run(
        ["uv", "run", "llm-wiki", "ingest", "--workspace", str(workspace), "--target", str(target)],
        check=True,
        cwd=Path.cwd(),
    )

    assert any((workspace / "raw").rglob("README.md"))
    assert any((workspace / "wiki" / "projects").rglob("project-card.md"))
    assert (workspace / "wiki" / "indexes" / "index.md").exists()
    assert (workspace / "logs" / "ingest-log.md").exists()
    assert (workspace / "refs" / "sample-project.yaml").exists()


def test_ingest_command_normalizes_relative_targets_to_absolute_refs(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    target = tmp_path / "sample_project"
    docs = target / "docs"
    docs.mkdir(parents=True)
    (target / "README.md").write_text("# Demo\n\nOwner: Data Team\nStatus: Active\n")
    (docs / "plan.md").write_text("Next steps: ship guided ingest")

    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )
    subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "ingest",
            "--workspace",
            str(workspace),
            "--target",
            "sample_project",
        ],
        check=True,
        cwd=tmp_path,
    )

    card_text = (workspace / "wiki" / "projects" / "sample-project" / "project-card.md").read_text()
    manifest = yaml.safe_load((workspace / "refs" / "sample-project.yaml").read_text())

    assert str(target.resolve()) in card_text
    assert manifest["authoritative_live_paths"] == [str(target.resolve())]


def test_ingest_command_prefers_overview_docs_over_support_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    target = Path("tests/fixtures/overview_priority_project")

    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )
    subprocess.run(
        ["uv", "run", "llm-wiki", "ingest", "--workspace", str(workspace), "--target", str(target)],
        check=True,
        cwd=Path.cwd(),
    )

    card_text = (
        workspace / "wiki" / "projects" / "overview-priority-project" / "project-card.md"
    ).read_text()

    assert 'project_name: "Monthly Review Brain"' in card_text
    assert "aliases:" in card_text
    assert '  - "MBR Brain"' in card_text
    assert (
        "Monthly Review Brain compiles evidence and narrative for recurring business reviews."
        in card_text
    )
    assert "run lint after every edit" not in card_text

    alias_query = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "query",
            "--workspace",
            str(workspace),
            "--project",
            "mbr-brain",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert alias_query.returncode == 0
    assert "Project: Monthly Review Brain" in alias_query.stdout
    assert "Aliases: MBR Brain" in alias_query.stdout
