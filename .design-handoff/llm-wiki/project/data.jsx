/* global React */
// LLM Wiki — mock workspace data
// Mimics the shape of state/index.db content. Read-only.

// ── Projects ───────────────────────────────────────────────────────────────
const PROJECTS = [
  { slug: 'hcv',                  name: 'HCV',                       owner: 'Data Team',          status: 'active',     phase: 'phase-3', updated: '2026-05-09', pages: 5, backlinks: 23 },
  { slug: 'notion-sync',          name: 'Notion Sync',               owner: 'Eng / Knowledge',    status: 'active',     phase: 'phase-2', updated: '2026-05-07', pages: 4, backlinks: 18 },
  { slug: 'data-catalog-mcp',     name: 'Data Catalog MCP',          owner: 'Data Team',          status: 'active',     phase: 'phase-3', updated: '2026-05-09', pages: 6, backlinks: 31 },
  { slug: 'image-indexing',       name: 'Image Indexing',            owner: 'ML Platform',        status: 'active',     phase: 'phase-1', updated: '2026-05-06', pages: 3, backlinks: 9  },
  { slug: 'team-memory-wiki',     name: 'Team Memory Wiki',          owner: 'Akshay Jain',        status: 'active',     phase: 'phase-3', updated: '2026-05-09', pages: 8, backlinks: 42 },
  { slug: 'karpathy-exports',     name: 'Karpathy Exports',          owner: 'Akshay Jain',        status: 'active',     phase: 'phase-2', updated: '2026-05-04', pages: 3, backlinks: 7  },
  { slug: 'slack-digest',         name: 'Slack Digest',              owner: 'Internal Tools',     status: 'paused',     phase: 'phase-1', updated: '2026-04-22', pages: 3, backlinks: 4  },
  { slug: 'github-sync',          name: 'GitHub Sync',               owner: 'Eng / Knowledge',    status: 'active',     phase: 'phase-2', updated: '2026-05-08', pages: 4, backlinks: 14 },
  { slug: 'eval-harness',         name: 'Eval Harness',              owner: 'ML Platform',        status: 'active',     phase: 'phase-2', updated: '2026-05-07', pages: 5, backlinks: 19 },
  { slug: 'embedding-pipeline',   name: 'Embedding Pipeline',        owner: 'ML Platform',        status: 'active',     phase: 'phase-3', updated: '2026-05-09', pages: 4, backlinks: 22 },
  { slug: 'snapshot-manager',     name: 'Snapshot Manager',          owner: 'Eng / Knowledge',    status: 'active',     phase: 'phase-2', updated: '2026-05-05', pages: 3, backlinks: 11 },
  { slug: 'schema-migrator',      name: 'Schema Migrator',           owner: 'Data Team',          status: 'active',     phase: 'phase-2', updated: '2026-05-03', pages: 3, backlinks: 8  },
  { slug: 'query-synthesizer',    name: 'Query Synthesizer',         owner: 'ML Platform',        status: 'active',     phase: 'phase-2', updated: '2026-05-08', pages: 4, backlinks: 17 },
  { slug: 'doc-bot',              name: 'Doc Bot',                   owner: 'Internal Tools',     status: 'archived',   phase: 'shipped', updated: '2026-03-19', pages: 2, backlinks: 3  },
];

// ── People ─────────────────────────────────────────────────────────────────
const PEOPLE = [
  { id: 'person:akshay-jain',  name: 'Akshay Jain',  role: 'Solo operator',     refs: 47 },
  { id: 'person:marta-vega',   name: 'Marta Vega',   role: 'Eng / Knowledge',   refs: 21 },
  { id: 'person:dhruv-shah',   name: 'Dhruv Shah',   role: 'ML Platform',       refs: 18 },
  { id: 'person:lin-park',     name: 'Lin Park',     role: 'Data Team',         refs: 14 },
  { id: 'person:tomas-iglesias',name:'Tomás Iglesias',role:'Internal Tools',    refs: 9  },
  { id: 'person:codex',        name: 'Codex',        role: 'Coding agent',      refs: 31 },
  { id: 'person:claude-code',  name: 'Claude Code',  role: 'Coding agent',      refs: 28 },
];

