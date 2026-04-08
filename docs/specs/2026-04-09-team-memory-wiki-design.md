# Team Memory Wiki Design Spec
**Date:** 2026-04-09
**Author:** Codex with Akshay Jain
**Status:** Draft - pending user review

---

## Problem Statement

Akshay has knowledge-bearing work artifacts spread across multiple roots:

- `/Users/akshay.jain/Desktop/AI_V2`
- `/Users/akshay.jain/Documents`
- `/Users/akshay.jain/Library/CloudStorage/GoogleDrive-akshay.jain@theporter.in/My Drive/AI`

Those roots include a mix of project repos, docs, specs, notes, screenshots, exports, and operational artifacts. The current state makes it hard to answer a simple project-orientation question quickly and reliably:

- What is this project?
- Who owns it?
- What is its current status?
- What should happen next?

The goal is to build an LLM-maintained team memory workspace that compiles understanding from those artifacts into a durable, inspectable wiki rather than re-discovering context from raw files on every question.

---

## Primary Goal

Build a Karpathy-aligned layered LLM wiki at:

`/Users/akshay.jain/Desktop/AI_V2/team_memory_wiki`

V1 should optimize for **project orientation**:

- what the project is
- who owns it
- current status
- next steps

V2 should extend that foundation into **decision memory**:

- what was decided
- why
- what changed

---

## Core Design Commitments

This design must stay faithful to the core concepts in Karpathy's LLM Wiki gist:

1. Use a **three-layer model**:
   - raw sources
   - maintained wiki
   - schema/instructions
2. Treat the wiki as a **persistent, compounding artifact**, not a stateless query wrapper.
3. Support **ingest, query, and lint** as first-class operations.
4. Maintain an **index** and an append-only **log**.
5. Prefer **wiki-first answers**, consulting raw sources when verification is needed.
6. Allow strong answers and syntheses to be **written back** into the wiki.

---

## Scope

### In Scope for V1

- Create one dedicated workspace for team memory.
- Consolidate knowledge artifacts into curated raw-source copies.
- Keep project repos and live folders as authoritative references.
- Create and maintain one `project-card.md` per project.
- Generate shared indexes for project navigation.
- Support guided ingest for one target folder/project at a time.
- Record ingest actions in a chronological log.
- Support lint checks for stale, missing, or contradictory project orientation data.

### Out of Scope for V1

- Full repo mirroring
- Continuous background automation
- Large-scale semantic search infrastructure
- Fully automated decision extraction from every artifact
- Org-wide collaboration workflows or review UIs
- Replacing source systems such as Git, Drive, or Notion

---

## User Decisions Already Made

The following choices are fixed unless the user changes them later:

- Implementation style: **Layered LLM Wiki foundation**
- Source strategy: **hybrid**
  - copy knowledge artifacts
  - keep project repos as linked references
  - exclude `.git`, `.venv`, caches, binaries, secrets, and generated outputs
- Destination: `/Users/akshay.jain/Desktop/AI_V2/team_memory_wiki`
- V1 outcome: **project orientation**
- V2 outcome: **decision memory**
- Metadata sourcing: **infer from existing artifacts, then standardize with a lightweight `project-card.md`**
- Update mode: **guided ingest**

---

## Architecture

The workspace will have three explicit layers:

### 1. Raw Sources Layer

`raw/` stores curated copied knowledge artifacts as **immutable ingest snapshots**. Each guided ingest creates a new timestamped snapshot for the affected project slice. Existing snapshots are never edited in place.

### 2. Wiki Layer

`wiki/` stores LLM-maintained markdown pages. This includes project cards, indexes, overview pages, and later decision pages. This is the primary layer for answering project-orientation questions.

### 3. Schema Layer

`schema/` stores the maintenance rules and templates that make the LLM behave like a disciplined wiki maintainer rather than a generic chat agent.

This preserves the exact raw/wiki/schema separation from the Karpathy model.

### Query Boundary Rule

Normal queries must answer from:

- the maintained wiki
- the latest ingested raw snapshot
- the ref manifest metadata

Normal queries must **not** read live repos or live folders directly, because that would make answers drift from the last compiled wiki state. Live sources may only be consulted during:

- guided ingest
- explicit refresh
- explicit verification requested by the user

