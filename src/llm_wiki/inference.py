from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from llm_wiki.models import Confidence, ProjectCardData, ProjectStatus
from llm_wiki.project_id import slugify_project_name


OWNER_PATTERN = re.compile(r"^Owner:\s*(?P<value>.+)$", re.IGNORECASE | re.MULTILINE)
STATUS_PATTERN = re.compile(r"^Status:\s*(?P<value>.+)$", re.IGNORECASE | re.MULTILINE)
NEXT_STEPS_PATTERN = re.compile(r"^Next steps:\s*(?P<value>.+)$", re.IGNORECASE | re.MULTILINE)
TITLE_PATTERN = re.compile(r"^#\s+(?P<value>.+)$", re.MULTILINE)
SECTION_HEADING_PATTERN = re.compile(
    r"^#{1,6}\s+(?P<value>next steps|action items)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
INGEST_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}t\d{2}[-:]\d{2}[-:]\d{2}z$", re.IGNORECASE
)

SUPPORT_DOC_NAMES = {"claude.md", "agents.md"}
OVERVIEW_KEYWORDS = {
    "overview",
    "onboarding",
    "architecture",
    "charter",
    "brief",
    "summary",
    "hld",
}
MAX_INFERRED_ALIASES = 3

STATUS_MAP: dict[str, ProjectStatus] = {
    "planned": "planned",
    "active": "active",
    "paused": "paused",
    "blocked": "blocked",
    "completed": "completed",
}


def _read_markdown_files(project_dir: Path) -> list[Path]:
    return sorted(path for path in project_dir.rglob("*.md") if path.is_file())


def _document_priority(project_dir: Path, file_path: Path) -> int:
    relative = file_path.relative_to(project_dir)
    path_parts = [part.lower() for part in relative.parts]
    file_name = relative.name.lower()
    stem = file_path.stem.lower()
    score = 0

    if file_name in SUPPORT_DOC_NAMES:
        score -= 250
    if file_name == "readme.md":
        score += 120
    if any(keyword in stem for keyword in OVERVIEW_KEYWORDS):
        score += 200
    if any(keyword in part for keyword in OVERVIEW_KEYWORDS for part in path_parts):
        score += 100
    if "docs" in path_parts:
        score += 25
    if len(relative.parts) == 1:
        score += 10
    return score


def _rank_markdown_files(project_dir: Path, files: list[Path]) -> list[Path]:
    return sorted(
        files,
        key=lambda path: (
            -_document_priority(project_dir, path),
            str(path.relative_to(project_dir)).lower(),
        ),
    )


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


def _extract_first_title(file_path: Path) -> str:
    match = TITLE_PATTERN.search(file_path.read_text())
    return match.group("value").strip() if match else ""


def _infer_project_name(project_dir: Path, files: list[Path]) -> str:
    for file_path in files:
        title = _extract_first_title(file_path)
        if title:
            return title
    return project_dir.name.replace("-", " ").replace("_", " ").title()


def _is_support_doc(file_path: Path) -> bool:
    return file_path.name.lower() in SUPPORT_DOC_NAMES


def _infer_summary(project_dir: Path, files: list[Path]) -> str:
    candidate_groups = [
        [file_path for file_path in files if not _is_support_doc(file_path)],
        files,
    ]
    for candidates in candidate_groups:
        for file_path in candidates:
            for paragraph in file_path.read_text().split("\n\n"):
                stripped = paragraph.strip()
                lowered = stripped.lower()
                if (
                    not stripped
                    or stripped.startswith("#")
                    or lowered.startswith(("owner:", "status:", "next steps:"))
                ):
                    continue
                return stripped
    return "Summary unavailable from current evidence."


