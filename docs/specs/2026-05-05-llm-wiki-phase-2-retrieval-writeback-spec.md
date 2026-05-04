# LLM Wiki Phase 2: Retrieval And Write-Back Spec
**Date:** 2026-05-05
**Last Updated:** 2026-05-05
**Author:** Codex with Akshay Jain
**Status:** Proposed - design approved, pending written spec review

---

## Problem Statement

`llm-wiki` V1 is a strong project-orientation compiler, but it is still too narrow relative to the intended LLM wiki pattern.

Current strengths:

- immutable raw snapshots
- maintained markdown project cards
- wiki-first project orientation
- append-only ingest and lint logs
- reviewable markdown state

Current limitations:

- query can only answer one project at a time
- query cannot synthesize across wiki pages and snapshot evidence
- useful analyses do not compound automatically into durable wiki memory
- lint is mostly project-card hygiene, not knowledge-health
- derived markdown indexes are not sufficient as the only retrieval substrate

The goal of Phase 2 is to improve the usefulness of the wiki **without** turning the system into a broad platform rewrite.

---

## Goal

Add a **hybrid retrieval, multi-project synthesis, and manual-approval write-back** layer to `llm-wiki`, while preserving the current trust model:

- CLI-first
- project-centric
- wiki-first + latest immutable snapshot fallback
- raw snapshots and markdown remain durable human-facing artifacts
- no entity graph, public API, or UI in this phase

---

## Product Boundary

### In Scope

- richer query answers across **2 to 5 explicitly named projects**
- hybrid retrieval from markdown wiki pages and latest immutable raw snapshots
- embedded OpenAI-first model calls for synthesis and write-back proposal generation
- durable richer project pages:
  - `project-card.md`
  - `overview.md`
  - `decisions.md`
- durable cross-project outputs under `wiki/reports/`
- derived SQLite retrieval/provenance/logging store
- expanded lint/health checks for citations, page freshness, retrieval drift, and write-back state
- side-by-side versioned rollout and migration support from V1 workspaces

### Explicitly Out Of Scope For This Phase

- entity pages
- concept hubs
- first-class graph navigation UI
- workspace-wide open-ended query
- live-source reads during normal query
- multimodal retrieval from images/screenshots
- public HTTP API
- browser review UI
- autonomous write-back without explicit approval

These are deferred, not ignored. This spec includes future extension seams where necessary.

---

## Primary Persona

### Solo Technical Operator

One technically capable operator:

- curates source folders
- runs ingest, query, lint, and migration commands
- reviews citations and write-back proposals
- edits project pages when judgment is required
- wants reliable cross-project answers without rediscovering context every session

This persona choice materially simplifies:

- auth and permission design
- collaboration workflows
- approval flows
- rollout strategy
- UI requirements

---

## User Motivation And Success Shape

The operator wants:

- answers to cross-project questions in minutes instead of manual file spelunking
- citations that make the answer inspectable and trustworthy
- durable reports/briefings that do not disappear into chat history
- a retrieval stack that is good enough without becoming operationally heavy
- migration safety for an already-trusted V1 workspace

The operator does **not** want:

- a platform migration disguised as a feature upgrade
- a UI or API surface before the retrieval value is proven
- a knowledge graph project before project-level synthesis works reliably

---

## Phase 2 Summary

Phase 2 should turn `query` from a fixed project-card formatter into a real retrieval-and-synthesis operation.

The new behavior:

1. The user names 2 to 5 projects explicitly.
2. The system retrieves evidence from:
   - maintained project pages
   - latest immutable raw snapshots for those projects
3. Retrieval uses:
   - lexical search via SQLite FTS5
   - semantic search via OpenAI embeddings
   - app-layer fusion ranking
4. The system synthesizes a cited answer using an embedded OpenAI-first model.
5. The system logs the run, evidence decisions, cost, and write-back decision.
6. The system may propose saving the output into durable markdown pages, but only after explicit user approval.

