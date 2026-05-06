from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from llm_wiki.citations import format_wiki_citation
from llm_wiki.models import ProjectCardData
from llm_wiki.state_db import ensure_schema, index_db_path


@dataclass(frozen=True)
class QueryEvidence:
    card: ProjectCardData
    citation: str


def _append_query_log(
    workspace: Path,
    *,
    query_id: str,
    projects: list[str],
    question: str,
    used_snapshot_fallback: bool,
) -> None:
    log_path = workspace / "logs" / "query-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    existing = log_path.read_text() if log_path.exists() else "# Query Log\n\n"
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    entry = "\n".join(
        [
            f"## [{timestamp}] query | {query_id}",
            "",
            f"- projects: {', '.join(projects)}",
            f"- question: {question}",
            f"- snapshot fallback: {'yes' if used_snapshot_fallback else 'no'}",
            "- write-back: not proposed",
            "",
        ]
    )
    log_path.write_text(existing + entry)


def _persist_query(
    workspace: Path,
    *,
    query_id: str,
    question: str,
    projects: list[str],
    evidence: list[QueryEvidence],
    used_snapshot_fallback: bool,
) -> None:
    db_path = index_db_path(workspace)
    ensure_schema(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO query_runs (
                query_id, asked_at, question_text, requested_projects, model_provider,
                model_name, used_snapshot_fallback, status, token_input, token_output,
                cost_estimate, latency_ms
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                query_id,
                question,
                json.dumps(projects),
                "local",
                "deterministic-card-summary",
                int(used_snapshot_fallback),
                "success",
                0,
                0,
                0.0,
                0,
            ),
        )
        for rank, item in enumerate(evidence, start=1):
            conn.execute(
                """
                INSERT INTO query_evidence (
                    query_id, chunk_id, lexical_score, semantic_score, fused_score, rank
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    query_id,
                    item.citation,
                    float(rank),
                    float(rank),
                    float(rank),
                    rank,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def run_phase2_query(
    *,
    workspace: Path,
    project_cards: list[ProjectCardData],
    question: str,
) -> str:
    if len(project_cards) < 2 or len(project_cards) > 5:
        raise ValueError("Phase 2 query requires between 2 and 5 projects")

    evidence = [
        QueryEvidence(
            card=card,
            citation=format_wiki_citation(
                path=f"wiki/projects/{card.slug}/project-card.md",
                heading="Summary",
            ),
        )
        for card in project_cards
        if card.summary.strip()
    ]
    if not evidence:
        raise ValueError("no valid evidence available for cited synthesis")

    query_id = f"qry_{uuid4().hex[:12]}"
    used_snapshot_fallback = False
    projects = [item.card.slug for item in evidence]
    answer_lines = [
        "Answer:",
        f"Compared {len(evidence)} projects for: {question}",
        "",
    ]
    for item in evidence:
        answer_lines.append(f"- {item.card.project_name}: {item.card.summary}")
    answer_lines.extend(
        [
            "",
            f"Snapshot fallback: {'yes' if used_snapshot_fallback else 'no'}",
            "",
            "Citations:",
            *[item.citation for item in evidence],
            "",
        ]
    )

    _persist_query(
        workspace,
        query_id=query_id,
        question=question,
        projects=projects,
        evidence=evidence,
        used_snapshot_fallback=used_snapshot_fallback,
    )
    _append_query_log(
        workspace,
        query_id=query_id,
        projects=projects,
        question=question,
        used_snapshot_fallback=used_snapshot_fallback,
    )
    return "\n".join(answer_lines)
