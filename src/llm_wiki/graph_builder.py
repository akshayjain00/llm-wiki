"""LLM Wiki Phase 3 — graph rebuild orchestration.

rebuild_graph(workspace) is the single entry point.  It:
1. Parses all durable wiki pages
2. Builds the entity/alias registry
3. Creates graph nodes (pages + projects + entities)
4. Creates graph edges (links_to, mentions, belongs_to_project)
5. Generates high-confidence link proposals
6. Persists everything in one atomic transaction
7. Writes an audit log entry to logs/graph-log.md

No markdown files are mutated during this process (FR NFR1).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from llm_wiki.entity_resolution import (
    AliasRegistry,
    alias_id,
    build_registry_from_pages,
    normalize,
)
from llm_wiki.graph_models import (
    EntityAlias,
    GraphEdge,
    GraphNode,
    GraphRebuildResult,
    LinkProposal,
)
from llm_wiki.graph_repo import (
    clear_graph_tables,
    insert_aliases,
    insert_edges,
    insert_nodes,
    insert_proposals,
    record_rebuild_run,
)
from llm_wiki.link_proposals import generate_proposals
from llm_wiki.markdown_graph import ParsedPage, parse_all_pages
from llm_wiki.state_db import ensure_graph_schema, index_db_path


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------

def _edge_id(src: str, edge_type: str, tgt: str, line: int) -> str:
    raw = f"{src}\x00{edge_type}\x00{tgt}\x00{line}"
    return "edge_" + hashlib.sha256(raw.encode()).hexdigest()[:20]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Project discovery from workspace
# ---------------------------------------------------------------------------

def _discover_projects(workspace: Path) -> list[tuple[str, str]]:
    """Return [(slug, name), ...] from wiki/projects/*/project-card.md metadata."""
    results: list[tuple[str, str]] = []
    projects_dir = workspace / "wiki" / "projects"
    if not projects_dir.exists():
        return results
    for card in sorted(projects_dir.glob("*/project-card.md")):
        slug = card.parent.name
        # Try to read name from frontmatter or H1
        try:
            text = card.read_text(errors="replace")
            name = slug  # default
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("name:"):
                    name = stripped[5:].strip().strip('"').strip("'")
                    break
                if stripped.startswith("# "):
                    name = stripped[2:].strip()
                    break
            results.append((slug, name))
        except Exception:
            results.append((slug, slug))
    return results


# ---------------------------------------------------------------------------
# Node / edge / alias construction
# ---------------------------------------------------------------------------

def _build_project_nodes(
    project_slugs: list[tuple[str, str]], now: str
) -> list[GraphNode]:
    return [
        GraphNode(
            node_id=f"project:{slug}",
            node_type="project",
            canonical_name=name,
            canonical_path=f"wiki/projects/{slug}/project-card.md",
            project_slug=slug,
            content_hash="",
            metadata_json="{}",
            created_at=now,
        )
        for slug, name in project_slugs
    ]


def _build_page_nodes(pages: list[ParsedPage], now: str) -> list[GraphNode]:
    nodes: list[GraphNode] = []
    for page in pages:
        # Determine node_type from path
        if "project-card" in page.path:
            ntype = "project"
        elif "/reports/" in page.path:
            ntype = "report"
        else:
            ntype = "page"

        # Extract project_slug from path: wiki/projects/<slug>/...
        parts = Path(page.path).parts
        pslug = ""
        if len(parts) >= 3 and parts[0] == "wiki" and parts[1] == "projects":
            pslug = parts[2]

        nodes.append(GraphNode(
            node_id=f"page:{page.path}",
            node_type=ntype,
            canonical_name=page.title,
            canonical_path=page.path,
            project_slug=pslug,
            content_hash=page.content_hash[:16],
            metadata_json="{}",
            created_at=now,
        ))
    return nodes


def _build_edges_from_pages(
    pages: list[ParsedPage],
    registry: AliasRegistry,
    all_node_ids: set[str],
    now: str,
) -> tuple[list[GraphEdge], list[str]]:
    """Build links_to, mentions, belongs_to_project edges."""
    edges: list[GraphEdge] = []
    warnings: list[str] = []

    for page in pages:
        src_node_id = f"page:{page.path}"
        parts = Path(page.path).parts
        project_slug = parts[2] if len(parts) >= 3 and parts[0] == "wiki" else ""

        # belongs_to_project
        if project_slug:
            proj_node = f"project:{project_slug}"
            if proj_node in all_node_ids:
                eid = _edge_id(src_node_id, "belongs_to_project", proj_node, 0)
                edges.append(GraphEdge(
                    edge_id=eid,
                    source_node_id=src_node_id,
                    target_node_id=proj_node,
                    edge_type="belongs_to_project",
                    source_path=page.path,
                    source_line=0,
                    confidence=1.0,
                    evidence_text="",
                    created_at=now,
                ))

        # links_to — from explicit markdown links
        for link in page.links:
            href = link.target_href
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            # Resolve relative path to workspace-relative
            try:
                abs_target = (Path(page.path).parent / href).resolve()
                # We can't use workspace.resolve() here, so just normalize the path
                rel_target = str(Path(page.path).parent / href)
                # Clean up ../
                from pathlib import PurePosixPath
                rel_target = str(PurePosixPath(rel_target))
            except Exception:
                continue
            tgt_node = f"page:{rel_target}"
            if tgt_node not in all_node_ids:
                # Try stripping leading component
                continue
            eid = _edge_id(src_node_id, "links_to", tgt_node, link.line_no)
            edges.append(GraphEdge(
                edge_id=eid,
                source_node_id=src_node_id,
                target_node_id=tgt_node,
                edge_type="links_to",
                source_path=page.path,
                source_line=link.line_no,
                confidence=1.0,
                evidence_text=link.target_text[:120],
                created_at=now,
            ))

        # mentions — from entity alias matches in prose (for entities only)
        for lineno, line_text in enumerate(page.raw_text.splitlines(), start=1):
            if lineno in page.frontmatter_lines or lineno in page.code_block_lines:
                continue
            for reg in registry.all_aliases():
                if reg.node_id == src_node_id:
                    continue
                import re
                pattern = re.compile(re.escape(reg.alias), re.IGNORECASE)
                if pattern.search(line_text):
                    tgt_node = reg.node_id
                    if tgt_node not in all_node_ids:
                        continue
                    eid = _edge_id(src_node_id, "mentions", tgt_node, lineno)
                    evidence = line_text.strip()[:120]
                    edges.append(GraphEdge(
                        edge_id=eid,
                        source_node_id=src_node_id,
                        target_node_id=tgt_node,
                        edge_type="mentions",
                        source_path=page.path,
                        source_line=lineno,
                        confidence=reg.confidence,
                        evidence_text=evidence,
                        created_at=now,
                    ))

    # Deduplicate by edge_id
    seen: set[str] = set()
    unique: list[GraphEdge] = []
    for e in edges:
        if e.edge_id not in seen:
            seen.add(e.edge_id)
            unique.append(e)
    return unique, warnings