// ── Concepts (deterministic, derived from headings & internal links) ───────
const CONCEPTS = [
  { id: 'concept:backlinks',           name: 'Backlinks',              refs: 36 },
  { id: 'concept:proposed-links',      name: 'Proposed Links',         refs: 27 },
  { id: 'concept:graph-rebuild',       name: 'Graph Rebuild',          refs: 22 },
  { id: 'concept:entity-resolution',   name: 'Entity Resolution',      refs: 19 },
  { id: 'concept:mcp-server',          name: 'MCP Server',             refs: 25 },
  { id: 'concept:read-only',           name: 'Read-Only',              refs: 18 },
  { id: 'concept:fts',                 name: 'FTS',                    refs: 14 },
  { id: 'concept:embeddings',          name: 'Embeddings',             refs: 16 },
  { id: 'concept:fastmcp',             name: 'FastMCP',                refs: 11 },
  { id: 'concept:adjacency-list',      name: 'Adjacency List',         refs: 7  },
  { id: 'concept:cytoscape',           name: 'Cytoscape.js',           refs: 5  },
  { id: 'concept:starlette',           name: 'Starlette',              refs: 6  },
  { id: 'concept:writeback',           name: 'Writeback',              refs: 12 },
  { id: 'concept:durable-state',       name: 'Durable State',          refs: 14 },
  { id: 'concept:audit-log',           name: 'Audit Log',              refs: 8  },
  { id: 'concept:base-content-hash',   name: 'Base Content Hash',      refs: 9  },
  { id: 'concept:link-confidence',     name: 'Link Confidence',        refs: 11 },
  { id: 'concept:ambiguous-alias',     name: 'Ambiguous Alias',        refs: 6  },
  { id: 'concept:karpathy-layer',      name: 'Karpathy Layered Wiki',  refs: 13 },
];

// ── Pages ──────────────────────────────────────────────────────────────────
function pagesForProjects() {
  const pages = [];
  for (const p of PROJECTS) {
    pages.push({ id: `page:wiki/projects/${p.slug}/project-card.md`,
      title: `${p.name} — Project Card`, kind: 'project-card', project: p.slug,
      path: `wiki/projects/${p.slug}/project-card.md`, hash: 'a1b2c3', words: 240, updated: p.updated });
    pages.push({ id: `page:wiki/projects/${p.slug}/overview.md`,
      title: `${p.name} Overview`, kind: 'overview', project: p.slug,
      path: `wiki/projects/${p.slug}/overview.md`, hash: 'a1b2c4', words: 1240, updated: p.updated });
    pages.push({ id: `page:wiki/projects/${p.slug}/decisions.md`,
      title: `${p.name} Decisions`, kind: 'decisions', project: p.slug,
      path: `wiki/projects/${p.slug}/decisions.md`, hash: 'a1b2c5', words: 880, updated: p.updated });
    if (p.pages >= 4) {
      pages.push({ id: `page:wiki/projects/${p.slug}/architecture.md`,
        title: `${p.name} Architecture`, kind: 'page', project: p.slug,
        path: `wiki/projects/${p.slug}/architecture.md`, hash: 'a1b2c6', words: 1620, updated: p.updated });
    }
    if (p.pages >= 5) {
      pages.push({ id: `page:wiki/projects/${p.slug}/runbook.md`,
        title: `${p.name} Runbook`, kind: 'page', project: p.slug,
        path: `wiki/projects/${p.slug}/runbook.md`, hash: 'a1b2c7', words: 1180, updated: p.updated });
    }
    if (p.pages >= 6) {
      pages.push({ id: `page:wiki/projects/${p.slug}/integration-spec.md`,
        title: `${p.name} Integration Spec`, kind: 'page', project: p.slug,
        path: `wiki/projects/${p.slug}/integration-spec.md`, hash: 'a1b2c8', words: 2340, updated: p.updated });
    }
  }
  return pages;
}

