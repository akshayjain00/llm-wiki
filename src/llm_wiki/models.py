from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Confidence = Literal["low", "medium", "high"]
ProjectStatus = Literal["planned", "active", "paused", "blocked", "completed", "unknown"]


@dataclass(frozen=True)
class ProjectCardData:
    project_name: str
    slug: str
    domain: str = "unknown"
    source_roots: list[str] = field(default_factory=list)
    live_refs: list[str] = field(default_factory=list)
    owner: str = "unknown"
    owner_confidence: Confidence = "low"
    status: ProjectStatus = "unknown"
    status_confidence: Confidence = "low"
    last_ingested: str = "unknown"
    last_reviewed: str = "unknown"
    canonical_snapshot: str = "unknown"
    summary: str = "Summary unavailable from current evidence."
    current_scope: list[str] = field(default_factory=list)
    key_artifacts: list[str] = field(default_factory=list)
    key_questions: list[str] = field(default_factory=list)
    risks_or_blockers: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    related_pages: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RefManifestData:
    project_slug: str
    authoritative_live_paths: list[str]
    repo_roots: list[str] = field(default_factory=list)
    origin_roots: list[str] = field(default_factory=list)
    excluded_paths: list[str] = field(default_factory=list)
    duplicate_source_notes: list[str] = field(default_factory=list)
    last_scanned_timestamp: str = "unknown"
    ref_rationale: str = (
        "Refs preserve authoritative live locations without mirroring entire repos."
    )
