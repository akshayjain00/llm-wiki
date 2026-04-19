from __future__ import annotations

import os
from pathlib import Path
import shutil


def _common_source_root(files: list[Path]) -> Path:
    if not files:
        raise ValueError("copy_snapshot requires at least one file")
    common_root = Path(os.path.commonpath([str(file_path) for file_path in files]))
    return common_root.parent if common_root.is_file() else common_root


def copy_snapshot(files: list[Path], destination_root: Path, ingest_timestamp: str) -> Path:
    snapshot_dir = destination_root / ingest_timestamp
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    common_root = _common_source_root(files)

    for file_path in files:
        relative_path = file_path.relative_to(common_root)
        destination = snapshot_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, destination)
    return snapshot_dir
