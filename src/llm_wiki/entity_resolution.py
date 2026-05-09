"""LLM Wiki Phase 3 — entity normalization and alias resolution.

All resolution is deterministic: no AI calls.  Ambiguous matches are
flagged and excluded from high-confidence proposals.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

_PUNCT_RE = re.compile(r"[^\w\s-]")
_MULTI_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Normalize an entity name to a stable matching key.

    Steps:
    1. Unicode NFKD → ASCII
    2. Lowercase
    3. Strip non-word chars except hyphens and spaces
    4. Collapse whitespace
    5. Strip leading/trailing whitespace
    """
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_bytes = nfkd.encode("ascii", errors="ignore")
    s = ascii_bytes.decode("ascii").lower()
    s = _PUNCT_RE.sub(" ", s)
    s = _MULTI_WS.sub(" ", s).strip()
    return s


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    s = normalize(text)
    return re.sub(r"[\s]+", "-", s).strip("-")


# ---------------------------------------------------------------------------
# Alias registry
# ---------------------------------------------------------------------------

@dataclass
class ResolvedEntity:
    node_id: str            # canonical graph node ID
    canonical_name: str
    project_slug: str


@dataclass
class AliasRegistration:
    alias: str              # original text
    normalized: str         # normalize(alias)
    node_id: str
    source: str             # "slug"|"title"|"heading"|"metadata"|"link"
    confidence: float


@dataclass
class AliasRegistry:
    """In-memory map from normalized alias → candidate entities.

    If multiple entities share a normalized alias → ambiguous, do not propose.
    """
    _map: dict[str, list[AliasRegistration]] = field(default_factory=dict)

    def register(self, alias: str, node_id: str, source: str, confidence: float = 1.0) -> None:
        norm = normalize(alias)
        if not norm:
            return
        reg = AliasRegistration(
            alias=alias,
            normalized=norm,
            node_id=node_id,
            source=source,
            confidence=confidence,
        )
        self._map.setdefault(norm, []).append(reg)

    def resolve(self, text: str) -> tuple[str | None, bool, str]:
        """Resolve text → (node_id | None, is_ambiguous, first_candidate_or_"").

        Returns:
            node_id: canonical node ID if exactly one match, else None
            is_ambiguous: True if multiple distinct entities match
            candidate: first candidate node_id (useful for logging)
        """
        norm = normalize(text)
        candidates = self._map.get(norm, [])
        if not candidates:
            return None, False, ""
        # Deduplicate by node_id
        unique_ids = list(dict.fromkeys(r.node_id for r in candidates))
        if len(unique_ids) == 1:
            return unique_ids[0], False, unique_ids[0]
        return None, True, unique_ids[0]

    def all_aliases(self) -> list[AliasRegistration]:
        """Return deduplicated alias registrations (one per alias+node_id combo)."""
        seen: set[tuple[str, str]] = set()
        result: list[AliasRegistration] = []
        for regs in self._map.values():
            for r in regs:
                key = (r.normalized, r.node_id)
                if key not in seen:
                    seen.add(key)
                    result.append(r)
        return result


# ---------------------------------------------------------------------------
# Alias ID generation
# ---------------------------------------------------------------------------

def alias_id(node_id: str, alias_text: str) -> str:
    """Deterministic alias primary key."""
    raw = f"{node_id}\x00{normalize(alias_text)}"
    return "alias_" + hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Helpers for building the registry from parsed pages
# ---------------------------------------------------------------------------

def build_registry_from_pages(
    pages: list[object],  # list[ParsedPage] — typed as object to avoid circular import
    project_slugs: list[tuple[str, str]],  # [(slug, name), ...]
) -> AliasRegistry:
    """Build an AliasRegistry from project metadata and page content.

    Called by graph_builder after parsing all pages.
    """
    from llm_wiki.markdown_graph import ParsedPage  # local import to break circular dep

    registry = AliasRegistry()

    # Register project slugs and names first (highest confidence)
    for slug, name in project_slugs:
        node_id = f"project:{slug}"
        registry.register(slug, node_id, "slug", 1.0)
        registry.register(name, node_id, "title", 1.0)
        # Common shortening: first word / acronym
        words = name.split()
        if len(words) > 1:
            acronym = "".join(w[0] for w in words if w)
            if len(acronym) >= 2:
                registry.register(acronym, node_id, "metadata", 0.85)

    # Register page titles and headings
    for page in pages:
        if not isinstance(page, ParsedPage):
            continue
        # Derive node_id from path
        node_id = f"page:{page.path}"
        if page.title:
            registry.register(page.title, node_id, "title", 1.0)
        for h in page.headings:
            if h.level <= 3 and len(h.text) > 2:
                registry.register(h.text, node_id, "heading", 0.9)
        # Frontmatter aliases list
        aliases_raw = page.frontmatter.get("aliases") or page.frontmatter.get("also_known_as") or []
        if isinstance(aliases_raw, str):
            aliases_raw = [aliases_raw]
        for a in aliases_raw:
            registry.register(str(a), node_id, "metadata", 0.95)

    return registry
