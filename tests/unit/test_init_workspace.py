from pathlib import Path

from llm_wiki.cli import build_parser
from llm_wiki.init_workspace import initialize_workspace


def test_cli_exposes_expected_commands() -> None:
    parser = build_parser()
    subparsers = {action.dest for action in parser._actions if getattr(action, "choices", None)}
    assert "command" in subparsers


def test_initialize_workspace_creates_expected_directories_and_schema(tmp_path: Path) -> None:
    initialize_workspace(tmp_path)

    assert (tmp_path / "raw").is_dir()
    assert (tmp_path / "refs").is_dir()
    assert (tmp_path / "wiki" / "projects").is_dir()
    assert (tmp_path / "wiki" / "indexes").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "schema").is_dir()
    assert (tmp_path / "schema" / "wiki-maintainer.md").is_file()
    assert (tmp_path / "schema" / "ingest-rules.yaml").is_file()
    assert (tmp_path / "schema" / "project-card-template.md").is_file()
    assert (tmp_path / "schema" / "lint-rules.md").is_file()
