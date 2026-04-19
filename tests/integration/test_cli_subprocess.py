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