---

## Workspace Layout

```text
/Users/akshay.jain/Desktop/AI_V2/team_memory_wiki/
├── raw/
│   └── <source-root>/<project-slug>/<ingest-timestamp>/...
├── refs/
│   └── <project-slug>.yaml
├── wiki/
│   ├── projects/
│   │   └── <project-slug>/
│   │       ├── project-card.md
│   │       ├── overview.md
│   │       └── decisions.md
│   └── indexes/
│       ├── index.md
│       ├── active-projects.md
│       ├── by-owner.md
│       ├── by-domain.md
│       └── needs-review.md
├── logs/
│   ├── ingest-log.md
│   └── lint-log.md
└── schema/
    ├── wiki-maintainer.md
    ├── ingest-rules.yaml
    ├── project-card-template.md
    └── lint-rules.md
```

Notes:

- `overview.md` and `decisions.md` may be absent initially.
- `Documents` must use a project allowlist in V1. It is too broad to sweep indiscriminately.

---

## Tech Stack and Component Model

### Recommended V1 Stack

- Python 3 for ingest, filtering, inference, lint, and CLI commands
- Markdown for wiki pages and logs
- YAML for ref manifests and ingest-rule configuration
- Standard library plus a small CLI layer for deterministic file operations
- Pytest for unit, fixture, integration, and golden-file tests

### Core Components

- `workspace_init`
  - creates the folder structure and seed schema files
- `source_scanner`
  - applies allow/deny rules and discovers eligible artifacts
- `artifact_copier`
  - writes immutable ingest snapshots into `raw/`
- `ref_manifest_writer`
  - records authoritative live sources and exclusions
- `project_inference`
  - derives project orientation fields with confidence scoring
- `wiki_writer`
  - updates project cards and derived indexes
- `lint_runner`
  - detects stale, contradictory, or incomplete wiki state
- `query_rules`
  - defines wiki-first lookup order and write-back destinations

### Interface Boundaries

- scanners and copiers operate only on filesystems
- inference operates only on copied snapshots plus manifests
- wiki writing consumes structured inference outputs, not raw filesystem traversal
- lint reads wiki pages and manifests, not live repos

---

## Source Selection Strategy

### Copy Into `raw/`

Include by default:

- `README*`
- `CLAUDE.md`
- `AGENTS.md`
- `docs/**`
- `*.md`
- `*.pdf`
- `*.txt`
- `*.yaml`
- `*.yml`
- `*.toml`
- `*.json`
- `*.csv`
- selected screenshots and supporting images near docs: `*.png`, `*.jpg`, `*.jpeg`
- plans, specs, runbooks, onboarding docs, meeting outputs, and manually promoted exports

### Do Not Copy by Default

- `.git/**`
- `.venv/**`
- `node_modules/**`
- `.pytest_cache/**`
- `__pycache__/**`
- temp directories and caches
- build outputs and generated artifacts
- `.env*`
- secrets, credentials, tokens, private keys
- lockfiles unless they carry real context and are manually promoted
- binaries and opaque assets such as `*.zip`, `*.jar`, `*.pt`, `*.p8`

### Repo and Live Folder Handling

Project repos and live working folders are authoritative references, not the wiki itself. V1 should write structured ref manifests pointing back to them instead of copying them wholesale.

### Initial `Documents` Allowlist for V1

To avoid sweeping personal or irrelevant material from `/Users/akshay.jain/Documents`, V1 should restrict that root to this starting allowlist:

- `/Users/akshay.jain/Documents/mbr_brain`
- `/Users/akshay.jain/Documents/ai-marketplace-community`
- `/Users/akshay.jain/Documents/metabase-mcp-local`
- `/Users/akshay.jain/Documents/New project`

Everything else under `/Users/akshay.jain/Documents` is excluded unless manually promoted later.

---

## Deduplication and Snapshot Rules

### Deduplication

- Deduplicate copied files by normalized path, size, and content hash.
- If one file exists in multiple roots, keep one copied raw artifact and record all origins in the ref manifest.
- If two files are similar but not identical, keep both and mark them as possible duplicates for lint review.

### Snapshot / Immutability

