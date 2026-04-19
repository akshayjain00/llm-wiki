# Team Memory Wiki Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that initializes the Team Memory Wiki workspace, runs guided ingest for one project/folder, answers project-orientation queries from maintained wiki state, rebuilds project indexes, and runs lint against the maintained wiki.

**Architecture:** The implementation is a small Python package with deterministic filesystem operations and markdown/yaml outputs. The CLI orchestrates focused modules for workspace initialization, source scanning, snapshot copying, ref manifest writing, inference, wiki writing, querying, index rebuilding, and linting, with tests proving each layer independently before integration.

**Tech Stack:** Python 3.12, `argparse`, `pathlib`, `dataclasses`, `hashlib`, `shutil`, `datetime`, `PyYAML`, `pytest`, `ruff`, `mypy`, packaging smoke checks via `uv`, and a CLI-first interface before any API or UI.

---

## Execution Snapshot

As of `2026-04-20`, V1 is implemented in the worktree branch with:

- CLI commands for `init`, `ingest`, `query`, `rebuild-indexes`, and `lint`
- immutable snapshots, ref manifests, project-card generation, shared indexes, and append-only logs
- wiki-first query output with snapshot and ref evidence reporting
- lint coverage for unknown, stale, contradictory, duplicate, and missing-review cases
- full automated verification plus CLI smoke checks

The detailed task sections below are preserved as the execution record. Another engineer should use this summary first, then consult the step-by-step sections only when they need historical implementation detail.

### Remaining V1 Limitations

- no explicit reset command for manual overrides
- deduplication is scoped to a single guided-ingest slice
- query verifies evidence locations but does not re-summarize snapshot text on demand

---

## Decision Log

| Topic | Options Considered | Choice | Rationale |
| --- | --- | --- | --- |
| Primary interface | CLI-first, API-first, frontend-first | CLI-first | The system is local and filesystem-centric. CLI is the smallest useful surface and the easiest one to verify end to end. |
| Source model | Full mirroring, refs only, hybrid | Hybrid | Snapshotted artifacts provide stable evidence; refs preserve authoritative live locations without copying entire repos. |
| Query model | Live-source-first, raw-first, wiki-first | Wiki-first with snapshot verification | This preserves compiled memory and avoids silent drift from live repositories. |
| Raw storage | Mutable latest copy, replace in place, immutable snapshots | Immutable snapshots | Auditability and temporal debugging depend on preserved ingest history. |
| Update mode | Background automation, guided ingest, ad hoc scripts | Guided ingest | V1 should remain inspectable and operator-driven. |
| Verification posture | Tests only, tests plus lint, full quality gates | Full quality gates | The project should prove correctness through tests, static analysis, formatting, packaging smoke, and CLI roundtrip checks. |
| Browser automation | Use Playwright now, later if needed, never | Later if UI exists | V1 has no frontend; browser automation would not increase confidence for the current surface. |

---

## Verification Strategy For This Plan

Verification is part of the implementation plan, not a final cleanup step.

### Required Quality Gates

The project is not complete unless all of the following pass:

