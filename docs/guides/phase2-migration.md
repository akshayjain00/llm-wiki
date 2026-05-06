# Phase 2 Migration

Phase 2 adds a derived SQLite retrieval database, multi-project query, query logs, and manual write-back proposals while keeping raw snapshots and markdown pages as the durable workspace source of truth.

Use side-by-side migration instead of changing a V1 workspace in place:

1. Run `uv run llm-wiki migrate-workspace --workspace <path> --target-version 2`.
2. Confirm the original workspace still exists and the new sibling `<path>-v2` contains `state/index.db`.
3. Run `uv run llm-wiki rebuild-retrieval --workspace <path>-v2`.
4. Run `uv run llm-wiki health --workspace <path>-v2`.
5. Run at least one multi-project query and inspect citations before broader adoption.
6. Approve one write-back only after reviewing the pending markdown content.

If `health` reports missing chunks, run `rebuild-retrieval` after ingesting or refreshing project pages. If it reports missing query runs, run a query before treating the workspace as exercised.
