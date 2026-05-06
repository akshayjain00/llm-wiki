from pathlib import Path
import subprocess


def _ingest_target(workspace: Path, target: Path) -> None:
    subprocess.run(
        ["uv", "run", "llm-wiki", "ingest", "--workspace", str(workspace), "--target", str(target)],
        check=True,
        cwd=Path.cwd(),
    )


def test_query_accepts_two_projects_and_returns_citations(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    first = tmp_path / "hcv"
    second = tmp_path / "notion_sync"
    first.mkdir()
    second.mkdir()
    (first / "README.md").write_text("# HCV\n\nOwner: Data Team\nStatus: Completed\n")
    (second / "README.md").write_text("# Notion Sync\n\nOwner: Data Team\nStatus: Active\n")

    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )
    _ingest_target(workspace, first)
    _ingest_target(workspace, second)

    result = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "query",
            "--workspace",
            str(workspace),
            "--project",
            "hcv",
            "--project",
            "notion-sync",
            "--question",
            "Compare how mature these projects are.",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert "Citations:" in result.stdout
    assert "[wiki:" in result.stdout
    assert result.stderr == ""


def test_query_rejects_invalid_project_counts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )

    too_few = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "query",
            "--workspace",
            str(workspace),
            "--project",
            "hcv",
            "--question",
            "Compare",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    too_many = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "query",
            "--workspace",
            str(workspace),
            "--project",
            "a",
            "--project",
            "b",
            "--project",
            "c",
            "--project",
            "d",
            "--project",
            "e",
            "--project",
            "f",
            "--question",
            "Compare",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert too_few.returncode == 1
    assert too_many.returncode == 1
    assert "between 2 and 5 projects" in too_few.stderr
    assert "between 2 and 5 projects" in too_many.stderr
