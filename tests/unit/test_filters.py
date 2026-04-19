from pathlib import Path

from llm_wiki.filters import should_copy_file


def test_should_copy_markdown_but_not_git_metadata(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    git_file = tmp_path / ".git" / "config"
    readme.parent.mkdir(parents=True, exist_ok=True)
    git_file.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text("hello")
    git_file.write_text("secret")

    assert should_copy_file(readme) is True
    assert should_copy_file(git_file) is False
