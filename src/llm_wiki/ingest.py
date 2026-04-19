from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from llm_wiki.filters import should_copy_file
from llm_wiki.inference import infer_project_card_fields
from llm_wiki.indexes import write_indexes
from llm_wiki.manifests import build_ref_manifest, write_ref_manifest
from llm_wiki.project_id import slugify_project_name
from llm_wiki.snapshot import copy_snapshot
from llm_wiki.wiki_writer import append_log_entry, render_ingest_log_entry, write_project_card


def collect_copyable_files(target: Path) -> list[Path]:
    return sorted(path for path in target.rglob("*") if path.is_file() and should_copy_file(path))


def run_ingest(workspace: Path, target: Path, ingest_timestamp: str | None = None) -> Path:
    timestamp = ingest_timestamp or datetime.now(tz=UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    project_slug = slugify_project_name(target.name)
    source_root_slug = slugify_project_name(target.parent.name or "source-root")

    files = collect_copyable_files(target)
    if not files:
        raise ValueError(f"No copyable files found under {target}")
    snapshot_root = workspace / "raw" / source_root_slug / project_slug
    snapshot_path = copy_snapshot(files, snapshot_root, timestamp)

    manifest = build_ref_manifest(
        project_slug=project_slug,
        live_paths=[str(target)],
        origin_roots=[str(target.parent)],
        last_scanned_timestamp=timestamp,
    )
    manifest["repo_roots"] = [str(target)] if (target / ".git").exists() else []
    manifest["excluded_paths"] = [".git", ".venv", ".pytest_cache", "__pycache__"]
    write_ref_manifest(manifest, workspace / "refs" / f"{project_slug}.yaml")

    inferred = infer_project_card_fields(target)
    project_card = replace(
        inferred,
        slug=project_slug,
        source_roots=[str(target.parent)],
        live_refs=[str(target)],
        last_ingested=timestamp,
        canonical_snapshot=str(snapshot_path.relative_to(workspace)),
    )
    project_card_path = workspace / "wiki" / "projects" / project_slug / "project-card.md"
    write_project_card(project_card, project_card_path)

    write_indexes(workspace)

    timestamp_label = datetime.strptime(timestamp, "%Y-%m-%dT%H-%M-%SZ").strftime(
        "%Y-%m-%d %H:%M UTC"
    )
    log_entry = render_ingest_log_entry(
        timestamp_label=timestamp_label,
        project_slug=project_slug,
        ingest_target=str(target),
        roots_scanned=[str(target)],
        snapshot_path=str(snapshot_path.relative_to(workspace)),
        files_copied=len(files),
        refs_recorded=[f"refs/{project_slug}.yaml"],
        wiki_pages_updated=[str(project_card_path.relative_to(workspace))],
        unresolved_gaps=project_card.key_questions,
        outcome="partial" if project_card.key_questions else "success",
    )
    append_log_entry(workspace / "logs" / "ingest-log.md", log_entry)
    return snapshot_path
