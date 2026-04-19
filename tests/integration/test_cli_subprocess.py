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


def test_lint_command_writes_review_surfaces_and_stays_quiet_when_clean(tmp_path: Path) -> None:
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

    result = subprocess.run(
        ["uv", "run", "llm-wiki", "lint", "--workspace", str(workspace)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert (
        workspace / "wiki" / "indexes" / "needs-review.md"
    ).read_text().strip() == "# Needs Review\n\nNo findings."
    assert "- no findings" in (workspace / "logs" / "lint-log.md").read_text()


def test_ingest_empty_folder_exits_with_clean_error(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    empty_target = tmp_path / "empty"
    empty_target.mkdir()

    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "llm-wiki",
            "ingest",
            "--workspace",
            str(workspace),
            "--target",
            str(empty_target),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 1
    assert "no copyable files found" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()
