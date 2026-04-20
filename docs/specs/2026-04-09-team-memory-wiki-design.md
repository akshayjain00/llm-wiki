# Team Memory Wiki Design Spec
**Date:** 2026-04-09
**Last Updated:** 2026-04-20
**Author:** Codex with Akshay Jain
**Status:** Implemented V1 draft - pending user review

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
- Support a project-orientation query surface that answers from the maintained wiki and latest snapshot evidence.
- Record ingest actions in a chronological log.
- Support lint checks for stale, missing, or contradictory project orientation data.

### Out of Scope for V1

- Full repo mirroring
- Continuous background automation
- Large-scale semantic search infrastructure
- Fully automated decision extraction from every artifact
- Org-wide collaboration workflows or review UIs
- Replacing source systems such as Git, Drive, or Notion

These items may still be designed explicitly in this spec as next-phase architecture. Designing them now does not make them implementation requirements for the current V1 plan.

---

## V1 / Next-Phase Boundary

This spec now has two distinct layers of detail:

- **V1 implementation contract**
  - the parts that must exist for the current implementation plan to be considered complete
- **Next-phase architecture**
  - the parts that are intentionally designed now so the system can evolve without a redesign later

The boundary is strict:

- the current implementation plan remains V1-only
- V1 commands remain:
  - initialize the workspace
  - run guided ingest for one target
  - query project orientation from wiki-first state
  - rebuild indexes
  - run lint
- next-phase features must not become hidden blockers for V1 delivery
- any future graph, search, automation, or collaboration layer must still honor the existing query-boundary rule and snapshot-first trust model

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

### Optional Next-Phase Storage Extensions

These paths are not required for V1, but they define where next-phase artifacts should live so future design stays coherent:

```text
wiki/
├── entities/
│   └── <entity-type>/<entity-slug>.md
├── episodes/
│   └── <project-slug>/<episode-id>.md
├── procedures/
│   └── <procedure-slug>.md
├── crystallized/
│   └── <project-slug>/<YYYY-MM-DD>-<topic>.md
└── graph/
    ├── entities.yaml
    └── relationships.yaml
```

Rules:

- `wiki/entities/` stores typed entity pages for people, projects, decisions, systems, libraries, files, and concepts
- `wiki/episodes/` stores session or ingest-level digests promoted above raw snapshots but below stable semantic facts
- `wiki/procedures/` stores reusable workflows proven across multiple episodes or projects
- `wiki/crystallized/` stores durable research, debugging, or analysis digests filed back into memory
- `wiki/graph/` stores lightweight typed relationship indexes derived from wiki and snapshots, not from live repos

---

## Tech Stack and Component Model

### Recommended V1 Stack

- Python 3 for ingest, filtering, inference, lint, and CLI commands
- Markdown for wiki pages and logs
- YAML for ref manifests and ingest-rule configuration
- Standard library plus a small CLI layer for deterministic file operations
- Pytest for unit, fixture, integration, and golden-file tests
- Ruff for linting and format checks
- Mypy for static analysis over `src/`
- `uv` for reproducible local execution and packaging smoke checks

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
6. reads copied artifacts plus ref manifests, but does not infer from live repo contents
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
aliases:
  - "<alternate name>"
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
- Aliases
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

Canonical identity rules:

- prefer ranked overview docs over support files for project name and summary extraction
- treat `CLAUDE.md` and `AGENTS.md` as supporting instructions, not canonical project identity, unless no better overview evidence exists
- preserve alternate titles and meaningful folder identity as aliases when they differ from the canonical project name

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

## Next-Phase Knowledge Lifecycle Model

These rules are not part of the V1 implementation contract, but they are the canonical direction for evolution after project orientation is stable.

### Confidence vs Quality

The system must keep these concepts separate:

- **confidence**
  - how well-supported and current a claim is
- **quality**
  - how readable, structured, cited, and internally consistent a generated artifact is

Confidence answers "is this likely true?" Quality answers "is this memory artifact good enough to keep?"

### Claim Metadata

For next-phase semantic claims, decision records, and entity relationship assertions, the canonical metadata model should include:

