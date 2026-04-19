from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import yaml

from llm_wiki.models import RefManifestData


def build_ref_manifest(
    project_slug: str,
    live_paths: list[str],
    origin_roots: list[str],
    last_scanned_timestamp: str = "unknown",
    repo_roots: list[str] | None = None,
    excluded_paths: list[str] | None = None,
    duplicate_source_notes: list[str] | None = None,
) -> dict[str, object]:
    manifest = RefManifestData(
        project_slug=project_slug,
        authoritative_live_paths=live_paths,
        repo_roots=repo_roots or [],
        origin_roots=origin_roots,
        excluded_paths=excluded_paths or [],
        duplicate_source_notes=duplicate_source_notes or [],
        last_scanned_timestamp=last_scanned_timestamp,
    )
    return asdict(manifest)


def write_ref_manifest(manifest: dict[str, object], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(yaml.safe_dump(manifest, sort_keys=False))
