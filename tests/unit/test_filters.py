from pathlib import Path

from llm_wiki.filters import should_copy_file


def test_should_copy_markdown_but_not_git_metadata(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    git_file = tmp_path / ".git" / "config"
    env_file = tmp_path / ".env"
    readme.parent.mkdir(parents=True, exist_ok=True)
    git_file.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text("hello")
    git_file.write_text("secret")
    env_file.write_text("TOP_SECRET=yes")

    assert should_copy_file(readme) is True
    assert should_copy_file(git_file) is False
    assert should_copy_file(env_file) is False
