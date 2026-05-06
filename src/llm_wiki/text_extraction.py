from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class IndexedChunk:
    chunk_id: str
    source_kind: str
    page_id: str | None
    file_id: str | None
    project_slug: str
    chunk_text: str
    content_hash: str
    line_start: int | None
    line_end: int | None
    token_count: int


def _stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_text_into_chunks(
    text: str,
    *,
    project_slug: str,
    source_kind: str,
    source_id: str,
    page_id: str | None = None,
    file_id: str | None = None,
    max_lines: int = 20,
    overlap_lines: int = 3,
) -> list[IndexedChunk]:
    if max_lines < 1:
        raise ValueError("max_lines must be at least 1")
    if overlap_lines < 0 or overlap_lines >= max_lines:
        raise ValueError("overlap_lines must be non-negative and smaller than max_lines")

    chunks: list[IndexedChunk] = []
    lines = text.splitlines()
    if not lines:
        return chunks

    step = max_lines - overlap_lines
    for start in range(0, len(lines), step):
        chunk_lines = lines[start : start + max_lines]
        if not chunk_lines:
            continue
        chunk_text = "\n".join(chunk_lines)
        chunks.append(
            IndexedChunk(
                chunk_id=f"{project_slug}:{source_id}:{len(chunks)}",
                source_kind=source_kind,
                page_id=page_id,
                file_id=file_id,
                project_slug=project_slug,
                chunk_text=chunk_text,
                content_hash=_stable_hash(chunk_text),
                line_start=start + 1,
                line_end=start + len(chunk_lines),
                token_count=len(chunk_text.split()),
            )
        )
    return chunks


def _extract_pdf_text(path: Path) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_path_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _extract_pdf_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_text_chunks(paths: list[Path], project_slug: str) -> list[IndexedChunk]:
    chunks: list[IndexedChunk] = []
    for path in paths:
        text = _extract_path_text(path)
        file_id = f"{project_slug}:{path.name}"
        chunks.extend(
            split_text_into_chunks(
                text,
                project_slug=project_slug,
                source_kind="snapshot_file",
                source_id=path.name,
                file_id=file_id,
            )
        )
    return chunks
