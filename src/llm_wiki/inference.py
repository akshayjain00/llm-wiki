from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from llm_wiki.models import Confidence, ProjectCardData, ProjectStatus
from llm_wiki.project_id import slugify_project_name


OWNER_PATTERN = re.compile(r"^Owner:\s*(?P<value>.+)$", re.IGNORECASE | re.MULTILINE)
STATUS_PATTERN = re.compile(r"^Status:\s*(?P<value>.+)$", re.IGNORECASE | re.MULTILINE)
NEXT_STEPS_PATTERN = re.compile(r"Next steps:\s*(?P<value>.+)", re.IGNORECASE)
TITLE_PATTERN = re.compile(r"^#\s+(?P<value>.+)$", re.MULTILINE)

STATUS_MAP: dict[str, ProjectStatus] = {
    "planned": "planned",
    "active": "active",
    "paused": "paused",
    "blocked": "blocked",
    "completed": "completed",
}


def _read_markdown_files(project_dir: Path) -> list[Path]:
    return sorted(path for path in project_dir.rglob("*.md") if path.is_file())


def _extract_unique_values(files: list[Path], pattern: re.Pattern[str]) -> list[str]:
    values: list[str] = []
    for file_path in files:
        matches = [
            match.group("value").strip() for match in pattern.finditer(file_path.read_text())
        ]
        values.extend(match for match in matches if match)
    return sorted({value for value in values})


def _resolve_confident_value(values: Sequence[str]) -> tuple[str, Confidence]:
    if not values:
        return "unknown", "low"
    if len(values) > 1:
        return "unknown", "low"
    return values[0], "medium"


def _resolve_confident_status(values: Sequence[ProjectStatus]) -> tuple[ProjectStatus, Confidence]:
    if not values:
        return "unknown", "low"
    if len(values) > 1:
        return "unknown", "low"
    return values[0], "medium"


def _infer_project_name(project_dir: Path, files: list[Path]) -> str:
    for file_path in files:
        match = TITLE_PATTERN.search(file_path.read_text())
        if match:
            return match.group("value").strip()
    return project_dir.name.replace("-", " ").replace("_", " ").title()


def _infer_summary(project_dir: Path) -> str:
    readme = project_dir / "README.md"
    if not readme.exists():
        return "Summary unavailable from current evidence."

    for paragraph in readme.read_text().split("\n\n"):
        stripped = paragraph.strip()
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.lower().startswith(("owner:", "status:"))
        ):
            continue
        return stripped
    return "Summary unavailable from current evidence."


def _normalize_status(value: str) -> ProjectStatus:
    return STATUS_MAP.get(value.strip().lower(), "unknown")


def infer_project_card_fields(project_dir: Path) -> ProjectCardData:
    markdown_files = _read_markdown_files(project_dir)
    project_name = _infer_project_name(project_dir, markdown_files)
    owner, owner_confidence = _resolve_confident_value(
        _extract_unique_values(markdown_files, OWNER_PATTERN)
    )

    status_values = [
        _normalize_status(value) for value in _extract_unique_values(markdown_files, STATUS_PATTERN)
    ]
    status_values = sorted({value for value in status_values if value != "unknown"})
    status, status_confidence = _resolve_confident_status(status_values)

    next_steps = _extract_unique_values(markdown_files, NEXT_STEPS_PATTERN)
    key_questions = []
    if owner == "unknown":
        key_questions.append("Owner needs human review.")
    if status == "unknown":
        key_questions.append("Status needs human review.")

    return ProjectCardData(
        project_name=project_name,
        slug=slugify_project_name(project_name),
        owner=owner,
        owner_confidence=owner_confidence,
        status=status,
        status_confidence=status_confidence,
        summary=_infer_summary(project_dir),
        next_steps=next_steps,
        key_questions=key_questions,
    )
