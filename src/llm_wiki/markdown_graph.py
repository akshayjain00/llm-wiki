"""LLM Wiki Phase 3 — deterministic markdown page discovery and extraction.

Discovers durable wiki pages and extracts:
- internal markdown links (existing cross-links)
- heading text
- frontmatter title / project name / aliases
- prose entity mentions (used for proposal generation)

Uses markdown-it-py for token-based parsing.  No markdown is mutated.
"""
from __future__ import annotations

import fnmatch
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from markdown_it import MarkdownIt  # type: ignore[import-untyped]
    _HAS_MD_IT = True
except ImportError:
    _HAS_MD_IT = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DURABLE_PAGE_GLOBS = (
    "wiki/projects/**/project-card.md",
    "wiki/projects/**/overview.md",
    "wiki/projects/**/decisions.md",
    "wiki/reports/*.md",
)

EXCLUDE_PATH_PREFIXES = (
    "wiki/indexes/",
    "logs/",
    "raw/",
    "state/",
    ".venv/",
)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ExtractedLink:
    """A markdown link found in a source page."""
    source_path: str    # workspace-relative
    target_text: str    # link label
    target_href: str    # link href (may be relative path or URL)
    line_no: int        # 1-based


@dataclass
class ExtractedHeading:
    source_path: str
    level: int          # 1–6
    text: str
    line_no: int


@dataclass
class ParsedPage:
    """All extracted information from one durable wiki page."""
    path: str                               # workspace-relative
    title: str                              # first H1 or frontmatter title
    content_hash: str                       # sha256 hex of raw bytes
    raw_text: str                           # full file content
    frontmatter: dict[str, Any]             # parsed YAML frontmatter (empty if absent)
    headings: list[ExtractedHeading] = field(default_factory=list)
    links: list[ExtractedLink] = field(default_factory=list)
    # Line numbers of spans to SKIP during proposal generation
    code_block_lines: set[int] = field(default_factory=set)
    frontmatter_lines: set[int] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Page discovery
# ---------------------------------------------------------------------------

def _is_excluded(rel_path: str) -> bool:
    for prefix in EXCLUDE_PATH_PREFIXES:
        if rel_path.startswith(prefix):
            return True
    return False


def discover_durable_pages(workspace: Path) -> list[Path]:
    """Return absolute paths of durable wiki markdown pages in the workspace."""
    found: list[Path] = []
    seen: set[Path] = set()
    for glob in DURABLE_PAGE_GLOBS:
        for path in workspace.glob(glob):
            if path in seen:
                continue
            seen.add(path)
            rel = str(path.relative_to(workspace))
            if _is_excluded(rel):
                continue
            if path.is_file() and path.suffix == ".md":
                found.append(path)
    return sorted(found)


# ---------------------------------------------------------------------------
# Frontmatter parsing (no external dep)
# ---------------------------------------------------------------------------

_FM_FENCE = re.compile(r"^---\s*$")


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str, int]:
    """Return (frontmatter_dict, body_text, body_start_line_1based)."""
    lines = text.splitlines(keepends=True)
    if not lines or not _FM_FENCE.match(lines[0].rstrip()):
        return {}, text, 1
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if _FM_FENCE.match(line.rstrip()):
            end = i
            break
    if end is None:
        return {}, text, 1
    fm_text = "".join(lines[1:end])
    try:
        import yaml  # type: ignore[import-untyped]
        fm = yaml.safe_load(fm_text) or {}
    except Exception:
        fm = {}
    body = "".join(lines[end + 1:])
    return fm, body, end + 2  # body starts at line end+2 (1-based)


# ---------------------------------------------------------------------------
# Code block / inline code span detection (regex-based, conservative)
# ---------------------------------------------------------------------------

_CODE_FENCE_RE = re.compile(r"^(`{3,}|~{3,})", re.MULTILINE)


def _code_block_line_set(text: str) -> set[int]:
    """Return 1-based line numbers that are inside fenced code blocks."""
    lines = text.splitlines()
    in_block = False
    fence_char = ""
    fence_len = 0
    blocked: set[int] = set()
    for i, line in enumerate(lines, start=1):
        m = re.match(r"^(`{3,}|~{3,})", line)
        if m:
            ch = m.group(1)[0]
            ln = len(m.group(1))
            if not in_block:
                in_block = True
                fence_char = ch
                fence_len = ln
                blocked.add(i)
            elif ch == fence_char and ln >= fence_len:
                blocked.add(i)
                in_block = False
        elif in_block:
            blocked.add(i)
    return blocked


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_URL_RE = re.compile(r"^https?://")


