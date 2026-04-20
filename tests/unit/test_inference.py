from pathlib import Path

from llm_wiki.inference import infer_project_card_fields


def test_infer_project_card_fields_uses_readme_and_docs() -> None:
    project_dir = Path("tests/fixtures/sample_project")

    inferred = infer_project_card_fields(project_dir)

    assert inferred.project_name == "Demo Project"
    assert inferred.owner == "Data Team"
    assert inferred.status == "active"
    assert "guided ingest" in inferred.next_steps[0]


def test_infer_project_card_fields_drops_conflicting_owner_and_status_to_unknown() -> None:
    project_dir = Path("tests/fixtures/conflicting_project")

    inferred = infer_project_card_fields(project_dir)

    assert inferred.owner == "unknown"
    assert inferred.owner_confidence == "low"
    assert inferred.status == "unknown"
    assert inferred.status_confidence == "low"


def test_infer_project_card_fields_prefers_overview_docs_for_identity_and_summary() -> None:
    project_dir = Path("tests/fixtures/overview_priority_project")

    inferred = infer_project_card_fields(project_dir)

    assert inferred.project_name == "Monthly Review Brain"
    assert inferred.summary == (
        "Monthly Review Brain compiles evidence and narrative for recurring business reviews."
    )
    assert "MBR Brain" in inferred.aliases


def test_infer_project_card_fields_filters_support_file_next_steps() -> None:
    project_dir = Path("tests/fixtures/noisy_next_steps_project")

    inferred = infer_project_card_fields(project_dir)

    assert inferred.next_steps == ["validate tray alert coverage with ops before rollout"]


def test_infer_project_card_fields_limits_inferred_aliases(tmp_path: Path) -> None:
    project_dir = tmp_path / "broad_project"
    docs = project_dir / "docs"
    docs.mkdir(parents=True)
    (project_dir / "README.md").write_text("# Canonical Brain\n\nPrimary project overview.")
    for index in range(1, 6):
        (docs / f"overview-{index}.md").write_text(f"# Alternate Identity {index}\n\nContext.")

    inferred = infer_project_card_fields(project_dir)

    assert inferred.project_name == "Alternate Identity 1"
    assert len(inferred.aliases) == 3
    assert inferred.aliases == ["Broad Project", "Canonical Brain", "Alternate Identity 2"]
