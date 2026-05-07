from __future__ import annotations

from pathlib import Path
import shutil

from llm_wiki.state_db import ensure_schema, index_db_path


def clone_workspace_for_migration(source_workspace: Path, target_workspace: Path) -> None:
    if not source_workspace.exists():
        raise FileNotFoundError(f"workspace not found: {source_workspace}")
    if target_workspace.exists():
        raise FileExistsError(f"migration target already exists: {target_workspace}")
    shutil.copytree(source_workspace, target_workspace)


def migrate_workspace_to_v2(workspace: Path) -> Path:
    target_workspace = workspace.parent / f"{workspace.name}-v2"
    clone_workspace_for_migration(workspace, target_workspace)
    ensure_schema(index_db_path(target_workspace))
    return target_workspace
