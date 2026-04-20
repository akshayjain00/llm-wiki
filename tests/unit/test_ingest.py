from pathlib import Path

import yaml

from llm_wiki.ingest import run_ingest
from llm_wiki.init_workspace import initialize_workspace
from llm_wiki.wiki_writer import load_project_card, write_project_card


def test_run_ingest_writes_absolute_paths_and_duplicate_notes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    initialize_workspace(workspace)

    target = tmp_path / "demo_project"
    docs = target / "docs"
    docs.mkdir(parents=True)
    duplicate_text = "# Demo Project\n\nOwner: Data Team\nStatus: Active\n"
    (target / "README.md").write_text(duplicate_text)
    (docs / "copied-readme.md").write_text(duplicate_text)

    run_ingest(workspace, target, ingest_timestamp="2026-04-20T10-00-00Z")

    card = load_project_card(workspace / "wiki" / "projects" / "demo-project" / "project-card.md")
    manifest = yaml.safe_load((workspace / "refs" / "demo-project.yaml").read_text())

    assert card.source_roots == [str(target.parent.resolve())]
    assert card.live_refs == [str(target.resolve())]
    assert manifest["authoritative_live_paths"] == [str(target.resolve())]
    assert manifest["origin_roots"] == [str(target.parent.resolve())]
    assert manifest["duplicate_source_notes"]


def test_run_ingest_preserves_existing_manual_overrides_on_weak_inference(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    initialize_workspace(workspace)

    target = tmp_path / "demo_project"
    docs = target / "docs"
    docs.mkdir(parents=True)
    (target / "README.md").write_text("# Demo Project\n\nOwner: Data Team\nStatus: Active\n")
    (docs / "plan.md").write_text("Next steps: ship guided ingest")

    run_ingest(workspace, target, ingest_timestamp="2026-04-20T10-00-00Z")

    card_path = workspace / "wiki" / "projects" / "demo-project" / "project-card.md"
    original = card_path.read_text()
    updated = original.replace('owner: "Data Team"', 'owner: "Platform Team"')
    updated = updated.replace("\nData Team\n", "\nPlatform Team\n")
    updated = updated.replace(
        "Summary unavailable from current evidence.",
        "Human-written summary that should stay in place.",
    )
    card_path.write_text(updated)
    (docs / "owner-conflict.md").write_text("Owner: Another Team\n")

    run_ingest(workspace, target, ingest_timestamp="2026-04-21T10-00-00Z")

    card = load_project_card(card_path)

    assert card.owner == "Platform Team"
    assert card.summary == "Human-written summary that should stay in place."
    assert card.live_refs == [str(target.resolve())]
    assert card.last_ingested == "2026-04-21T10-00-00Z"


def test_run_ingest_preserves_reviewed_canonical_identity(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    initialize_workspace(workspace)

    target = tmp_path / "reviewed_project"
    docs = target / "docs"
    docs.mkdir(parents=True)
    (target / "README.md").write_text("# Initial Title\n\nOwner: Data Team\nStatus: Active\n")
    (docs / "plan.md").write_text("Next steps: ship guided ingest")

    run_ingest(workspace, target, ingest_timestamp="2026-04-20T10-00-00Z")

    card_path = workspace / "wiki" / "projects" / "reviewed-project" / "project-card.md"
    reviewed_card = load_project_card(card_path)
    reviewed_card = reviewed_card.__class__(
        project_name="Curated Identity",
        slug=reviewed_card.slug,
        aliases=["Legacy Identity"],
        domain="analytics",
        source_roots=reviewed_card.source_roots,
        live_refs=reviewed_card.live_refs,
        owner=reviewed_card.owner,
        owner_confidence=reviewed_card.owner_confidence,
        status=reviewed_card.status,
        status_confidence=reviewed_card.status_confidence,
        last_ingested=reviewed_card.last_ingested,
        last_reviewed="2026-04-20",
        canonical_snapshot=reviewed_card.canonical_snapshot,
        summary="Human-reviewed summary.",
        current_scope=reviewed_card.current_scope,
        key_artifacts=reviewed_card.key_artifacts,
        key_questions=reviewed_card.key_questions,
        risks_or_blockers=reviewed_card.risks_or_blockers,
        next_steps=reviewed_card.next_steps,
        related_pages=reviewed_card.related_pages,
    )
    write_project_card(reviewed_card, card_path)
    (docs / "onboarding.md").write_text("# Inferred New Identity\n\nA better inferred summary.\n")

    run_ingest(workspace, target, ingest_timestamp="2026-04-21T10-00-00Z")

    merged_card = load_project_card(card_path)

    assert merged_card.project_name == "Curated Identity"
    assert merged_card.aliases == ["Legacy Identity"]
    assert merged_card.summary == "Human-reviewed summary."