def _build_aliases(
    registry: AliasRegistry, now: str
) -> list[EntityAlias]:
    result: list[EntityAlias] = []
    for reg in registry.all_aliases():
        result.append(EntityAlias(
            alias_id=alias_id(reg.node_id, reg.alias),
            node_id=reg.node_id,
            alias=reg.alias,
            normalized_alias=reg.normalized,
            source=reg.source,
            confidence=reg.confidence,
        ))
    return result


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def _write_audit_log(workspace: Path, result: GraphRebuildResult) -> None:
    log_dir = workspace / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "graph-log.md"
    entry = (
        f"\n## Rebuild {result.run_id} — {result.completed_at}\n\n"
        f"- Status: `{result.status}`\n"
        f"- Pages scanned: {result.pages_scanned}\n"
        f"- Nodes created: {result.nodes_created}\n"
        f"- Edges created: {result.edges_created}\n"
        f"- Aliases created: {result.aliases_created}\n"
        f"- Proposals created: {result.proposals_created}\n"
    )
    if result.warnings:
        entry += "- Warnings:\n"
        for w in result.warnings:
            entry += f"  - {w}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def rebuild_graph(workspace: Path) -> GraphRebuildResult:
    """Rebuild the full graph from durable wiki markdown.

    Clears and repopulates graph tables in a single atomic SQLite transaction.
    Does NOT mutate any markdown files.
    """
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    started_at = _now()
    warnings: list[str] = []

    # Ensure DB + graph schema exist
    db_path = index_db_path(workspace)
    ensure_graph_schema(db_path)

    # 1. Parse all durable pages
    pages: list[ParsedPage] = []
    try:
        pages = parse_all_pages(workspace)
    except Exception as exc:
        warnings.append(f"Page parse error: {exc}")

    # 2. Discover projects
    project_slugs = _discover_projects(workspace)

    # 3. Build alias registry
    registry = build_registry_from_pages(pages, project_slugs)

    now = _now()

    # 4. Build nodes
    project_nodes = _build_project_nodes(project_slugs, now)
    page_nodes = _build_page_nodes(pages, now)
    all_nodes = project_nodes + page_nodes
    all_node_ids = {n.node_id for n in all_nodes}

    # 5. Build edges
    edges, edge_warnings = _build_edges_from_pages(pages, registry, all_node_ids, now)
    warnings.extend(edge_warnings)

    # 6. Build aliases
    aliases = _build_aliases(registry, now)

    # 7. Build proposals
    node_titles = {n.node_id: n.canonical_name for n in all_nodes}
    node_paths = {n.node_id: n.canonical_path for n in all_nodes}
    proposals: list[LinkProposal] = []
    try:
        proposals = generate_proposals(pages, registry, node_titles, node_paths)
    except Exception as exc:
        warnings.append(f"Proposal generation error: {exc}")

    # 8. Persist atomically
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("BEGIN")
        clear_graph_tables(conn)
        insert_nodes(conn, all_nodes)
        insert_edges(conn, edges)
        insert_aliases(conn, aliases)
        insert_proposals(conn, proposals)
        completed_at = _now()
        result = GraphRebuildResult(
            run_id=run_id,
            status="success" if not warnings else "partial",
            pages_scanned=len(pages),
            nodes_created=len(all_nodes),
            edges_created=len(edges),
            aliases_created=len(aliases),
            proposals_created=len(proposals),
            warnings=warnings,
            started_at=started_at,
            completed_at=completed_at,
        )
        record_rebuild_run(conn, result)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        result = GraphRebuildResult(
            run_id=run_id,
            status="failed",
            pages_scanned=len(pages),
            nodes_created=0,
            edges_created=0,
            aliases_created=0,
            proposals_created=0,
            warnings=[str(exc)],
            started_at=started_at,
            completed_at=_now(),
        )
    finally:
        conn.close()

    # 9. Write audit log
    try:
        _write_audit_log(workspace, result)
    except Exception:
        pass  # audit log failure is non-fatal

    return result


def get_graph_summary(workspace: Path, project_slug: str | None = None) -> dict[str, object]:
    """Return summary counts and last rebuild metadata."""
    from llm_wiki.graph_repo import get_summary
    s = get_summary(workspace, project_slug)
    return {
        "nodes": s.nodes,
        "edges": s.edges,
        "entities": s.entities,
        "pages": s.pages,
        "pending_link_proposals": s.pending_link_proposals,
        "last_rebuild_at": s.last_rebuild_at,
    }