---

## Functional Requirements

### FR1: Multi-Project Query

- The system must support query over **2 to 5 explicitly named projects**.
- The system must reject:
  - zero projects
  - one project for Phase 2 multi-project mode
  - more than five projects
- The system must resolve project identity through canonical slug and known aliases.

### FR2: Hybrid Retrieval

- The system must support lexical retrieval over project pages and snapshot-derived text chunks.
- The system must support semantic retrieval over those same chunkable sources.
- The system must combine both streams in a deterministic app-layer fusion step.
- Retrieval must be scoped only to explicitly named projects.

### FR3: Wiki-First + Snapshot Fallback

- Query must prefer wiki pages first.
- Query may consult the latest immutable snapshot when wiki coverage is incomplete or less relevant.
- Query must never read live source refs during normal query.
- Every answer must disclose whether snapshot fallback was used.

### FR4: Cited Synthesis

- Every non-trivial factual answer must include citations.
- Citations must resolve to:
  - a wiki page section, or
  - a snapshot file span/chunk
- Unsupported claims must not be emitted as grounded facts.
- If grounding is insufficient, the answer must say so explicitly.

### FR5: Manual-Approval Write-Back

- Query may propose durable write-back when the answer is likely to be reused.
- Write-back must require explicit operator approval.
- Write-back targets in this phase are:
  - `wiki/projects/<slug>/overview.md`
  - `wiki/projects/<slug>/decisions.md`
  - `wiki/reports/<YYYY-MM-DD>-<topic>.md`
- Query must not mutate durable wiki pages automatically.

### FR6: Richer Project Pages

- The system must support richer project pages beyond `project-card.md`.
- `overview.md` should hold durable, current project briefings.
- `decisions.md` should hold decision summaries, trade-offs, and changes.
- `project-card.md` remains the orientation anchor and operator-maintained canonical identity page.

### FR7: Derived Retrieval Store

- The system must maintain a derived SQLite database for:
  - page metadata
  - snapshot metadata
  - chunk metadata
  - lexical search
  - embeddings metadata
  - query logs
  - write-back proposal records
- The database is derived and rebuildable.
- Raw snapshots and markdown remain the durable human-facing artifacts.

### FR8: Expanded Lint And Health Checks

- `lint` must continue to own `wiki/indexes/needs-review.md`.
- Phase 2 lint/health must additionally detect:
  - uncited synthesized durable pages
  - citations that no longer resolve
  - stale `overview.md` / `decisions.md`
  - retrieval index drift relative to workspace state
  - write-back proposals left in ambiguous or invalid states
  - missing text extraction for queryable files that should be indexable

### FR9: Query Auditability

- The system must log query runs in both:
  - human-readable markdown
  - structured SQLite tables
- A query record must include:
  - timestamp
  - requested projects
  - user question
  - retrieval configuration
  - whether snapshot fallback was used
  - model info
  - token/cost/latency metadata
  - cited evidence set
  - whether write-back was proposed
  - whether write-back was approved or rejected

### FR10: Side-By-Side Rollout And Migration

- The system must support migration from a V1 workspace to a Phase 2 retrieval-capable workspace without destructive overwrite.
- The system must support building Phase 2 retrieval state from an existing V1 workspace.
- The system must preserve trusted V1 markdown and raw snapshot artifacts.

---

## Non-Functional Requirements

### NFR1: Trust And Explainability

- Answers must be inspectable through stable citations.
- The system must disclose when it fell back to raw snapshots.
- The system must prefer incompleteness over hallucinated certainty.

### NFR2: Determinism

- Given the same workspace state, retrieval indexing must be deterministic.
- Ranking and citation formatting must be deterministic apart from model generation.
- All write-back targets must be explicit and reproducible.

### NFR3: Safety Of Human Curation