const REPORTS = [
  { id: 'page:wiki/reports/2026-05-09-phase-3-graph-mcp-ui-spec.md', title: 'Phase 3: Graph, MCP, And Read-Only UI Spec', kind: 'report', project: null,
    path: 'wiki/reports/2026-05-09-phase-3-graph-mcp-ui-spec.md', hash: 'r3a8b1', words: 5840, updated: '2026-05-09' },
  { id: 'page:wiki/reports/2026-05-05-phase-2-retrieval-writeback.md', title: 'Phase 2: Retrieval & Writeback', kind: 'report', project: null,
    path: 'wiki/reports/2026-05-05-phase-2-retrieval-writeback.md', hash: 'r2c4d2', words: 4220, updated: '2026-05-05' },
  { id: 'page:wiki/reports/2026-04-09-team-memory-wiki-design.md', title: 'Team Memory Wiki — Initial Design', kind: 'report', project: null,
    path: 'wiki/reports/2026-04-09-team-memory-wiki-design.md', hash: 'r1e7f3', words: 3120, updated: '2026-04-09' },
  { id: 'page:wiki/reports/2026-05-01-graph-research-synthesis.md', title: 'Graph UX Research Synthesis (Obsidian / Dendron / Mem)', kind: 'report', project: null,
    path: 'wiki/reports/2026-05-01-graph-research-synthesis.md', hash: 'r4g9h0', words: 2410, updated: '2026-05-01' },
  { id: 'page:wiki/reports/2026-05-08-mcp-inspector-results.md', title: 'MCP Inspector Verification Run #14', kind: 'report', project: null,
    path: 'wiki/reports/2026-05-08-mcp-inspector-results.md', hash: 'r5i3j7', words: 980,  updated: '2026-05-08' },
  { id: 'page:wiki/reports/2026-04-30-phase-2-retro.md', title: 'Phase 2 Retrospective', kind: 'report', project: null,
    path: 'wiki/reports/2026-04-30-phase-2-retro.md', hash: 'r6k2l8', words: 1430, updated: '2026-04-30' },
];

const PAGES = [...pagesForProjects(), ...REPORTS];

// ── Entities (everything you can resolve) ─────────────────────────────────
const ENTITIES = [
  ...PROJECTS.map(p => ({
    id: `project:${p.slug}`, type: 'project', name: p.name, slug: p.slug,
    aliases: [p.name, p.slug, p.name.toLowerCase()],
    pages: PAGES.filter(g => g.project === p.slug).length,
    backlinks: p.backlinks,
    project: p.slug,
  })),
  ...PEOPLE.map(p => ({
    id: p.id, type: 'person', name: p.name,
    aliases: [p.name, p.name.split(' ')[0]],
    pages: 0, backlinks: p.refs, role: p.role,
  })),
  ...CONCEPTS.map(c => ({
    id: c.id, type: 'concept', name: c.name,
    aliases: [c.name, c.name.toLowerCase()],
    pages: 0, backlinks: c.refs,
  })),
];

