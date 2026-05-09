"""Unit tests for markdown_graph.py"""
from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki.markdown_graph import (
    _code_block_line_set,
    _parse_frontmatter,
    parse_page,
)


class TestFrontmatterParsing:
    def test_extracts_yaml(self) -> None:
        text = "---\nname: My Project\n---\n# Heading\n"
        fm, body, body_line = _parse_frontmatter(text)
        assert fm.get("name") == "My Project"
        assert "Heading" in body
        assert body_line == 4

    def test_no_frontmatter(self) -> None:
        text = "# Just a heading\n"
        fm, body, body_line = _parse_frontmatter(text)
        assert fm == {}
        assert body == text
        assert body_line == 1

    def test_malformed_frontmatter_graceful(self) -> None:
        text = "---\nnot: valid: yaml:\n---\n# body\n"
        fm, body, _ = _parse_frontmatter(text)
        # Should not raise; fm may be {} or partial
        assert isinstance(fm, dict)


class TestCodeBlockLineSet:
    def test_basic_fence(self) -> None:
        text = "line1\n```\ncode here\n```\nline5\n"
        blocked = _code_block_line_set(text)
        assert 2 in blocked  # opening fence
        assert 3 in blocked  # inside
        assert 4 in blocked  # closing fence
        assert 1 not in blocked
        assert 5 not in blocked

    def test_tilde_fence(self) -> None:
        text = "~~~\ncode\n~~~\n"
        blocked = _code_block_line_set(text)
        assert 1 in blocked
        assert 2 in blocked
        assert 3 in blocked

    def test_unclosed_fence(self) -> None:
        text = "```\ncode line\nnever closed\n"
        blocked = _code_block_line_set(text)
        assert 1 in blocked
        assert 2 in blocked


class TestParsePage:
    def test_extracts_title_from_h1(self, tmp_path: Path) -> None:
        md_file = tmp_path / "wiki" / "projects" / "x" / "project-card.md"
        md_file.parent.mkdir(parents=True)
        md_file.write_text("# My Project\n\nSome body text.\n")
        page = parse_page(tmp_path, md_file)
        assert page.title == "My Project"
        assert page.path == "wiki/projects/x/project-card.md"

    def test_extracts_frontmatter_title(self, tmp_path: Path) -> None:
        md_file = tmp_path / "wiki" / "projects" / "y" / "project-card.md"
        md_file.parent.mkdir(parents=True)
        md_file.write_text("---\ntitle: FM Title\n---\n# Different\n")
        page = parse_page(tmp_path, md_file)
        assert page.title == "FM Title"

    def test_content_hash_deterministic(self, tmp_path: Path) -> None:
        md_file = tmp_path / "wiki" / "projects" / "z" / "project-card.md"
        md_file.parent.mkdir(parents=True)
        md_file.write_text("# Hello\n")
        page1 = parse_page(tmp_path, md_file)
        page2 = parse_page(tmp_path, md_file)
        assert page1.content_hash == page2.content_hash

    def test_links_extracted(self, tmp_path: Path) -> None:
        md_file = tmp_path / "wiki" / "projects" / "w" / "project-card.md"
        md_file.parent.mkdir(parents=True)
        md_file.write_text("# W\n\nSee [Alpha](../alpha/project-card.md) for details.\n")
        page = parse_page(tmp_path, md_file)
        assert any(lk.target_href == "../alpha/project-card.md" for lk in page.links)

    def test_code_block_lines_populated(self, tmp_path: Path) -> None:
        md_file = tmp_path / "wiki" / "projects" / "v" / "project-card.md"
        md_file.parent.mkdir(parents=True)
        md_file.write_text("# V\n```python\ncode\n```\n")
        page = parse_page(tmp_path, md_file)
        # Code block lines should be present (offset by frontmatter=0)
        assert len(page.code_block_lines) > 0