- Raw copied artifacts are treated as immutable evidence for a given ingest.
- Re-ingest creates a new timestamped snapshot directory for that project slice.
- Existing snapshot directories are never modified or replaced.
- The wiki and indexes point to the most recent successful ingest, while logs preserve full history.
- Temporal truth lives in the snapshot directories plus logs, not in live-source state.

---

## Guided Ingest Workflow

Guided ingest is the only update mode in V1.

The user points the system at one folder or project. The system then:

1. identifies the project slug and project boundary
2. scans only that slice
3. filters files through allow/deny rules
4. copies eligible knowledge artifacts into `raw/`
5. writes or updates `refs/<project-slug>.yaml`
6. reads copied artifacts and live refs
7. infers project orientation data conservatively
8. updates `wiki/projects/<project-slug>/project-card.md`
9. updates affected shared indexes
10. appends one entry to `logs/ingest-log.md`

A single ingest should usually touch multiple wiki pages, not just one.

---

## Project Boundary and Slugging Rules

### Project Boundary Heuristics

Ingest should treat a target as one project when one or more of the following is true:

- it has a repo root
- it has a `README`, `CLAUDE.md`, or `AGENTS.md`
- it has a coherent `docs/` subtree
- it already maps to an existing project slug

If a directory appears to contain multiple projects, guided ingest should stop at the top level and require the user to point to a narrower slice.

### Slugging Rules

- normalize directory or project title to lowercase kebab-case
- strip duplicate environment suffixes like `copy`, `backup`, `tmp` unless they are the only distinguishing identity
- prefer an explicit existing slug from `project-card.md` or ref manifest when available
- if two candidates collide, add a deterministic suffix and raise a lint warning

---

## Project Card Canonical Model

Each project gets one canonical `project-card.md`. Human edits to the project card override future weak inference unless explicitly reset.

Required frontmatter:

```yaml
---
project_name: "<string>"
slug: "<kebab-case>"
domain: "<string|unknown>"
source_roots:
  - "<absolute path>"
live_refs:
  - "<absolute path or repo url>"
owner: "<string|unknown>"
owner_confidence: low|medium|high
status: planned|active|paused|blocked|completed|unknown
status_confidence: low|medium|high
last_ingested: "<ISO-8601 timestamp>"
last_reviewed: "<ISO-8601 date|unknown>"
canonical_snapshot: "raw/<source-root>/<project-slug>/<ingest-timestamp>/"
---
```

Required body sections:

- Project name
- Slug
- Summary
- Domain / category
- Source roots
- Live references
- Owner
- Owner confidence
- Status
- Status confidence
- Current scope
- Key artifacts
- Key questions
- Risks / blockers
- Next steps
- Last ingested
- Last reviewed
- Related pages

Status enum:

- `planned`
- `active`
- `paused`
- `blocked`
- `completed`
- `unknown`

If evidence is weak or conflicting:

- set owner/status to `unknown`
- reduce confidence
- record the ambiguity in open questions

---

## Index and Log Formats

### `wiki/indexes/index.md`

Purpose:

- master navigation page for all projects

Format:

- one markdown table row per project
- sorted by status priority, then recency

Required columns:

- project link
- one-line summary
- owner
- status
- last updated

### Other Indexes

- `active-projects.md`
- `by-owner.md`
- `by-domain.md`
- `needs-review.md`

These are derived navigation views over the same project-card data.

### `logs/ingest-log.md`

Append-only chronological log.

Format:

- one heading per ingest using:
  - `## [YYYY-MM-DD HH:MM TZ] ingest | <project-slug>`

Each entry must capture:

- timestamp
- ingest target
- roots scanned
- snapshot path
- files copied
- refs recorded
- wiki pages updated
- unresolved gaps
- success / partial / failed outcome

### `refs/<project-slug>.yaml`

Required fields:

- project slug
- authoritative live paths
- repo roots
- origin roots
- excluded sensitive or technical paths
- duplicate-source notes
- last scanned timestamp
- rationale for using refs rather than full copies

---

## Inference Rules

Inference must be conservative and traceable.

### Evidence Priority

Owner and status are inferred in this order:

1. explicit value in `project-card.md`
2. explicit value in specs, plans, runbooks, onboarding docs
3. `README`, `CLAUDE.md`, `AGENTS.md`, structured docs
4. repo activity and surrounding evidence as weak signal only

