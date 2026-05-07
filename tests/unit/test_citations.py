from llm_wiki.citations import format_snapshot_citation, format_wiki_citation


def test_format_snapshot_citation_is_stable() -> None:
    citation = format_snapshot_citation(
        project_slug="demo",
        snapshot_id="2026-05-05T00-00-00Z",
        relative_path="README.md",
        chunk_id="demo:README.md:0",
        line_start=1,
        line_end=4,
    )

    assert citation == "[snapshot:demo/2026-05-05T00-00-00Z/README.md#L1-L4 chunk=demo:README.md:0]"


def test_format_wiki_citation_is_stable() -> None:
    citation = format_wiki_citation(path="wiki/projects/demo/project-card.md", heading="Summary")

    assert citation == "[wiki:wiki/projects/demo/project-card.md#Summary]"
