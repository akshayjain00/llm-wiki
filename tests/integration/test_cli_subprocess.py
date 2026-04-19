from pathlib import Path
import subprocess


def test_cli_help_exits_zero() -> None:
    result = subprocess.run(
        ["uv", "run", "llm-wiki", "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert "init" in result.stdout
    assert result.stderr == ""


def test_rebuild_indexes_help_exits_zero() -> None:
    result = subprocess.run(
        ["uv", "run", "llm-wiki", "rebuild-indexes", "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert "--workspace" in result.stdout
    assert result.stderr == ""


def test_query_missing_project_exits_with_clean_error(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )

    result = subprocess.run(
        ["uv", "run", "llm-wiki", "query", "--workspace", str(workspace), "--project", "missing"],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 1
    assert "not found" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()