```yaml
claim_id: "<stable id>"
scope: private|shared
confidence: 0.00-1.00
confidence_band: low|medium|high
evidence_count: <integer>
last_confirmed: "<ISO-8601 timestamp>"
freshness_class: hot|warm|cold|stale
retention_class: transient|working|reference|durable
supersedes:
  - "<claim_id>"
superseded_by:
  - "<claim_id>"
quality_score: 0.00-1.00
quality_band: low|medium|high
```

### Supersession Rules

When a newer claim contradicts or updates an older claim:

- preserve the older claim
- mark the older claim as superseded, not deleted
- link old and new claims through `supersedes` / `superseded_by`
- prefer the newer claim in query ranking only if:
  - it has equal or better source authority
  - and it is more recent or better supported
- if neither claim clearly dominates, keep both active and route to lint or human review

Supersession applies most strongly to:

- project status
- ownership changes
- architecture choices
- dependency usage claims
- decisions and reversals

### Retention Rules

Retention is a ranking and visibility rule, not automatic deletion.

- `transient`
  - short-lived observations and one-off debugging details
- `working`
  - recent but not yet stabilized observations
- `reference`
  - useful factual knowledge that should stay visible
- `durable`
  - long-term decisions, architectural facts, and reusable procedures

Default retention behavior:

- transient knowledge decays fastest
- working knowledge decays unless reinforced or promoted
- reference knowledge decays slowly
- durable knowledge decays slowest and is usually reviewed rather than hidden

Decay signals:

- time since last confirmation
- time since last access
- contradiction by newer evidence
- lack of reinforcement across later ingests

### Formal Memory Tiers

The next-phase memory model should follow four tiers:

1. **Working memory**
   - recent observations from guided ingest or session activity
   - default storage:
     - `logs/ingest-log.md`
     - temporary extraction outputs
2. **Episodic memory**
   - session or ingest digests describing what happened and what was learned
   - default storage:
     - `wiki/episodes/`
     - `wiki/crystallized/`
3. **Semantic memory**
   - stabilized cross-session facts and decisions
   - default storage:
     - `project-card.md`
     - `decisions.md`
     - `wiki/entities/`
4. **Procedural memory**
   - reusable workflows, playbooks, and recurring patterns
   - default storage:
     - `wiki/procedures/`

### Promotion Rules

- working -> episodic
  - after successful ingest or session-end summarization
- episodic -> semantic
  - when supported by at least two reinforcing signals
  - or explicitly confirmed by a human
- semantic -> procedural
  - when a pattern recurs across multiple episodes or projects
  - or is intentionally curated as a team workflow

If promotion criteria are not met, keep the item in the lower tier.

---

## Next-Phase Structured Knowledge Model

The wiki should remain readable as markdown pages, but next-phase search and discovery should use typed entities and typed relationships layered on top of those pages.

### Entity Types

The first typed entity set should include:

- `project`
- `person`
- `decision`
- `system`
- `library`
- `service`
- `file`
- `document`
- `concept`

### Relationship Types

The first relationship vocabulary should include:

- `owns`
- `maintains`
- `uses`
- `depends_on`
- `references`
- `documents`
- `blocked_by`
- `supersedes`
- `contradicts`
- `caused`
- `resolved_by`
- `related_to`

### Storage Model

- entity detail remains readable in markdown under `wiki/entities/`
- relationship indexes are stored in `wiki/graph/relationships.yaml`
- entity summaries may be derived from `project-card.md`, `decisions.md`, `overview.md`, and crystallized digests
- graph indexes are derived artifacts and can be rebuilt from wiki pages plus snapshots

### Query Discipline

Typed entities and relationships must never bypass the snapshot-first trust boundary.

- graph indexes may only be built from:
  - wiki pages
  - ref manifests
  - ingested snapshots
- graph indexes must not read live repos directly except during explicit refresh or ingest

---

## Next-Phase Search Architecture

### Scale Thresholds

- up to roughly `100` maintained pages
  - `index.md` plus direct page reads remain sufficient
- roughly `100-300` maintained pages
  - add local lexical search over wiki pages and snapshots
- beyond roughly `300` maintained pages or dense cross-project questions
  - add hybrid retrieval and typed graph traversal

These thresholds are heuristics, not hard limits.

