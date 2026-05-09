"""LLM Wiki Phase 3 — graph data structures.

Dataclasses for all graph domain objects.  Column names here match
state_db / server.py expectations (some deviate from spec names;
deviations are noted inline).
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Core nodes / edges
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GraphNode:
    node_id: str           # stable: "page:<path>" or "project:<slug>" or "entity:<slug>"
    node_type: str         # "page" | "project" | "entity" | "concept" | "report" | "source"
    canonical_name: str    # human label  (spec calls this "title")
    canonical_path: str    # workspace-relative path if file-backed, else ""
    project_slug: str      # "" if not project-scoped
    content_hash: str      # sha256[:16] of source file, "" for synthetic nodes
    metadata_json: str     # "{}" by default
    created_at: str        # ISO-8601 rebuild timestamp


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str           # deterministic sha256 of source+type+target+line
    source_node_id: str
    target_node_id: str
    edge_type: str         # "links_to"|"mentions"|"backlinks_to"|"belongs_to_project"|"alias_of"|"derived_from"
    source_path: str       # file where edge was observed
    source_line: int       # spec calls this "line_start"; 0 if unknown
    confidence: float      # 0.0–1.0
    evidence_text: str     # short excerpt
    created_at: str


@dataclass(frozen=True)
class EntityAlias:
    alias_id: str          # deterministic sha256 of entity_id+alias
    node_id: str           # canonical entity node  (spec: "entity_id")
    alias: str             # original alias text    (spec: "alias_text")
    normalized_alias: str  # matching key
    source: str            # "slug"|"title"|"heading"|"metadata"|"link"
    confidence: float


# ---------------------------------------------------------------------------
# Link proposals
# ---------------------------------------------------------------------------

@dataclass
class LinkProposal:
    proposal_id: str       # deterministic sha256 of source_path+original_text+target_node_id+line
    source_path: str
    target_node_id: str
    target_title: str      # human label for the target (extra col vs spec)
    proposal_kind: str     # "missing_internal_link"
    original_text: str
    replacement_markdown: str
    source_line: int       # spec: "line_start"
    char_start: int
    char_end: int
    base_content_hash: str
    confidence: float
    rationale: str
    status: str            # "pending"|"dismissed"|"superseded"|"applied"
    created_at: str
    reviewed_at: str       # "" if not reviewed


# ---------------------------------------------------------------------------
# Result objects returned by service functions
# ---------------------------------------------------------------------------

@dataclass
class GraphRebuildResult:
    run_id: str
    status: str            # "success"|"failed"|"partial"
    pages_scanned: int
    nodes_created: int
    edges_created: int
    aliases_created: int
    proposals_created: int
    warnings: list[str] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""


@dataclass
class GraphSummary:
    nodes: int
    edges: int
    entities: int
    pages: int
    pending_link_proposals: int
    last_rebuild_at: str   # "" if never rebuilt


@dataclass(frozen=True)
class Backlink:
    source_node_id: str
    source_title: str
    edge_type: str
    evidence_text: str
    source_line: int
