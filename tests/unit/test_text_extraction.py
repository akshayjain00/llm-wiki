from pathlib import Path

from llm_wiki.text_extraction import extract_text_chunks, split_text_into_chunks


def test_split_text_into_chunks_emits_stable_line_ranges() -> None:
    text = "# Title\n\nalpha\nbeta\ngamma\n\ndelta\n"

    chunks = split_text_into_chunks(
        text,
        project_slug="demo",
        source_kind="snapshot_file",
        source_id="README.md",
        max_lines=3,
        overlap_lines=0,
    )

    assert chunks[0].line_start == 1
    assert chunks[0].line_end == 3
    assert "Title" in chunks[0].chunk_text


def test_extract_text_chunks_reads_markdown_and_txt(tmp_path: Path) -> None:
    md = tmp_path / "README.md"
    md.write_text("# Demo\n\nOne\nTwo\n")
    txt = tmp_path / "notes.txt"
    txt.write_text("alpha\nbeta\n")

    chunks = extract_text_chunks([md, txt], project_slug="demo")

    assert len(chunks) >= 2
    assert {chunk.source_kind for chunk in chunks} == {"snapshot_file"}
    assert {chunk.project_slug for chunk in chunks} == {"demo"}


def test_extract_text_chunks_supports_pdf_text(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "manual.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    class FakePage:
        def extract_text(self) -> str:
            return "pdf alpha beta"

    class FakeReader:
        pages = [FakePage()]

    monkeypatch.setattr("llm_wiki.text_extraction.PdfReader", lambda path: FakeReader())

    chunks = extract_text_chunks([pdf], project_slug="demo")

    assert any("pdf alpha beta" in chunk.chunk_text for chunk in chunks)