def _extract_with_regex(text: str, rel_path: str, line_offset: int) -> tuple[
    list[ExtractedLink], list[ExtractedHeading]
]:
    """Fallback regex extraction when markdown-it-py is unavailable."""
    links: list[ExtractedLink] = []
    headings: list[ExtractedHeading] = []
    for lineno, line in enumerate(text.splitlines(), start=line_offset):
        hm = _HEADING_RE.match(line)
        if hm:
            headings.append(ExtractedHeading(
                source_path=rel_path,
                level=len(hm.group(1)),
                text=hm.group(2),
                line_no=lineno,
            ))
        for lm in _MD_LINK_RE.finditer(line):
            links.append(ExtractedLink(
                source_path=rel_path,
                target_text=lm.group(1),
                target_href=lm.group(2),
                line_no=lineno,
            ))
    return links, headings


def _extract_with_markdown_it(text: str, rel_path: str, line_offset: int) -> tuple[
    list[ExtractedLink], list[ExtractedHeading]
]:
    """Token-based extraction using markdown-it-py."""
    md = MarkdownIt()
    tokens = md.parse(text)
    links: list[ExtractedLink] = []
    headings: list[ExtractedHeading] = []

    def _walk(toks: list[Any]) -> None:  # type: ignore[type-arg]
        i = 0
        while i < len(toks):
            tok = toks[i]
            if tok.type == "heading_open":
                level = int(tok.tag[1])
                inline_tok = toks[i + 1] if i + 1 < len(toks) else None
                if inline_tok and inline_tok.type == "inline" and inline_tok.children:
                    heading_text = "".join(
                        c.content for c in inline_tok.children if c.type == "text"
                    )
                    raw_line = (tok.map[0] if tok.map else 0) + line_offset
                    headings.append(ExtractedHeading(
                        source_path=rel_path,
                        level=level,
                        text=heading_text,
                        line_no=raw_line,
                    ))
            if tok.type == "inline" and tok.children:
                j = 0
                while j < len(tok.children):
                    child = tok.children[j]
                    if child.type == "link_open":
                        href = child.attrGet("href") or ""
                        label_parts: list[str] = []
                        k = j + 1
                        while k < len(tok.children) and tok.children[k].type != "link_close":
                            if tok.children[k].type == "text":
                                label_parts.append(tok.children[k].content)
                            k += 1
                        raw_line = (tok.map[0] if tok.map else 0) + line_offset
                        links.append(ExtractedLink(
                            source_path=rel_path,
                            target_text="".join(label_parts),
                            target_href=href,
                            line_no=raw_line,
                        ))
                    j += 1
            if tok.children:
                _walk(tok.children)
            i += 1

    _walk(tokens)
    return links, headings


def parse_page(workspace: Path, page_path: Path) -> ParsedPage:
    """Parse a single durable wiki page into a ParsedPage."""
    raw_bytes = page_path.read_bytes()
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    content_hash = hashlib.sha256(raw_bytes).hexdigest()
    rel_path = str(page_path.relative_to(workspace))

    frontmatter, body, body_line = _parse_frontmatter(raw_text)

    # Frontmatter line set (1-based)
    fm_lines: set[int] = set(range(1, body_line))

    # Code block line set (relative to full file, i.e. body_line offset)
    body_code_lines = _code_block_line_set(body)
    # Shift to absolute line numbers
    code_lines = {ln + body_line - 1 for ln in body_code_lines}

    # Extract title: frontmatter > first H1 > filename stem
    title = str(frontmatter.get("title", "") or frontmatter.get("name", "") or "")

    if _HAS_MD_IT:
        links, headings = _extract_with_markdown_it(body, rel_path, body_line)
    else:
        links, headings = _extract_with_regex(body, rel_path, body_line)

    if not title and headings:
        title = next((h.text for h in headings if h.level == 1), headings[0].text)
    if not title:
        title = page_path.stem.replace("-", " ").replace("_", " ").title()

    return ParsedPage(
        path=rel_path,
        title=title,
        content_hash=content_hash,
        raw_text=raw_text,
        frontmatter=frontmatter,
        headings=headings,
        links=links,
        code_block_lines=code_lines,
        frontmatter_lines=fm_lines,
    )


def parse_all_pages(workspace: Path) -> list[ParsedPage]:
    """Discover and parse all durable wiki pages."""
    pages: list[ParsedPage] = []
    for path in discover_durable_pages(workspace):
        try:
            pages.append(parse_page(workspace, path))
        except Exception:
            pass  # skip unreadable files; graph_builder logs warnings
    return pages
