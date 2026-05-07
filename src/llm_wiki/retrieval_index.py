from __future__ import annotations

import sqlite3
from pathlib import Path

from llm_wiki.state_db import ensure_schema, index_db_path, upsert_chunks
from llm_wiki.text_extraction import IndexedChunk, extract_text_chunks, split_text_into_chunks
from llm_wiki.wiki_writer import load_project_card

SUPPORTED_TEXT_SUFFIXES = {".md", ".txt", ".pdf"}


def _clear_retrieval_index(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM embeddings")
        conn.execute("DELETE FROM fts_chunks")
        conn.execute("DELETE FROM chunks")
        conn.commit()
    finally:
        conn.close()


def _iter_supported_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root] if root.suffix.lower() in SUPPORTED_TEXT_SUFFIXES else []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_TEXT_SUFFIXES
    )


def _wiki_page_chunks(workspace: Path, project_dir: Path, project_slug: str) -> list[IndexedChunk]:
    chunks: list[IndexedChunk] = []
    for page_path in sorted(project_dir.glob("*.md")):
        relative_path = page_path.relative_to(workspace).as_posix()
        chunks.extend(
            split_text_into_chunks(
                page_path.read_text(encoding="utf-8", errors="ignore"),
                project_slug=project_slug,
                source_kind="wiki_page",
                source_id=relative_path,
                page_id=relative_path,
            )
        )
    return chunks


def rebuild_retrieval_index(workspace: Path) -> int:
    db_path = index_db_path(workspace)
    ensure_schema(db_path)
    _clear_retrieval_index(db_path)

    chunks: list[IndexedChunk] = []
    for card_path in sorted((workspace / "wiki" / "projects").rglob("project-card.md")):
        card = load_project_card(card_path)
        chunks.extend(_wiki_page_chunks(workspace, card_path.parent, card.slug))
        if card.canonical_snapshot != "unknown":
            snapshot_root = workspace / card.canonical_snapshot
            chunks.extend(extract_text_chunks(_iter_supported_files(snapshot_root), card.slug))

    upsert_chunks(db_path, chunks)
    return len(chunks)
