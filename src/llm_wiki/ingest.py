from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from llm_wiki.filters import should_copy_file
from llm_wiki.inference import infer_project_card_fields
from llm_wiki.indexes import write_indexes
from llm_wiki.manifests import build_ref_manifest, write_ref_manifest
from llm_wiki.project_id import slugify_project_name
from llm_wiki.snapshot import copy_snapshot
from llm_wiki.wiki_writer import (
    append_log_entry,
    load_project_card,
    render_ingest_log_entry,
    write_project_card,
)
from llm_wiki.models import ProjectCardData


DEFAULT_SUMMARY = "Summary unavailable from current evidence."


def _humanize_target_name(target: Path) -> str:
    return target.name.replace("-", " ").replace("_", " ").title()


def _should_promote_target_alias(target: Path, inferred_name: str) -> bool:
    if any(separator in target.name for separator in ("-", "_", " ")):
        return False
    return slugify_project_name(_humanize_target_name(target)) != slugify_project_name(
        inferred_name
    )


def collect_copyable_files(target: Path) -> list[Path]:
    return sorted(path for path in target.rglob("*") if path.is_file() and should_copy_file(path))


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deduplicate_files(files: list[Path], root: Path) -> tuple[list[Path], list[str]]:
    kept: list[Path] = []
    duplicate_notes: list[str] = []
    seen: dict[tuple[int, str], Path] = {}
    for file_path in files:
        fingerprint = (file_path.stat().st_size, _file_hash(file_path))
        original = seen.get(fingerprint)
        if original is None:
            seen[fingerprint] = file_path
            kept.append(file_path)
            continue
        duplicate_notes.append(
            f"{file_path.relative_to(root)} duplicates {original.relative_to(root)}"
        )
    return kept, duplicate_notes


def _merge_with_existing_card(
    existing: ProjectCardData, incoming: ProjectCardData
) -> ProjectCardData:
    reviewed = existing.last_reviewed != "unknown"

    aliases = list(existing.aliases) if reviewed else list(existing.aliases)
    if not reviewed:
        for alias in incoming.aliases:
            if alias not in aliases:
                aliases.append(alias)

    owner = incoming.owner
    owner_confidence = incoming.owner_confidence
    if incoming.owner_confidence == "low" and existing.owner != "unknown":
        owner = existing.owner
        owner_confidence = existing.owner_confidence

    status = incoming.status
    status_confidence = incoming.status_confidence
    if incoming.status_confidence == "low" and existing.status != "unknown":
        status = existing.status
        status_confidence = existing.status_confidence

    summary = incoming.summary
    if reviewed and existing.summary != DEFAULT_SUMMARY:
        summary = existing.summary
    elif incoming.summary == DEFAULT_SUMMARY and existing.summary != DEFAULT_SUMMARY:
        summary = existing.summary

    return replace(
        incoming,
        project_name=existing.project_name if reviewed else incoming.project_name,
        aliases=aliases,
        domain=existing.domain
        if reviewed or (incoming.domain == "unknown" and existing.domain != "unknown")
        else incoming.domain,
        owner=owner,
        owner_confidence=owner_confidence,
        status=status,
        status_confidence=status_confidence,
        last_reviewed=existing.last_reviewed
        if existing.last_reviewed != "unknown"
        else incoming.last_reviewed,
        summary=summary,
        current_scope=existing.current_scope or incoming.current_scope,
        key_artifacts=existing.key_artifacts or incoming.key_artifacts,
        key_questions=existing.key_questions or incoming.key_questions,
        risks_or_blockers=existing.risks_or_blockers or incoming.risks_or_blockers,
        next_steps=existing.next_steps or incoming.next_steps,
        related_pages=existing.related_pages or incoming.related_pages,
    )


def run_ingest(workspace: Path, target: Path, ingest_timestamp: str | None = None) -> Path:
    workspace = workspace.resolve()
    target = target.resolve()
    timestamp = ingest_timestamp or datetime.now(tz=UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    project_slug = slugify_project_name(target.name)
    source_root_slug = slugify_project_name(target.parent.name or "source-root")

    files = collect_copyable_files(target)
    if not files:
        raise ValueError(f"No copyable files found under {target}")
    files, duplicate_notes = deduplicate_files(files, target)
    snapshot_root = workspace / "raw" / source_root_slug / project_slug
    snapshot_path = copy_snapshot(files, snapshot_root, timestamp)

    manifest = build_ref_manifest(
        project_slug=project_slug,
        live_paths=[str(target)],
        origin_roots=[str(target.parent)],
        last_scanned_timestamp=timestamp,
        duplicate_source_notes=duplicate_notes,
    )
    manifest["repo_roots"] = [str(target)] if (target / ".git").exists() else []
    manifest["excluded_paths"] = [".git", ".venv", ".pytest_cache", "__pycache__"]
    write_ref_manifest(manifest, workspace / "refs" / f"{project_slug}.yaml")

    inferred = infer_project_card_fields(snapshot_path)
    project_card = replace(
        inferred,
        slug=project_slug,
        aliases=[
            *inferred.aliases,
            *(
                [_humanize_target_name(target)]
                if _should_promote_target_alias(target, inferred.project_name)
                else []
            ),
        ],
        source_roots=[str(target.parent)],
        live_refs=[str(target)],
        last_ingested=timestamp,
        canonical_snapshot=str(snapshot_path.relative_to(workspace)),
    )
    project_card_path = workspace / "wiki" / "projects" / project_slug / "project-card.md"
    if project_card_path.exists():
        project_card = _merge_with_existing_card(load_project_card(project_card_path), project_card)
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
