from __future__ import annotations

from pathlib import Path

from llm_wiki.wiki_writer import load_project_card


def answer_project_orientation(wiki_root: Path, project_slug: str) -> str:
    card_path = wiki_root / "projects" / project_slug / "project-card.md"
    card = load_project_card(card_path)
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
        "Next steps:\n"
        f"{next_steps}\n"
    )
