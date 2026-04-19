# LLM Wiki

CLI-first implementation of the Team Memory Wiki spec for guided ingest,
wiki-backed project orientation queries, index rebuilding, and lint checks.

## Requirements

- Python `>=3.12`
- `uv`

## Commands

Initialize a workspace:

```bash
uv run llm-wiki init --workspace /tmp/team-memory-wiki-smoke
```

Ingest one project or folder:

```bash
uv run llm-wiki ingest \
  --workspace /tmp/team-memory-wiki-smoke \
  --target tests/fixtures/sample_project
```

Query project orientation from maintained wiki state:

```bash
uv run llm-wiki query \
  --workspace /tmp/team-memory-wiki-smoke \
  --project sample-project
```

Rebuild derived indexes:

```bash
uv run llm-wiki rebuild-indexes --workspace /tmp/team-memory-wiki-smoke
```

Run lint and refresh review surfaces:

```bash
uv run llm-wiki lint --workspace /tmp/team-memory-wiki-smoke
```

## Verified Outputs

The verified smoke flow above produced:

- `raw/fixtures/sample-project/<timestamp>/README.md`
- `raw/fixtures/sample-project/<timestamp>/docs/plan.md`
- `refs/sample-project.yaml`
- `wiki/projects/sample-project/project-card.md`
- `wiki/indexes/index.md`
- `wiki/indexes/active-projects.md`
- `wiki/indexes/by-owner.md`
- `wiki/indexes/by-domain.md`
- `logs/ingest-log.md`
- `wiki/indexes/needs-review.md` after running `lint`
- `logs/lint-log.md`

The verified query output included:

```text
Project: Demo Project
Slug: sample-project
Owner: Data Team
Status: active
Summary: Summary unavailable from current evidence.
Evidence snapshot: raw/fixtures/sample-project/<timestamp> (present)
Reference manifest: refs/sample-project.yaml (present)
Next steps:
- ship guided ingest
```

## Verification

The following checks were run successfully on this implementation:

- `uv run pytest -v`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`
- `uv build`
- `uv run llm-wiki --help`
- `uv run llm-wiki init --workspace /tmp/team-memory-wiki-smoke`
- `uv run llm-wiki ingest --workspace /tmp/team-memory-wiki-smoke --target tests/fixtures/sample_project`
- `uv run llm-wiki query --workspace /tmp/team-memory-wiki-smoke --project sample-project`
- `uv run llm-wiki rebuild-indexes --workspace /tmp/team-memory-wiki-smoke`
- `uv run llm-wiki lint --workspace /tmp/team-memory-wiki-smoke`
- manual inspection of generated project card, indexes, ingest log, lint log, and ref manifest

## Current V1 Limits

- manual project-card overrides are preserved only against later low-confidence inference; there is no explicit reset command yet
- duplicate detection is content-based within one guided-ingest slice
- query verifies evidence locations but does not re-summarize snapshot contents on demand

## Applicability Notes

These verification items were not applicable to V1:

- Docker deployment: not implemented
- Database migrations: not implemented
- HTTP API verification: not implemented
- Playwright/browser verification: not applicable because V1 has no frontend or browser-accessible review UI
