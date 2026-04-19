from llm_wiki.indexes import sort_index_rows


def test_sort_index_rows_orders_by_status_priority_then_recency() -> None:
    rows = [
        {"name": "Blocked", "status": "blocked", "updated": "2026-04-08"},
        {"name": "Active New", "status": "active", "updated": "2026-04-10"},
        {"name": "Active Old", "status": "active", "updated": "2026-04-07"},
    ]

    sorted_rows = sort_index_rows(rows)

    assert [row["name"] for row in sorted_rows] == ["Active New", "Active Old", "Blocked"]
