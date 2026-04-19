from __future__ import annotations

from pathlib import Path

from llm_wiki.wiki_writer import load_project_card


STATUS_PRIORITY = {
    "active": 0,
    "planned": 1,
    "blocked": 2,
    "paused": 3,
    "completed": 4,
    "unknown": 5,
}


def sort_index_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped_rows = sorted(rows, key=_sort_key)
    active_rows = sorted(
        [row for row in grouped_rows if row.get("status", "unknown") == "active"],
        key=lambda row: row.get("updated", ""),
        reverse=True,
    )
    non_active_rows = [row for row in grouped_rows if row.get("status", "unknown") != "active"]
    return active_rows + non_active_rows


def _sort_key(row: dict[str, str]) -> tuple[int, str]:
    return (
        STATUS_PRIORITY.get(row.get("status", "unknown"), STATUS_PRIORITY["unknown"]),
        row.get("updated", ""),
    )


def render_index_markdown(rows: list[dict[str, str]]) -> str:
    ordered_rows = sort_index_rows(rows)

    lines = [
        "# Project Index",
        "",
        "| Project | Summary | Owner | Status | Last Updated |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in ordered_rows:
        lines.append(
            f"| [{row['name']}]({row['path']}) | {row['summary']} | {row['owner']} | {row['status']} | {row['updated']} |"
        )
    return "\n".join(lines) + "\n"


def build_index_rows(projects_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for card_path in sorted(projects_root.rglob("project-card.md")):
        card = load_project_card(card_path)
        rows.append(
            {
                "name": card.project_name,
                "path": str(card_path.relative_to(projects_root.parent.parent)),
                "summary": card.summary,
                "owner": card.owner,
                "status": card.status,
                "updated": card.last_ingested.split("T", 1)[0]
                if card.last_ingested != "unknown"
                else "unknown",
            }
        )
    return sort_index_rows(rows)


def write_indexes(workspace_root: Path) -> None:
    projects_root = workspace_root / "wiki" / "projects"
    indexes_root = workspace_root / "wiki" / "indexes"
    indexes_root.mkdir(parents=True, exist_ok=True)
    rows = build_index_rows(projects_root)

    (indexes_root / "index.md").write_text(render_index_markdown(rows))
    (indexes_root / "active-projects.md").write_text(
        render_index_markdown([row for row in rows if row["status"] == "active"])
    )
    (indexes_root / "by-owner.md").write_text(
        render_index_markdown(sorted(rows, key=lambda row: row["owner"]))
    )
    (indexes_root / "by-domain.md").write_text(
        "# Projects By Domain\n\nDomain grouping not implemented yet.\n"
    )
    needs_review_rows = [
        row for row in rows if row["owner"] == "unknown" or row["status"] == "unknown"
    ]
    (indexes_root / "needs-review.md").write_text(render_index_markdown(needs_review_rows))
