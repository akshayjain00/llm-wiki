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
