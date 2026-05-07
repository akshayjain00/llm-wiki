from llm_wiki.retrieval import fuse_ranked_results


def test_fuse_ranked_results_prefers_joint_matches() -> None:
    lexical = [{"chunk_id": "a", "lexical_score": 0.2}, {"chunk_id": "b", "lexical_score": 0.5}]
    semantic = [{"chunk_id": "b", "semantic_score": 0.1}, {"chunk_id": "c", "semantic_score": 0.2}]

    fused = fuse_ranked_results(lexical, semantic)

    assert fused[0]["chunk_id"] == "b"