- Manual edits to durable markdown must not be silently overwritten.
- Write-back must be staged through a proposal/approval workflow.
- Migration must be non-destructive.

### NFR4: Operational Simplicity

- The first retrieval stack must stay local and operationally lightweight.
- No external search server is allowed in this phase.
- No background daemon is required.

### NFR5: Cost Visibility

- Model usage and embedding costs must be traceable per query/indexing action.
- Configuration must support conservative defaults and opt-in expensive modes.

### NFR6: Performance

- Query latency should be acceptable for solo interactive use.
- Reindex operations may be slower than query, but must provide progress feedback.
- The system must scale to hundreds of projects and thousands of chunks on a single workstation without introducing a separate service tier.

---

## Key User Journeys

### Journey 1: Ask A Cross-Project Question

1. Operator runs `query` with 2 to 5 named projects and a natural-language question.
2. System resolves project identities.
3. System checks retrieval index freshness.
4. System retrieves relevant wiki and snapshot chunks.
5. System synthesizes an answer with citations.
6. System logs the run.
7. System optionally proposes durable write-back if the output looks reusable.

Success condition:

- operator gets a useful answer without manually opening raw files
- operator can inspect the evidence quickly

### Journey 2: Approve A Durable Report

1. Operator reviews a query result and its proposed write-back target.
2. Operator approves saving to a target path.
3. System writes the markdown page.
4. System updates retrieval indexes and logs the decision.
5. Lint can validate the resulting page later.

Success condition:

- useful output becomes durable wiki memory instead of disappearing into chat

### Journey 3: Refresh Retrieval State After Ingest

1. Operator ingests updated project artifacts.
2. System writes raw snapshot and markdown as usual.
3. Retrieval index is rebuilt or incrementally updated.
4. Health checks confirm query readiness.

Success condition:

- query uses fresh evidence without forcing a full workspace rebuild every time

### Journey 4: Migrate A Trusted V1 Workspace

1. Operator runs a migration/reindex command on an existing V1 workspace.
2. System creates Phase 2 retrieval state non-destructively.
3. Operator validates health and test queries.
4. Existing V1 wiki state remains readable and trusted during rollout.

Success condition:

- no data loss
- clear fallback to V1 if Phase 2 state is not yet trusted

---

## First-Time User Experience

### New Workspace

For a brand-new Phase 2 workspace, the operator flow should be:

1. initialize workspace
2. ingest one or more projects
3. build retrieval state
4. run health
5. run the first multi-project query
6. optionally approve one durable write-back

The system should guide the operator clearly when:

- retrieval state has not been built yet
- no queryable chunks exist yet
- model credentials are missing
- only one project was provided to a multi-project query

### Existing V1 Workspace

For a migrated V1 workspace, the operator flow should be:

1. run migration
2. build or validate retrieval state
3. run health
4. run one or two sample queries
5. compare trust and usefulness against V1 behavior before broad adoption

---

## Empty States And Edge Cases

### Empty States

- query invoked before retrieval state exists
- project has no `overview.md` or `decisions.md`
- project snapshot exists but text extraction yielded zero queryable chunks
- no OpenAI API key configured
- write-back proposal requested but no valid destination can be inferred

### Edge Cases

- named projects resolve ambiguously through aliases
- one or more named projects were migrated incompletely
- query asks for comparison but evidence across projects is uneven
- cited snapshot file exists but extracted chunk span is invalid
- `overview.md` has manual edits that conflict with a new write-back proposal
- embedding index exists for some chunks but not others
- query exceeds cost or token budget
- one project has current pages but stale snapshot metadata

For all of these, the system must fail clearly and preserve trust.

---

## Recommended Workspace Shape

Phase 2 extends the current layout:

