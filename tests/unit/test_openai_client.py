from llm_wiki.openai_client import OpenAIConfig, parse_embedding_response


def test_parse_embedding_response_extracts_vector_and_model() -> None:
    payload = {"data": [{"embedding": [0.1, 0.2]}], "model": "text-embedding-3-small"}

    result = parse_embedding_response(payload)

    assert result.model == "text-embedding-3-small"
    assert result.vector == [0.1, 0.2]


def test_openai_config_uses_budgeted_defaults() -> None:
    config = OpenAIConfig(
        embedding_model="text-embedding-3-small",
        query_model="gpt-5-mini",
        api_key_env="OPENAI_API_KEY",
        max_query_cost_usd=0.25,
    )

    assert config.embedding_model == "text-embedding-3-small"
    assert config.query_model == "gpt-5-mini"
    assert config.max_query_cost_usd == 0.25
