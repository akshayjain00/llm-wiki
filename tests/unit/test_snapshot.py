from pathlib import Path

from llm_wiki.snapshot import copy_snapshot


def test_copy_snapshot_writes_files_into_timestamped_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    docs = source / "docs"
    docs.mkdir(parents=True)
    readme = source / "README.md"
    plan = docs / "plan.md"
    readme.write_text("hello")
    plan.write_text("ship it")

    destination = tmp_path / "workspace" / "raw" / "desktop-ai-v2" / "demo-project"
    snapshot_path = copy_snapshot([readme, plan], destination, "2026-04-09T10-00-00Z")

    assert snapshot_path.name == "2026-04-09T10-00-00Z"
    assert (snapshot_path / "README.md").read_text() == "hello"
    assert (snapshot_path / "docs" / "plan.md").read_text() == "ship it"
