"""LLM Wiki Phase 3 — high-confidence missing link proposal generation.

Scans durable wiki page prose for entity mentions that do not already have
a markdown link, and generates structured proposals.

Safety rules (FR6):
- Skip code blocks and inline code spans
- Skip frontmatter
- Skip existing markdown links [text](href)
- Skip URLs (http/https)
- Skip citation-like patterns ([1], [^fn])
- Only propose for unambiguously resolved entities
- Only propose when confidence >= MIN_CONFIDENCE
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from llm_wiki.entity_resolution import AliasRegistry, normalize
from llm_wiki.graph_models import LinkProposal
from llm_wiki.markdown_graph import ParsedPage

MIN_CONFIDENCE = 0.90

# Pattern matching existing markdown links — skip these spans
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
# Inline code spans
_INLINE_CODE_RE = re.compile(r"`[^`]+`")
# URL-only mentions
_URL_RE = re.compile(r"https?://\S+")
# Citation patterns [1], [^fn], [ref]
_CITATION_RE = re.compile(r"\[\^?[\w-]+\](?!\()")


def _proposal_id(source_path: str, original_text: str, target_node_id: str, line: int) -> str:
    raw = f"{source_path}\x00{original_text}\x00{target_node_id}\x00{line}"
    return "prop_" + hashlib.sha256(raw.encode()).hexdigest()[:20]


def _relative_link(source_path: str, target_path: str) -> str:
    """Compute a relative markdown href from source_path to target_path."""
    src = Path(source_path)
    tgt = Path(target_path)
    try:
        rel = tgt.relative_to(src.parent)
        return str(rel)
    except ValueError:
        # Not a common ancestor — use path from workspace root
        parts_src = src.parent.parts
        parts_tgt = tgt.parts
        common = 0
        for a, b in zip(parts_src, parts_tgt):
            if a == b:
                common += 1
            else:
                break
        ups = len(parts_src) - common
        downs = parts_tgt[common:]
        return "/".join([".."] * ups + list(downs))


def _collect_skip_spans(line_text: str) -> list[tuple[int, int]]:
    """Return character spans to skip in a line (existing links, inline code, URLs, citations)."""
    spans: list[tuple[int, int]] = []
    for pattern in (_MD_LINK_RE, _INLINE_CODE_RE, _URL_RE, _CITATION_RE):
        for m in pattern.finditer(line_text):
            spans.append((m.start(), m.end()))
    return spans


def _is_in_skip_span(start: int, end: int, skip_spans: list[tuple[int, int]]) -> bool:
    for ss, se in skip_spans:
        if start < se and end > ss:
            return True
    return False


def generate_proposals(
    pages: list[ParsedPage],
    registry: AliasRegistry,
    node_titles: dict[str, str],   # node_id -> canonical_name
    node_paths: dict[str, str],    # node_id -> canonical_path (empty for non-file-backed)
) -> list[LinkProposal]:
    """Generate missing-link proposals for all durable pages."""
    proposals: list[LinkProposal] = []
    now = datetime.now(timezone.utc).isoformat()

    # Build set of all normalized alias texts for fast scanning
    all_aliases = registry.all_aliases()
    # Group by normalized form for efficient lookup
    norm_to_aliases: dict[str, list[str]] = {}
    for reg in all_aliases:
        norm_to_aliases.setdefault(reg.normalized, []).append(reg.alias)

    # Sort normalized keys longest-first to prefer longer matches
    sorted_norms = sorted(norm_to_aliases.keys(), key=len, reverse=True)

    for page in pages:
        lines = page.raw_text.splitlines()

        for lineno, line_text in enumerate(lines, start=1):
            # Skip frontmatter and code block lines
            if lineno in page.frontmatter_lines or lineno in page.code_block_lines:
                continue

            skip_spans = _collect_skip_spans(line_text)

            for norm in sorted_norms:
                # Try each original alias form for this normalized key
                original_aliases = norm_to_aliases[norm]
                for orig_alias in original_aliases:
                    # Case-sensitive whole-word match in prose
                    pattern = re.compile(
                        r"(?<![^\s\[\(])" + re.escape(orig_alias) + r"(?![^\s\]\),.:;!?])",
                        re.IGNORECASE,
                    )
                    for m in pattern.finditer(line_text):
                        start, end = m.start(), m.end()
                        if _is_in_skip_span(start, end, skip_spans):
                            continue

                        # Resolve to canonical entity
                        node_id, is_ambiguous, _ = registry.resolve(orig_alias)
                        if is_ambiguous or not node_id:
                            continue

                        # Don't propose a link to the same page
                        if node_id == f"page:{page.path}":
                            continue

                        # Only high-confidence
                        regs = [r for r in all_aliases
                                if r.normalized == norm and r.node_id == node_id]
                        confidence = max((r.confidence for r in regs), default=0.0)
                        if confidence < MIN_CONFIDENCE:
                            continue

                        target_title = node_titles.get(node_id, node_id)
                        target_path = node_paths.get(node_id, "")

                        if target_path:
                            href = _relative_link(page.path, target_path)
                        else:
                            href = f"#{normalize(target_title).replace(' ', '-')}"

                        replacement = f"[{m.group(0)}]({href})"
                        rationale = (
                            f"Exact alias match '{orig_alias}' → {node_id} "
                            f"(source: {regs[0].source if regs else 'unknown'})"
                        )

                        proposals.append(LinkProposal(
                            proposal_id=_proposal_id(page.path, m.group(0), node_id, lineno),
                            source_path=page.path,
                            target_node_id=node_id,
                            target_title=target_title,
                            proposal_kind="missing_internal_link",
                            original_text=m.group(0),
                            replacement_markdown=replacement,
                            source_line=lineno,
                            char_start=start,
                            char_end=end,
                            base_content_hash=page.content_hash,
                            confidence=confidence,
                            rationale=rationale,
                            status="pending",
                            created_at=now,
                            reviewed_at="",
                        ))
                        # Add this match to skip_spans to avoid double-proposing overlapping text
                        skip_spans.append((start, end))

    # Deduplicate by proposal_id
    seen: set[str] = set()
    unique: list[LinkProposal] = []
    for p in proposals:
        if p.proposal_id not in seen:
            seen.add(p.proposal_id)
            unique.append(p)
    return unique
