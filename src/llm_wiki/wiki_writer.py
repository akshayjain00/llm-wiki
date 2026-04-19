from __future__ import annotations

from pathlib import Path

from llm_wiki.models import ProjectCardData


def _render_list(values: list[str], empty_message: str = "- None recorded.") -> str:
    if not values:
        return empty_message
    return "\n".join(f"- {value}" for value in values)


def _quote(value: str) -> str:
    return f'"{value}"'


def _render_frontmatter_list(name: str, values: list[str]) -> list[str]:
    return [f"{name}:"] + [f"  - {_quote(value)}" for value in values]


def _render_frontmatter(card: ProjectCardData) -> str:
    lines = [
        f"project_name: {_quote(card.project_name)}",
        f"slug: {_quote(card.slug)}",
        f"domain: {_quote(card.domain)}",
        *_render_frontmatter_list("source_roots", card.source_roots),
        *_render_frontmatter_list("live_refs", card.live_refs),
        f"owner: {_quote(card.owner)}",
        f"owner_confidence: {card.owner_confidence}",
        f"status: {card.status}",
        f"status_confidence: {card.status_confidence}",
        f"last_ingested: {_quote(card.last_ingested)}",
        f"last_reviewed: {_quote(card.last_reviewed)}",
        f"canonical_snapshot: {_quote(card.canonical_snapshot)}",
    ]
    return "\n".join(lines)


def render_project_card(card: ProjectCardData) -> str:
    frontmatter = _render_frontmatter(card)
    sections = [
        f"# {card.project_name}",
        "",
        "## Summary",
        "",
        card.summary,
        "",
        "## Domain / Category",
        "",
        card.domain,
        "",
        "## Source Roots",
        "",
        _render_list(card.source_roots),
        "",
        "## Live References",
        "",
        _render_list(card.live_refs),
        "",
        "## Owner",
        "",
        f"{card.owner} ({card.owner_confidence})",
        "",
        "## Status",
        "",
        f"{card.status} ({card.status_confidence})",
        "",
        "## Current Scope",
        "",
        _render_list(card.current_scope),
        "",
        "## Key Artifacts",
        "",
        _render_list(card.key_artifacts),
        "",
        "## Key Questions",
        "",
        _render_list(card.key_questions),
        "",
        "## Risks / Blockers",
        "",
        _render_list(card.risks_or_blockers),
        "",
        "## Next Steps",
        "",
        _render_list(card.next_steps),
        "",
        "## Last Ingested",
        "",
        card.last_ingested,
        "",
        "## Last Reviewed",
        "",
        card.last_reviewed,
        "",
        "## Related Pages",
        "",
        _render_list(card.related_pages),
        "",
    ]
    return f"---\n{frontmatter}\n---\n\n" + "\n".join(sections)


def write_project_card(card: ProjectCardData, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_project_card(card))


def render_ingest_log_entry(
    *,
    timestamp_label: str,
    project_slug: str,
    ingest_target: str,
    roots_scanned: list[str],
    snapshot_path: str,
    files_copied: int,
    refs_recorded: list[str],
    wiki_pages_updated: list[str],
    unresolved_gaps: list[str],
    outcome: str,
) -> str:
    sections = [
        f"## [{timestamp_label}] ingest | {project_slug}",
        "",
        f"- ingest target: `{ingest_target}`",
        f"- roots scanned: {', '.join(f'`{root}`' for root in roots_scanned) or '`none`'}",
        f"- snapshot path: `{snapshot_path}`",
        f"- files copied: {files_copied}",
        f"- refs recorded: {', '.join(f'`{ref}`' for ref in refs_recorded) or '`none`'}",
        f"- wiki pages updated: {', '.join(f'`{page}`' for page in wiki_pages_updated) or '`none`'}",
        f"- unresolved gaps: {', '.join(unresolved_gaps) or 'none'}",
        f"- outcome: {outcome}",
        "",
    ]
    return "\n".join(sections)


def append_log_entry(destination: Path, entry: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing = destination.read_text() if destination.exists() else "# Ingest Log\n\n"
    destination.write_text(existing + entry)
