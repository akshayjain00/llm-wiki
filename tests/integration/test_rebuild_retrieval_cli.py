from pathlib import Path
import subprocess


def test_rebuild_retrieval_creates_index_db_for_existing_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )

    result = subprocess.run(
        ["uv", "run", "llm-wiki", "rebuild-retrieval", "--workspace", str(workspace)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert (workspace / "state" / "index.db").exists()


def test_rebuild_retrieval_clears_dirty_flag(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
        cwd=Path.cwd(),
    )
    dirty_flag = workspace / "state" / "retrieval-dirty.flag"
    dirty_flag.write_text("dirty\n")

    result = subprocess.run(
        ["uv", "run", "llm-wiki", "rebuild-retrieval", "--workspace", str(workspace)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0
    assert not dirty_flag.exists()