- targeted red -> green test cycle for each task
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`
- `uv run pytest -v`
- `uv build`
- CLI smoke checks for:
  - `uv run llm-wiki --help`
  - `uv run llm-wiki init`
  - `uv run llm-wiki ingest`
  - `uv run llm-wiki query`
  - `uv run llm-wiki rebuild-indexes`
  - `uv run llm-wiki lint`

### Determinism Rules

Implementation choices should support reliable verification:

- inject or patch timestamps instead of depending on wall-clock time in tests
- keep filesystem scans, manifest entries, and index rows stably ordered
- keep markdown rendering deterministic
- assert explicit exit codes from CLI commands
- keep successful CLI stderr clean unless warnings are intentional

### Fixture Coverage Requirements

The suite should cover:

- a healthy single-project fixture
- conflicting owner or status signals
- excluded/noisy files such as `.env`, `.git`, caches, and binaries
- duplicate artifacts across origins
- weak evidence that must resolve to `unknown`

### Browser Automation

Playwright is intentionally out of scope for this plan because V1 has no browser surface. If a future UI or review console is added, that decision must be revisited.

---

## Field Iteration Learnings

### Iteration 1 — `onboarding-charter`

**Target:** `/Users/akshay.jain/Library/CloudStorage/GoogleDrive-akshay.jain@theporter.in/My Drive/AI/onboarding-charter`

**Observed behavior:**
- Documentation-heavy folders are valid first ingests because they create a clean snapshot, ref manifest, and project shell.
- Conservative inference can still miss `owner`, `status`, and `summary` when the folder lacks one canonical README-style entry document.
- Rich markdown formatting can produce noisy `next_steps` extraction when the source bundle contains multiple planning formats.

**Operator adjustment for future iterations:**
- Prefer targets with one strong top-level README or CLAUDE-style overview plus 2-4 supporting docs.
- After every ingest, run `query` and `lint` immediately, then manually curate the card if `owner`, `status`, `summary`, or `next_steps` are weak.
- Treat the generated card as the durable semantic layer; do not expect raw ingest heuristics alone to produce final-quality project orientation.

**Implementation follow-up to watch:**
- Summary extraction should prefer explicit overview documents more strongly.
- `next_steps` extraction needs tighter filtering against formatting and prompt artifacts.
- The generated `schema/` files are guidance only today; future iterations may benefit from making portions of them executable configuration.

### Iteration 2 — `HCV` / Spot Orders on Tray

**Target:** `/Users/akshay.jain/Library/CloudStorage/GoogleDrive-akshay.jain@theporter.in/My Drive/AI/HCV`

**Observed behavior:**
- Focused narrative bundles produce cleaner ingests than broad mixed documentation folders.
- The default slug followed the folder name (`hcv`), while the actual semantic project identity came from the strongest document title (`Spot Orders on Tray`).
- A post-curation `rebuild-indexes` is essential whenever project identity is normalized after ingest.

**Operator adjustment for future iterations:**
- Prefer narrow folders whose files all describe the same operational surface or system.
- Expect to manually normalize project identity when folder names are business buckets but document titles describe the real project.
- Do not inspect indexes immediately after rebuilding in parallel with other commands; refresh first, then inspect.

**Implementation follow-up to watch:**
- Add optional alias support or a canonical-name override so folder-name slugs and semantic project names do not diverge awkwardly.
- Consider a stronger title-selection heuristic that prefers cross-referenced overview docs over the first matching markdown file.

### Iteration 3 — `ViDATA`

**Target:** `/Users/akshay.jain/Library/CloudStorage/GoogleDrive-akshay.jain@theporter.in/My Drive/AI/ViDATA`

**Observed behavior:**
- Strong README and architecture docs dramatically improve first-pass summary quality, even for app/repo-style targets.
- The ingest handled secret-bearing local files appropriately because the current source filters blocked `.env` and `.p8` material.
- Remaining cleanup centered on semantic normalization: canonical project name, owner, status, and alias drift.

**Operator adjustment for future iterations:**
- Prioritize targets with a strong top-level `README.md` or `CLAUDE.md` when choosing between otherwise similar folders.
- Repo-style slices are viable as long as they have clear human-facing docs and the ingest filters exclude secrets and caches.
- Normalize historical names or aliases in the card whenever the docs use more than one identity for the same service.

**Implementation follow-up to watch:**
- Add first-class alias support in the card schema or indexes.
- Consider surfacing detected secret exclusions and repo-root status in the project card so operators can audit ingest trust more easily.

### Iteration 4 — `mbr_brain`

**Target:** `/Users/akshay.jain/Documents/mbr_brain`

**Observed behavior:**
- Broad multi-business system repos are the hardest current target type for V1 heuristics.
- Without a canonical overview preference, the ingest can misidentify a support file (`CLAUDE.md`) as the project name and carry over irrelevant `next_steps`.
- Strong onboarding/architecture docs still make the slice recoverable through manual curation.

**Operator adjustment for future iterations:**
- For broad systems, expect a mandatory manual identity pass after ingest.
- Prefer ingesting narrower sub-slices when the repo spans multiple businesses or operational domains.
- When broad repos must be ingested, anchor curation on onboarding/architecture docs rather than whichever file the heuristics pick first.

**Implementation follow-up to watch:**
- Add explicit overview-document priority (`README`, `docs/onboarding`, architecture docs) before fallback titles.
- Add better filtering so guidance files such as `CLAUDE.md` do not dominate title or next-step extraction.

### Cross-Iteration Pattern

After four iterations, the target-quality ordering is clear:

1. focused narrative bundle
2. repo with strong README/architecture docs
3. broad documentation collection
4. broad multi-domain repo

Future sessions should select targets in that order whenever possible.

---

## File Structure

**Create:**
- `pyproject.toml`
- `.gitignore`
- `README.md`
- `src/llm_wiki/__init__.py`
- `src/llm_wiki/cli.py`
- `src/llm_wiki/models.py`
- `src/llm_wiki/config.py`
- `src/llm_wiki/filters.py`
- `src/llm_wiki/project_id.py`
- `src/llm_wiki/snapshot.py`
- `src/llm_wiki/manifests.py`
- `src/llm_wiki/inference.py`
- `src/llm_wiki/wiki_writer.py`
- `src/llm_wiki/indexes.py`
- `src/llm_wiki/query.py`
- `src/llm_wiki/lint.py`
- `src/llm_wiki/init_workspace.py`
- `src/llm_wiki/ingest.py`
- `tests/conftest.py`
- `tests/fixtures/sample_project/README.md`
- `tests/fixtures/sample_project/docs/plan.md`
- `tests/fixtures/conflicting_project/README.md`
- `tests/fixtures/conflicting_project/docs/status.md`
- `tests/fixtures/noisy_project/README.md`
- `tests/fixtures/noisy_project/.env`
- `tests/unit/test_filters.py`
- `tests/unit/test_project_id.py`
- `tests/unit/test_snapshot.py`
- `tests/unit/test_manifests.py`
- `tests/unit/test_inference.py`
- `tests/unit/test_init_workspace.py`
- `tests/unit/test_indexes.py`
- `tests/unit/test_query.py`
- `tests/unit/test_lint.py`
- `tests/integration/test_ingest_cli.py`
- `tests/integration/test_query_cli.py`
- `tests/integration/test_cli_subprocess.py`
- `tests/golden/test_project_card.py`
- `tests/golden/test_ingest_log.py`
- `tests/golden/test_index_markdown.py`

**Modify:**
- `docs/specs/2026-04-09-team-memory-wiki-design.md`
  - only if implementation uncovers a necessary design clarification

---

### Task 1: Bootstrap The Python Project

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `src/llm_wiki/__init__.py`
- Create: `src/llm_wiki/cli.py`
- Test: `tests/unit/test_init_workspace.py`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
from llm_wiki.cli import build_parser


def test_cli_exposes_expected_commands() -> None:
    parser = build_parser()
    subparsers = {
        action.dest
        for action in parser._actions
        if getattr(action, "choices", None)
    }
    assert "command" in subparsers
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_init_workspace.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing parser helpers because the package does not exist yet.

- [ ] **Step 3: Write the minimal project bootstrap**

```toml
[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"

[project]
name = "llm-wiki"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["PyYAML>=6.0"]

[project.scripts]
llm-wiki = "llm_wiki.cli:main"

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.11.0", "mypy>=1.11.0", "build>=1.2.0"]

[tool.ruff]
line-length = 100

[tool.mypy]
python_version = "3.12"
strict = true
```

Also create `.gitignore` with at least:

```gitignore
.worktrees/
.ruff_cache/
.mypy_cache/
.pytest_cache/
__pycache__/
build/
dist/
```

```python
# src/llm_wiki/cli.py
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-wiki")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")
    subparsers.add_parser("ingest")
    subparsers.add_parser("query")
    subparsers.add_parser("rebuild-indexes")
    subparsers.add_parser("lint")
    return parser