```text
<workspace>/
├── raw/
├── refs/
├── wiki/
│   ├── projects/
│   │   └── <project-slug>/
│   │       ├── project-card.md
│   │       ├── overview.md
│   │       └── decisions.md
│   ├── reports/
│   │   └── <YYYY-MM-DD>-<topic>.md
│   └── indexes/
├── logs/
│   ├── ingest-log.md
│   ├── lint-log.md
│   └── query-log.md
├── schema/
├── state/
│   └── index.db
└── cache/
    └── extraction/
```

Notes:

- `state/index.db` is derived and rebuildable.
- `cache/extraction/` is optional derived text extraction cache.
- `wiki/reports/` is the home for durable cross-project outputs in this phase.

---

## Page Ownership Model

To avoid silent scope drift and accidental overwrite, page ownership must be explicit.

### Operator-Curated Anchor Pages

- `project-card.md`

Rules:

- remains the canonical orientation anchor
- may be edited directly by the operator
- automated updates must remain conservative

### Mixed-Ownership Durable Pages

- `overview.md`
- `decisions.md`

Rules:

- may be created or updated through approved write-back
- must preserve existing operator judgment unless the approved update explicitly replaces it

### Machine-Originated Durable Pages

- `wiki/reports/*.md`

Rules:

- can be created through approved write-back
- may be regenerated or amended through later approved write-backs
- must still retain citations and audit traceability

---

## Retrieval Architecture

### Recommendation

Use:

- **SQLite FTS5** for lexical retrieval
- **OpenAI embeddings** for semantic retrieval
- **application-layer fusion ranking**

This is the recommended resolution because:

- it satisfies hybrid retrieval from day one
- it fits the OpenAI-first embedded model choice
- it avoids introducing an external retrieval service
- it keeps rollout and debugging manageable for a solo operator

### Why Not Other Options Yet

- Markdown/index-only retrieval is too weak for the desired value target.
- Provider-agnostic vector infrastructure adds complexity before the product value is proven.
- Local embedding models are viable later, but are not necessary in the first implementation wave.

### Retrieval Flow

1. Resolve named projects.
2. Collect candidate sources:
   - `project-card.md`
   - `overview.md`
   - `decisions.md`
   - approved `wiki/reports/` pages that reference the projects
   - latest snapshot-derived text chunks for those projects
3. Run lexical retrieval in FTS5.
4. Compute query embedding and semantic similarity against candidate chunks.
5. Fuse lexical and semantic scores in the app layer.
6. Select top evidence set.
7. Pass the evidence set into synthesis.

### Semantic Index Scope

The system does **not** need ANN/vector-DB infrastructure in this phase.

Reason:

- query is constrained to 2 to 5 explicitly named projects
- candidate corpus sizes are small enough for app-layer vector scoring over filtered chunks
- this keeps the system simpler and more inspectable

---

## Synthesis And Citation Design

### Synthesis Rules

- Synthesis must only use retrieved evidence passed into the model call.
- Unsupported claims must be labeled as uncertainty or omitted.
- The answer should separate:
  - supported conclusions
  - unresolved gaps
  - recommended next checks when evidence is thin

### Citation Rules

- Every material claim in the answer must have at least one citation.
- Citation targets:
  - wiki page path + heading/section locator
  - snapshot id + relative path + chunk/span locator
- Citation formatting must be stable and machine-checkable.

### Snapshot Provenance Model

Each snapshot citation should resolve through:

- `project_slug`
- `snapshot_id`
- `relative_path`
- `chunk_id`
- `content_hash`
- optional `line_start`, `line_end`, or equivalent span locator

This ensures evidence remains stable even if the live source moves later.

---

## Write-Back Design

### Durable Targets

#### Project-Specific Durable Targets

- `wiki/projects/<project-slug>/overview.md`
- `wiki/projects/<project-slug>/decisions.md`

#### Cross-Project Durable Targets

- `wiki/reports/<YYYY-MM-DD>-<topic>.md`

### Write-Back Approval Flow

1. Query finishes with answer and citations.
2. System evaluates whether the output is likely reusable.
3. System proposes:
   - target path
   - page type
   - one-paragraph reason for saving