// ── Edges (selected handcrafted set, plus auto-generated belongs_to) ──────
const EDGES_RAW = [
  // links_to (existing markdown links)
  { src: 'page:wiki/projects/notion-sync/overview.md',         tgt: 'project:hcv',                       type: 'links_to',  evidence: 'Notion Sync feeds into [HCV](../hcv/project-card.md) for entity resolution.', line: 14 },
  { src: 'page:wiki/projects/data-catalog-mcp/overview.md',    tgt: 'project:hcv',                       type: 'links_to',  evidence: 'See [HCV](../hcv/project-card.md) for downstream ownership data.', line: 22 },
  { src: 'page:wiki/projects/data-catalog-mcp/architecture.md',tgt: 'project:notion-sync',               type: 'links_to',  evidence: 'Catalog rows are reconciled against [Notion Sync](../notion-sync/project-card.md).', line: 41 },
  { src: 'page:wiki/projects/embedding-pipeline/overview.md',  tgt: 'project:eval-harness',              type: 'links_to',  evidence: 'Embedding quality is measured by [Eval Harness](../eval-harness/project-card.md).', line: 9 },
  { src: 'page:wiki/projects/team-memory-wiki/architecture.md',tgt: 'project:embedding-pipeline',        type: 'links_to',  evidence: 'Lexical retrieval is augmented by [Embedding Pipeline](../embedding-pipeline/project-card.md).', line: 76 },
  { src: 'page:wiki/projects/team-memory-wiki/overview.md',    tgt: 'concept:karpathy-layer',            type: 'links_to',  evidence: 'A [Karpathy Layered Wiki](../../concepts/karpathy-layer.md) compounds team understanding.', line: 4 },
  { src: 'page:wiki/reports/2026-05-09-phase-3-graph-mcp-ui-spec.md', tgt: 'project:team-memory-wiki', type: 'links_to', evidence: 'See [Team Memory Wiki](../projects/team-memory-wiki/project-card.md) workspace state.', line: 18 },
  { src: 'page:wiki/reports/2026-05-09-phase-3-graph-mcp-ui-spec.md', tgt: 'concept:mcp-server',          type: 'links_to', evidence: 'A read-only [MCP Server](../concepts/mcp-server.md) exposes graph state.', line: 32 },
  { src: 'page:wiki/reports/2026-05-09-phase-3-graph-mcp-ui-spec.md', tgt: 'concept:proposed-links',      type: 'links_to', evidence: 'High-confidence [Proposed Links](../concepts/proposed-links.md) populate the queue.', line: 88 },
  { src: 'page:wiki/projects/hcv/decisions.md',                tgt: 'project:notion-sync',               type: 'links_to',  evidence: 'Decision: defer raw entity merges to [Notion Sync](../notion-sync/decisions.md).', line: 33 },
  { src: 'page:wiki/projects/karpathy-exports/overview.md',    tgt: 'concept:karpathy-layer',            type: 'links_to',  evidence: 'Exports follow the [Karpathy Layered Wiki](../../concepts/karpathy-layer.md) shape.', line: 7 },
  { src: 'page:wiki/projects/eval-harness/integration-spec.md',tgt: 'project:embedding-pipeline',        type: 'links_to',  evidence: 'Each run snapshots [Embedding Pipeline](../embedding-pipeline/project-card.md) hashes.', line: 56 },
  { src: 'page:wiki/projects/query-synthesizer/architecture.md',tgt: 'concept:fts',                      type: 'links_to',  evidence: 'Queries fall back to [FTS](../../concepts/fts.md) when embeddings miss.', line: 92 },
  { src: 'page:wiki/projects/snapshot-manager/decisions.md',   tgt: 'project:github-sync',               type: 'links_to',  evidence: 'See [GitHub Sync](../github-sync/decisions.md) for snapshot ownership.', line: 12 },

  // mentions (graph-extracted, no markdown link yet — likely proposal candidates)
  { src: 'page:wiki/projects/hcv/overview.md',                  tgt: 'project:notion-sync',               type: 'mentions', evidence: 'We rely on Notion Sync to surface owners that the catalog cannot resolve.', line: 31 },
  { src: 'page:wiki/projects/hcv/overview.md',                  tgt: 'project:data-catalog-mcp',          type: 'mentions', evidence: 'Data Catalog MCP exposes the same project rows over MCP read-only tools.', line: 47 },
  { src: 'page:wiki/projects/image-indexing/overview.md',       tgt: 'project:notion-sync',               type: 'mentions', evidence: 'Notion Sync provides labels for the small image cohort.', line: 19 },
  { src: 'page:wiki/projects/data-catalog-mcp/decisions.md',    tgt: 'project:image-indexing',            type: 'mentions', evidence: 'Image Indexing should not fan out to the catalog without batching.', line: 6 },
  { src: 'page:wiki/projects/eval-harness/overview.md',         tgt: 'project:query-synthesizer',         type: 'mentions', evidence: 'Query Synthesizer outputs feed the synthesis evals nightly.', line: 24 },
  { src: 'page:wiki/projects/team-memory-wiki/decisions.md',    tgt: 'concept:fastmcp',                   type: 'mentions', evidence: 'We adopt FastMCP for the Phase 3 server because of structured outputs.', line: 11 },
  { src: 'page:wiki/projects/team-memory-wiki/architecture.md', tgt: 'concept:starlette',                 type: 'mentions', evidence: 'A Starlette app factory will host the Phase 3 UI.', line: 102 },
  { src: 'page:wiki/projects/team-memory-wiki/overview.md',     tgt: 'concept:cytoscape',                 type: 'mentions', evidence: 'Cytoscape.js is recommended only paired with an adjacency list fallback.', line: 64 },
  { src: 'page:wiki/projects/snapshot-manager/overview.md',     tgt: 'concept:durable-state',             type: 'mentions', evidence: 'Snapshots are write-once; the durable state contract forbids edits.', line: 8 },
  { src: 'page:wiki/projects/embedding-pipeline/decisions.md',  tgt: 'concept:embeddings',                type: 'mentions', evidence: 'Embeddings remain optional in Phase 3 to keep local installs cheap.', line: 14 },

  // belongs_to_project (synthetic, applied to every page)
];

