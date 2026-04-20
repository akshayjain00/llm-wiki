from __future__ import annotations

from pathlib import Path

from llm_wiki.project_id import slugify_project_name
from llm_wiki.wiki_writer import load_project_card


def _resolve_card_path(workspace_root: Path, project_or_alias: str) -> Path:
    projects_root = workspace_root / "wiki" / "projects"
    direct = projects_root / project_or_alias / "project-card.md"
    if direct.exists():
        return direct

    target_slug = slugify_project_name(project_or_alias)
    matches: list[Path] = []
    for card_path in projects_root.rglob("project-card.md"):
        card = load_project_card(card_path)
        alias_slugs = {slugify_project_name(alias) for alias in card.aliases}
        if target_slug in alias_slugs:
            matches.append(card_path)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"Project alias '{project_or_alias}' is ambiguous in workspace wiki")
    raise FileNotFoundError(f"Project '{project_or_alias}' not found in workspace wiki")


def answer_project_orientation(workspace_root: Path, project_slug: str) -> str:
    card_path = _resolve_card_path(workspace_root, project_slug)
    if not card_path.exists():
        raise FileNotFoundError(f"Project '{project_slug}' not found in workspace wiki")
    card = load_project_card(card_path)
    snapshot_path = workspace_root / card.canonical_snapshot
    refs_path = workspace_root / "refs" / f"{card.slug}.yaml"
    next_steps = (
        "\n".join(f"- {step}" for step in card.next_steps)
        if card.next_steps
        else "- None recorded."
    )
    aliases = ", ".join(card.aliases) if card.aliases else "None recorded."
    return (
        f"Project: {card.project_name}\n"
        f"Slug: {card.slug}\n"
        f"Aliases: {aliases}\n"
        f"Owner: {card.owner}\n"
        f"Status: {card.status}\n"
        f"Summary: {card.summary}\n"
        f"Evidence snapshot: {card.canonical_snapshot} ({'present' if snapshot_path.exists() else 'missing'})\n"
        f"Reference manifest: refs/{card.slug}.yaml ({'present' if refs_path.exists() else 'missing'})\n"
        "Next steps:\n"
        f"{next_steps}\n"
    )
