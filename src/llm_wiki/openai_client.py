from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OpenAIConfig:
    embedding_model: str
    query_model: str
    api_key_env: str = "OPENAI_API_KEY"
    max_query_cost_usd: float = 0.25


@dataclass(frozen=True)
class EmbeddingResult:
    model: str
    vector: list[float]


def parse_embedding_response(payload: dict[str, Any]) -> EmbeddingResult:
    data = payload["data"]
    first = data[0]
    return EmbeddingResult(
        model=str(payload["model"]),
        vector=[float(value) for value in first["embedding"]],
    )
