from __future__ import annotations


def format_snapshot_citation(
    *,
    project_slug: str,
    snapshot_id: str,
    relative_path: str,
    chunk_id: str,
    line_start: int | None,
    line_end: int | None,
) -> str:
    if line_start is not None and line_end is not None:
        return (
            f"[snapshot:{project_slug}/{snapshot_id}/{relative_path}"
            f"#L{line_start}-L{line_end} chunk={chunk_id}]"
        )
    return f"[snapshot:{project_slug}/{snapshot_id}/{relative_path} chunk={chunk_id}]"


def format_wiki_citation(*, path: str, heading: str) -> str:
    return f"[wiki:{path}#{heading}]"
