from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from llm_wiki.state_db import index_db_path


def choose_writeback_target(*, project_slugs: list[str], topic_slug: str, page_type: str) -> str:
    today = date.today().isoformat()
    if page_type == "report":
        if len(project_slugs) < 2:
            raise ValueError("report write-backs require at least two projects")
        return f"wiki/reports/{today}-{topic_slug}.md"
    if page_type == "decisions":
        if len(project_slugs) != 1:
            raise ValueError("decisions requires exactly one project")
        return f"wiki/projects/{project_slugs[0]}/decisions.md"
    if page_type == "overview":
        if len(project_slugs) != 1:
            raise ValueError("overview requires exactly one project")
        return f"wiki/projects/{project_slugs[0]}/overview.md"
    raise ValueError(f"unknown page type: {page_type}")


def render_report_markdown(
    *, title: str, question: str, answer: str, citations: list[str]
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Question",
        "",
        question,
        "",
        "## Answer",
        "",
        answer,
        "",
        "## Citations",
        "",
    ]
    lines.extend(f"- {citation}" for citation in citations)
    lines.append("")
    return "\n".join(lines)


def render_project_overview_markdown(*, title: str, summary: str, citations: list[str]) -> str:
    lines = [f"# {title}", "", "## Summary", "", summary, "", "## Citations", ""]
    lines.extend(f"- {citation}" for citation in citations)
    lines.append("")
    return "\n".join(lines)


def render_decisions_markdown(
    *, title: str, decision: str, rationale: str, citations: list[str]
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Decision",
        "",
        decision,
        "",
        "## Rationale",
        "",
        rationale,
        "",
        "## Citations",
        "",
    ]
    lines.extend(f"- {citation}" for citation in citations)
    lines.append("")
    return "\n".join(lines)


def apply_approved_writeback(target_path: Path, rendered_markdown: str, *, allow_replace: bool) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and not allow_replace:
        raise ValueError("manual review required before replacing an existing durable page")
    target_path.write_text(rendered_markdown)


def approve_writeback(workspace: Path, proposal_id: str, *, allow_replace: bool = False) -> Path:
    db_path = index_db_path(workspace)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        proposal = conn.execute(
            """
            SELECT proposal_id, target_path, status, rendered_markdown
            FROM writeback_proposals
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        ).fetchone()
        if proposal is None:
            raise ValueError(f"Write-back proposal '{proposal_id}' not found")
        if proposal["status"] != "pending":
            raise ValueError(f"Write-back proposal '{proposal_id}' is not pending")
        target_path = workspace / str(proposal["target_path"])
        apply_approved_writeback(
            target_path,
            str(proposal["rendered_markdown"]),
            allow_replace=allow_replace,
        )
        conn.execute(
            """
            UPDATE writeback_proposals
            SET status = 'applied', reviewed_at = datetime('now'), applied_at = datetime('now')
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        )
        conn.commit()
        return target_path
    finally:
        conn.close()