const EDGES = [...EDGES_RAW];
for (const page of PAGES) {
  if (page.project) {
    EDGES.push({ src: page.id, tgt: `project:${page.project}`, type: 'belongs_to_project',
      evidence: 'Page lives in project folder.', line: null });
  }
}

// ── Proposed link queue ────────────────────────────────────────────────────
const PROPOSALS = [
  { id: 'link_a8d31c', source_path: 'wiki/projects/hcv/overview.md', target_node_id: 'project:notion-sync',
    target_title: 'Notion Sync', original_text: 'Notion Sync', confidence: 0.96, status: 'pending', line: 31,
    rationale: 'Exact alias match to project slug notion-sync. Mention in prose, no existing markdown link, no code fence.' },
  { id: 'link_b2c481', source_path: 'wiki/projects/hcv/overview.md', target_node_id: 'project:data-catalog-mcp',
    target_title: 'Data Catalog MCP', original_text: 'Data Catalog MCP', confidence: 0.95, status: 'pending', line: 47,
    rationale: 'Exact alias match to project slug data-catalog-mcp. Single canonical resolution.' },
  { id: 'link_c4e102', source_path: 'wiki/projects/image-indexing/overview.md', target_node_id: 'project:notion-sync',
    target_title: 'Notion Sync', original_text: 'Notion Sync', confidence: 0.94, status: 'pending', line: 19,
    rationale: 'Exact alias match. Mention occurs once outside frontmatter and code.' },
  { id: 'link_d6f7a0', source_path: 'wiki/projects/data-catalog-mcp/decisions.md', target_node_id: 'project:image-indexing',
    target_title: 'Image Indexing', original_text: 'Image Indexing', confidence: 0.93, status: 'pending', line: 6,
    rationale: 'Exact alias match. No existing link.' },
  { id: 'link_e8a932', source_path: 'wiki/projects/eval-harness/overview.md', target_node_id: 'project:query-synthesizer',
    target_title: 'Query Synthesizer', original_text: 'Query Synthesizer', confidence: 0.92, status: 'pending', line: 24,
    rationale: 'Exact alias match. Multiple mentions resolved to single canonical entity.' },
  { id: 'link_f0b1c8', source_path: 'wiki/projects/team-memory-wiki/decisions.md', target_node_id: 'concept:fastmcp',
    target_title: 'FastMCP', original_text: 'FastMCP', confidence: 0.91, status: 'pending', line: 11,
    rationale: 'Exact alias match to concept fastmcp via heading-derived alias.' },
  { id: 'link_a1d502', source_path: 'wiki/projects/team-memory-wiki/architecture.md', target_node_id: 'concept:starlette',
    target_title: 'Starlette', original_text: 'Starlette', confidence: 0.91, status: 'pending', line: 102,
    rationale: 'Exact alias match to concept starlette.' },
  { id: 'link_b3e642', source_path: 'wiki/projects/team-memory-wiki/overview.md', target_node_id: 'concept:cytoscape',
    target_title: 'Cytoscape.js', original_text: 'Cytoscape.js', confidence: 0.94, status: 'pending', line: 64,
    rationale: 'Exact alias match. Mention in prose; no existing link.' },
  { id: 'link_c5f783', source_path: 'wiki/projects/snapshot-manager/overview.md', target_node_id: 'concept:durable-state',
    target_title: 'Durable State', original_text: 'durable state contract', confidence: 0.90, status: 'pending', line: 8,
    rationale: 'Alias match via lowercased normalization. Single resolution.' },
  { id: 'link_d7a014', source_path: 'wiki/projects/embedding-pipeline/decisions.md', target_node_id: 'concept:embeddings',
    target_title: 'Embeddings', original_text: 'Embeddings', confidence: 0.93, status: 'pending', line: 14,
    rationale: 'Heading-derived alias match. Skipped frontmatter and code fences.' },
  { id: 'link_e9b125', source_path: 'wiki/projects/query-synthesizer/architecture.md', target_node_id: 'concept:fts',
    target_title: 'FTS', original_text: 'FTS', confidence: 0.91, status: 'pending', line: 92,
    rationale: 'Acronym alias resolved deterministically. Single canonical concept.' },
  { id: 'link_f1c236', source_path: 'wiki/projects/karpathy-exports/decisions.md', target_node_id: 'project:team-memory-wiki',
    target_title: 'Team Memory Wiki', original_text: 'Team Memory Wiki', confidence: 0.97, status: 'pending', line: 5,
    rationale: 'Exact alias match. Highest-confidence proposal in queue.' },
  { id: 'link_a2d347', source_path: 'wiki/projects/github-sync/overview.md', target_node_id: 'project:snapshot-manager',
    target_title: 'Snapshot Manager', original_text: 'Snapshot Manager', confidence: 0.94, status: 'pending', line: 38,
    rationale: 'Exact alias match. No existing markdown link in surrounding span.' },
  { id: 'link_b4e458', source_path: 'wiki/projects/schema-migrator/architecture.md', target_node_id: 'project:data-catalog-mcp',
    target_title: 'Data Catalog MCP', original_text: 'Data Catalog MCP', confidence: 0.95, status: 'pending', line: 21,
    rationale: 'Exact alias match. Skipped citation block.' },
  { id: 'link_c6f569', source_path: 'wiki/projects/hcv/decisions.md', target_node_id: 'concept:writeback',
    target_title: 'Writeback', original_text: 'writeback', confidence: 0.90, status: 'pending', line: 7,
    rationale: 'Lowercased alias match. Heading-derived concept.' },
  { id: 'link_d8a67a', source_path: 'wiki/reports/2026-04-30-phase-2-retro.md', target_node_id: 'project:notion-sync',
    target_title: 'Notion Sync', original_text: 'Notion Sync', confidence: 0.93, status: 'pending', line: 12,
    rationale: 'Exact alias match. Mention in retro context.' },
  { id: 'link_e0b78b', source_path: 'wiki/projects/team-memory-wiki/overview.md', target_node_id: 'concept:karpathy-layer',
    target_title: 'Karpathy Layered Wiki', original_text: 'layered LLM wiki', confidence: 0.88, status: 'pending', line: 4,
    rationale: 'Soft alias match — slightly below high-confidence threshold but kept for review.' },
];