4. Operator explicitly approves or rejects.
5. If approved:
   - page is written
   - retrieval index is updated
   - query log records the outcome

### Overwrite Rules

- The system must never silently replace a manually curated page.
- If a write-back target already exists:
  - the system proposes append/update semantics
  - the operator must confirm

---

## CLI Contracts

This phase remains CLI-first. No public API is required.

### Existing Commands To Preserve

- `init`
- `ingest`
- `query`
- `rebuild-indexes`
- `lint`

`rebuild-indexes` must remain limited to markdown navigation pages.
It must not become the retrieval rebuild command.

### Phase 2 Command Surface

#### `query`

Example:

```bash
uv run llm-wiki query \
  --workspace /path/to/wiki \
  --project hcv \
  --project notion-sync \
  --question "How do these projects differ in operational maturity?"
```

Required behavior:

- accepts 2 to 5 projects in Phase 2 multi-project mode
- accepts a natural-language question
- returns:
  - answer
  - citations
  - evidence summary
  - write-back proposal if applicable

#### `rebuild-retrieval`

Example:

```bash
uv run llm-wiki rebuild-retrieval --workspace /path/to/wiki
```

Required behavior:

- rebuilds derived retrieval state from markdown + snapshots
- does not modify raw snapshots
- does not rewrite human markdown except derived machine-owned artifacts if defined
- is the canonical command for rebuilding SQLite retrieval state, FTS indexes, embeddings state, and retrieval metadata

#### `migrate-workspace`

Example:

```bash
uv run llm-wiki migrate-workspace \
  --workspace /path/to/wiki \
  --target-version 2
```

Required behavior:

- creates Phase 2 retrieval state from a V1 workspace
- is non-destructive
- performs compatibility checks

#### `approve-writeback`

Example:

```bash
uv run llm-wiki approve-writeback \
  --workspace /path/to/wiki \
  --proposal-id qry_20260505_001
```

Required behavior:

- applies a pending write-back proposal
- updates indexes/retrieval state
- records audit outcome

#### `health`

Example:

```bash
uv run llm-wiki health --workspace /path/to/wiki
```

Required behavior:

- validates retrieval readiness, citation integrity, and schema compatibility

---

## Internal Service Contracts

These are internal interfaces, not public APIs.

### `TextExtractionService`

Responsibilities:

- extract queryable text from allowed source artifacts
- normalize text into chunkable units
- record extraction status and failures

### `RetrievalIndexService`

Responsibilities:

- materialize SQLite rows for pages, snapshots, files, chunks, and embeddings
- maintain FTS5 indexes
- maintain embedding freshness state

### `RetrievalService`

Responsibilities:

- resolve project scopes
- run lexical retrieval
- run semantic retrieval
- fuse scores
- return ordered evidence set

### `SynthesisService`

Responsibilities:

- assemble prompt input from ordered evidence
- call OpenAI-first model
- enforce answer structure and citation rules

### `CitationResolver`

Responsibilities:

- map claims and evidence to stable citation strings
- validate that citations resolve

### `WriteBackService`

Responsibilities:

- detect durable output candidates
- generate proposal metadata
- apply approved writes safely

### `WorkspaceMigrationService`

Responsibilities:

- detect workspace version
- backfill Phase 2 retrieval state
- preserve V1 artifacts

### `HealthCheckService`

Responsibilities:

- detect retrieval drift
- detect citation failures
- detect config/version incompatibilities

---

## Database Schema Design

SQLite is a **derived local index**, not the source of truth.

### Recommended Core Tables

#### `workspace_meta`

- `workspace_version`
- `schema_version`
- `created_at`
- `migrated_at`

#### `projects`

- `project_slug`
- `project_name`
- `owner`
- `status`
- `canonical_project_card_path`
- `last_ingested`
- `last_indexed`

#### `wiki_pages`

