from pathlib import Path
import subprocess


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