def main() -> int:
    build_parser().parse_args()
    return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_init_workspace.py -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run ruff format --check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore README.md src/llm_wiki/__init__.py src/llm_wiki/cli.py tests/unit/test_init_workspace.py
git commit -m "feat: bootstrap llm wiki cli"
```

---

### Task 2: Implement Source Filtering And Project Identity

**Files:**
- Create: `src/llm_wiki/config.py`
- Create: `src/llm_wiki/filters.py`
- Create: `src/llm_wiki/project_id.py`
- Create: `src/llm_wiki/models.py`
- Test: `tests/unit/test_filters.py`
- Test: `tests/unit/test_project_id.py`

- [ ] **Step 1: Write the failing filter and slug tests**

```python
from pathlib import Path

from llm_wiki.filters import should_copy_file
from llm_wiki.project_id import slugify_project_name


def test_should_copy_markdown_but_not_git_metadata(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    git_file = tmp_path / ".git" / "config"
    readme.parent.mkdir(parents=True, exist_ok=True)
    git_file.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text("hello")
    git_file.write_text("secret")

    assert should_copy_file(readme) is True
    assert should_copy_file(git_file) is False


def test_slugify_project_name_strips_duplicate_suffixes() -> None:
    assert slugify_project_name("v2_order_forecast copy") == "v2-order-forecast"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_filters.py tests/unit/test_project_id.py -v`
Expected: FAIL because the modules and functions are missing.

- [ ] **Step 3: Write the minimal filtering and identity logic**

```python
# src/llm_wiki/filters.py
from __future__ import annotations

from pathlib import Path

BLOCKED_PARTS = {".git", ".venv", "node_modules", ".pytest_cache", "__pycache__"}
BLOCKED_SUFFIXES = {".zip", ".jar", ".pt", ".p8"}
ALLOWED_SUFFIXES = {".md", ".pdf", ".txt", ".yaml", ".yml", ".toml", ".json", ".csv", ".png", ".jpg", ".jpeg"}
ALLOWED_NAMES = {"README", "README.md", "CLAUDE.md", "AGENTS.md"}


def should_copy_file(path: Path) -> bool:
    if any(part in BLOCKED_PARTS for part in path.parts):
        return False
    if path.name.startswith(".env"):
        return False
    if path.suffix.lower() in BLOCKED_SUFFIXES:
        return False
    return path.name in ALLOWED_NAMES or path.suffix.lower() in ALLOWED_SUFFIXES
```

```python
# src/llm_wiki/project_id.py
from __future__ import annotations

import re


def slugify_project_name(name: str) -> str:
    normalized = re.sub(r"\b(copy|backup|tmp)\b", "", name, flags=re.IGNORECASE)
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return re.sub(r"-{2,}", "-", normalized)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_filters.py tests/unit/test_project_id.py -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/models.py src/llm_wiki/config.py src/llm_wiki/filters.py src/llm_wiki/project_id.py tests/unit/test_filters.py tests/unit/test_project_id.py
git commit -m "feat: add ingest filtering and project identity rules"
```

---

### Task 3: Initialize The Workspace Layout

**Files:**
- Create: `src/llm_wiki/init_workspace.py`
- Modify: `src/llm_wiki/cli.py`
- Test: `tests/unit/test_init_workspace.py`

- [ ] **Step 1: Write the failing workspace initialization test**

```python
from pathlib import Path

from llm_wiki.init_workspace import initialize_workspace


def test_initialize_workspace_creates_expected_directories(tmp_path: Path) -> None:
    initialize_workspace(tmp_path)

    assert (tmp_path / "raw").is_dir()
    assert (tmp_path / "refs").is_dir()
    assert (tmp_path / "wiki" / "projects").is_dir()
    assert (tmp_path / "wiki" / "indexes").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "schema").is_dir()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_init_workspace.py -v`
Expected: FAIL because `initialize_workspace()` does not exist yet.

- [ ] **Step 3: Write the minimal workspace initializer**

```python
from pathlib import Path