- `page_id`
- `project_slug` nullable for cross-project reports
- `page_type` (`project_card`, `overview`, `decisions`, `report`)
- `path`
- `title`
- `content_hash`
- `last_modified`
- `manual_edit_detected`

#### `snapshots`

- `snapshot_id`
- `project_slug`
- `snapshot_path`
- `ingested_at`
- `source_root`

#### `snapshot_files`

- `file_id`
- `snapshot_id`
- `relative_path`
- `file_type`
- `sha256`
- `text_extract_status`
- `text_extract_error` nullable

#### `chunks`

- `chunk_id`
- `source_kind` (`wiki_page`, `snapshot_file`)
- `page_id` nullable
- `file_id` nullable
- `project_slug`
- `chunk_text`
- `content_hash`
- `line_start` nullable
- `line_end` nullable
- `token_count`

#### `fts_chunks`

SQLite FTS5 virtual table over chunk text and relevant metadata.

#### `embeddings`

- `chunk_id`
- `provider`
- `model`
- `dimensions`
- `vector_blob`
- `embedded_at`

#### `query_runs`

- `query_id`
- `asked_at`
- `question_text`
- `requested_projects`
- `model_provider`
- `model_name`
- `used_snapshot_fallback`
- `status`
- `token_input`
- `token_output`
- `cost_estimate`
- `latency_ms`

#### `query_evidence`

- `query_id`
- `chunk_id`
- `lexical_score`
- `semantic_score`
- `fused_score`
- `rank`

#### `writeback_proposals`

- `proposal_id`
- `query_id`
- `target_path`
- `target_page_type`
- `proposal_reason`
- `status` (`pending`, `approved`, `rejected`, `applied`, `failed`)
- `reviewed_at` nullable

### Migration Strategy

- use explicit schema versioning
- apply forward-only migrations for the derived DB
- support full DB rebuild from workspace artifacts if migration fails

---

## Prompt Templates

These are phase-level contracts, not final wording locks.

### Query Synthesis Prompt

**System prompt**

```text
You are the llm-wiki query synthesizer.
Answer only from the supplied evidence set.
Prefer the maintained wiki when it is sufficient.
Use snapshot evidence only when it adds necessary support or fills a gap.
Do not state unsupported claims as facts.
Every material factual claim must cite one or more evidence items.
If evidence is incomplete or conflicting, say so explicitly.
```

**User payload template**

```text
Question:
{{question}}

Projects:
{{project_list}}

Evidence items:
{{ordered_evidence}}

Required output:
1. Answer
2. Key differences / conclusions
3. Known gaps or weak evidence
4. Citations inline
5. Write-back suitability: yes/no with one-line reason
```

### Write-Back Proposal Prompt

**System prompt**

```text
You decide whether a query result deserves durable storage in the wiki.
Only recommend write-back when the output is likely to be reused.
Pick the smallest correct durable target.
Never recommend overwriting a manually curated page without explicit operator review.
```

**User payload template**

```text
Query result:
{{answer}}

Projects:
{{project_list}}

Candidate durable targets:
- per-project overview
- per-project decisions
- cross-project report

Return:
- recommended target path
- target page type
- short reason
- append/update/new recommendation
```

### Durable Page Update Prompt

**System prompt**

```text
Update the target markdown page conservatively.
Preserve existing human judgment unless the new evidence clearly improves the page.
Keep claims cited.
Do not invent facts not present in the provided evidence.
```

---

## Expanded Lint And Health Rules

### Keep Existing V1 Rules

- unknown owner
- unknown status
- missing next steps
- stale project card
- contradictory status
- duplicate slugs
- missing live refs
- orphan cards

### Add Phase 2 Rules

- `overview.md` missing for projects that have approved write-back history
- `decisions.md` missing for projects with saved decision write-backs
- query-generated report missing citations
- citation resolves to missing page/chunk/span
- retrieval DB schema version mismatch
- FTS index drift relative to chunk table
- chunk exists without embedding where semantic retrieval is required
- write-back proposal stuck in `pending` too long
- report references projects that do not match its frontmatter

