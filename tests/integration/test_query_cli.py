from pathlib import Path
import subprocess


def test_query_command_returns_wiki_first_project_orientation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    target = Path("tests/fixtures/sample_project")

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

    result = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "query",
            "--workspace",
            str(workspace),
            "--project",
            "sample-project",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert "Demo Project" in result.stdout
    assert "Data Team" in result.stdout
    assert "active" in result.stdout.lower()
    assert "ship guided ingest" in result.stdout.lower()
    assert result.stderr == ""