### Search Streams

The future retrieval stack should combine:

- lexical search
  - BM25 or equivalent keyword ranking over wiki pages, entity pages, and selected snapshot text
- semantic search
  - embedding-backed similarity over project pages, decision pages, and crystallized artifacts
- graph traversal
  - expansion over typed entity and relationship indexes

### Result Fusion

The default fusion strategy should be reciprocal rank fusion or equivalent weighted reranking across:

- lexical matches
- semantic matches
- graph expansion candidates

### Query Retrieval Order

For next-phase queries, the retrieval order should be:

1. direct wiki navigation hints
   - `index.md`
   - `project-card.md`
   - `decisions.md`
2. lexical and semantic candidates from the maintained wiki
3. graph expansion over related entities and decisions
4. raw snapshot verification if confidence is still low
5. live-source verification only on explicit refresh or explicit request

This preserves the V1 trust model while scaling retrieval.

---

## Next-Phase Event-Driven Automation

Background automation remains out of scope for V1, but the canonical trigger design should be:

### Trigger Types

- **on new source**
  - queue ingest for the affected project slice
- **on ingest completion**
  - rebuild affected indexes
  - refresh entity and relationship indexes
- **on query completion**
  - evaluate whether the result deserves write-back
- **on session end**
  - crystallize valuable exploration into episodic memory
- **on memory write**
  - run contradiction and supersession checks
- **on schedule**
  - run lint
  - apply retention decay
  - surface review queues

### Human Review Gates

Automation may propose changes automatically, but human review is required when:

- confidence is below the configured threshold
- quality is below the configured threshold
- the write changes owner or status
- the write supersedes an existing durable claim
- the write promotes a private memory into shared scope
- contradiction resolution is ambiguous

### V1 Compatibility Rule

The current implementation should expose these triggers as future design only. V1 remains manual and guided.

---

## Next-Phase Content Quality and Self-Correction

### Quality Scoring

Every next-phase generated artifact should receive a quality score based on:

- structure
- citation or source traceability
- consistency with existing wiki state
- specificity and usefulness
- absence of unresolved ambiguity where certainty is claimed

Suggested quality bands:

- `high`
  - durable, well-cited, safe to keep
- `medium`
  - usable but should remain editable and reviewable
- `low`
  - do not promote automatically; route to review or rewrite

### Self-Correction Rules

Lint and maintenance flows should eventually support safe auto-fixes for:

- broken links
- missing reverse links
- stale claim markers
- duplicate entity aliases
- index drift

Auto-fixes must not silently change:

- owner
- status
- decision rationale
- claim supersession state

Those remain review-gated.

---

## Next-Phase Crystallization

Crystallization is the process of turning a completed exploration thread into durable memory.

### Valid Inputs

- debugging sessions
- research threads
- design explorations
- implementation retrospectives
- project briefings

### Output Destinations

- `project-card.md`
  - when orientation fields change
- `decisions.md`
  - when the artifact records a decision, rationale, or reversal
- `wiki/crystallized/<project-slug>/<date>-<topic>.md`
  - when the artifact is a durable digest of a thread or investigation
- `wiki/procedures/<procedure-slug>.md`
  - when the artifact captures a reusable workflow

### Routing Rule

One crystallized output may update more than one destination:

- summary into `project-card.md`
- decision into `decisions.md`
- full digest into `wiki/crystallized/`

The digest page is the durable narrative. The project card and decisions page hold the concise canonical state.

---

## Next-Phase Shared / Private Scoping

The current workspace is effectively single-user, but the design should support scoped memory from the start.

### Scope Types

- `private`
  - personal notes, preferences, tentative interpretations, or sensitive context not ready for team memory
- `shared`
  - project architecture, team decisions, runbooks, and broadly reusable context

### Default Rules

- raw snapshots inherit the sensitivity of their source
- project orientation facts default to shared if they are source-grounded and non-sensitive
- exploratory interpretations default to private until promoted

### Promotion Rules

Private -> shared promotion requires:

- passing privacy filters
- sufficient confidence
- sufficient quality
- no unresolved contradiction with existing shared knowledge

### Conflict Rule

If a private claim contradicts shared memory:

- do not overwrite shared memory automatically
- preserve the private claim as a private observation
- surface the contradiction for review

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

For next-phase crystallization, these V1 write-back destinations remain canonical summaries, while full digests may additionally be written to `wiki/crystallized/` or `wiki/procedures/`.

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

`needs-review.md` is a lint-owned review surface. `rebuild-indexes` must not rewrite it.

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

## CLI Exit and Error Contract

V1 is CLI-first, so operators need predictable command behavior:

- exit code `0`
  - successful command completion
- exit code `1`
  - runtime failure such as missing project card, missing target path, or no copyable artifacts
- exit code `2`
  - argument parsing failure from `argparse`

Runtime errors should be printed as concise stderr messages without Python tracebacks during normal operator flows.

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

### Deterministic Design Requirements

Verification must be supported by the architecture, not bolted on afterward.

V1 implementation should therefore prefer:

- injectable clocks or timestamp providers for snapshot and log generation
- stable ordering for all file scans, index rows, and manifest entries
- deterministic markdown rendering
- pure functions at the inference and formatting boundaries where possible
- subprocess-invocable CLI commands so end-to-end tests exercise the real entrypoints
- explicit exit codes and quiet stderr behavior for successful CLI flows

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
- subprocess-based CLI smoke tests for:
  - `llm-wiki --help`
  - `llm-wiki init`
  - `llm-wiki ingest`
  - `llm-wiki query`
  - `llm-wiki rebuild-indexes`
  - `llm-wiki lint`

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

### Fixture Matrix

The verification suite should cover at least these fixture classes:

- a clean single-project fixture
- a fixture with conflicting owner or status signals
- a fixture with noisy or excluded files such as `.env`, `.git`, caches, and binaries
- a fixture with duplicate files across source roots
- a fixture with partial evidence that should resolve to `unknown`
- a fixture whose rerun ingest proves snapshot growth plus stable wiki behavior

---

## Verification Strategy

Verification is a core part of the design, not a final cleanup step.

### Quality Gates

The V1 implementation should not be considered complete unless all of the following pass:

- unit tests
- integration tests
- golden-file tests
- subprocess CLI end-to-end tests
- Ruff lint check
- Ruff format check
- Mypy over `src/`
- packaging smoke check through `uv build` or equivalent

### End-to-End Verification Contract

At minimum, the end-to-end verification flow must prove:

1. a new workspace can be initialized from the real CLI
2. guided ingest against a fixture creates:
   - an immutable snapshot
   - a ref manifest
   - a project card
   - rebuilt indexes
   - an append-only ingest log entry
3. query returns a wiki-first project-orientation answer from maintained state
4. lint produces stable findings and writes the expected review surfaces
5. rerunning ingest does not mutate prior snapshots and only changes the latest derived state plus append-only logs
6. successful CLI commands exit cleanly with code `0`

### Static and Contract Verification

Verification should also include:

- frontmatter contract checks for `project-card.md`
- manifest schema checks for `refs/<project-slug>.yaml`
- markdown contract checks for `index.md`, `needs-review.md`, `ingest-log.md`, and `lint-log.md`
- static analysis ensuring typed internal models match emitted data structures

### Operational Verification

The implementation should support a local smoke workspace under `/tmp` so the full init -> ingest -> rebuild-indexes -> lint path can be run outside tests as an operator check.

### Browser / Frontend Verification

Playwright or browser automation is **not** part of V1 verification because V1 has no frontend or browser workflow. If a future UI, review console, or search interface is introduced, browser automation and console-cleanliness checks should become mandatory for that surface.

---

## V1 Implementation Shape

The first implementation should focus on a small, clean command surface:

- initialize the workspace
- run guided ingest for one target
- query project orientation
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

Also add:

- explicit supersession between changed decisions
- retention classes for transient vs durable knowledge
- episodic and semantic memory separation

### Phase 3: Structured Knowledge and Search

- typed entities and typed relationships
- entity pages and relationship indexes
- lexical plus semantic plus graph-aware retrieval
- graph-backed impact and dependency questions

### Phase 4: Automation and Crystallization

- event-triggered indexing and maintenance
- query-time write-back evaluation
- session-end crystallization
- quality scoring and safe self-correction