---

## Configuration

Configuration should remain workspace-local and explicit.

### Required Config Areas

- OpenAI API key source
- query model name
- embedding model name
- chunk size / overlap
- lexical/semantic fusion weights
- top-k retrieval counts
- max query cost budget
- write-back enablement
- migration safety flags

### Recommended Config Files

- `schema/workspace-config.yaml`
- `schema/retrieval-config.yaml`
- `schema/prompt-contracts.md`

### Secret Handling

- API keys must not be written into the workspace
- environment variables or local secret managers are acceptable
- logs must never emit secrets

---

## Rollout Strategy

### Recommendation

Use a **side-by-side, versioned rollout**.

### Rollout Steps

1. introduce workspace/schema versioning
2. ship migration and retrieval rebuild commands
3. enable Phase 2 retrieval on a copied or explicitly migrated workspace
4. validate health checks and sample queries
5. only then treat the Phase 2 path as primary

### Rollback

- existing V1 markdown and snapshots remain valid
- derived DB can be deleted and rebuilt
- migration must not destroy trusted V1 artifacts

---

## Risk Mitigation

### Hallucinated Synthesis

Mitigation:

- answer only from retrieved evidence set
- require citations
- add unsupported-claim evals

### Manual Edit Loss

Mitigation:

- no automatic write-back
- conservative page update prompt
- proposal state machine

### Cost Blow-Up

Mitigation:

- project scope limited to 2 to 5 explicit projects
- log query cost
- cap semantic candidate sizes

### Retrieval Drift

Mitigation:

- health checks
- retrieval rebuild command
- content-hash-based invalidation

### Migration Corruption

Mitigation:

- side-by-side rollout
- explicit schema version checks
- rebuildable derived DB

---

## Testing And Verification Plan

Verification is a core product requirement for this phase.

### Unit Tests

Cover:

- alias and project resolution
- chunk generation
- FTS indexing
- fusion score calculation
- citation formatting and validation
- write-back routing
- migration version checks

### Integration Tests

Cover:

- ingest -> retrieval rebuild -> query
- query -> write-back proposal -> approval -> page update
- migration from V1 workspace -> retrieval-ready Phase 2 state
- lint/health against mixed fresh/stale workspaces

### CLI End-To-End Tests

Use subprocess-driven CLI tests to verify:

- correct stdout/stderr behavior
- non-zero exits on invalid query/project counts
- health and migration flows
- write-back approval/rejection behavior

This replaces browser E2E for this phase, because there is no UI.

### Golden Tests

Cover:

- rendered `overview.md`
- rendered `decisions.md`
- rendered `wiki/reports/*.md`
- citation formatting
- query-log markdown shape

### Property-Based Tests

Use Hypothesis for:

- alias normalization
- chunk span normalization
- provenance round-trip invariants
- write-back target routing

### Evals

Maintain a versioned eval dataset with:

- named project sets
- user questions
- expected evidence projects
- expected durable target recommendation
- acceptable cited answer fragments

Evaluate:

- citation precision
- citation coverage
- unsupported-claim rate
- retrieval hit quality
- write-back recommendation quality

### Health Checks

The system must support a CLI health pass for:

- DB schema integrity
- FTS consistency
- unresolved citations
- missing embedding rows
- stale retrieval state

---

## Success Criteria

Phase 2 is successful when all of the following are true:

1. A solo operator can ask a cross-project question over 2 to 5 named projects and get a cited answer without manual file hunting.
2. The answer clearly discloses whether snapshot fallback was used.
3. The operator can approve durable write-back into project pages or cross-project reports.
4. Retrieval state can be rebuilt from workspace artifacts.
5. Existing V1 workspaces can be migrated non-destructively.
6. Lint and health checks can catch citation and retrieval integrity issues.
7. Automated tests and evals show acceptable grounding quality and migration safety.