def _humanize_folder_name(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def _looks_like_ingest_timestamp(name: str) -> bool:
    normalized = name.replace("_", "-")
    return bool(INGEST_TIMESTAMP_PATTERN.match(normalized))


def _infer_aliases(project_dir: Path, files: list[Path], canonical_name: str) -> list[str]:
    aliases: list[str] = []
    canonical_slug = slugify_project_name(canonical_name)

    folder_alias = _humanize_folder_name(project_dir.name)
    if (
        not _looks_like_ingest_timestamp(project_dir.name)
        and slugify_project_name(folder_alias) != canonical_slug
    ):
        aliases.append(folder_alias)

    readme = next(
        (file_path for file_path in files if file_path.name.lower() == "readme.md"),
        None,
    )
    if readme is not None:
        title = _extract_first_title(readme)
        if title and slugify_project_name(title) != canonical_slug and title not in aliases:
            aliases.append(title)

    for file_path in files:
        if _is_support_doc(file_path):
            continue
        if readme is not None and file_path == readme:
            continue
        title = _extract_first_title(file_path)
        if not title:
            continue
        if slugify_project_name(title) == canonical_slug:
            continue
        if title not in aliases:
            aliases.append(title)
        if len(aliases) >= MAX_INFERRED_ALIASES:
            break
    return aliases


def _extract_section_bullets(file_path: Path) -> list[str]:
    lines = file_path.read_text().splitlines()
    results: list[str] = []
    capture = False
    for line in lines:
        stripped = line.strip()
        if SECTION_HEADING_PATTERN.match(stripped):
            capture = True
            continue
        if capture and stripped.startswith("#"):
            break
        if capture and stripped.startswith(("- ", "* ")):
            results.append(stripped[2:].strip())
        if capture and re.match(r"^\d+\.\s+", stripped):
            results.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
    return results


def _is_valid_next_step(candidate: str) -> bool:
    stripped = candidate.strip()
    lowered = stripped.lower()
    if not stripped or len(stripped) < 8:
        return False
    if any(
        phrase in lowered
        for phrase in (
            "query and lint after every change",
            "run lint after every edit",
            "project-card",
            "workspace",
        )
    ):
        return False
    if stripped.startswith("#") or stripped.endswith(":"):
        return False
    return True


def _infer_next_steps(files: list[Path]) -> list[str]:
    next_steps: list[str] = []
    for file_path in files:
        if _is_support_doc(file_path):
            continue
        matches = [
            match.group("value").strip()
            for match in NEXT_STEPS_PATTERN.finditer(file_path.read_text())
        ]
        matches.extend(_extract_section_bullets(file_path))
        for match in matches:
            if not _is_valid_next_step(match):
                continue
            if match not in next_steps:
                next_steps.append(match)
    return next_steps


def _normalize_status(value: str) -> ProjectStatus:
    return STATUS_MAP.get(value.strip().lower(), "unknown")


def infer_project_card_fields(project_dir: Path) -> ProjectCardData:
    markdown_files = _read_markdown_files(project_dir)
    ranked_markdown_files = _rank_markdown_files(project_dir, markdown_files)
    project_name = _infer_project_name(project_dir, ranked_markdown_files)
    owner, owner_confidence = _resolve_confident_value(
        _extract_unique_values(ranked_markdown_files, OWNER_PATTERN)
    )

    status_values = [
        _normalize_status(value)
        for value in _extract_unique_values(ranked_markdown_files, STATUS_PATTERN)
    ]
    status_values = sorted({value for value in status_values if value != "unknown"})
    status, status_confidence = _resolve_confident_status(status_values)

    next_steps = _infer_next_steps(ranked_markdown_files)
    key_questions = []
    if owner == "unknown":
        key_questions.append("Owner needs human review.")
    if status == "unknown":
        key_questions.append("Status needs human review.")

    return ProjectCardData(
        project_name=project_name,
        slug=slugify_project_name(project_name),
        aliases=_infer_aliases(project_dir, ranked_markdown_files, project_name),
        owner=owner,
        owner_confidence=owner_confidence,
        status=status,
        status_confidence=status_confidence,
        summary=_infer_summary(project_dir, ranked_markdown_files),
        next_steps=next_steps,
        key_questions=key_questions,
    )
