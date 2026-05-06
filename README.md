# LLM Wiki

CLI-first implementation of the Team Memory Wiki spec for guided ingest,
wiki-backed project orientation queries, index rebuilding, and lint checks.

## Read This First

- [Getting Started](docs/guides/getting-started.md)
- [How It Works](docs/guides/how-it-works.md)
- [Cookbook](docs/guides/cookbook.md)
- [Phase 2 Quickstart](docs/guides/phase2-quickstart.md)
- [Phase 2 Migration](docs/guides/phase2-migration.md)
- [V1 Release Notes](docs/releases/v0.1.0.md)

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

`query` accepts the canonical slug or a stored alias.

Rebuild derived indexes:

```bash
uv run llm-wiki rebuild-indexes --workspace /tmp/team-memory-wiki-smoke
```

Run lint and refresh review surfaces:

```bash
uv run llm-wiki lint --workspace /tmp/team-memory-wiki-smoke
```

## Phase 2 Commands

Phase 2 adds cross-project retrieval, health checks, side-by-side migration, and manual write-back approval:

```bash
uv run llm-wiki migrate-workspace --workspace /tmp/team-memory-wiki-smoke --target-version 2
uv run llm-wiki rebuild-retrieval --workspace /tmp/team-memory-wiki-smoke-v2
uv run llm-wiki health --workspace /tmp/team-memory-wiki-smoke-v2
uv run llm-wiki query --workspace /tmp/team-memory-wiki-smoke-v2 --project hcv --project notion-sync --question "Compare how mature these projects are."
uv run llm-wiki approve-writeback --workspace /tmp/team-memory-wiki-smoke-v2 --proposal-id <id>
```

Cross-project durable write-backs are written under `wiki/reports/`. Single-project write-backs use `wiki/projects/<slug>/overview.md` or `wiki/projects/<slug>/decisions.md`.

## Effective Usage Pattern

Use the service in this order:

1. `init` once per workspace
2. `ingest` one project slice at a time
3. `query` the resulting slug immediately
4. `lint` to see whether the maintained state is trustworthy enough
5. `rebuild-indexes` only when you want to refresh shared navigation pages after card edits

This is a local CLI and markdown workspace, not an API service or background daemon.

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
- `state/index.db` after running `rebuild-retrieval` or `migrate-workspace`
- `logs/query-log.md` after Phase 2 initialization
- `wiki/reports/<date>-<topic>.md` after approving a cross-project write-back

The verified query output included:

```text
Project: Demo Project
Slug: sample-project
Aliases: None recorded.
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
- overview ranking and alias extraction are heuristic, not model-based; broad multi-domain repos can still require manual identity cleanup

## Applicability Notes

These verification items were not applicable to V1:

- Docker deployment: not implemented
- Database migrations: not implemented
- HTTP API verification: not implemented
- Playwright/browser verification: not applicable because V1 has no frontend or browser-accessible review UI
