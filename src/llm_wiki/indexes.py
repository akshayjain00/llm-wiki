from __future__ import annotations


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
    grouped_rows = sorted(rows, key=_sort_key)
    active_rows = sorted(
        [row for row in grouped_rows if row.get("status", "unknown") == "active"],
        key=lambda row: row.get("updated", ""),
        reverse=True,
    )
    non_active_rows = [row for row in grouped_rows if row.get("status", "unknown") != "active"]
    ordered_rows = active_rows + non_active_rows

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