---

## Future Extension Notes

These are explicitly deferred from this phase.

### Public API

No public API is required in this phase.

Future extension:

- expose internal services through a local HTTP/JSON API if non-CLI consumers emerge

### UI / Frontend

No frontend is required in this phase.

Future extension candidates:

- workspace health dashboard
- query history browser
- write-back review screen
- citation drill-down page

If a future UI is added, recommended route families are:

- `/projects/:slug`
- `/reports/:report_id`
- `/queries/:query_id`
- `/health`
- `/writeback/:proposal_id`

State management and routing are therefore **not applicable in this phase**, but these extension points are reserved intentionally.

### Entity And Graph Layer

Entity pages, relationship hubs, and graph navigation are deferred until project-level retrieval and write-back prove their value.

---

## Decision Log

| Topic | Options Considered | Chosen Option | Rationale |
| --- | --- | --- | --- |
| Product boundary | CLI-only, headless platform, full product surface | CLI-first with future extension seams | Matches solo-operator usage and avoids premature platform work. |
| Query evidence boundary | strict wiki-only, wiki + snapshot fallback, adaptive with live refs | wiki-first + latest snapshot fallback | Preserves compiled memory while allowing materially better answers. |
| Primary persona | solo operator, small technical team, mixed team, broad self-serve | solo technical operator | Simplifies approval, rollout, config, and UX assumptions. |
| Knowledge model | project-centric, multi-entity, episode-centric | project-centric plus richer project pages | Best fit for immediate value without graph overreach. |
| Highest-value gap | richer query, write-back, maintenance, navigation | richer query answers | Strongest direct operator value. |
| Query scope | single-project, selected multi-project, workspace-wide | selected multi-project | Gives cross-project value without open-ended retrieval complexity. |
| Write-back mode | none, manual approval, automatic | manual approval | Adds compounding memory while preserving trust. |
| Retrieval baseline | markdown-only, derived local index, full hybrid | hybrid from day one | Required for desired answer quality. |
| Model execution | agent-assisted, embedded calls, dual mode | embedded OpenAI-first calls | Needed for CLI-native synthesis and prompt/eval contracts. |
| Derived store | no DB, SQLite derived store, optional cache only | SQLite derived store | Strongest balance of simplicity, inspectability, and retrieval needs. |
| Modalities | text-first, text + PDF-native, multimodal | text-first | Keeps the first phase verifiable and focused. |
| Entity pages | none yet, lightweight, full entity layer | none yet | Avoids front-loading graph complexity before query value is proven. |
| Public API | none, local API, MCP-first | no public API in this phase | Keeps the phase aligned with CLI-first delivery. |
| Rollout | side-by-side, in-place, fresh-workspace only | side-by-side versioned rollout | Safest migration path for an already-trusted workspace. |
| Provider strategy | OpenAI-first, provider-agnostic, agent-runtime-bound | OpenAI-first with abstraction seam | Minimizes early complexity while leaving room for later adapters. |
| Semantic retrieval implementation | local embeddings, OpenAI embeddings, vector DB | OpenAI embeddings in Phase 2 | Best fit with OpenAI-first and avoids another model stack before value is proven. |
| Cross-project write-back location | force into one project, cross-project reports, transient only | `wiki/reports/` | Cross-project memory needs a durable home that is not semantically tied to one project. |

---

## Final Recommendation

Implement Phase 2 as a **retrieval-engine phase**, not a platform phase.

The system should:

- stay CLI-first
- keep project pages as the durable wiki surface
- add a derived SQLite retrieval store
- support cited multi-project synthesis over named projects
- allow manual-approval durable write-back
- ship with explicit migration, health, and eval support

This is the smallest coherent step that materially advances `llm-wiki` toward a richer LLM-maintained wiki without losing the trust and inspectability of V1.
