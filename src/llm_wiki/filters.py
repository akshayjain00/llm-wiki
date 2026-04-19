from __future__ import annotations

from pathlib import Path

from llm_wiki.config import SourceRules


def should_copy_file(path: Path, rules: SourceRules | None = None) -> bool:
    effective_rules = rules or SourceRules()
    normalized_parts = {part.lower() for part in path.parts}

    if any(blocked.lower() in normalized_parts for blocked in effective_rules.blocked_parts):
        return False

    lowered_name = path.name.lower()
    if any(lowered_name.startswith(prefix.lower()) for prefix in effective_rules.blocked_prefixes):
        return False

    suffix = path.suffix.lower()
    if suffix in effective_rules.blocked_suffixes:
        return False

    return path.name in effective_rules.allowed_names or suffix in effective_rules.allowed_suffixes