// Backlinks: derived from EDGES (target ← source)
function backlinksFor(targetId, edgeTypes) {
  return EDGES
    .filter(e => e.tgt === targetId && (!edgeTypes || edgeTypes.includes(e.type)))
    .map(e => {
      const srcPage = PAGES.find(p => p.id === e.src);
      return {
        source_node_id: e.src,
        source_title: srcPage ? srcPage.title : e.src,
        source_path: srcPage ? srcPage.path : null,
        edge_type: e.type,
        evidence: e.evidence,
        line: e.line,
      };
    });
}

function outboundFor(sourceId) {
  return EDGES
    .filter(e => e.src === sourceId)
    .map(e => {
      const tgtEnt = ENTITIES.find(n => n.id === e.tgt) || PAGES.find(n => n.id === e.tgt);
      return { ...e, target_title: tgtEnt ? tgtEnt.name || tgtEnt.title : e.tgt };
    });
}

// Activity stream
const ACTIVITY = [
  { when: '14:02 today', what: <>Graph rebuild <b>graph_a91c</b> · 142 pages · 318 edges · 17 proposals</> },
  { when: '13:58 today', what: <>MCP server connected to Claude Code · 4 tools listed</> },
  { when: '11:24 today', what: <>New report indexed: <b>Phase 3: Graph, MCP, And Read-Only UI Spec</b></> },
  { when: '09:30 today', what: <>3 new proposed links queued from <b>team-memory-wiki/overview.md</b></> },
  { when: 'yesterday',   what: <>Decision recorded in <b>hcv/decisions.md</b> · 1 backlink resolved</> },
  { when: '2 days ago',  what: <>Snapshot ingested from <b>github-sync</b> · 12 files added</> },
  { when: '2 days ago',  what: <>Eval Harness baseline rerun · regression on 2 cases</> },
];

