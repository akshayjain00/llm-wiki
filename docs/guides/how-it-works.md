# How It Works

## Service Model

This project is a local CLI with a maintained filesystem workspace. The user-facing surface is `llm-wiki`, and the command model is:

- `init`
- `ingest`
- `query`
- `rebuild-indexes`
- `lint`

There is no long-running process. Each command reads or writes the workspace directly.

## Core Data Flow

### 1. `init`

`init` creates the workspace structure and seed schema files:

- `raw/`
- `refs/`
- `wiki/projects/`
- `wiki/indexes/`
- `logs/`
- `schema/`

### 2. `ingest`

`ingest` is the main operator command.

It does the following:

1. resolves the target to an absolute path
2. scans the target recursively
3. filters files using the allow/deny rules
4. deduplicates identical files within that ingest slice
5. copies the kept files into an immutable timestamped snapshot under `raw/`
6. writes `refs/<project>.yaml`
7. infers project-card fields from the copied snapshot
8. merges weak inference with any existing manually maintained card values
9. writes `wiki/projects/<slug>/project-card.md`
10. rebuilds shared indexes
11. appends one ingest entry to `logs/ingest-log.md`

### 3. `query`

`query` is intentionally narrow.

It reads:

- the project card
- the canonical snapshot path referenced by the card
- the corresponding ref manifest path

It returns a text answer with:

- project name
- slug
- aliases
- owner
- status
- summary
- snapshot presence
- ref manifest presence
- next steps

It does not rescan the live repo during the query path.

### 4. `rebuild-indexes`

`rebuild-indexes` regenerates the shared navigation pages from project cards:

- `index.md`
- `active-projects.md`
- `by-owner.md`
- `by-domain.md`

It does not ingest content and it does not own `needs-review.md`.

### 5. `lint`

`lint` inspects the maintained workspace and writes:

- `wiki/indexes/needs-review.md`
- `logs/lint-log.md`

Current V1 checks include:

- unknown owner
- unknown status
- missing next steps
- stale project cards
- contradictory status evidence
- duplicate slugs
- missing live paths in manifests
- duplicate-source notes from ingest
- orphan cards missing from the main index

## Important Implementation Details

### Inference Is Ranked And Pattern-Based

V1 inference is deliberately heuristic, but not purely first-match. It:

- ranks overview-style docs above support files such as `CLAUDE.md` and `AGENTS.md`
- prefers stronger overview docs for project identity and summary extraction
- extracts aliases from alternate strong titles and folder identity
- `Owner: ...`
- `Status: ...`
- `Next steps: ...` and next-step sections from preferred docs

If conflicting owner or status values are found, the result drops to `unknown` with low confidence.

Support files are intentionally excluded from canonical `next_steps` extraction so operational instructions do not leak into maintained project memory.

### Manual Edits Matter

If you manually improve a project card, later ingests preserve the existing value when the new inference is weak. This is how V1 supports human correction without an admin UI.

### Snapshots Are The Evidence Layer

The raw snapshot is immutable and timestamped. It is the evidence base for what was seen during that ingest. The ref manifest points back to the live location, but normal queries do not consult the live location directly.

## What This Means For Effective Use

- Keep ingests scoped to one project slice at a time.
- Put useful project context in copyable markdown files.
- Prefer targets with one strong overview, onboarding, architecture, or charter doc.
- Query immediately after ingest to inspect the current maintained state.
- Use lint as your trust gate.
- Treat project cards as the canonical summary layer.
