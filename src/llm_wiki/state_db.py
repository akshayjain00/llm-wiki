from __future__ import annotations

from pathlib import Path


def index_db_path(workspace: Path) -> Path:
    return workspace / "state" / "index.db"
