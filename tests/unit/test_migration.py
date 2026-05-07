from pathlib import Path

import pytest

from llm_wiki.migration import migrate_workspace_to_v2


def test_migrate_workspace_to_v2_creates_sibling_without_mutating_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "wiki" / "projects").mkdir(parents=True)
    (workspace / "wiki" / "projects" / "project-card.md").write_text("# Existing\n")

    migrated = migrate_workspace_to_v2(workspace)

    assert migrated == tmp_path / "workspace-v2"
    assert (workspace / "wiki" / "projects" / "project-card.md").exists()
    assert (migrated / "wiki" / "projects" / "project-card.md").exists()
    assert (migrated / "state" / "index.db").exists()


def test_migrate_workspace_to_v2_refuses_existing_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (tmp_path / "workspace-v2").mkdir()

    with pytest.raises(FileExistsError, match="migration target already exists"):
        migrate_workspace_to_v2(workspace)
