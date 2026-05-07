from __future__ import annotations

from pathlib import Path


WORKSPACE_DIRS = (
    "raw",
    "refs",
    "wiki/projects",
    "wiki/reports",
    "wiki/indexes",
    "logs",
    "schema",
    "state",
    "cache/extraction",
)

SCHEMA_SEED_FILES = {
    "wiki-maintainer.md": "# Wiki Maintainer\n\nFollow the project-card template and keep answers wiki-first.\n",
    "ingest-rules.yaml": "mode: guided\nsnapshot_policy: immutable\nquery_boundary: wiki-first\n",
    "project-card-template.md": "# Project Card Template\n\n- Summary\n- Owner\n- Status\n- Next steps\n",
    "lint-rules.md": "# Lint Rules\n\nFlag unknown owner, unknown status, and conflicting evidence.\n",
    "workspace-config.yaml": (
        "workspace_version: 2\n"
        "query_model: gpt-5-mini\n"
        "embedding_model: text-embedding-3-small\n"
        "max_query_cost_usd: 0.25\n"
        "writeback_enabled: true\n"
        "migration_safety_mode: side_by_side\n"
    ),
    "retrieval-config.yaml": (
        "fts_top_k: 20\n"
        "semantic_top_k: 20\n"
        "fusion_weight_lexical: 0.6\n"
        "fusion_weight_semantic: 0.4\n"
        "chunk_max_lines: 20\n"
        "chunk_overlap_lines: 3\n"
    ),
    "prompt-contracts.md": "# Prompt Contracts\n\nPhase 2 prompt contracts live here.\n",
}

LOG_SEED_FILES = {
    "query-log.md": "# Query Log\n\n",
}


def initialize_workspace(root: Path) -> None:
    for relative in WORKSPACE_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)

    schema_root = root / "schema"
    for filename, contents in SCHEMA_SEED_FILES.items():
        schema_file = schema_root / filename
        if not schema_file.exists():
            schema_file.write_text(contents)

    logs_root = root / "logs"
    for filename, contents in LOG_SEED_FILES.items():
        log_file = logs_root / filename
        if not log_file.exists():
            log_file.write_text(contents)