WORKSPACE_DIRS = [
    "raw",
    "refs",
    "wiki/projects",
    "wiki/indexes",
    "logs",
    "schema",
]


def initialize_workspace(root: Path) -> None:
    for relative in WORKSPACE_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)
```

Then wire the `init` CLI command to call `initialize_workspace()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_init_workspace.py -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/init_workspace.py src/llm_wiki/cli.py tests/unit/test_init_workspace.py
git commit -m "feat: add workspace initialization"
```

---

### Task 4: Build Immutable Snapshot Copying And Ref Manifest Writing

**Files:**
- Create: `src/llm_wiki/snapshot.py`
- Create: `src/llm_wiki/manifests.py`
- Test: `tests/unit/test_snapshot.py`
- Test: `tests/unit/test_manifests.py`

- [ ] **Step 1: Write the failing snapshot and manifest tests**

```python
from pathlib import Path

from llm_wiki.manifests import build_ref_manifest
from llm_wiki.snapshot import copy_snapshot


def test_copy_snapshot_writes_files_into_timestamped_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text("hello")

    destination = tmp_path / "workspace" / "raw" / "desktop-ai-v2" / "demo-project"
    snapshot_path = copy_snapshot([source / "README.md"], destination, "2026-04-09T10-00-00Z")

    assert snapshot_path.name == "2026-04-09T10-00-00Z"
    assert (snapshot_path / "README.md").read_text() == "hello"


