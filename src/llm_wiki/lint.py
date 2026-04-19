from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llm_wiki.wiki_writer import load_project_card


def run_lint(wiki_root: Path) -> list[str]:
    findings: list[str] = []
    for card_path in sorted(wiki_root.rglob("project-card.md")):
        card = load_project_card(card_path)
        if card.owner == "unknown":
            findings.append(f"{card.slug}: unknown owner")
        if card.status == "unknown":
            findings.append(f"{card.slug}: unknown status")
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
