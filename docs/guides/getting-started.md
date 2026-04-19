# Getting Started

## What This Is

`llm-wiki` is a local CLI that builds and maintains a markdown workspace for project orientation. It does not run as a background service, API, or UI. You point it at a project folder, it snapshots the allowed artifacts, updates a project card, rebuilds shared indexes, and gives you a wiki-first way to query the result.

The current V1 scope is:

- initialize a workspace
- ingest one project or folder at a time
- query one project by slug
- rebuild shared indexes
- lint the maintained state for review issues

## Install And Verify

From the repo root:

```bash
uv run llm-wiki --help
```

You should see the five commands: `init`, `ingest`, `query`, `rebuild-indexes`, and `lint`.

## First Run

Create a workspace:

```bash
uv run llm-wiki init --workspace /tmp/team-memory-wiki-smoke
```

Ingest one project:

```bash
uv run llm-wiki ingest \
  --workspace /tmp/team-memory-wiki-smoke \
  --target tests/fixtures/sample_project
```

Query the result:

```bash
uv run llm-wiki query \
  --workspace /tmp/team-memory-wiki-smoke \
  --project sample-project
```

Run lint:

```bash
uv run llm-wiki lint --workspace /tmp/team-memory-wiki-smoke
```

Refresh navigation pages if you edited cards manually:

```bash
uv run llm-wiki rebuild-indexes --workspace /tmp/team-memory-wiki-smoke
```

## Workspace Layout

After the first ingest, the workspace should contain:

- `raw/`
  - immutable timestamped snapshots of copied artifacts
- `refs/`
  - one YAML manifest per project with live refs and duplicate notes
- `wiki/projects/<slug>/project-card.md`
  - the maintained canonical summary for one project
- `wiki/indexes/`
  - derived navigation pages such as `index.md`, `active-projects.md`, `by-owner.md`, `by-domain.md`
- `wiki/indexes/needs-review.md`
  - lint-owned review surface
- `logs/`
  - append-only ingest and lint logs
- `schema/`
  - seed rules and templates for the workspace

## How To Think About A Good Target

Choose a target folder that already contains knowledge-bearing artifacts:

- `README.md`
- `docs/`
- plans, specs, markdown notes, YAML, JSON, CSV

Avoid pointing ingest at:

- empty folders
- overly broad roots with many unrelated projects
- directories where the useful context only exists in excluded/generated files

If the target has no copyable files, `ingest` exits with code `1` and prints a clean error.

## Best Operator Sequence

Use this sequence for reliable results:

1. Initialize a workspace once.
2. Ingest a single project slice.
3. Query the slug right away to inspect the generated orientation.
4. Run lint to see whether the state is incomplete, stale, or contradictory.
5. Manually edit the project card if needed.
6. Rebuild indexes if your edit changes the shared navigation view.

## Important Limits

- Query is wiki-first. It checks whether the snapshot and ref manifest exist, but it does not re-summarize snapshot contents on demand.
- Manual project-card edits are preserved only against later low-confidence inference. There is no reset command yet.
- Duplicate detection is content-based within a single ingest slice.
- There is no Docker deployment, database layer, HTTP API, or frontend in V1.
