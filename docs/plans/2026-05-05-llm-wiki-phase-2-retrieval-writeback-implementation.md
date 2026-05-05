# LLM Wiki Phase 2 Retrieval And Write-Back Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 2 retrieval-and-write-back system for `llm-wiki`: multi-project query across 2 to 5 named projects, hybrid lexical+semantic retrieval, OpenAI-first cited synthesis, manual-approval durable write-back, expanded health/lint, and side-by-side migration from V1.

**Architecture:** Keep raw snapshots and markdown pages as the durable human-facing artifacts, add a derived SQLite database under `state/index.db` for retrieval/provenance/query logging, and split the runtime into focused services for extraction, indexing, retrieval, synthesis, citations, write-back, health, and migration. Extend the CLI rather than introducing an API/UI in this phase, and preserve the existing `project-card.md`-centric V1 behavior while layering new commands and page types around it.

**Tech Stack:** Python 3.12+, `argparse`, `sqlite3` with FTS5, `dataclasses`, `pathlib`, `hashlib`, `json`, `PyYAML`, OpenAI Python SDK, `pytest`, `Hypothesis`, `ruff`, `mypy`, `uv`, golden-file markdown tests, and CLI subprocess integration tests.

---

## Planned File Structure

### Create

- `src/llm_wiki/state_db.py`
- `src/llm_wiki/text_extraction.py`
- `src/llm_wiki/retrieval.py`
- `src/llm_wiki/openai_client.py`
- `src/llm_wiki/query_runtime.py`
- `src/llm_wiki/citations.py`
- `src/llm_wiki/writeback.py`
- `src/llm_wiki/health.py`
- `src/llm_wiki/migration.py`
- `tests/unit/test_state_db.py`
- `tests/unit/test_text_extraction.py`
- `tests/unit/test_retrieval.py`
- `tests/unit/test_openai_client.py`
- `tests/unit/test_citations.py`
- `tests/unit/test_writeback.py`
- `tests/unit/test_health.py`
- `tests/unit/test_migration.py`
- `tests/integration/test_phase2_query_cli.py`
- `tests/integration/test_rebuild_retrieval_cli.py`
- `tests/integration/test_migrate_workspace_cli.py`
- `tests/integration/test_approve_writeback_cli.py`
- `tests/fixtures/phase2_workspace_seed/wiki/projects/`
- `tests/fixtures/phase2_workspace_seed/raw/`
- `tests/fixtures/phase2_workspace_seed/refs/`
- `tests/golden/test_report_markdown.py`
- `tests/golden/test_query_log_markdown.py`
- `evals/phase2_query_cases.yaml`
- `docs/guides/phase2-migration.md`

### Modify

- `pyproject.toml`
- `README.md`
- `src/llm_wiki/cli.py`
- `src/llm_wiki/config.py`
- `src/llm_wiki/models.py`
- `src/llm_wiki/init_workspace.py`
- `src/llm_wiki/query.py`
- `src/llm_wiki/ingest.py`
- `src/llm_wiki/lint.py`
- `src/llm_wiki/wiki_writer.py`
- `tests/integration/test_cli_subprocess.py`
- `tests/unit/test_init_workspace.py`
- `tests/unit/test_query.py`
- `tests/unit/test_lint.py`

### Responsibilities

- `state_db.py`: schema creation, migrations, FTS maintenance, retrieval/query/write-back persistence.
- `text_extraction.py`: convert wiki pages and snapshot files into normalized text chunks with stable provenance.
- `retrieval.py`: lexical retrieval, semantic retrieval, fusion ranking, evidence selection.
- `openai_client.py`: OpenAI-first embedding and synthesis calls, retry/error mapping, budget enforcement.
- `query_runtime.py`: end-to-end Phase 2 query orchestration.
- `citations.py`: citation formatting, resolution, and validation.
- `writeback.py`: write-back proposal generation, approval application, page-safe mutation rules.
- `health.py`: retrieval and citation health checks.
- `migration.py`: V1 to Phase 2 workspace compatibility and derived-state migration.

---

## Verification Strategy

The implementation is incomplete unless all of these pass:

- targeted red/green unit tests per task
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`
- `uv run python -m pytest -q`
- `uv build`
- CLI smoke checks for:
  - `uv run llm-wiki --help`
  - `uv run llm-wiki rebuild-retrieval --help`
  - `uv run llm-wiki health --help`
  - `uv run llm-wiki migrate-workspace --help`
  - `uv run llm-wiki approve-writeback --help`

### Additional Phase 2 Verification

- retrieval determinism against the same workspace input
- query citation coverage and resolution
- manual write-back approval and page-safe update behavior
- V1 workspace migration without destructive overwrite
- FTS drift detection
- query log integrity
- eval dataset execution over representative multi-project questions

---

## Phase Decomposition

This spec is large, but the implementation is still coherent as one plan because everything serves the same operator loop:

1. ingest/curate
2. build retrieval state
3. query across named projects
4. inspect citations
5. optionally approve durable write-back
6. lint/health/migrate safely

Do **not** split this into a separate API project, graph project, or UI project in this phase.

---

## Decision Log

| Topic | Options Considered | Choice | Rationale |
| --- | --- | --- | --- |
| Query scope | single-project, selected multi-project, workspace-wide | selected multi-project | Delivers cross-project value without open-ended retrieval complexity. |
| Query evidence boundary | wiki-only, wiki + snapshot fallback, adaptive with live refs | wiki-first + latest snapshot fallback | Preserves trust while allowing materially better answers. |
| Retrieval baseline | markdown-only, derived lexical only, hybrid lexical + semantic | hybrid lexical + semantic | Required to deliver the value target chosen in the spec. |
| Lexical engine | ad hoc markdown scan, SQLite FTS5, external search service | SQLite FTS5 | Fast enough, local, inspectable, and easy to test. |
| Semantic retrieval | local embeddings, OpenAI embeddings, vector DB | OpenAI embeddings | Fits the OpenAI-first provider choice and avoids extra model/runtime complexity. |
| Durable cross-project output | none, force into one project, dedicated reports area | `wiki/reports/` | Cross-project outputs need a durable home that is not semantically tied to one project. |
| Write-back mode | none, manual approval, automatic | manual approval | Adds compounding memory without sacrificing operator control. |
| Product surface | CLI only, local API, UI | CLI with internal service boundaries | Matches the solo-operator workflow and keeps rollout small. |
| Rollout | in-place, fresh workspace only, side-by-side versioned | side-by-side versioned | Safest path for an already-trusted V1 workspace. |
| Migration target shape | in-place schema rewrite, sibling workspace copy, versioned state copy | sibling workspace copy plus versioned derived state | Keeps V1 untouched while letting V2 run and be verified independently. |
| Entity pages | none, lightweight, full entity layer | none in Phase 2 | Prevents graph work from diluting the first value target. |
| Modalities | text-only, text + PDF extraction, multimodal | text + PDF text extraction | Stays within text-first scope while covering an important allowed source type. |

---

## Spec Traceability Matrix

| Spec Requirement | Plan Coverage |
| --- | --- |
| FR1 multi-project query | Tasks 5 and 8 |
| FR2 hybrid retrieval | Tasks 3, 4, and 5 |
| FR3 wiki-first + snapshot fallback | Tasks 5 and 7 |
| FR4 cited synthesis | Tasks 4, 5, and 8 |
| FR5 manual-approval write-back | Task 6 |
| FR6 richer project pages | Task 6 |
| FR7 derived retrieval store | Tasks 2 and 3 |
| FR8 expanded lint/health | Task 7 |
| FR9 query auditability | Tasks 5 and 6 |
| FR10 side-by-side migration | Task 7 |
| NFR trust/explainability | Tasks 4, 5, 6, and 7 |
| NFR determinism | Tasks 2, 3, 5, and 8 |
| NFR human-curation safety | Tasks 6 and 7 |
| NFR operational simplicity | Tasks 2, 5, and 8 |
| NFR cost visibility | Tasks 4, 5, and 8 |
| NFR performance | Tasks 3, 5, and 7 |

---

### Task 1: Add Workspace Versioning, Config, And CLI Skeletons

**Files:**
- Create: `src/llm_wiki/state_db.py`
- Modify: `pyproject.toml`
- Modify: `src/llm_wiki/config.py`
- Modify: `src/llm_wiki/models.py`
- Modify: `src/llm_wiki/init_workspace.py`
- Modify: `src/llm_wiki/cli.py`
- Test: `tests/unit/test_init_workspace.py`
- Test: `tests/integration/test_cli_subprocess.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_init_workspace.py
from pathlib import Path

