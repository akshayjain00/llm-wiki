from __future__ import annotations

from pathlib import Path

import yaml

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
        "## Project Name",
        "",
        card.project_name,
        "",
        "## Slug",
        "",
        card.slug,
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
        card.owner,
        "",
        "## Owner Confidence",
        "",
        card.owner_confidence,
        "",
        "## Status",
        "",
        card.status,
        "",
        "## Status Confidence",
        "",
        card.status_confidence,
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


def load_project_card(card_path: Path) -> ProjectCardData:
    text = card_path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"Project card {card_path} is missing frontmatter")

    _, remainder = text.split("---\n", 1)
    frontmatter_text, body = remainder.split("\n---\n", 1)
    frontmatter = yaml.safe_load(frontmatter_text) or {}

    return ProjectCardData(
        project_name=frontmatter.get("project_name", card_path.parent.name),
        slug=frontmatter.get("slug", card_path.parent.name),
        domain=frontmatter.get("domain", "unknown"),
        source_roots=list(frontmatter.get("source_roots", [])),
        live_refs=list(frontmatter.get("live_refs", [])),
        owner=frontmatter.get("owner", "unknown"),
        owner_confidence=frontmatter.get("owner_confidence", "low"),
        status=frontmatter.get("status", "unknown"),
        status_confidence=frontmatter.get("status_confidence", "low"),
        last_ingested=frontmatter.get("last_ingested", "unknown"),
        last_reviewed=frontmatter.get("last_reviewed", "unknown"),
        canonical_snapshot=frontmatter.get("canonical_snapshot", "unknown"),
        summary=_extract_section(body, "Summary") or "Summary unavailable from current evidence.",
        current_scope=_extract_bullet_section(body, "Current Scope"),
        key_artifacts=_extract_bullet_section(body, "Key Artifacts"),
        key_questions=_extract_bullet_section(body, "Key Questions"),
        risks_or_blockers=_extract_bullet_section(body, "Risks / Blockers"),
        next_steps=_extract_bullet_section(body, "Next Steps"),
        related_pages=_extract_bullet_section(body, "Related Pages"),
    )


def _extract_section(body: str, heading: str) -> str:
    marker = f"## {heading}\n\n"
    if marker not in body:
        return ""
    section = body.split(marker, 1)[1]
    return section.split("\n## ", 1)[0].strip()


def _extract_bullet_section(body: str, heading: str) -> list[str]:
    section = _extract_section(body, heading)
    if not section or section == "- None recorded.":
        return []
    return [
        line.removeprefix("- ").strip() for line in section.splitlines() if line.startswith("- ")
    ]
