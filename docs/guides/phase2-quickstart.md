# Phase 2 Quickstart

Phase 2 is for comparing two to five known project slugs and saving reviewed answers back into the wiki.

First-time flow:

1. Initialize or copy a workspace.
2. Run `uv run llm-wiki migrate-workspace --workspace <path> --target-version 2` if the workspace was created before Phase 2.
3. Run `uv run llm-wiki rebuild-retrieval --workspace <path>-v2`.
4. Run your first query with two named projects:

```bash
uv run llm-wiki query \
  --workspace <path>-v2 \
  --project hcv \
  --project notion-sync \
  --question "Compare how mature these projects are."
```

5. Inspect the answer citations. Do not treat uncited synthesis as durable knowledge.
6. Run `uv run llm-wiki health --workspace <path>-v2` before broader usage.
7. Approve one write-back only after reviewing the rendered markdown:

```bash
uv run llm-wiki approve-writeback --workspace <path>-v2 --proposal-id <id>
```

Cross-project durable outputs are stored under `wiki/reports/`. Single-project synthesized pages use `wiki/projects/<slug>/overview.md` or `wiki/projects/<slug>/decisions.md`.
