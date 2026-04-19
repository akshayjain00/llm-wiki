from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_ALLOWED_NAMES = frozenset({"README", "README.md", "CLAUDE.md", "AGENTS.md"})
DEFAULT_ALLOWED_SUFFIXES = frozenset(
    {".md", ".pdf", ".txt", ".yaml", ".yml", ".toml", ".json", ".csv", ".png", ".jpg", ".jpeg"}
)
DEFAULT_BLOCKED_PARTS = frozenset(
    {".git", ".venv", "node_modules", ".pytest_cache", "__pycache__", ".ruff_cache", ".mypy_cache"}
)
DEFAULT_BLOCKED_SUFFIXES = frozenset({".zip", ".jar", ".pt", ".p8", ".pyc"})
DEFAULT_BLOCKED_PREFIXES = (".env",)


@dataclass(frozen=True)
class SourceRules:
    allowed_names: frozenset[str] = DEFAULT_ALLOWED_NAMES
    allowed_suffixes: frozenset[str] = DEFAULT_ALLOWED_SUFFIXES
    blocked_parts: frozenset[str] = DEFAULT_BLOCKED_PARTS
    blocked_suffixes: frozenset[str] = DEFAULT_BLOCKED_SUFFIXES
    blocked_prefixes: tuple[str, ...] = DEFAULT_BLOCKED_PREFIXES


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    raw: Path = field(init=False)
    refs: Path = field(init=False)
    wiki: Path = field(init=False)
    logs: Path = field(init=False)
    schema: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw", self.root / "raw")
        object.__setattr__(self, "refs", self.root / "refs")
        object.__setattr__(self, "wiki", self.root / "wiki")
        object.__setattr__(self, "logs", self.root / "logs")
        object.__setattr__(self, "schema", self.root / "schema")