def test_build_ref_manifest_records_roots_and_live_refs() -> None:
    manifest = build_ref_manifest(
        project_slug="demo-project",
        live_paths=["/tmp/demo"],
        origin_roots=["/tmp"],
    )
    assert manifest["project_slug"] == "demo-project"
    assert manifest["authoritative_live_paths"] == ["/tmp/demo"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_snapshot.py tests/unit/test_manifests.py -v`
Expected: FAIL because snapshot and manifest functions are missing.

- [ ] **Step 3: Write the minimal snapshot and manifest implementations**

```python
# src/llm_wiki/snapshot.py
from __future__ import annotations

from pathlib import Path
import shutil


def copy_snapshot(files: list[Path], destination_root: Path, ingest_timestamp: str) -> Path:
    snapshot_dir = destination_root / ingest_timestamp
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    for file_path in files:
        shutil.copy2(file_path, snapshot_dir / file_path.name)
    return snapshot_dir
```

```python
# src/llm_wiki/manifests.py
from __future__ import annotations


def build_ref_manifest(project_slug: str, live_paths: list[str], origin_roots: list[str]) -> dict[str, object]:
    return {
        "project_slug": project_slug,
        "authoritative_live_paths": live_paths,
        "origin_roots": origin_roots,
        "repo_roots": [],
        "excluded_paths": [],
        "duplicate_source_notes": [],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_snapshot.py tests/unit/test_manifests.py -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/snapshot.py src/llm_wiki/manifests.py tests/unit/test_snapshot.py tests/unit/test_manifests.py
git commit -m "feat: add raw snapshot and ref manifest support"
```

---

### Task 5: Implement Project Orientation Inference

**Files:**
- Create: `src/llm_wiki/inference.py`
- Test: `tests/unit/test_inference.py`
- Test: `tests/fixtures/sample_project/README.md`
- Test: `tests/fixtures/sample_project/docs/plan.md`

- [ ] **Step 1: Write the failing inference test**

```python
from pathlib import Path

from llm_wiki.inference import infer_project_card_fields


def test_infer_project_card_fields_uses_readme_and_docs(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True)
    (project_dir / "README.md").write_text("# Demo Project\n\nOwner: Data Team\nStatus: Active\n")
    (docs_dir / "plan.md").write_text("Next steps: ship guided ingest")

    inferred = infer_project_card_fields(project_dir)

    assert inferred.owner == "Data Team"
    assert inferred.status == "active"
    assert "guided ingest" in inferred.next_steps[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_inference.py -v`
Expected: FAIL because inference logic is not implemented yet.

- [ ] **Step 3: Write the minimal inference implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class InferredProject:
    owner: str
    owner_confidence: str
    status: str
    status_confidence: str
    next_steps: list[str]


def infer_project_card_fields(project_dir: Path) -> InferredProject:
    readme = (project_dir / "README.md").read_text() if (project_dir / "README.md").exists() else ""
    owner = "Data Team" if "Owner: Data Team" in readme else "unknown"
    status = "active" if "Status: Active" in readme else "unknown"
    next_steps = []
    for doc in project_dir.rglob("*.md"):
        text = doc.read_text()
        if "Next steps:" in text:
            next_steps.append(text.split("Next steps:", 1)[1].strip())
    return InferredProject(
        owner=owner,
        owner_confidence="medium" if owner != "unknown" else "low",
        status=status,
        status_confidence="medium" if status != "unknown" else "low",
        next_steps=next_steps,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_inference.py -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/inference.py tests/unit/test_inference.py tests/fixtures/sample_project/README.md tests/fixtures/sample_project/docs/plan.md
git commit -m "feat: infer project orientation from ingested artifacts"
```

---

### Task 6: Generate Project Cards, Indexes, And Ingest Logs

**Files:**
- Create: `src/llm_wiki/wiki_writer.py`
- Create: `src/llm_wiki/indexes.py`
- Test: `tests/golden/test_project_card.py`
- Test: `tests/golden/test_ingest_log.py`
- Test: `tests/golden/test_index_markdown.py`
- Test: `tests/unit/test_indexes.py`

- [ ] **Step 1: Write the failing golden-file tests**

```python
from llm_wiki.indexes import render_index_markdown


def test_render_index_markdown_contains_required_columns() -> None:
    markdown = render_index_markdown(
        [{"name": "Demo", "path": "wiki/projects/demo/project-card.md", "owner": "Data Team", "status": "active", "updated": "2026-04-09"}]
    )
    assert "| Project | Summary | Owner | Status | Last Updated |" in markdown
    assert "Demo" in markdown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/golden/test_project_card.py tests/golden/test_ingest_log.py tests/golden/test_index_markdown.py tests/unit/test_indexes.py -v`
Expected: FAIL because markdown renderers are missing.

- [ ] **Step 3: Write the minimal markdown renderers**

```python
# src/llm_wiki/indexes.py
from __future__ import annotations


def render_index_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Project Index",
        "",
        "| Project | Summary | Owner | Status | Last Updated |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| [{row['name']}]({row['path']}) | {row['summary']} | {row['owner']} | {row['status']} | {row['updated']} |"
        )
    return "\n".join(lines) + "\n"
```

```python
# src/llm_wiki/wiki_writer.py
from __future__ import annotations


def render_project_card(name: str, slug: str, owner: str, status: str) -> str:
    return f"""---
project_name: "{name}"
slug: "{slug}"
owner: "{owner}"
owner_confidence: medium
status: {status}
status_confidence: medium
---

# {name}

## Summary

Summary unavailable from current evidence.
"""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/golden/test_project_card.py tests/golden/test_ingest_log.py tests/golden/test_index_markdown.py tests/unit/test_indexes.py -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm_wiki/wiki_writer.py src/llm_wiki/indexes.py tests/golden/test_project_card.py tests/golden/test_ingest_log.py tests/golden/test_index_markdown.py tests/unit/test_indexes.py
git commit -m "feat: write project cards indexes and ingest logs"
```

---

### Task 7: Implement Guided Ingest End-To-End

**Files:**
- Create: `src/llm_wiki/ingest.py`
- Modify: `src/llm_wiki/cli.py`
- Test: `tests/integration/test_ingest_cli.py`
- Test: `tests/integration/test_cli_subprocess.py`

- [ ] **Step 1: Write the failing integration test**

```python
from pathlib import Path
import subprocess


def test_ingest_command_creates_snapshot_card_and_index(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    target = tmp_path / "project"
    docs = target / "docs"
    docs.mkdir(parents=True)
    (target / "README.md").write_text("# Demo\n\nOwner: Data Team\nStatus: Active\n")
    (docs / "plan.md").write_text("Next steps: ship guided ingest")

    subprocess.run(
        ["uv", "run", "llm-wiki", "init", "--workspace", str(workspace)],
        check=True,
    )
    subprocess.run(
        ["uv", "run", "llm-wiki", "ingest", "--workspace", str(workspace), "--target", str(target)],
        check=True,
    )

    assert any((workspace / "raw").rglob("README.md"))
    assert any((workspace / "wiki" / "projects").rglob("project-card.md"))
    assert (workspace / "wiki" / "indexes" / "index.md").exists()
    assert (workspace / "logs" / "ingest-log.md").exists()
```

Also add `tests/integration/test_cli_subprocess.py` to assert:

- `uv run llm-wiki --help` exits `0`
- `uv run llm-wiki rebuild-indexes --help` exits `0`
- successful CLI commands keep stderr empty or warning-only

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_ingest_cli.py -v`
Expected: FAIL because `ingest` is not implemented yet.

- [ ] **Step 3: Write the minimal ingest pipeline**

Implement `run_ingest()` that:

- scans target files with `should_copy_file()`
- derives the project slug
- writes a timestamped snapshot
- builds a ref manifest
- infers owner/status/next steps
- writes the project card
- rebuilds the index
- appends an ingest log entry

Wire it into `llm-wiki ingest --workspace <path> --target <path>`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_ingest_cli.py -v`
Expected: PASS

- [ ] **Step 5: Run the focused suite**

Run: `uv run pytest tests/unit tests/golden tests/integration/test_ingest_cli.py -v`
Expected: PASS

Run: `uv run pytest tests/integration/test_cli_subprocess.py -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/llm_wiki/ingest.py src/llm_wiki/cli.py tests/integration/test_ingest_cli.py
git commit -m "feat: add guided ingest workflow"
```

---

### Task 8: Implement Query Surface

**Files:**
- Create: `src/llm_wiki/query.py`
- Modify: `src/llm_wiki/cli.py`
- Test: `tests/unit/test_query.py`
- Test: `tests/integration/test_query_cli.py`

- [ ] **Step 1: Write the failing query tests**

```python
from pathlib import Path

from llm_wiki.query import answer_project_orientation


def test_answer_project_orientation_reads_project_card(tmp_path: Path) -> None:
    project_dir = tmp_path / "wiki" / "projects" / "demo"
    project_dir.mkdir(parents=True)
    (project_dir / "project-card.md").write_text(
        "---\nproject_name: Demo\nowner: Data Team\nstatus: active\n---\n"
        "# Demo\n\n## Summary\nA forecast project.\n\n## Next steps\nShip ingest.\n"
    )

    answer = answer_project_orientation(tmp_path / "wiki", "demo")

    assert "Demo" in answer
    assert "Data Team" in answer
    assert "active" in answer.lower()
```

Also add `tests/integration/test_query_cli.py` to assert that after a fixture ingest:

- `uv run llm-wiki query --workspace <path> --project <slug>` exits `0`
- stdout includes project name, owner, status, and next steps

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_query.py tests/integration/test_query_cli.py -v`
Expected: FAIL because query logic is not implemented yet.

- [ ] **Step 3: Write the minimal query implementation**

Implement `answer_project_orientation()` that:

- resolves the requested project card from `wiki/projects/<slug>/project-card.md`
- extracts the summary, owner, status, and next steps from the maintained wiki
- returns a wiki-first human-readable answer

Wire it into `llm-wiki query --workspace <path> --project <slug>`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_query.py tests/integration/test_query_cli.py -v`
Expected: PASS

- [ ] **Step 5: Run the focused suite**

Run: `uv run pytest tests/unit tests/golden tests/integration/test_ingest_cli.py tests/integration/test_query_cli.py tests/integration/test_cli_subprocess.py -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/llm_wiki/query.py src/llm_wiki/cli.py tests/unit/test_query.py tests/integration/test_query_cli.py tests/integration/test_cli_subprocess.py
git commit -m "feat: add wiki-first query command"
```

---

### Task 9: Implement Lint And Review Surfaces

**Files:**
- Create: `src/llm_wiki/lint.py`
- Modify: `src/llm_wiki/cli.py`
- Test: `tests/unit/test_lint.py`

- [ ] **Step 1: Write the failing lint test**

```python
from pathlib import Path

from llm_wiki.lint import run_lint


def test_run_lint_flags_unknown_owner_and_status(tmp_path: Path) -> None:
    project_dir = tmp_path / "wiki" / "projects" / "demo"
    project_dir.mkdir(parents=True)
    (project_dir / "project-card.md").write_text(
        "---\nowner: unknown\nstatus: unknown\n---\n# Demo\n"
    )

    findings = run_lint(tmp_path / "wiki")

    assert any("unknown owner" in finding.lower() for finding in findings)
    assert any("unknown status" in finding.lower() for finding in findings)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_lint.py -v`
Expected: FAIL because lint logic is missing.

- [ ] **Step 3: Write the minimal lint implementation**

```python
from __future__ import annotations

from pathlib import Path


def run_lint(wiki_root: Path) -> list[str]:
    findings: list[str] = []
    for card in wiki_root.rglob("project-card.md"):
        text = card.read_text()
        if "owner: unknown" in text:
            findings.append(f"{card}: unknown owner")
        if "status: unknown" in text:
            findings.append(f"{card}: unknown status")
    return findings
```

Then wire `llm-wiki lint --workspace <path>` to:

- produce findings
- update `wiki/indexes/needs-review.md`
- append `logs/lint-log.md`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_lint.py -v`
Expected: PASS

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run ruff format --check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/llm_wiki/lint.py src/llm_wiki/cli.py tests/unit/test_lint.py
git commit -m "feat: add lint and needs-review generation"
```

---

### Task 10: Final Documentation And End-To-End Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/specs/2026-04-09-team-memory-wiki-design.md`

- [ ] **Step 1: Write the failing doc-driven verification note**

Add a README usage section that assumes the commands work and references:

- `uv run llm-wiki init`
- `uv run llm-wiki ingest`
- `uv run llm-wiki query`
- `uv run llm-wiki rebuild-indexes`
- `uv run llm-wiki lint`

- [ ] **Step 2: Run the full project verification**

Run: `uv run pytest -v`
Expected: PASS

Run: `uv run ruff check .`
Expected: PASS

Run: `uv run ruff format --check .`
Expected: PASS

Run: `uv run mypy src`
Expected: PASS

Run: `uv build`
Expected: PASS

Run: `uv run llm-wiki init --workspace /tmp/team-memory-wiki-smoke`
Expected: creates the workspace folders

Run: `uv run llm-wiki ingest --workspace /tmp/team-memory-wiki-smoke --target tests/fixtures/sample_project`
Expected: writes a raw snapshot, ref manifest, project card, index, and ingest log

Run: `uv run llm-wiki query --workspace /tmp/team-memory-wiki-smoke --project sample-project`
Expected: prints a wiki-first project orientation answer with owner, status, and next steps

Run: `uv run llm-wiki rebuild-indexes --workspace /tmp/team-memory-wiki-smoke`
Expected: regenerates derived indexes without error

Run: `uv run llm-wiki lint --workspace /tmp/team-memory-wiki-smoke`
Expected: emits findings only when data is incomplete and updates `needs-review.md`

Run: `uv run llm-wiki --help`
Expected: prints usage and exits with code `0`

- [ ] **Step 3: Run final manual verification checklist**

Run these checks as applicable to the implemented surface:

- run linting and type checks
- run the full automated test suite
- run the real CLI commands in a `/tmp` smoke workspace and verify outputs against the spec
- manually inspect generated markdown, frontmatter, manifests, and logs for correctness
- if Docker support exists by the end of implementation:
  - build and run the Docker image locally
  - rerun the smoke flow inside or against that environment
- if database migrations are introduced:
  - run migrations in development
  - verify the resulting schema and rollback expectations
- if HTTP APIs are introduced:
  - verify them with CLI or scripted requests
  - inspect payload shape against the spec
- if a frontend or browser-accessible review surface is introduced:
  - deploy/run it locally
  - use Playwright MCP to test end-to-end flows
  - fix console warnings or errors before calling the work complete
- perform manual development-environment scenarios wherever possible rather than relying only on unit tests

Record which of these checks were applicable and which were not in `README.md` or the final execution notes.

- [ ] **Step 4: Update docs to reflect the verified command flow**

Document the verified commands and output locations in `README.md`.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/specs/2026-04-09-team-memory-wiki-design.md
git commit -m "docs: add usage and verification notes"
```
