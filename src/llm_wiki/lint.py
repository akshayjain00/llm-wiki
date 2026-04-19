from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import yaml

from llm_wiki.wiki_writer import load_project_card

STATUS_PATTERN = re.compile(r"^Status:\s*(?P<value>.+)$", re.IGNORECASE | re.MULTILINE)
STALE_DAYS = 30
KNOWN_STATUSES = {"planned", "active", "paused", "blocked", "completed", "unknown"}


def _parse_timestamp(value: str) -> datetime | None:
    if value == "unknown":
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _normalize_status(value: str) -> str:
    lowered = value.strip().lower()
    return lowered if lowered in KNOWN_STATUSES else "unknown"


def run_lint(workspace_root: Path, now_timestamp: str | None = None) -> list[str]:
    findings: list[str] = []
    projects_root = workspace_root / "wiki" / "projects"
    now = _parse_timestamp(now_timestamp) if now_timestamp else None
    effective_now = now or datetime.now(tz=UTC)
    slug_to_paths: dict[str, list[Path]] = {}
    card_paths = sorted(projects_root.rglob("project-card.md"))
    for card_path in card_paths:
        card = load_project_card(card_path)
        slug_to_paths.setdefault(card.slug, []).append(card_path)
        if card.owner == "unknown":
            findings.append(f"{card.slug}: unknown owner")
        if card.status == "unknown":
            findings.append(f"{card.slug}: unknown status")
        if not card.next_steps:
            findings.append(f"{card.slug}: missing next steps")
        ingested_at = _parse_timestamp(card.last_ingested)
        if ingested_at is not None and (effective_now - ingested_at).days > STALE_DAYS:
            findings.append(f"{card.slug}: stale project card")
        project_dir = card_path.parent
        discovered_statuses: set[str] = set()
        for page_path in sorted(project_dir.glob("*.md")):
            if page_path.name == "project-card.md":
                continue
            matches = STATUS_PATTERN.findall(page_path.read_text())
            page_statuses = {_normalize_status(match) for match in matches}
            page_statuses.discard("unknown")
            discovered_statuses.update(page_statuses)
            if page_statuses and card.status != "unknown" and card.status not in page_statuses:
                findings.append(
                    f"{card.slug}: contradictory status in {page_path.name} ({', '.join(sorted(page_statuses))})"
                )
        if len(discovered_statuses) > 1:
            findings.append(
                f"{card.slug}: contradictory status across project pages ({', '.join(sorted(discovered_statuses))})"
            )
        index_path = workspace_root / "wiki" / "indexes" / "index.md"
        if index_path.exists():
            expected_ref = str(card_path.relative_to(workspace_root))
            if expected_ref not in index_path.read_text():
                findings.append(f"{card.slug}: orphan project not present in index.md")

    for slug, paths in slug_to_paths.items():
        if len(paths) > 1:
            findings.append(f"{slug}: duplicate slug across {len(paths)} project cards")

    refs_root = workspace_root / "refs"
    for manifest_path in sorted(refs_root.glob("*.yaml")):
        manifest = yaml.safe_load(manifest_path.read_text()) or {}
        project_slug = manifest.get("project_slug", manifest_path.stem)
        for live_path in manifest.get("authoritative_live_paths", []):
            if not Path(live_path).exists():
                findings.append(f"{project_slug}: missing live path {live_path}")
        for note in manifest.get("duplicate_source_notes", []):
            findings.append(f"{project_slug}: possible duplicate raw artifact ({note})")
    return findings


def render_needs_review_markdown(findings: list[str]) -> str:
    lines = ["# Needs Review", ""]
    if not findings:
        lines.append("No findings.")
    else:
        lines.extend(f"- {finding}" for finding in findings)
    lines.append("")
    return "\n".join(lines)


def append_lint_log(log_path: Path, findings: list[str], timestamp: str) -> None:
    existing = log_path.read_text() if log_path.exists() else "# Lint Log\n\n"
    lines = [f"## [{timestamp}] lint", ""]
    if not findings:
        lines.append("- no findings")
    else:
        lines.extend(f"- {finding}" for finding in findings)
    lines.append("")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(existing + "\n".join(lines))


def write_lint_outputs(
    workspace_root: Path, findings: list[str], timestamp: str | None = None
) -> None:
    effective_timestamp = timestamp or datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    indexes_root = workspace_root / "wiki" / "indexes"
    indexes_root.mkdir(parents=True, exist_ok=True)
    (indexes_root / "needs-review.md").write_text(render_needs_review_markdown(findings))
    append_lint_log(workspace_root / "logs" / "lint-log.md", findings, effective_timestamp)