### Conflict Handling

If signals disagree:

- preserve the conflict
- lower confidence
- do not collapse into a confident but unsupported answer

### Manual Override

If a human edits the project card, the project card wins unless an explicit reset or override workflow is invoked later.

### Human Review Trigger

Any ingest that leaves `owner` or `status` as `unknown`, or surfaces conflicting evidence, must mark the project as requiring human review in `needs-review.md`.

---

## Query Behavior

Project-orientation answers should start from the maintained wiki.

### Read Order

1. `wiki/indexes/index.md`
2. relevant `project-card.md`
3. related `overview.md` or `decisions.md`
4. latest ingested raw snapshot only if verification or deeper evidence is needed

Live repositories and live folders may only be consulted after an explicit refresh or explicit user request to verify against current state.

### Query Outputs

V1 should support answers like:

- brief me on this project
- who owns this and what is the status
- what are the current blockers
- what changed since the last ingest
- what projects need review

### Write-Back Rule

If a generated answer is high value and durable, it should be stored as:

- a `project-card.md` update when the answer changes factual orientation fields
- `overview.md` when the answer is a durable project briefing or synthesis
- `decisions.md` when the answer captures a decision, rationale, alternatives, or changed direction

This keeps the wiki compounding over time.

---

## Lint Behavior

Lint is a first-class maintenance operation.

V1 lint should flag:

- unknown owner
- unknown status
- missing next steps
- stale project cards
- orphan projects not present in indexes
- duplicate slugs
- contradictory statuses across pages
- ref manifests pointing to missing live paths
- possible duplicates in copied raw artifacts

Lint output should update:

- `wiki/indexes/needs-review.md`
- `logs/lint-log.md`

---

## Error Handling

The system should fail soft and surface uncertainty.

### Cases

- Missing path:
  - skip ingest for that target
  - record failure in the ingest log
- Permission/read failure:
  - continue with readable files
  - mark coverage as partial
- No usable artifacts:
  - still create a ref manifest
  - create a minimal project card with unknown fields
- Conflicting evidence:
  - lower confidence
  - preserve contradiction in the project card and lint output
- Duplicate project identity:
  - stop auto-merge
  - route to manual review
- Oversized/noisy folder:
  - stop at configured scan limits
  - report truncation
- Sensitive file encountered:
  - exclude content
  - log only the exclusion event, not the secret material

---

## Privacy and Sharing Policy

- The wiki is optimized for work/team memory, not personal archiving.
- Files from broad roots must be filtered aggressively before copying.
- Sensitive artifacts are excluded by rule and never summarized into the wiki body.
- Ref manifests may note that sensitive paths were intentionally excluded, but must not expose secret values.
- If the workspace is later shared, only the consolidated wiki and curated raw artifacts should be considered shareable by default; live refs remain subject to the permissions of their source systems.

---

## Testing Strategy

The first implementation should be test-first and mostly deterministic.

### Unit Tests

- file filtering
- slug generation
- deduplication
- confidence scoring
- inference conflict handling

### Fixture-Based Tests

- sample project folders with known docs
- expected owner/status/next-step inference
- generated project-card content

### Golden-File Tests

- `project-card.md`
- `index.md`
- `ingest-log.md`
- ref manifests

### Integration Tests

- guided ingest against a small synthetic workspace
- rerun ingest and verify idempotent behavior except expected log growth

### Lint Tests

- stale cards
- missing owner/status
- missing next steps
- duplicate refs/slugs
- contradictory statuses

Success criteria:

- copied artifacts are predictable
- project cards are auditable
- indexes remain coherent
- logs are trustworthy

---

## V1 Implementation Shape

The first implementation should focus on a small, clean command surface:

- initialize the workspace
- run guided ingest for one target
- rebuild indexes
- run lint

No scheduler is needed in V1.

---

## Human Review and Override Workflow

V1 should support a simple human-in-the-loop loop:

1. guided ingest runs
2. low-confidence or conflicting projects are added to `needs-review.md`
3. a human edits `project-card.md` fields directly where needed
4. later ingests preserve those explicit overrides unless reset

This gives the system a clean correction path without requiring a separate admin UI.

---

## Enrichment Roadmap

### Phase 1: Project Orientation