// Health checks
const HEALTH = [
  { id: 'graph_tables',     label: 'Graph tables present',         desc: 'graph_nodes, graph_edges, entity_aliases, link_proposals', status: 'ok',   value: '4/4' },
  { id: 'rebuild_fresh',    label: 'Graph rebuild freshness',      desc: 'Last rebuild matches current file hashes',                  status: 'ok',   value: '0 stale' },
  { id: 'unresolved_links', label: 'Unresolved internal links',    desc: 'Markdown links pointing to missing pages',                   status: 'warn', value: '3' },
  { id: 'duplicate_alias',  label: 'Duplicate entity aliases',     desc: 'Aliases that resolve to multiple entities',                  status: 'ok',   value: '0' },
  { id: 'ambiguous',        label: 'Ambiguous resolutions',        desc: 'Mentions that match multiple canonical entities',            status: 'warn', value: '2' },
  { id: 'stale_proposals',  label: 'Proposals with stale base hash',desc: 'Proposals that no longer match source content',             status: 'ok',   value: '0' },
  { id: 'orphan_nodes',     label: 'Graph nodes without source',   desc: 'Nodes that should be file-backed but are not',               status: 'ok',   value: '0' },
  { id: 'embeddings',       label: 'Embedding rows',               desc: 'Optional embedding index over chunks',                       status: 'warn', value: 'disabled' },
  { id: 'fts',              label: 'FTS index',                    desc: 'Lexical index over wiki chunks',                             status: 'ok',   value: '142 docs' },
  { id: 'mcp_stdout',       label: 'MCP stdout cleanliness',       desc: 'No non-MCP logs on stdout in stdio mode',                    status: 'ok',   value: 'clean' },
];

// Lookup helpers
const byId = id => ENTITIES.find(e => e.id === id) || PAGES.find(p => p.id === id);

window.WikiData = {
  PROJECTS, PEOPLE, CONCEPTS, PAGES, REPORTS,
  ENTITIES, EDGES, PROPOSALS, ACTIVITY, HEALTH,
  backlinksFor, outboundFor, byId,
};
