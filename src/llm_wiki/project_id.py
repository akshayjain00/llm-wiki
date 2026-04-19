from __future__ import annotations

import re


TRAILING_DUPLICATE_MARKERS = re.compile(
    r"(?:[-_\s]+(?:copy|backup|tmp|temp))(?:[-_\s]*\d+)?$",
    flags=re.IGNORECASE,
)


def slugify_project_name(name: str) -> str:
    normalized = TRAILING_DUPLICATE_MARKERS.sub("", name.strip())
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return re.sub(r"-{2,}", "-", slug)