### Phase 5: Higher-Order Synthesis and Collaboration

- domain brief pages
- cross-project rollups
- onboarding summaries
- review packs for management or planning
- shared/private promotion rules
- optional multi-agent coordination

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
- Rohit Ghumare's LLM Wiki v2:
  - memory lifecycle, typed graph structure, automation, crystallization, and scoped memory as scaling layers on top of the Karpathy pattern

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
- treat graph/search/automation as explicit next-phase upgrades, not reasons to overcomplicate V1

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
- run lint and surface unknown, stale, contradictory, missing, and duplicate-review cases promised in V1
- answer a project-orientation query using wiki-first logic, exposing snapshot and ref evidence without silently consulting live repo state
- pass the defined verification gates for tests, static analysis, CLI end-to-end checks, and packaging smoke

---

## Operational Assumptions

These are V1 operating rules, not future design goals:

- relative ingest targets are normalized to absolute paths before they are written to project cards or ref manifests
- stale-card detection uses a default threshold of `30` days since `last_ingested`
- query reads `project-card.md`, checks `canonical_snapshot`, and checks the ref manifest; it does not re-scan live repos
- query accepts either the canonical slug or a stored alias and always returns the canonical project record
- lint owns `needs-review.md`; index rebuilds own all other derived index pages
- human edits preserve existing project-card values against later low-confidence inference; explicit reset tooling is deferred

---

## Current V1 Known Limitations

- deduplication is content-based within the guided-ingest slice; there is no multi-target batch dedup workflow in V1
- manual override reset is not yet a first-class command
- query verifies evidence locations but does not re-summarize snapshot content on demand
- contradictory status lint is limited to project-card-adjacent markdown pages and manifest state

---

## Open Assumptions

These assumptions are explicit and should remain visible during implementation:

- `/Users/akshay.jain/Documents` will use an allowlisted set of project directories in V1.
- Repo references remain authoritative; the wiki does not replace Git history or source systems.
- Weak evidence resolves to `unknown`, not a guess.
- V1 is optimized for trust and inspectability over full automation.
- Next-phase graph, search, lifecycle, and automation rules are designed now but are not required to ship the current V1 implementation.

---

## Requirements Traceability (V1)

| Requirement | Primary implementation | Verification |
| --- | --- | --- |
| Guided ingest with allow/deny filtering | `src/llm_wiki/ingest.py`, `src/llm_wiki/filters.py` | `tests/integration/test_ingest_cli.py`, `tests/unit/test_filters.py` |
| Immutable raw snapshots | `src/llm_wiki/snapshot.py` | `tests/unit/test_snapshot.py` |
| Ref manifests with live refs and duplicate notes | `src/llm_wiki/manifests.py`, `src/llm_wiki/ingest.py` | `tests/unit/test_manifests.py`, `tests/unit/test_ingest.py` |
| Project-card generation and low-confidence override preservation | `src/llm_wiki/inference.py`, `src/llm_wiki/wiki_writer.py`, `src/llm_wiki/ingest.py` | `tests/unit/test_inference.py`, `tests/unit/test_ingest.py`, `tests/golden/test_project_card.py` |
| Rebuildable shared indexes | `src/llm_wiki/indexes.py` | `tests/unit/test_indexes.py`, `tests/golden/test_index_markdown.py` |
| Wiki-first project-orientation query with evidence reporting | `src/llm_wiki/query.py` | `tests/unit/test_query.py`, `tests/integration/test_query_cli.py` |
| Lint-owned review surface and append-only lint log | `src/llm_wiki/lint.py`, `src/llm_wiki/cli.py` | `tests/unit/test_lint.py` |
| CLI usability and error contract | `src/llm_wiki/cli.py` | `tests/integration/test_cli_subprocess.py` |
| End-to-end operator verification | CLI plus docs | `README.md` smoke flow, `uv run pytest -v`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `uv build` |

---

## References

- Karpathy LLM Wiki gist:
  - [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Rohit Ghumare LLM Wiki v2 gist:
  - [LLM Wiki v2 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)
  - [agentmemory](https://github.com/rohitg00/agentmemory)
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
