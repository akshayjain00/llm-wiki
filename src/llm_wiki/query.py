from __future__ import annotations

from pathlib import Path

from llm_wiki.wiki_writer import load_project_card


def answer_project_orientation(workspace_root: Path, project_slug: str) -> str:
    card_path = workspace_root / "wiki" / "projects" / project_slug / "project-card.md"
    if not card_path.exists():
        raise FileNotFoundError(f"Project '{project_slug}' not found in workspace wiki")
    card = load_project_card(card_path)
    snapshot_path = workspace_root / card.canonical_snapshot
    refs_path = workspace_root / "refs" / f"{project_slug}.yaml"
    next_steps = (
        "\n".join(f"- {step}" for step in card.next_steps)
        if card.next_steps
        else "- None recorded."
    )
    return (
        f"Project: {card.project_name}\n"
        f"Slug: {card.slug}\n"
        f"Owner: {card.owner}\n"
        f"Status: {card.status}\n"
        f"Summary: {card.summary}\n"
        f"Evidence snapshot: {card.canonical_snapshot} ({'present' if snapshot_path.exists() else 'missing'})\n"
        f"Reference manifest: refs/{project_slug}.yaml ({'present' if refs_path.exists() else 'missing'})\n"
        "Next steps:\n"
        f"{next_steps}\n"
    )