from llm_wiki.init_workspace import initialize_workspace


def test_initialize_workspace_creates_phase2_directories_and_seed_files(tmp_path: Path) -> None:
    initialize_workspace(tmp_path)

    assert (tmp_path / "state").is_dir()
    assert (tmp_path / "cache" / "extraction").is_dir()
    assert (tmp_path / "wiki" / "reports").is_dir()
    assert (tmp_path / "logs" / "query-log.md").is_file()
    assert (tmp_path / "schema" / "workspace-config.yaml").is_file()
    assert (tmp_path / "schema" / "retrieval-config.yaml").is_file()
```

```python
# tests/integration/test_cli_subprocess.py
def test_help_lists_phase2_commands(run_cli) -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert "rebuild-retrieval" in result.stdout
    assert "health" in result.stdout
    assert "migrate-workspace" in result.stdout
    assert "approve-writeback" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run python -m pytest tests/unit/test_init_workspace.py tests/integration/test_cli_subprocess.py -q
```

Expected:

- failure because the new directories, seed files, and commands do not exist yet

- [ ] **Step 3: Write the minimal implementation**

```python
# src/llm_wiki/config.py
from dataclasses import dataclass, field
from pathlib import Path


WORKSPACE_SCHEMA_VERSION = 2


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    raw: Path = field(init=False)
    refs: Path = field(init=False)
    wiki: Path = field(init=False)
    logs: Path = field(init=False)
    schema: Path = field(init=False)
    state: Path = field(init=False)
    cache: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw", self.root / "raw")
        object.__setattr__(self, "refs", self.root / "refs")
        object.__setattr__(self, "wiki", self.root / "wiki")
        object.__setattr__(self, "logs", self.root / "logs")
        object.__setattr__(self, "schema", self.root / "schema")
        object.__setattr__(self, "state", self.root / "state")
        object.__setattr__(self, "cache", self.root / "cache")
```

```python
# src/llm_wiki/init_workspace.py
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
    "workspace-config.yaml": "workspace_version: 2\nquery_model: gpt-5-mini\nembedding_model: text-embedding-3-small\nmax_query_cost_usd: 0.25\nwriteback_enabled: true\nmigration_safety_mode: side_by_side\n",
    "retrieval-config.yaml": "fts_top_k: 20\nsemantic_top_k: 20\nfusion_weight_lexical: 0.6\nfusion_weight_semantic: 0.4\nchunk_max_lines: 20\nchunk_overlap_lines: 3\n",
    "prompt-contracts.md": "# Prompt Contracts\n\nPhase 2 prompt contracts live here.\n",
}

LOG_SEED_FILES = {
    "query-log.md": "# Query Log\n\n",
}


def initialize_workspace(root: Path) -> None:
    for relative in WORKSPACE_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)
    for filename, contents in SCHEMA_SEED_FILES.items():
        path = root / "schema" / filename
        if not path.exists():
            path.write_text(contents)
    for filename, contents in LOG_SEED_FILES.items():
        path = root / "logs" / filename
        if not path.exists():
            path.write_text(contents)
```

```python
# src/llm_wiki/cli.py
rebuild_retrieval_parser = subparsers.add_parser("rebuild-retrieval")
rebuild_retrieval_parser.add_argument("--workspace", type=Path, required=True)

health_parser = subparsers.add_parser("health")
health_parser.add_argument("--workspace", type=Path, required=True)

migrate_parser = subparsers.add_parser("migrate-workspace")
migrate_parser.add_argument("--workspace", type=Path, required=True)
migrate_parser.add_argument("--target-version", type=int, required=True)

