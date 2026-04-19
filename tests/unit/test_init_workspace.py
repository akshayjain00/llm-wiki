from llm_wiki.cli import build_parser


def test_cli_exposes_expected_commands() -> None:
    parser = build_parser()
    subparsers = {action.dest for action in parser._actions if getattr(action, "choices", None)}
    assert "command" in subparsers