- stable project cards
- useful indexes
- reliable status / owner / next-step summaries

### Phase 2: Decision Memory

Add `decisions.md` or a structured decision section per project capturing:

- decision
- rationale
- alternatives considered
- supporting evidence
- what changed

### Phase 3: Higher-Order Synthesis

- domain brief pages
- cross-project rollups
- onboarding summaries
- review packs for management or planning

---

## Expert-Practice Alignment

This design intentionally follows practical patterns visible in strong AI workflows:

- Karpathy-style persistent wiki:
  - synthesize once
  - maintain continuously
  - answer from a structured markdown knowledge layer
- Anthropic-style project grounding:
  - keep project-specific instructions close to the work
  - make the schema layer explicit and versioned
- OpenAI project-memory pattern:
  - keep context scoped to a bounded project space instead of mixing unrelated memory
- source-grounded notebook pattern:
  - preserve links to source artifacts
  - prefer cited, inspectable answers
- Simon Willison-style durable notes:
  - store useful outputs as files
  - let small markdown artifacts compound over time

These patterns support the same core outcome: a trustworthy project memory layer that improves with use instead of resetting every session.

### Concrete, Vetted Use Cases

- Karpathy's LLM wiki pattern:
  - persistent markdown wiki maintained by an LLM instead of redoing synthesis on every query
- OpenAI Projects:
  - project-scoped instructions, chats, and files for long-running work with memory boundaries
- NotebookLM:
  - source collections per notebook, source-scoped Q&A, reports, and citation-backed answers
- Anthropic Claude Code:
  - repository-root `CLAUDE.md` used as a durable project instruction layer
- Simon Willison's TIL practice:
  - accumulate small file-backed notes, then build search and browse over them

These are not identical products, but together they validate the core operating model:

- keep context bounded
- keep sources explicit
- save durable artifacts
- make the system searchable and maintainable over time

---

## Practical Value for Akshay

This system is most valuable if it becomes the default place to answer:

- what is this project
- which docs matter
- who likely owns it
- what status is supported by evidence
- what needs attention next

The highest-return operating habits will be:

- ingest important project areas one at a time
- treat project cards as maintained canonical summaries
- file valuable briefings back into the wiki
- run lint periodically to expose stale or missing metadata
- add decision memory only after project orientation is stable

---

## Acceptance Criteria

The spec is implementation-ready only if V1 can satisfy all of the following:

- initialize a new workspace under `/Users/akshay.jain/Desktop/AI_V2/team_memory_wiki`
- ingest one allowlisted project or folder without reading unrelated roots
- create an immutable raw snapshot for that ingest
- write a ref manifest for the project
- generate or update a valid `project-card.md`
- rebuild shared indexes coherently
- write an append-only ingest log entry
- run lint and surface at least unknown/conflicting owner or status cases
- answer a project-orientation query using wiki-first logic without silently consulting live repo state

---

## Open Assumptions

These assumptions are explicit and should remain visible during implementation:

- `/Users/akshay.jain/Documents` will use an allowlisted set of project directories in V1.
- Repo references remain authoritative; the wiki does not replace Git history or source systems.
- Weak evidence resolves to `unknown`, not a guess.
- V1 is optimized for trust and inspectability over full automation.

---

## References

- Karpathy LLM Wiki gist:
  - [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- OpenAI Help:
  - [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)
- Anthropic Docs:
  - [Claude Code overview](https://code.claude.com/docs/en/overview)
  - [Claude Code GitHub Actions / `CLAUDE.md`](https://code.claude.com/docs/en/github-actions)
- Google NotebookLM Help:
  - [Create a notebook in NotebookLM](https://support.google.com/notebooklm/answer/16206563)
  - [Use chat in NotebookLM](https://support.google.com/notebooklm/answer/16179559?hl=en&ref_topic=16164070)
- Simon Willison:
  - [TIL index](https://til.simonwillison.net/)
  - [Weeknotes: California Protected Areas in Datasette](https://simonwillison.net/2020/Aug/28/weeknotes-cpad/)

---

## Definition of Success

V1 is successful if, after a few guided ingests, Akshay can ask project-orientation questions and get fast, source-grounded answers from the wiki without manually searching across the three source roots.

V2 is successful if decision memory builds on that foundation without making the system noisy or speculative.
