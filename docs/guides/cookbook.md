# Cookbook

## 1. Create A New Workspace

Use this when you want a clean local wiki workspace.

```bash
uv run llm-wiki init --workspace /tmp/team-memory-wiki-demo
```

Then verify the skeleton:

```bash
find /tmp/team-memory-wiki-demo -maxdepth 2 -type d | sort
```

## 2. Ingest A New Project Folder

Use this when you have a project folder with a `README.md` or `docs/`.

```bash
uv run llm-wiki ingest \
  --workspace /tmp/team-memory-wiki-demo \
  --target /path/to/project
```

Then inspect the result:

```bash
uv run llm-wiki query \
  --workspace /tmp/team-memory-wiki-demo \
  --project project-slug
```

Useful follow-up checks:

```bash
sed -n '1,200p' /tmp/team-memory-wiki-demo/wiki/projects/project-slug/project-card.md
sed -n '1,200p' /tmp/team-memory-wiki-demo/refs/project-slug.yaml
```

## 3. Refresh A Project After Docs Changed

Use this when the repo docs changed and you want the maintained state refreshed.

```bash
uv run llm-wiki ingest \
  --workspace /tmp/team-memory-wiki-demo \
  --target /path/to/project

uv run llm-wiki lint --workspace /tmp/team-memory-wiki-demo
```

This is the normal V1 update cycle.

## 4. Inspect A Conflicting Project

Use this when owner or status evidence disagrees across files.

```bash
uv run llm-wiki ingest \
  --workspace /tmp/team-memory-wiki-demo \
  --target tests/fixtures/conflicting_project

uv run llm-wiki lint --workspace /tmp/team-memory-wiki-demo
sed -n '1,200p' /tmp/team-memory-wiki-demo/wiki/indexes/needs-review.md
```

Expected outcome:

- the project card may fall back to `unknown`
- lint should surface the problem

## 5. Ingest A Noisy Project

Use this when the target contains `.git`, `.env`, caches, or other excluded files.

```bash
uv run llm-wiki ingest \
  --workspace /tmp/team-memory-wiki-demo \
  --target tests/fixtures/noisy_project
```

The service should ignore excluded artifacts and keep the ingest focused on useful source files.

## 6. Manually Improve A Project Card

Use this when the inferred summary or ownership is weak but you know the correct answer.

1. Edit the project card directly:

```bash
$EDITOR /tmp/team-memory-wiki-demo/wiki/projects/project-slug/project-card.md
```

2. Re-ingest the same project later:

```bash
uv run llm-wiki ingest \
  --workspace /tmp/team-memory-wiki-demo \
  --target /path/to/project
```

Current V1 behavior preserves existing values when the new inference is weak.

## 7. Rebuild Navigation Pages After Card Edits

Use this when you edited project cards directly and want navigation pages refreshed.

```bash
uv run llm-wiki rebuild-indexes --workspace /tmp/team-memory-wiki-demo
```

This command does not ingest content and does not rewrite `needs-review.md`.

## 8. Common Failure Cases

### Query Before Ingest

```bash
uv run llm-wiki query \
  --workspace /tmp/team-memory-wiki-demo \
  --project missing-project
```

Expected:

- exit code `1`
- clean stderr message
- no traceback

### Empty Folder Ingest

```bash
mkdir -p /tmp/empty-project
uv run llm-wiki ingest \
  --workspace /tmp/team-memory-wiki-demo \
  --target /tmp/empty-project
```

Expected:

- exit code `1`
- `No copyable files found ...`

## 9. Effective Usage Rules

- Ingest one project slice at a time.
- Query by slug, not by display name.
- Treat `project-card.md` as the canonical maintained summary.
- Use `lint` after ingest when you care about trust and reviewability.
- Use `rebuild-indexes` after manual edits to cards, not as a replacement for ingest.
