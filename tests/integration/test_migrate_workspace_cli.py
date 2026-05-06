from pathlib import Path
import subprocess


def test_migrate_workspace_creates_phase2_state_non_destructively(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "wiki" / "projects").mkdir(parents=True)
    (workspace / "wiki" / "projects" / "project-card.md").write_text("# Existing\n")

    result = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "migrate-workspace",
            "--workspace",
            str(workspace),
            "--target-version",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    migrated = tmp_path / "workspace-v2"
    assert result.returncode == 0
    assert str(migrated) in result.stdout
    assert (workspace / "wiki" / "projects" / "project-card.md").exists()
    assert (migrated / "wiki" / "projects" / "project-card.md").exists()
    assert (migrated / "state" / "index.db").exists()


def test_migrate_workspace_rejects_unsupported_target_version(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "migrate-workspace",
            "--workspace",
            str(workspace),
            "--target-version",
            "3",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 1
    assert "only target-version 2 is supported" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()
