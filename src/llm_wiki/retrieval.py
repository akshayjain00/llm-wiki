from __future__ import annotations

from typing import Any


def fuse_ranked_results(
    lexical: list[dict[str, Any]],
    semantic: list[dict[str, Any]],
    lexical_weight: float = 0.6,
    semantic_weight: float = 0.4,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in lexical:
        chunk_id = str(row["chunk_id"])
        merged.setdefault(
            chunk_id,
            {"chunk_id": chunk_id, "lexical_score": 1.0, "semantic_score": 1.0},
        )
        merged[chunk_id]["lexical_score"] = float(row["lexical_score"])
    for row in semantic:
        chunk_id = str(row["chunk_id"])
        merged.setdefault(
            chunk_id,
            {"chunk_id": chunk_id, "lexical_score": 1.0, "semantic_score": 1.0},
        )
        merged[chunk_id]["semantic_score"] = float(row["semantic_score"])

    for value in merged.values():
        value["fused_score"] = lexical_weight * float(
            value["lexical_score"]
        ) + semantic_weight * float(value["semantic_score"])
    return sorted(merged.values(), key=lambda row: float(row["fused_score"]))
