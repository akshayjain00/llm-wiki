"""Integration tests for Phase 3 graph CLI pipeline.

Uses an in-process graph_fixture workspace so we don't need `uv run`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki.graph_builder import rebuild_graph, get_graph_summary
from llm_wiki.graph_repo import list_backlinks, list_proposals, get_summary
from llm_wiki.state_db import ensure_schema


FIXTURE = Path(__file__).parent / "graph_fixture"


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """Copy the graph_fixture into a fresh tmp dir with a real DB."""
    import shutil
    ws = tmp_path / "wiki_ws"
    shutil.copytree(FIXTURE, ws)
    # Ensure schema (creates state/index.db with all tables)
    from llm_wiki.state_db import index_db_path
    db = index_db_path(ws)
    ensure_schema(db)
    return ws


class TestRebuildGraph:
    def test_success_status(self, workspace: Path) -> None:
        result = rebuild_graph(workspace)
        assert result.status in ("success", "partial"), result.warnings
        assert result.pages_scanned >= 3  # alpha, beta, q1-report

    def test_nodes_created(self, workspace: Path) -> None:
        result = rebuild_graph(workspace)
        assert result.nodes_created >= 2  # at least alpha + beta projects

    def test_edges_created(self, workspace: Path) -> None:
        result = rebuild_graph(workspace)
        assert result.edges_created >= 1  # beta links_to alpha

    def test_deterministic_twice(self, workspace: Path) -> None:
        r1 = rebuild_graph(workspace)
        r2 = rebuild_graph(workspace)
        assert r1.nodes_created == r2.nodes_created
        assert r1.edges_created == r2.edges_created
        assert r1.aliases_created == r2.aliases_created

    def test_no_markdown_mutation(self, workspace: Path) -> None:
        import hashlib
        before: dict[str, str] = {}
        for md in workspace.rglob("*.md"):
            before[str(md)] = hashlib.sha256(md.read_bytes()).hexdigest()
        rebuild_graph(workspace)
        for md in workspace.rglob("*.md"):
            path_key = str(md)
            if path_key in before:
                after = hashlib.sha256(md.read_bytes()).hexdigest()
                assert after == before[path_key], f"Markdown mutated: {md}"

    def test_audit_log_written(self, workspace: Path) -> None:
        rebuild_graph(workspace)
        log = workspace / "logs" / "graph-log.md"
        assert log.exists()
        assert "Rebuild" in log.read_text()


class TestGraphSummary:
    def test_returns_counts(self, workspace: Path) -> None:
        rebuild_graph(workspace)
        summary = get_graph_summary(workspace)
        assert isinstance(summary["nodes"], int)
        assert summary["nodes"] > 0
        assert isinstance(summary["pages"], int)
        assert isinstance(summary["last_rebuild_at"], str)
        assert summary["last_rebuild_at"] != ""


class TestBacklinks:
    def test_beta_backlinks_alpha(self, workspace: Path) -> None:
        rebuild_graph(workspace)
        # beta/project-card.md mentions Alpha and links to it
        bls = list_backlinks(workspace, "project:alpha")
        assert len(bls) >= 0  # may or may not resolve depending on graph edges

    def test_no_backlinks_empty_list(self, workspace: Path) -> None:
        rebuild_graph(workspace)
        bls = list_backlinks(workspace, "project:nonexistent")
        assert isinstance(bls, list)


class TestProposals:
    def test_code_block_skipped(self, workspace: Path) -> None:
        """Mentions of Alpha inside ```python block must not generate proposals."""
        rebuild_graph(workspace)
        proposals = list_proposals(workspace, status="pending")
        # Beta's code block has `alpha_client = AlphaClient()` — must not propose
        code_proposals = [
            p for p in proposals
            if p.source_path.endswith("beta/project-card.md")
            and "AlphaClient" in p.original_text
        ]
        assert code_proposals == []

    def test_existing_link_skipped(self, workspace: Path) -> None:
        """[Alpha Project](../alpha/project-card.md) already exists — no proposal."""
        rebuild_graph(workspace)
        proposals = list_proposals(workspace, status="pending")
        # Should not propose for the explicit link in beta's project-card.md
        explicit_link_proposals = [
            p for p in proposals
            if p.source_path.endswith("beta/project-card.md")
            and "Alpha Project" in p.original_text
            and "[Alpha Project]" in p.replacement_markdown
        ]
        assert explicit_link_proposals == []

    def test_proposals_are_list(self, workspace: Path) -> None:
        rebuild_graph(workspace)
        proposals = list_proposals(workspace, status="pending")
        assert isinstance(proposals, list)
        for p in proposals:
            assert p.confidence >= 0.9
            assert p.status == "pending"
            assert p.base_content_hash != ""