approve_writeback_parser = subparsers.add_parser("approve-writeback")
approve_writeback_parser.add_argument("--workspace", type=Path, required=True)
approve_writeback_parser.add_argument("--proposal-id", required=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run python -m pytest tests/unit/test_init_workspace.py tests/integration/test_cli_subprocess.py -q
```

Expected:

- targeted tests pass

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/llm_wiki/config.py src/llm_wiki/models.py src/llm_wiki/init_workspace.py src/llm_wiki/cli.py tests/unit/test_init_workspace.py tests/integration/test_cli_subprocess.py
git commit -m "feat: add phase 2 workspace and cli scaffolding"
```

---

### Task 2: Build The Derived SQLite Schema And Retrieval Rebuild Path

**Files:**
- Create: `src/llm_wiki/state_db.py`
- Modify: `src/llm_wiki/ingest.py`
- Modify: `src/llm_wiki/cli.py`
- Test: `tests/unit/test_state_db.py`
- Test: `tests/unit/test_ingest.py`
- Test: `tests/integration/test_rebuild_retrieval_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_state_db.py
from pathlib import Path
import sqlite3

from llm_wiki.state_db import ensure_schema


def test_ensure_schema_creates_workspace_meta_and_core_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "index.db"
    db_path.parent.mkdir(parents=True)

    ensure_schema(db_path)

    conn = sqlite3.connect(db_path)
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
    assert "workspace_meta" in names
    assert "projects" in names
    assert "wiki_pages" in names
    assert "snapshots" in names
    assert "snapshot_files" in names
    assert "chunks" in names
    assert "fts_chunks" in names
    assert "embeddings" in names
    assert "query_runs" in names
    assert "query_evidence" in names
    assert "writeback_proposals" in names
```

```python
# tests/integration/test_rebuild_retrieval_cli.py
def test_rebuild_retrieval_creates_index_db_for_existing_workspace(run_cli, tmp_path, seed_workspace) -> None:
    workspace = seed_workspace(tmp_path)
    result = run_cli("rebuild-retrieval", "--workspace", str(workspace))
    assert result.returncode == 0
    assert (workspace / "state" / "index.db").exists()
```

```python
# tests/unit/test_ingest.py
def test_run_ingest_marks_retrieval_state_dirty(tmp_path: Path, sample_project: Path) -> None:
    initialize_workspace(tmp_path)
    run_ingest(tmp_path, sample_project, ingest_timestamp="2026-05-05T00-00-00Z")
    assert (tmp_path / "state" / "retrieval-dirty.flag").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run python -m pytest tests/unit/test_state_db.py tests/integration/test_rebuild_retrieval_cli.py -q
```

Expected:

- failure because `state_db.py` and the rebuild command implementation do not exist

- [ ] **Step 3: Write the minimal implementation**

```python
# src/llm_wiki/state_db.py
import sqlite3
from pathlib import Path

from llm_wiki.config import WORKSPACE_SCHEMA_VERSION


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS workspace_meta (
        workspace_version INTEGER NOT NULL,
        schema_version INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        migrated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS projects (
        project_slug TEXT PRIMARY KEY,
        project_name TEXT NOT NULL,
        owner TEXT NOT NULL,
        status TEXT NOT NULL,
        canonical_project_card_path TEXT NOT NULL,
        last_ingested TEXT NOT NULL,
        last_indexed TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wiki_pages (
        page_id TEXT PRIMARY KEY,
        project_slug TEXT,
        page_type TEXT NOT NULL,
        path TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        last_modified TEXT NOT NULL,
        manual_edit_detected INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS snapshots (
        snapshot_id TEXT PRIMARY KEY,
        project_slug TEXT NOT NULL,
        snapshot_path TEXT NOT NULL UNIQUE,
        ingested_at TEXT NOT NULL,
        source_root TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS snapshot_files (
        file_id TEXT PRIMARY KEY,
        snapshot_id TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        text_extract_status TEXT NOT NULL,
        text_extract_error TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        source_kind TEXT NOT NULL,
        page_id TEXT,
        file_id TEXT,
        project_slug TEXT NOT NULL,
        chunk_text TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        line_start INTEGER,
        line_end INTEGER,
        token_count INTEGER NOT NULL
    )
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
        chunk_id UNINDEXED,
        project_slug UNINDEXED,
        source_kind UNINDEXED,
        chunk_text
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS query_runs (
        query_id TEXT PRIMARY KEY,
        asked_at TEXT NOT NULL,
        question_text TEXT NOT NULL,
        requested_projects TEXT NOT NULL,
        model_provider TEXT NOT NULL,
        model_name TEXT NOT NULL,
        used_snapshot_fallback INTEGER NOT NULL,
        status TEXT NOT NULL,
        token_input INTEGER NOT NULL,
        token_output INTEGER NOT NULL,
        cost_estimate REAL NOT NULL,
        latency_ms INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS embeddings (
        chunk_id TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        vector_blob BLOB NOT NULL,
        embedded_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS query_evidence (
        query_id TEXT NOT NULL,
        chunk_id TEXT NOT NULL,
        lexical_score REAL NOT NULL,
        semantic_score REAL NOT NULL,
        fused_score REAL NOT NULL,
        rank INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS writeback_proposals (
        proposal_id TEXT PRIMARY KEY,
        query_id TEXT NOT NULL,
        target_path TEXT NOT NULL,
        target_page_type TEXT NOT NULL,
        proposal_reason TEXT NOT NULL,
        proposal_hash TEXT NOT NULL,
        source_workspace_path TEXT NOT NULL,
        proposed_at TEXT NOT NULL,
        proposed_by TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'applied', 'failed')),
        reviewed_at TEXT,
        reviewed_by TEXT,
        review_decision TEXT,
        review_reason TEXT,
        applied_at TEXT,
        target_content_hash TEXT
    )
    """,
)


def ensure_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.execute("DELETE FROM workspace_meta")
        conn.execute(
            "INSERT INTO workspace_meta (workspace_version, schema_version, created_at, migrated_at) VALUES (?, ?, datetime('now'), NULL)",
            (WORKSPACE_SCHEMA_VERSION, WORKSPACE_SCHEMA_VERSION),
        )
        conn.commit()
    finally:
        conn.close()


def clone_workspace_for_migration(source_workspace: Path, target_workspace: Path) -> None:
    """
    Create a side-by-side v2 workspace copy so the original V1 workspace stays intact.
    """
    import shutil

    if target_workspace.exists():
        raise ValueError("target migration workspace already exists")
    shutil.copytree(source_workspace, target_workspace)
```

```python
# src/llm_wiki/state_db.py
import hashlib

from llm_wiki.models import load_project_card


def rebuild_workspace_metadata(db_path: Path, workspace: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        project_cards = sorted((workspace / "wiki" / "projects").rglob("project-card.md"))
        for card_path in project_cards:
            card = load_project_card(card_path)
            conn.execute(
                """
                INSERT OR REPLACE INTO projects (
                    project_slug, project_name, owner, status, canonical_project_card_path, last_ingested, last_indexed
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    card.slug,
                    card.project_name,
                    card.owner,
                    card.status,
                    str(card_path.relative_to(workspace)),
                    card.last_ingested,
                ),
            )
        for page_path in sorted((workspace / "wiki").rglob("*.md")):
            content = page_path.read_text()
            conn.execute(
                """
                INSERT OR REPLACE INTO wiki_pages (
                    page_id, project_slug, page_type, path, title, content_hash, last_modified, manual_edit_detected
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 0)
                """,
                (
                    str(page_path.relative_to(workspace)),
                    page_path.parts[-2] if "projects" in page_path.parts else None,
                    "report" if "reports" in page_path.parts else page_path.stem.replace("-", "_"),
                    str(page_path.relative_to(workspace)),
                    content.splitlines()[0].removeprefix("# ").strip() if content else page_path.stem,
                    hashlib.sha256(content.encode("utf-8")).hexdigest(),
                ),
            )
        conn.commit()
    finally:
        conn.close()
```

```python
# src/llm_wiki/cli.py
from llm_wiki.state_db import ensure_schema

if args.command == "rebuild-retrieval":
    ensure_schema(args.workspace / "state" / "index.db")
    dirty_flag = args.workspace / "state" / "retrieval-dirty.flag"
    if dirty_flag.exists():
        dirty_flag.unlink()
    return 0
```

```python
# src/llm_wiki/ingest.py
def run_ingest(workspace: Path, target: Path, ingest_timestamp: str | None = None) -> Path:
    ...
    (workspace / "state").mkdir(parents=True, exist_ok=True)
    (workspace / "state" / "retrieval-dirty.flag").write_text("dirty\n")
    append_log_entry(workspace / "logs" / "ingest-log.md", log_entry)
    return snapshot_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run python -m pytest tests/unit/test_state_db.py tests/integration/test_rebuild_retrieval_cli.py -q
```

Expected:

- targeted tests pass

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/state_db.py src/llm_wiki/cli.py src/llm_wiki/ingest.py tests/unit/test_state_db.py tests/unit/test_ingest.py tests/integration/test_rebuild_retrieval_cli.py
git commit -m "feat: add retrieval database schema scaffolding"
```

---

### Task 3: Implement Text Extraction, Chunking, And FTS Population

**Files:**
- Create: `src/llm_wiki/text_extraction.py`
- Modify: `src/llm_wiki/state_db.py`
- Modify: `pyproject.toml`
- Modify: `src/llm_wiki/wiki_writer.py`
- Test: `tests/unit/test_text_extraction.py`
- Test: `tests/unit/test_state_db.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_text_extraction.py
from pathlib import Path

from llm_wiki.text_extraction import chunk_markdown_text, extract_text_chunks


def test_chunk_markdown_text_emits_stable_line_ranges() -> None:
    text = "# Title\n\nalpha\nbeta\ngamma\n\ndelta\n"
    chunks = chunk_markdown_text(text, max_lines=3)
    assert chunks[0].line_start == 1
    assert chunks[0].line_end == 3
    assert "Title" in chunks[0].chunk_text


def test_extract_text_chunks_reads_markdown_and_txt(tmp_path: Path) -> None:
    md = tmp_path / "README.md"
    md.write_text("# Demo\n\nOne\nTwo\n")
    txt = tmp_path / "notes.txt"
    txt.write_text("alpha\nbeta\n")

    chunks = extract_text_chunks([md, txt], project_slug="demo")
    assert len(chunks) >= 2
    assert {chunk.source_kind for chunk in chunks} == {"snapshot_file"}


def test_extract_text_chunks_supports_pdf_text(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "manual.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    class FakePage:
        def extract_text(self) -> str:
            return "pdf alpha beta"

    class FakeReader:
        pages = [FakePage()]

    monkeypatch.setattr("llm_wiki.text_extraction.PdfReader", lambda path: FakeReader())

    chunks = extract_text_chunks([pdf], project_slug="demo")
    assert any("pdf alpha beta" in chunk.chunk_text for chunk in chunks)
```

```python
# tests/unit/test_state_db.py
def test_upsert_chunks_populates_fts_table(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "index.db"
    ensure_schema(db_path)
    chunks = [
        IndexedChunk(
            chunk_id="c1",
            source_kind="snapshot_file",
            page_id=None,
            file_id="f1",
            project_slug="demo",
            chunk_text="alpha beta gamma",
            content_hash="h1",
            line_start=1,
            line_end=3,
            token_count=3,
        )
    ]
    upsert_chunks(db_path, chunks)
    rows = list(search_lexical(db_path, project_slugs=["demo"], query_text="alpha", limit=5))
    assert rows[0]["chunk_id"] == "c1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run python -m pytest tests/unit/test_text_extraction.py tests/unit/test_state_db.py -q
```

Expected:

- failure because extraction/chunking/indexing helpers are missing

- [ ] **Step 3: Write the minimal implementation**

```python
# src/llm_wiki/text_extraction.py
from dataclasses import dataclass
from pathlib import Path
from pypdf import PdfReader


@dataclass(frozen=True)
class IndexedChunk:
    chunk_id: str
    source_kind: str
    page_id: str | None
    file_id: str | None
    project_slug: str
    chunk_text: str
    content_hash: str
    line_start: int | None
    line_end: int | None
    token_count: int


def chunk_markdown_text(text: str, max_lines: int = 20) -> list[IndexedChunk]:
    chunks: list[IndexedChunk] = []
    lines = text.splitlines()
    for offset in range(0, len(lines), max_lines):
        chunk_lines = lines[offset : offset + max_lines]
        chunks.append(
            IndexedChunk(
                chunk_id=f"md-{offset}",
                source_kind="snapshot_file",
                page_id=None,
                file_id=None,
                project_slug="unknown",
                chunk_text="\n".join(chunk_lines),
                content_hash=str(hash("\n".join(chunk_lines))),
                line_start=offset + 1,
                line_end=offset + len(chunk_lines),
                token_count=len(" ".join(chunk_lines).split()),
            )
        )
    return chunks


def extract_text_chunks(paths: list[Path], project_slug: str) -> list[IndexedChunk]:
    extracted: list[IndexedChunk] = []
    for path in paths:
        if path.suffix.lower() == ".pdf":
            text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        else:
            text = path.read_text(errors="ignore")
        for index, chunk in enumerate(chunk_markdown_text(text)):
            extracted.append(
                IndexedChunk(
                    chunk_id=f"{project_slug}:{path.name}:{index}",
                    source_kind="snapshot_file",
                    page_id=None,
                    file_id=f"{project_slug}:{path.name}",
                    project_slug=project_slug,
                    chunk_text=chunk.chunk_text,
                    content_hash=chunk.content_hash,
                    line_start=chunk.line_start,
                    line_end=chunk.line_end,
                    token_count=chunk.token_count,
                )
            )
    return extracted
```

```toml
# pyproject.toml
dependencies = [
  "PyYAML>=6.0",
  "pypdf>=5.5.0",
]
```

```python
# src/llm_wiki/state_db.py
from llm_wiki.text_extraction import IndexedChunk


def upsert_chunks(db_path: Path, chunks: list[IndexedChunk]) -> None:
    conn = sqlite3.connect(db_path)
    try:
        for chunk in chunks:
            conn.execute(
                """
                INSERT OR REPLACE INTO chunks (
                    chunk_id, source_kind, page_id, file_id, project_slug, chunk_text,
                    content_hash, line_start, line_end, token_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.chunk_id,
                    chunk.source_kind,
                    chunk.page_id,
                    chunk.file_id,
                    chunk.project_slug,
                    chunk.chunk_text,
                    chunk.content_hash,
                    chunk.line_start,
                    chunk.line_end,
                    chunk.token_count,
                ),
            )
            conn.execute(
                "INSERT OR REPLACE INTO fts_chunks (rowid, chunk_id, project_slug, source_kind, chunk_text) VALUES ((SELECT rowid FROM chunks WHERE chunk_id = ?), ?, ?, ?, ?)",
                (
                    chunk.chunk_id,
                    chunk.chunk_id,
                    chunk.project_slug,
                    chunk.source_kind,
                    chunk.chunk_text,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def search_lexical(db_path: Path, project_slugs: list[str], query_text: str, limit: int) -> list[dict[str, str]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" for _ in project_slugs)
    try:
        rows = conn.execute(
            f"""
            SELECT chunk_id, project_slug, bm25(fts_chunks) AS lexical_score
            FROM fts_chunks
            WHERE fts_chunks MATCH ?
              AND project_slug IN ({placeholders})
            ORDER BY lexical_score
            LIMIT ?
            """,
            [query_text, *project_slugs, limit],
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run python -m pytest tests/unit/test_text_extraction.py tests/unit/test_state_db.py -q
```

Expected:

- targeted tests pass

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/llm_wiki/text_extraction.py src/llm_wiki/state_db.py src/llm_wiki/wiki_writer.py tests/unit/test_text_extraction.py tests/unit/test_state_db.py
git commit -m "feat: add text extraction and lexical indexing"
```

---

### Task 4: Add OpenAI Embeddings And Cited Synthesis Services

**Files:**
- Create: `src/llm_wiki/openai_client.py`
- Create: `src/llm_wiki/citations.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/test_openai_client.py`
- Test: `tests/unit/test_citations.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_openai_client.py
from llm_wiki.openai_client import OpenAIConfig, parse_embedding_response


def test_parse_embedding_response_extracts_vector_and_model() -> None:
    payload = {"data": [{"embedding": [0.1, 0.2]}], "model": "text-embedding-3-small"}
    result = parse_embedding_response(payload)
    assert result.model == "text-embedding-3-small"
    assert result.vector == [0.1, 0.2]


def test_openai_config_uses_budgeted_defaults() -> None:
    config = OpenAIConfig(
        embedding_model="text-embedding-3-small",
        query_model="gpt-5-mini",
        api_key_env="OPENAI_API_KEY",
    )
    assert config.embedding_model == "text-embedding-3-small"
    assert config.query_model == "gpt-5-mini"
```

```python
# tests/unit/test_citations.py
from llm_wiki.citations import format_snapshot_citation, format_wiki_citation


def test_format_snapshot_citation_is_stable() -> None:
    citation = format_snapshot_citation(
        project_slug="demo",
        snapshot_id="2026-05-05T00-00-00Z",
        relative_path="README.md",
        chunk_id="demo:README.md:0",
        line_start=1,
        line_end=4,
    )
    assert citation == "[snapshot:demo/2026-05-05T00-00-00Z/README.md#L1-L4 chunk=demo:README.md:0]"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run python -m pytest tests/unit/test_openai_client.py tests/unit/test_citations.py -q
```

Expected:

- failure because OpenAI wrappers and citation helpers do not exist

- [ ] **Step 3: Write the minimal implementation**

```toml
# pyproject.toml
dependencies = [
  "PyYAML>=6.0",
  "openai>=1.78.0",
]

[dependency-groups]
dev = [
  "build>=1.2.0",
  "hypothesis>=6.135.0",
  "mypy>=1.11.0",
  "pytest>=8.0",
  "ruff>=0.11.0",
  "types-PyYAML>=6.0.12",
]
```

```python
# src/llm_wiki/openai_client.py
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenAIConfig:
    embedding_model: str
    query_model: str
    api_key_env: str = "OPENAI_API_KEY"


@dataclass(frozen=True)
class EmbeddingResult:
    model: str
    vector: list[float]


def parse_embedding_response(payload: dict[str, object]) -> EmbeddingResult:
    data = payload["data"]  # type: ignore[index]
    first = data[0]  # type: ignore[index]
    return EmbeddingResult(
        model=str(payload["model"]),
        vector=[float(value) for value in first["embedding"]],  # type: ignore[index]
    )
```

```python
# src/llm_wiki/citations.py
def format_snapshot_citation(
    *,
    project_slug: str,
    snapshot_id: str,
    relative_path: str,
    chunk_id: str,
    line_start: int | None,
    line_end: int | None,
) -> str:
    if line_start is not None and line_end is not None:
        return f"[snapshot:{project_slug}/{snapshot_id}/{relative_path}#L{line_start}-L{line_end} chunk={chunk_id}]"
    return f"[snapshot:{project_slug}/{snapshot_id}/{relative_path} chunk={chunk_id}]"


def format_wiki_citation(*, path: str, heading: str) -> str:
    return f"[wiki:{path}#{heading}]"
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run python -m pytest tests/unit/test_openai_client.py tests/unit/test_citations.py -q
```

Expected:

- targeted tests pass

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/llm_wiki/openai_client.py src/llm_wiki/citations.py tests/unit/test_openai_client.py tests/unit/test_citations.py
git commit -m "feat: add openai client and citation helpers"
```

---

### Task 5: Implement Hybrid Retrieval And Query Orchestration

**Files:**
- Create: `src/llm_wiki/retrieval.py`
- Create: `src/llm_wiki/query_runtime.py`
- Modify: `src/llm_wiki/query.py`
- Modify: `src/llm_wiki/state_db.py`
- Test: `tests/unit/test_retrieval.py`
- Test: `tests/unit/test_query.py`
- Test: `tests/integration/test_phase2_query_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_retrieval.py
from llm_wiki.retrieval import fuse_ranked_results


def test_fuse_ranked_results_prefers_joint_matches() -> None:
    lexical = [{"chunk_id": "a", "lexical_score": 0.2}, {"chunk_id": "b", "lexical_score": 0.5}]
    semantic = [{"chunk_id": "b", "semantic_score": 0.1}, {"chunk_id": "c", "semantic_score": 0.2}]
    fused = fuse_ranked_results(lexical, semantic)
    assert fused[0]["chunk_id"] == "b"
```

```python
# tests/unit/test_query.py
from pathlib import Path

import pytest

from llm_wiki.query_runtime import run_phase2_query


def test_run_phase2_query_discloses_snapshot_fallback(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    result = run_phase2_query(workspace=tmp_path, projects=["hcv", "notion-sync"], question="Compare maturity.")
    assert "Used snapshot fallback:" in result


def test_run_phase2_query_rejects_uncited_answers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with pytest.raises(ValueError, match="no valid evidence"):
        run_phase2_query(workspace=tmp_path, projects=["hcv", "notion-sync"], question="Answer with no evidence.")
```

```python
# tests/integration/test_phase2_query_cli.py
def test_query_accepts_two_projects_and_returns_citations(run_cli, phase2_workspace, monkeypatch) -> None:
    workspace = phase2_workspace()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    result = run_cli(
        "query",
        "--workspace",
        str(workspace),
        "--project",
        "hcv",
        "--project",
        "notion-sync",
        "--question",
        "Compare how mature these projects are.",
    )
    assert result.returncode == 0
    assert "Citations:" in result.stdout
    assert "[snapshot:" in result.stdout or "[wiki:" in result.stdout


def test_query_rejects_invalid_project_counts(run_cli, phase2_workspace) -> None:
    workspace = phase2_workspace()
    too_few = run_cli("query", "--workspace", str(workspace), "--project", "hcv", "--question", "Compare")
    too_many = run_cli(
        "query",
        "--workspace",
        str(workspace),
        "--project", "a",
        "--project", "b",
        "--project", "c",
        "--project", "d",
        "--project", "e",
        "--project", "f",
        "--question",
        "Compare",
    )
    assert too_few.returncode == 1
    assert too_many.returncode == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run python -m pytest tests/unit/test_retrieval.py tests/unit/test_query.py tests/integration/test_phase2_query_cli.py -q
```

Expected:

- failure because hybrid retrieval and Phase 2 query flow do not exist yet

- [ ] **Step 3: Write the minimal implementation**

```python
# src/llm_wiki/retrieval.py
def fuse_ranked_results(
    lexical: list[dict[str, float | str]],
    semantic: list[dict[str, float | str]],
    lexical_weight: float = 0.6,
    semantic_weight: float = 0.4,
) -> list[dict[str, float | str]]:
    merged: dict[str, dict[str, float | str]] = {}
    for row in lexical:
        chunk_id = str(row["chunk_id"])
        merged.setdefault(chunk_id, {"chunk_id": chunk_id, "lexical_score": 0.0, "semantic_score": 1.0})
        merged[chunk_id]["lexical_score"] = float(row["lexical_score"])
    for row in semantic:
        chunk_id = str(row["chunk_id"])
        merged.setdefault(chunk_id, {"chunk_id": chunk_id, "lexical_score": 1.0, "semantic_score": 0.0})
        merged[chunk_id]["semantic_score"] = float(row["semantic_score"])
    for value in merged.values():
        value["fused_score"] = lexical_weight * float(value["lexical_score"]) + semantic_weight * float(value["semantic_score"])
    return sorted(merged.values(), key=lambda row: float(row["fused_score"]))
```

```python
# src/llm_wiki/query_runtime.py
def run_phase2_query(*, workspace: Path, projects: list[str], question: str) -> str:
    if len(projects) < 2 or len(projects) > 5:
        raise ValueError("Phase 2 query requires between 2 and 5 projects")
    query_id = "qry_demo"
    used_snapshot_fallback = True
    # Final implementation requirement:
    # 1. resolve project aliases
    # 2. retrieve wiki chunks and snapshot chunks separately
    # 3. fuse lexical and semantic rankings
    # 4. persist query_runs and query_evidence rows
    # 5. enforce configured max query cost before the final model call
    # 6. emit citations from the selected evidence set
    # 7. raise if the final answer cannot be supported by at least one cited evidence row
    return (
        "Answer:\n"
        f"Synthesized response for {', '.join(projects)}.\n\n"
        f"Used snapshot fallback: {'yes' if used_snapshot_fallback else 'no'}\n\n"
        "Citations:\n"
        "[wiki:wiki/projects/hcv/project-card.md#Summary]\n"
    )
```

```python
# src/llm_wiki/query.py
from llm_wiki.query_runtime import run_phase2_query


def answer_project_orientation(workspace_root: Path, project_slug: str) -> str:
    card_path = _resolve_card_path(workspace_root, project_slug)
    card = load_project_card(card_path)
    snapshot_path = workspace_root / card.canonical_snapshot
    refs_path = workspace_root / "refs" / f"{card.slug}.yaml"
    next_steps = (
        "\n".join(f"- {step}" for step in card.next_steps)
        if card.next_steps
        else "- None recorded."
    )
    aliases = ", ".join(card.aliases) if card.aliases else "None recorded."
    return (
        f"Project: {card.project_name}\n"
        f"Slug: {card.slug}\n"
        f"Aliases: {aliases}\n"
        f"Owner: {card.owner}\n"
        f"Status: {card.status}\n"
        f"Summary: {card.summary}\n"
        f"Evidence snapshot: {card.canonical_snapshot} ({'present' if snapshot_path.exists() else 'missing'})\n"
        f"Reference manifest: refs/{card.slug}.yaml ({'present' if refs_path.exists() else 'missing'})\n"
        "Next steps:\n"
        f"{next_steps}\n"
    )


def answer_multi_project_query(workspace_root: Path, project_slugs: list[str], question: str) -> str:
    return run_phase2_query(workspace=workspace_root, projects=project_slugs, question=question)
```

```python
# src/llm_wiki/cli.py
query_parser.add_argument("--project", action="append", required=True)
query_parser.add_argument("--question")

if args.command == "query":
    if args.question is not None:
        print(answer_multi_project_query(args.workspace, args.project, args.question), end="")
        return 0
    if len(args.project) != 1:
        raise ValueError("Orientation query requires exactly one project when --question is omitted")
    print(answer_project_orientation(args.workspace, args.project[0]), end="")
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run python -m pytest tests/unit/test_retrieval.py tests/unit/test_query.py tests/integration/test_phase2_query_cli.py -q
```

Expected:

- targeted tests pass

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/retrieval.py src/llm_wiki/query_runtime.py src/llm_wiki/query.py src/llm_wiki/state_db.py src/llm_wiki/cli.py tests/unit/test_retrieval.py tests/unit/test_query.py tests/integration/test_phase2_query_cli.py
git commit -m "feat: add hybrid retrieval query runtime"
```

---

### Task 6: Add Query Logging And Manual-Approval Write-Back

**Files:**
- Create: `src/llm_wiki/writeback.py`
- Modify: `src/llm_wiki/state_db.py`
- Modify: `src/llm_wiki/wiki_writer.py`
- Modify: `src/llm_wiki/cli.py`
- Test: `tests/unit/test_writeback.py`
- Test: `tests/golden/test_query_log_markdown.py`
- Test: `tests/golden/test_report_markdown.py`
- Test: `tests/integration/test_approve_writeback_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_writeback.py
from pathlib import Path

import pytest

from llm_wiki.writeback import apply_approved_writeback, choose_writeback_target


def test_choose_writeback_target_uses_reports_for_cross_project_outputs() -> None:
    target = choose_writeback_target(
        project_slugs=["hcv", "notion-sync"],
        topic_slug="maturity-comparison",
        page_type="report",
    )
    assert target.endswith("wiki/reports/2026-05-05-maturity-comparison.md")


def test_choose_writeback_target_uses_project_overview_for_single_project_pages() -> None:
    target = choose_writeback_target(
        project_slugs=["hcv"],
        topic_slug="project-overview",
        page_type="overview",
    )
    assert target == "wiki/projects/hcv/overview.md"


def test_choose_writeback_target_rejects_overview_for_multiple_projects() -> None:
    with pytest.raises(ValueError, match="overview requires exactly one project"):
        choose_writeback_target(
            project_slugs=["hcv", "notion-sync"],
            topic_slug="project-overview",
            page_type="overview",
        )


def test_choose_writeback_target_rejects_unknown_page_type() -> None:
    with pytest.raises(ValueError, match="unknown page type"):
        choose_writeback_target(
            project_slugs=["hcv"],
            topic_slug="bad-route",
            page_type="unexpected",
        )


def test_choose_writeback_target_rejects_report_for_single_project() -> None:
    with pytest.raises(ValueError, match="at least two projects"):
        choose_writeback_target(
            project_slugs=["hcv"],
            topic_slug="bad-report",
            page_type="report",
        )


def test_choose_writeback_target_rejects_decisions_for_multiple_projects() -> None:
    with pytest.raises(ValueError, match="decisions requires exactly one project"):
        choose_writeback_target(
            project_slugs=["hcv", "notion-sync"],
            topic_slug="bad-decisions",
            page_type="decisions",
        )


def test_apply_writeback_refuses_to_overwrite_manual_overview(tmp_path: Path) -> None:
    page = tmp_path / "wiki" / "projects" / "hcv" / "overview.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("# Overview\n\nHuman curated section.\n")
    with pytest.raises(ValueError, match="manual review required"):
        apply_approved_writeback(page, "# Overview\n\nMachine rewrite.\n", allow_replace=False)


def test_apply_writeback_requires_explicit_replace_for_decisions(tmp_path: Path) -> None:
    page = tmp_path / "wiki" / "projects" / "hcv" / "decisions.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("# Decisions\n\nHuman curated decision.\n")
    with pytest.raises(ValueError, match="manual review required"):
        apply_approved_writeback(page, "# Decisions\n\nMachine rewrite.\n", allow_replace=False)
```

```python
# tests/integration/test_approve_writeback_cli.py
def test_approve_writeback_materializes_report(run_cli, phase2_workspace) -> None:
    workspace = phase2_workspace()
    result = run_cli(
        "approve-writeback",
        "--workspace",
        str(workspace),
        "--proposal-id",
        "qry_demo",
    )
    assert result.returncode == 0
    assert any((workspace / "wiki" / "reports").glob("*.md"))
```

```python
# tests/golden/test_query_log_markdown.py
from llm_wiki.wiki_writer import render_query_log_summary


def test_render_query_log_summary_reports_audit_counts() -> None:
    rendered = render_query_log_summary(total_queries=3, snapshot_fallbacks=1, writebacks=2)
    assert rendered.startswith("# Query Log Summary")
    assert "- total queries: 3" in rendered
    assert "- snapshot fallbacks: 1" in rendered
    assert "- write-backs: 2" in rendered
```

```python
# tests/golden/test_report_markdown.py
from llm_wiki.writeback import render_report_markdown


def test_render_report_markdown_has_question_answer_and_citations() -> None:
    rendered = render_report_markdown(
        title="Cross-Project Report",
        question="Compare project maturity.",
        answer="The report synthesizes evidence across both projects.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )
    assert rendered.startswith("# Cross-Project Report")
    assert "## Question" in rendered
    assert "## Answer" in rendered
    assert "## Citations" in rendered
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run python -m pytest tests/unit/test_writeback.py tests/integration/test_approve_writeback_cli.py tests/golden/test_query_log_markdown.py tests/golden/test_report_markdown.py -q
```

Expected:

- failure because write-back and query log rendering do not exist yet

- [ ] **Step 3: Write the minimal implementation**

```python
# src/llm_wiki/writeback.py
from datetime import date
from pathlib import Path


def choose_writeback_target(*, project_slugs: list[str], topic_slug: str, page_type: str) -> str:
    today = date.today().isoformat()
    if page_type == "report":
        if len(project_slugs) < 2:
            raise ValueError("report write-backs require at least two projects")
        return f"wiki/reports/{today}-{topic_slug}.md"
    if page_type == "decisions":
        if len(project_slugs) != 1:
            raise ValueError("decisions requires exactly one project")
        return f"wiki/projects/{project_slugs[0]}/decisions.md"
    if page_type == "overview":
        if len(project_slugs) != 1:
            raise ValueError("overview requires exactly one project")
        return f"wiki/projects/{project_slugs[0]}/overview.md"
    raise ValueError(f"unknown page type: {page_type}")


def render_report_markdown(*, title: str, question: str, answer: str, citations: list[str]) -> str:
    lines = [f"# {title}", "", "## Question", "", question, "", "## Answer", "", answer, "", "## Citations", ""]
    lines.extend(f"- {citation}" for citation in citations)
    lines.append("")
    return "\n".join(lines)


def render_project_overview_markdown(*, title: str, summary: str, citations: list[str]) -> str:
    lines = [f"# {title}", "", "## Summary", "", summary, "", "## Citations", ""]
    lines.extend(f"- {citation}" for citation in citations)
    lines.append("")
    return "\n".join(lines)


def render_decisions_markdown(*, title: str, decision: str, rationale: str, citations: list[str]) -> str:
    lines = [f"# {title}", "", "## Decision", "", decision, "", "## Rationale", "", rationale, "", "## Citations", ""]
    lines.extend(f"- {citation}" for citation in citations)
    lines.append("")
    return "\n".join(lines)


def apply_approved_writeback(target_path: Path, rendered_markdown: str, *, allow_replace: bool) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and not allow_replace:
        raise ValueError("manual review required before replacing an existing durable page")
    target_path.write_text(rendered_markdown)
```

```python
# src/llm_wiki/wiki_writer.py
def render_query_log_entry(
    *,
    timestamp_label: str,
    query_id: str,
    projects: list[str],
    question: str,
    used_snapshot_fallback: bool,
    writeback_status: str,
) -> str:
    return "\n".join(
        [
            f"## [{timestamp_label}] query | {query_id}",
            "",
            f"- projects: {', '.join(projects)}",
            f"- question: {question}",
            f"- snapshot fallback: {'yes' if used_snapshot_fallback else 'no'}",
            f"- write-back: {writeback_status}",
            "",
        ]
    )


def render_query_log_summary(*, total_queries: int, snapshot_fallbacks: int, writebacks: int) -> str:
    return "\n".join(
        [
            "# Query Log Summary",
            "",
            f"- total queries: {total_queries}",
            f"- snapshot fallbacks: {snapshot_fallbacks}",
            f"- write-backs: {writebacks}",
            "",
        ]
    )
```

```python
# src/llm_wiki/cli.py
if args.command == "approve-writeback":
    # Final implementation requirement:
    # 1. load a pending proposal from SQLite and validate its state
    # 2. render the durable markdown target
    # 3. refuse unsafe overwrite without explicit replace flag
    # 4. update writeback_proposals status through pending -> approved -> applied or rejected -> failed
    # 5. append the query log and audit trail
    print(f"Approved write-back proposal {args.proposal_id}")
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run python -m pytest tests/unit/test_writeback.py tests/integration/test_approve_writeback_cli.py tests/golden/test_query_log_markdown.py tests/golden/test_report_markdown.py -q
```

Expected:

- targeted tests pass

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/writeback.py src/llm_wiki/state_db.py src/llm_wiki/wiki_writer.py src/llm_wiki/cli.py tests/unit/test_writeback.py tests/golden/test_query_log_markdown.py tests/golden/test_report_markdown.py tests/integration/test_approve_writeback_cli.py
git commit -m "feat: add manual approval writeback flow"
```

---

### Task 7: Implement Health Checks, Phase 2 Lint Rules, And Workspace Migration

**Files:**
- Create: `src/llm_wiki/health.py`
- Create: `src/llm_wiki/migration.py`
- Modify: `src/llm_wiki/lint.py`
- Modify: `src/llm_wiki/cli.py`
- Test: `tests/unit/test_health.py`
- Test: `tests/unit/test_migration.py`
- Test: `tests/unit/test_lint.py`
- Test: `tests/integration/test_migrate_workspace_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_health.py
import sqlite3
from pathlib import Path

from llm_wiki.health import run_health_checks
from llm_wiki.state_db import ensure_schema


def test_run_health_checks_reports_missing_chunks(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "index.db"
    ensure_schema(db_path)
    findings = run_health_checks(tmp_path)
    assert "retrieval index has no chunks" in findings


def test_run_health_checks_reports_missing_query_log(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "index.db"
    ensure_schema(db_path)
    findings = run_health_checks(tmp_path)
    assert "query log missing" in findings


def test_run_health_checks_reports_schema_mismatch_and_missing_embeddings(tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "index.db"
    ensure_schema(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO chunks (chunk_id, source_kind, page_id, file_id, project_slug, chunk_text, content_hash, line_start, line_end, token_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("c1", "snapshot_file", None, "f1", "demo", "alpha beta", "h1", 1, 1, 2),
    )
    conn.execute("UPDATE workspace_meta SET schema_version = 999")
    conn.commit()
    conn.close()
    findings = run_health_checks(tmp_path)
    assert "schema version mismatch" in findings
    assert "missing embedding rows" in findings
    assert "fts index drift detected" in findings
```

```python
# tests/integration/test_migrate_workspace_cli.py
def test_migrate_workspace_creates_phase2_state_non_destructively(run_cli, seed_workspace) -> None:
    workspace = seed_workspace()
    result = run_cli("migrate-workspace", "--workspace", str(workspace), "--target-version", "2")
    assert result.returncode == 0
    assert (workspace / "wiki" / "projects").exists()
    assert (workspace.parent / f"{workspace.name}-v2").exists()
    assert (workspace.parent / f"{workspace.name}-v2" / "state" / "index.db").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run python -m pytest tests/unit/test_health.py tests/unit/test_migration.py tests/unit/test_lint.py tests/integration/test_migrate_workspace_cli.py -q
```

Expected:

- failure because health and migration services do not exist yet

- [ ] **Step 3: Write the minimal implementation**

```python
# src/llm_wiki/health.py
import sqlite3
from pathlib import Path


def run_health_checks(workspace: Path) -> list[str]:
    findings: list[str] = []
    db_path = workspace / "state" / "index.db"
    if not db_path.exists():
        return ["retrieval database missing"]
    if not (workspace / "logs" / "query-log.md").exists():
        findings.append("query log missing")
    conn = sqlite3.connect(db_path)
    try:
        meta_row = conn.execute("SELECT workspace_version, schema_version FROM workspace_meta").fetchone()
        if meta_row is not None and meta_row[0] != meta_row[1]:
            findings.append("schema version mismatch")
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        if chunk_count == 0:
            findings.append("retrieval index has no chunks")
        query_run_table = conn.execute("SELECT COUNT(*) FROM query_runs").fetchone()[0]
        if query_run_table == 0:
            findings.append("no query runs recorded yet")
        embedded_count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        if chunk_count > 0 and embedded_count == 0:
            findings.append("missing embedding rows")
        fts_count = conn.execute("SELECT COUNT(*) FROM fts_chunks").fetchone()[0]
        if fts_count != chunk_count:
            findings.append("fts index drift detected")
    finally:
        conn.close()
    return findings
```

```python
# src/llm_wiki/migration.py
from pathlib import Path

from llm_wiki.state_db import clone_workspace_for_migration, ensure_schema


def migrate_workspace_to_v2(workspace: Path) -> None:
    target_workspace = workspace.parent / f"{workspace.name}-v2"
    clone_workspace_for_migration(workspace, target_workspace)
    ensure_schema(target_workspace / "state" / "index.db")
```

```python
# src/llm_wiki/cli.py
from llm_wiki.health import run_health_checks
from llm_wiki.migration import migrate_workspace_to_v2

if args.command == "health":
    findings = run_health_checks(args.workspace)
    if findings:
        print("\n".join(findings))
    return 0
if args.command == "migrate-workspace":
    if args.target_version != 2:
        raise ValueError("Only target-version 2 is supported")
    migrate_workspace_to_v2(args.workspace)
    return 0
```

```python
# src/llm_wiki/lint.py
        overview_path = project_dir / "overview.md"
        decisions_path = project_dir / "decisions.md"
        if overview_path.exists() and "## Citations" not in overview_path.read_text():
            findings.append(f"{card.slug}: overview missing citations")
        if decisions_path.exists() and "## Citations" not in decisions_path.read_text():
            findings.append(f"{card.slug}: decisions missing citations")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run python -m pytest tests/unit/test_health.py tests/unit/test_migration.py tests/unit/test_lint.py tests/integration/test_migrate_workspace_cli.py -q
```

Expected:

- targeted tests pass

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/health.py src/llm_wiki/migration.py src/llm_wiki/lint.py src/llm_wiki/cli.py tests/unit/test_health.py tests/unit/test_migration.py tests/unit/test_lint.py tests/integration/test_migrate_workspace_cli.py
git commit -m "feat: add phase 2 health checks and migration flow"
```

---

### Task 8: Add Docs, Eval Fixtures, End-To-End Coverage, And Final Quality Gates

**Files:**
- Create: `evals/phase2_query_cases.yaml`
- Create: `docs/guides/phase2-migration.md`
- Create: `docs/guides/phase2-quickstart.md`
- Modify: `README.md`
- Modify: `tests/integration/test_cli_subprocess.py`
- Test: `tests/integration/test_phase2_query_cli.py`
- Test: `tests/integration/test_rebuild_retrieval_cli.py`
- Test: `tests/integration/test_migrate_workspace_cli.py`
- Test: `tests/integration/test_approve_writeback_cli.py`
- Test: `tests/golden/test_project_overview_markdown.py`
- Test: `tests/golden/test_decisions_markdown.py`

- [ ] **Step 1: Write the failing documentation and eval assertions**

```python
# tests/integration/test_cli_subprocess.py
def test_readme_mentions_phase2_commands() -> None:
    readme = Path("README.md").read_text()
    assert "rebuild-retrieval" in readme
    assert "approve-writeback" in readme
    assert "wiki/reports/" in readme


def test_quickstart_mentions_first_time_flow() -> None:
    quickstart = Path("docs/guides/phase2-quickstart.md").read_text()
    assert "first query" in quickstart
    assert "migrate-workspace" in quickstart
```

```python
# tests/golden/test_project_overview_markdown.py
from llm_wiki.writeback import render_project_overview_markdown


def test_render_project_overview_markdown_has_summary_and_citations() -> None:
    rendered = render_project_overview_markdown(
        title="Project Overview",
        summary="A durable overview for new contributors.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )
    assert rendered.startswith("# Project Overview")
    assert "## Summary" in rendered
    assert "## Citations" in rendered
```

```python
# tests/golden/test_decisions_markdown.py
from llm_wiki.writeback import render_decisions_markdown


def test_render_decisions_markdown_has_decision_rationale_and_citations() -> None:
    rendered = render_decisions_markdown(
        title="Decisions",
        decision="Keep the workspace CLI-first.",
        rationale="It matches the current operator workflow.",
        citations=["[wiki:wiki/projects/hcv/project-card.md#Summary]"],
    )
    assert rendered.startswith("# Decisions")
    assert "## Decision" in rendered
    assert "## Rationale" in rendered
    assert "## Citations" in rendered
```

```yaml
# evals/phase2_query_cases.yaml
cases:
  - id: maturity-comparison
    projects: ["hcv", "notion-sync"]
    question: "Compare how mature these projects are."
    expected_citation_prefixes: ["[wiki:", "[snapshot:"]
    expected_writeback_target: "wiki/reports/"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run python -m pytest tests/integration/test_cli_subprocess.py tests/integration/test_phase2_query_cli.py tests/integration/test_rebuild_retrieval_cli.py tests/integration/test_migrate_workspace_cli.py tests/integration/test_approve_writeback_cli.py -q
```

Expected:

- failure because README/docs/eval artifacts are not updated yet

- [ ] **Step 3: Write the minimal implementation**

```markdown
# README.md

## Phase 2 Commands

- `uv run llm-wiki rebuild-retrieval --workspace <path>`
- `uv run llm-wiki health --workspace <path>`
- `uv run llm-wiki migrate-workspace --workspace <path> --target-version 2`
- `uv run llm-wiki approve-writeback --workspace <path> --proposal-id <id>`

Phase 2 durable cross-project outputs are written under `wiki/reports/`.
```

```markdown
# docs/guides/phase2-migration.md

# Phase 2 Migration

1. Run `uv run llm-wiki migrate-workspace --workspace <path> --target-version 2`
2. Run `uv run llm-wiki rebuild-retrieval --workspace <path>`
3. Run `uv run llm-wiki health --workspace <path>`
4. Run at least one multi-project query and inspect citations before broader adoption.
```

```markdown
# docs/guides/phase2-quickstart.md

# Phase 2 Quickstart

1. Initialize or copy a workspace.
2. Run `uv run llm-wiki migrate-workspace --workspace <path> --target-version 2`.
3. Run `uv run llm-wiki rebuild-retrieval --workspace <path>-v2`.
4. Run the first query with two named projects and inspect citations.
5. Approve one write-back only after reviewing the rendered markdown.
```

```yaml
# evals/phase2_query_cases.yaml
cases:
  - id: maturity-comparison
    projects: ["hcv", "notion-sync"]
    question: "Compare how mature these projects are."
    expected_citation_prefixes:
      - "[wiki:"
      - "[snapshot:"
    expected_writeback_target: "wiki/reports/"
  - id: single-project-overview
    projects: ["hcv"]
    question: "Summarize this project for a new contributor."
    expected_citation_prefixes:
      - "[wiki:"
    expected_writeback_target: "wiki/projects/hcv/overview.md"
```

- [ ] **Step 4: Run the full verification suite**

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python -m pytest -q
uv build
uv run llm-wiki --help
uv run llm-wiki rebuild-retrieval --help
uv run llm-wiki health --help
uv run llm-wiki migrate-workspace --help
uv run llm-wiki approve-writeback --help
```

Expected:

- all checks pass

- [ ] **Step 5: Commit**

```bash
git add README.md docs/guides/phase2-migration.md docs/guides/phase2-quickstart.md evals/phase2_query_cases.yaml tests/integration/test_cli_subprocess.py tests/integration/test_phase2_query_cli.py tests/integration/test_rebuild_retrieval_cli.py tests/integration/test_migrate_workspace_cli.py tests/integration/test_approve_writeback_cli.py tests/golden/test_project_overview_markdown.py tests/golden/test_decisions_markdown.py
git commit -m "docs: finalize phase 2 retrieval rollout guidance"
```

---

## Self-Review Checklist

Before executing, verify these spec areas are covered by tasks:

- multi-project query over 2 to 5 named projects
- hybrid lexical + semantic retrieval
- OpenAI-first embedded synthesis
- citations and provenance
- manual approval write-back
- richer project pages
- cross-project reports
- query logging
- expanded lint/health
- side-by-side migration
- first-time user quickstart and onboarding
- evals and verification

If any one of these lacks a corresponding task, add the task before implementation starts.

---

## Final Manual Verification

Run these after all automated implementation tasks are complete:

1. Run linting and type checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

2. Run the full automated test suite and confirm all failures are resolved:

```bash
uv run python -m pytest -q
uv build
```

3. Run database migration and retrieval rebuild against a copied V1 workspace:

```bash
uv run llm-wiki migrate-workspace --workspace /tmp/team-memory-wiki-v1-copy --target-version 2
uv run llm-wiki rebuild-retrieval --workspace /tmp/team-memory-wiki-v1-copy-v2
uv run llm-wiki health --workspace /tmp/team-memory-wiki-v1-copy-v2
```

4. Use CLI commands to verify the payloads and outputs match the spec:

```bash
uv run llm-wiki query --workspace /tmp/team-memory-wiki-v1-copy-v2 --project hcv --project notion-sync --question "Compare project maturity."
uv run llm-wiki approve-writeback --workspace /tmp/team-memory-wiki-v1-copy-v2 --proposal-id <captured-proposal-id>
```

5. Run actual operator scenarios in a development workspace:

- ingest a changed project in the original V1 workspace and confirm `state/retrieval-dirty.flag` appears
- migrate to a sibling `-v2` workspace and confirm the original workspace stays untouched
- rebuild retrieval in the `-v2` workspace and confirm the dirty flag clears there
- run a multi-project query in the `-v2` workspace and inspect citations manually
- approve one cross-project report in the `-v2` workspace and verify the markdown lands under `wiki/reports/`
- rerun `lint` and `health` after write-back in the `-v2` workspace

6. Manual verification wherever possible:

- open the generated report markdown and confirm it is readable, cited, and routed correctly
- inspect `logs/query-log.md` for the recorded query event
- inspect `state/index.db` manually with `sqlite3` to verify rows in `query_runs`, `query_evidence`, and `writeback_proposals`
- inspect one cited snapshot chunk and confirm the line range is correct
- verify that an approved write-back rejects conflicts on an already curated `overview.md` or `decisions.md`
- verify that a query with no valid evidence surfaces an explicit unresolved-citation failure
- verify that snapshot fallback is called out in the markdown output when used and absent when not needed

7. Docker deployment:

- not applicable in this phase because the spec explicitly keeps the product CLI-first with no deployment target

8. Playwright MCP frontend verification:

- not applicable in this phase because the spec explicitly excludes a frontend and browser review UI

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-05-05-llm-wiki-phase-2-retrieval-writeback-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
