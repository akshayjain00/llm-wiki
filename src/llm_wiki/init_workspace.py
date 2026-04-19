from __future__ import annotations

from pathlib import Path


WORKSPACE_DIRS = (
    "raw",
    "refs",
    "wiki/projects",
    "wiki/indexes",
    "logs",
    "schema",
)

SCHEMA_SEED_FILES = {
    "wiki-maintainer.md": "# Wiki Maintainer\n\nFollow the project-card template and keep answers wiki-first.\n",
    "ingest-rules.yaml": "mode: guided\nsnapshot_policy: immutable\nquery_boundary: wiki-first\n",
    "project-card-template.md": "# Project Card Template\n\n- Summary\n- Owner\n- Status\n- Next steps\n",
    "lint-rules.md": "# Lint Rules\n\nFlag unknown owner, unknown status, and conflicting evidence.\n",
}


def initialize_workspace(root: Path) -> None:
    for relative in WORKSPACE_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)

    schema_root = root / "schema"
    for filename, contents in SCHEMA_SEED_FILES.items():
        schema_file = schema_root / filename
        if not schema_file.exists():
            schema_file.write_text(contents)
