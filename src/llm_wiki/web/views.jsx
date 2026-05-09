/* global React, Icon, Pill, Confidence */
const { useState, useMemo } = React;

// ─── Overview ──────────────────────────────────────────────────────────────
function OverviewView({ navigate, actions }) {
  const { PROJECTS, PAGES, ENTITIES, EDGES, PROPOSALS, ACTIVITY } = window.WikiData;
  const tiles = [
    { label: 'Pages',         value: PAGES.length,        delta: '+3 today',     trend: 'up',   spark: [4,5,6,8,10,12,12,14,15,17] },
    { label: 'Entities',      value: ENTITIES.length,     delta: '+5 this week', trend: 'up',   spark: [10,12,12,14,16,18,20,22,22,24] },
    { label: 'Edges',         value: EDGES.length,        delta: '+22 this week',trend: 'up',   spark: [3,5,8,10,14,18,22,26,28,32] },
    { label: 'Pending Links', value: PROPOSALS.length,    delta: '4 new',        trend: 'flat', spark: [12,12,13,13,14,15,15,16,17,17] },
  ];
  return (
    <main className="main" id="main" tabIndex="-1">
      <div className="page-h">
        <div>
          <div className="breadcrumb">~/AI_V2/team_memory_wiki · phase-3 · graph</div>
          <h1>Workspace</h1>
          <div className="sub">
            Local read-only browser over the durable wiki graph. Search, inspect backlinks, review
            proposed cross-links — never mutates markdown.
          </div>
        </div>
        <div className="page-actions">
          <button className="btn ghost" onClick={() => actions && actions.openRebuild()}><Icon name="refresh" />rebuild</button>
          <button className="btn ghost" onClick={() => actions && actions.openNewProject()}><Icon name="plus" />new project</button>
          <button className="btn primary" onClick={() => navigate('graph')}><Icon name="graph" />open graph</button>
        </div>
      </div>

      <div className="tiles">
        {tiles.map(t => <StatTile key={t.label} {...t} />)}
      </div>

      <div className="cols-2">
        <div className="panel">
          <div className="panel__h">
            <h2>Projects</h2>
            <span className="meta">{PROJECTS.length} · sorted by last update</span>
          </div>
          <div className="panel__b panel__b--flush">
            <div className="thead grid-pages">
              <span>Project</span><span>Owner</span><span>Phase</span><span>Pages</span><span>Updated</span>
            </div>
            {PROJECTS.slice(0, 8).map(p => (
              <div key={p.slug} className="list-row grid-pages" onClick={() => navigate('entities', { id: 'project:' + p.slug })}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: p.status === 'active' ? 'var(--ok)' : p.status === 'paused' ? 'var(--warn)' : 'var(--ink-5)', flexShrink: 0 }} />
                  <span className="title truncate">{p.name}</span>
                  <span className="path">{p.slug}</span>
                </span>
                <span className="path truncate">{p.owner}</span>
                <span><Pill kind="project">{p.phase}</Pill></span>
                <span className="meta">{p.pages}</span>
                <span className="meta">{p.updated.slice(5)}</span>
              </div>
            ))}
          </div>
          <div className="panel__f">Showing 8 of {PROJECTS.length} · click a row to inspect</div>
        </div>

        <div className="panel">
          <div className="panel__h">
            <h2>Recent Activity</h2>
            <span className="meta">last 24h</span>
          </div>
          <div className="timeline">
            {ACTIVITY.map((a, i) => (
              <div key={i} className="item">
                <div className="when">{a.when}</div>
                <div className="what">{a.what}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="cols-2">
        <div className="panel">
          <div className="panel__h"><h2>Top Entities</h2><span className="meta">by backlinks</span></div>
          <div className="list">
            {[...ENTITIES].sort((a,b) => b.backlinks - a.backlinks).slice(0, 7).map(e => (
              <div key={e.id} className="list-row" style={{ gridTemplateColumns: '24px 1fr 70px 60px' }}
                   onClick={() => navigate('entities', { id: e.id })}>
                <Pill kind={e.type}>{e.type[0]}</Pill>
                <span className="title truncate">{e.name}</span>
                <span className="meta">{e.backlinks} bl</span>
                <span className="meta">{e.aliases.length} a</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel__h">
            <h2>High-Confidence Proposals</h2>
            <span className="meta">≥ 0.94</span>
          </div>
          <div className="list">
            {PROPOSALS.filter(p => p.confidence >= 0.94).slice(0, 6).map(p => (
              <div key={p.id} className="list-row" style={{ gridTemplateColumns: '1fr 90px 70px' }}
                   onClick={() => navigate('proposals', { id: p.id })}>
                <span className="truncate">
                  <span className="title">{p.original_text}</span>
                  <span style={{ color: 'var(--ink-4)' }}> → </span>
                  <span style={{ color: 'var(--accent-ink)' }}>{p.target_title}</span>
                </span>
                <Confidence value={p.confidence} />
                <span className="meta">{p.id.slice(5)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

function StatTile({ label, value, delta, trend, spark }) {
  const max = Math.max(...spark);
  const w = 56, h = 22;
  const path = spark.map((v, i) => `${i === 0 ? 'M' : 'L'} ${(i / (spark.length - 1)) * w} ${h - (v / max) * h}`).join(' ');
  const arrow = trend === 'up' ? '▲' : trend === 'down' ? '▼' : '→';
  return (
    <div className="tile">
      <div className="label">{label}</div>
      <div className="value">{value.toLocaleString()}</div>
      <div className={'delta ' + trend}><span>{arrow}</span> {delta}</div>
      <svg className="spark" viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
        <path d={path} fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    </div>
  );
}

// ─── Pages list ────────────────────────────────────────────────────────────
function PagesView({ navigate, selectedId, filters, setFilter }) {
  const { PAGES } = window.WikiData;
  const [q, setQ] = useState('');
  const [kind, setKind] = useState('all');

  const filtered = useMemo(() => {
    return PAGES.filter(p => {
      if (filters.project && p.project !== filters.project) return false;
      if (kind !== 'all' && (kind === 'report' ? p.kind !== 'report' : p.kind === 'report')) return false;
      if (q && !p.title.toLowerCase().includes(q.toLowerCase()) && !p.path.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [filters.project, kind, q]);

  const selected = selectedId ? PAGES.find(p => p.id === selectedId) : null;

  if (selected) return <PageDetailView page={selected} navigate={navigate} />;

  return (
    <main className="main" id="main" tabIndex="-1">
      <div className="page-h">
        <div>
          <div className="breadcrumb">wiki / pages</div>
          <h1>Pages</h1>
          <div className="sub">{PAGES.length} durable wiki pages · project cards, overviews, decisions, runbooks, reports.</div>
        </div>
      </div>

      <div className="search-inline">
        <Icon name="search" />
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Filter pages by title or path…" />
        <span className="meta">{filtered.length} / {PAGES.length}</span>
      </div>

      <div className="filter-bar">
        <button className={'f-chip' + (kind === 'all' ? ' is-on' : '')} onClick={() => setKind('all')}>All <span className="n">{PAGES.length}</span></button>
        <button className={'f-chip' + (kind === 'project' ? ' is-on' : '')} onClick={() => setKind('project')}>Project pages <span className="n">{PAGES.filter(p => p.kind !== 'report').length}</span></button>
        <button className={'f-chip' + (kind === 'report' ? ' is-on' : '')} onClick={() => setKind('report')}>Reports <span className="n">{PAGES.filter(p => p.kind === 'report').length}</span></button>
        {filters.project && (
          <button className="f-chip is-on" onClick={() => setFilter('project', null)}>
            project: {filters.project} <Icon name="x" />
          </button>
        )}
      </div>

      <div className="panel">
        <div className="thead grid-pages">
          <span>Title</span><span>Path</span><span>Kind</span><span>Words</span><span>Updated</span>
        </div>
        <div className="list">
          {filtered.map(p => (
            <div key={p.id} className="list-row grid-pages" onClick={() => navigate('pages', { id: p.id })}>
              <span className="title truncate">{p.title}</span>
              <span className="path truncate">{p.path}</span>
              <span><Pill kind={p.kind === 'report' ? 'report' : p.kind === 'decisions' ? 'decision' : 'page'}>{p.kind}</Pill></span>
              <span className="meta">{p.words.toLocaleString()}</span>
              <span className="meta">{p.updated.slice(5)}</span>
            </div>
          ))}
          {filtered.length === 0 && <div className="empty">No pages match your filters.</div>}
        </div>
      </div>
    </main>
  );
}

// ─── Page detail ────────────────────────────────────────────────────────────
function PageDetailView({ page, navigate }) {
  const { PROPOSALS } = window.WikiData;
  const toast = useToast();
  const myProps = PROPOSALS.filter(p => p.source_path === page.path);
  return (
    <main className="main" id="main" tabIndex="-1">
      <div className="page-h">
        <div>
          <div className="breadcrumb">
            <a onClick={() => navigate('pages')}>pages</a> / <span style={{ color: 'var(--ink-2)' }}>{page.path}</span>
          </div>
          <h1 style={{ fontSize: 'var(--t-xl)' }}>{page.title}</h1>
          <div className="sub" style={{ display: 'flex', gap: 16, fontSize: 'var(--t-sm)' }}>
            <span><Pill kind={page.kind === 'report' ? 'report' : page.kind === 'decisions' ? 'decision' : 'page'}>{page.kind}</Pill></span>
            <span className="mono" style={{ color: 'var(--ink-4)' }}>{page.words.toLocaleString()} words · {page.hash} · {page.updated}</span>
          </div>
        </div>
        <div className="page-actions">
          <button className="btn ghost" onClick={() => {
            const uri = `wiki://${page.id}`;
            navigator.clipboard && navigator.clipboard.writeText(uri);
            toast && toast.push('Copied MCP URI', { kind: 'ok', detail: uri });
          }}><Icon name="copy" />copy MCP URI</button>
          <button className="btn ghost" onClick={() => navigate('graph', { id: page.id })}><Icon name="graph" />open in graph</button>
        </div>
      </div>

      <div className="md">
        <div className="frontmatter">{`---
title: ${page.title}
project: ${page.project || '~'}
kind: ${page.kind}
hash: ${page.hash}
updated: ${page.updated}
---`}</div>

        <h1>{page.title}</h1>
        <p>
          {page.title} is part of the durable team memory workspace. This page is rendered
          read-only by the Phase 3 UI; mutations only ever happen through reviewed write-back flows.
        </p>
        <h2>Context</h2>
        <p>
          The {page.project || 'workspace'} surface composes with{' '}
          <a onClick={() => navigate('entities', { id: 'project:hcv' })}>HCV</a>,{' '}
          <a onClick={() => navigate('entities', { id: 'project:notion-sync' })}>Notion Sync</a>, and{' '}
          <span className="proposed-link" title="Proposed link · 0.95 · click to review">Data Catalog MCP</span>{' '}
          to compile a single inspectable view of project ownership and recent decisions.
        </p>
        <h2>Decisions</h2>
        <ul>
          <li>Graph state lives in <code>state/index.db</code> alongside lexical chunks.</li>
          <li>Proposed cross-links are inert records until a reviewer approves them.</li>
          <li>The MCP server exposes only <span className="proposed-link" title="Proposed link · 0.91 · click to review">FastMCP</span> read-only tools in this slice.</li>
        </ul>
        <h2>Backlinks (extract)</h2>
        <blockquote>
          Discoverable via the right context panel — every backlink in this view is materialized
          from <code>graph_edges</code>, never re-scanned at query time.
        </blockquote>

        {myProps.length > 0 && (
          <>
            <hr />
            <h3>Proposed links targeting this page</h3>
            <ul>
              {myProps.map(p => (
                <li key={p.id}>
                  <span className="mono" style={{ color: 'var(--ink-4)' }}>L{p.line}</span>{' · '}
                  <strong>{p.original_text}</strong> → <em>{p.target_title}</em>{' '}
                  <span className="mono" style={{ color: 'var(--ink-4)' }}>conf {p.confidence.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </main>
  );
}

// ─── Entities ──────────────────────────────────────────────────────────────
function EntitiesView({ navigate, selectedId, filters }) {
  const { ENTITIES } = window.WikiData;
  const [q, setQ] = useState('');
  const filtered = useMemo(() => {
    return ENTITIES.filter(e => {
      if (filters.types.length && !filters.types.includes(e.type)) return false;
      if (q && !e.name.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    }).sort((a, b) => b.backlinks - a.backlinks);
  }, [filters.types, q]);

  const selected = selectedId ? ENTITIES.find(e => e.id === selectedId) : null;
  if (selected) return <EntityDetailView entity={selected} navigate={navigate} />;

  return (
    <main className="main" id="main" tabIndex="-1">
      <div className="page-h">
        <div>
          <div className="breadcrumb">wiki / entities</div>
          <h1>Entities</h1>
          <div className="sub">Canonical projects, people, and concepts resolved deterministically from page content.</div>
        </div>
      </div>

      <div className="search-inline">
        <Icon name="search" />
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Filter entities by name or alias…" />
        <span className="meta">{filtered.length} / {ENTITIES.length}</span>
      </div>

      <div className="panel">
        <div className="thead grid-entities">
          <span></span><span>Name · aliases</span><span>Type</span><span>Pages</span><span>Backlinks</span><span>ID</span>
        </div>
        <div className="list">
          {filtered.map(e => (
            <div key={e.id} className="list-row grid-entities" onClick={() => navigate('entities', { id: e.id })}>
              <Pill kind={e.type}>{e.type[0]}</Pill>
              <span className="truncate">
                <span className="title">{e.name}</span>{' '}
                <span style={{ color: 'var(--ink-4)', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                  {e.aliases.slice(1, 3).join(', ')}
                </span>
              </span>
              <span className="path">{e.type}</span>
              <span className="meta">{e.pages}</span>
              <span className="meta">{e.backlinks}</span>
              <span className="path truncate">{e.id}</span>
            </div>
          ))}
          {filtered.length === 0 && <div className="empty">No entities match your filters.</div>}
        </div>
      </div>
    </main>
  );
}

function EntityDetailView({ entity, navigate }) {
  const { backlinksFor, outboundFor, PAGES } = window.WikiData;
  const toast = useToast();
  const backlinks = backlinksFor(entity.id);
  const outbound = outboundFor(entity.id).filter(e => e.type !== 'belongs_to_project');
  const pages = PAGES.filter(p => p.project === entity.slug);
  const co = useMemo(() => {
    const sources = new Set(backlinks.map(b => b.source_node_id));
    const counts = {};
    for (const e of window.WikiData.EDGES) {
      if (sources.has(e.src) && e.tgt !== entity.id && e.type !== 'belongs_to_project') {
        counts[e.tgt] = (counts[e.tgt] || 0) + 1;
      }
    }
    return Object.entries(counts).sort((a,b) => b[1] - a[1]).slice(0, 6)
      .map(([id, n]) => ({ id, n, ent: window.WikiData.byId(id) }))
      .filter(x => x.ent);
  }, [entity.id, backlinks]);

  return (
    <main className="main" id="main" tabIndex="-1">
      <div className="page-h">
        <div>
          <div className="breadcrumb">
            <a onClick={() => navigate('entities')}>entities</a> / {entity.type}
          </div>
          <h1 style={{ display: 'flex', gap: 12, alignItems: 'baseline' }}>
            {entity.name}
            <Pill kind={entity.type}>{entity.type}</Pill>
          </h1>
          <div className="sub" style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--t-sm)', color: 'var(--ink-4)' }}>
            {entity.id}
          </div>
        </div>
        <div className="page-actions">
          <button className="btn ghost" onClick={() => {
            const uri = `wiki://${entity.id}`;
            navigator.clipboard && navigator.clipboard.writeText(uri);
            toast && toast.push('Copied MCP URI', { kind: 'ok', detail: uri });
          }}><Icon name="copy" />copy MCP URI</button>
          <button className="btn primary" onClick={() => navigate('graph', { id: entity.id })}><Icon name="graph" />open in graph</button>
        </div>
      </div>

      <div className="cols-3">
        <div className="tile">
          <div className="label">Pages</div><div className="value">{pages.length}</div>
          <div className="delta flat">durable wiki pages</div>
        </div>
        <div className="tile">
          <div className="label">Backlinks</div><div className="value">{backlinks.length}</div>
          <div className="delta flat">inbound references</div>
        </div>
        <div className="tile">
          <div className="label">Outbound</div><div className="value">{outbound.length}</div>
          <div className="delta flat">links_to + mentions</div>
        </div>
      </div>

      <div className="cols-2">
        <div className="panel">
          <div className="panel__h"><h2>Backlinks</h2><span className="meta">{backlinks.length} sources</span></div>
          <div className="list">
            {backlinks.map((b, i) => (
              <div key={i} className="list-row grid-bl" onClick={() => navigate('pages', { id: b.source_node_id })}>
                <Pill kind={b.edge_type === 'mentions' ? 'concept' : 'project'}>{b.edge_type}</Pill>
                <span className="truncate">
                  <span className="title">{b.source_title}</span>
                  <div className="evidence" style={{ marginTop: 4 }}>{b.evidence}</div>
                </span>
                <span className="meta">L{b.line}</span>
              </div>
            ))}
            {backlinks.length === 0 && <div className="empty">No inbound references yet.</div>}
          </div>
        </div>

        <div className="panel">
          <div className="panel__h"><h2>Co-mentioned</h2><span className="meta">shared sources</span></div>
          <div className="list">
            {co.map(({ id, n, ent }) => (
              <div key={id} className="list-row" style={{ gridTemplateColumns: '24px 1fr 60px' }}
                   onClick={() => navigate('entities', { id })}>
                <Pill kind={ent.type || 'page'}>{(ent.type || 'p')[0]}</Pill>
                <span className="title truncate">{ent.name || ent.title}</span>
                <span className="meta">{n}×</span>
              </div>
            ))}
            {co.length === 0 && <div className="empty">No co-mentioned entities yet.</div>}
          </div>
        </div>
      </div>

      {entity.type === 'project' && (
        <div className="panel" style={{ marginTop: 12 }}>
          <div className="panel__h"><h2>Pages in this project</h2><span className="meta">{pages.length}</span></div>
          <div className="list">
            {pages.map(p => (
              <div key={p.id} className="list-row" style={{ gridTemplateColumns: '1fr 1fr 80px 70px' }}
                   onClick={() => navigate('pages', { id: p.id })}>
                <span className="title truncate">{p.title}</span>
                <span className="path truncate">{p.path}</span>
                <span><Pill kind={p.kind === 'decisions' ? 'decision' : 'page'}>{p.kind}</Pill></span>
                <span className="meta">{p.words.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}

// ─── Proposals queue ───────────────────────────────────────────────────────
function ProposalsView({ navigate, selectedId }) {
  const { PROPOSALS } = window.WikiData;
  const toast = useToast();
  const [q, setQ] = useState('');
  const [conf, setConf] = useState('all');

  const filtered = useMemo(() => {
    return PROPOSALS.filter(p => {
      if (conf === 'high' && p.confidence < 0.94) return false;
      if (conf === 'mid' && (p.confidence >= 0.94 || p.confidence < 0.9)) return false;
      if (q && !(p.original_text + ' ' + p.target_title + ' ' + p.source_path).toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [q, conf]);

  const handleExport = () => {
    // Try server endpoint first; fall back to client-side Blob
    const a = document.createElement('a');
    a.href = '/api/proposals/export?format=csv';
    a.download = 'proposed-links.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    toast && toast.push('Exported proposed-links.csv', { kind: 'ok', detail: `${PROPOSALS.length} rows · CSV` });
  };

  return (
    <main className="main" id="main" tabIndex="-1">
      <div className="page-h">
        <div>
          <div className="breadcrumb">wiki / proposed-links</div>
          <h1>Proposed Links</h1>
          <div className="sub">
            High-confidence missing links extracted from durable pages. Inert until reviewed —
            no markdown will be modified by this view.
          </div>
        </div>
        <div className="page-actions">
          <button className="btn ghost" onClick={handleExport}><Icon name="copy" />export queue</button>
        </div>
      </div>

      <div className="search-inline">
        <Icon name="search" />
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Filter by source path, target, or text…" />
        <span className="meta">{filtered.length} / {PROPOSALS.length}</span>
      </div>

      <div className="filter-bar">
        <button className={'f-chip' + (conf === 'all' ? ' is-on' : '')} onClick={() => setConf('all')}>All <span className="n">{PROPOSALS.length}</span></button>
        <button className={'f-chip' + (conf === 'high' ? ' is-on' : '')} onClick={() => setConf('high')}>≥ 0.94 <span className="n">{PROPOSALS.filter(p => p.confidence >= 0.94).length}</span></button>
        <button className={'f-chip' + (conf === 'mid' ? ' is-on' : '')} onClick={() => setConf('mid')}>0.90 – 0.94 <span className="n">{PROPOSALS.filter(p => p.confidence >= 0.9 && p.confidence < 0.94).length}</span></button>
      </div>

      <div className="panel">
        <div className="thead grid-props">
          <span>Source · text</span><span>Target</span><span>Conf</span><span>ID</span>
        </div>
        <div className="list">
          {filtered.map(p => (
            <div key={p.id} className={'list-row grid-props' + (p.id === selectedId ? ' is-active' : '')}
                 onClick={() => navigate('proposals', { id: p.id })}>
              <span className="truncate">
                <span className="path" style={{ display: 'block', marginBottom: 2 }}>{p.source_path} · L{p.line}</span>
                <span className="title">{p.original_text}</span>
              </span>
              <span className="truncate">
                <Pill kind={p.target_node_id.startsWith('project:') ? 'project' : 'concept'}>
                  {p.target_node_id.split(':')[0]}
                </Pill>{' '}
                <span style={{ color: 'var(--ink-1)' }}>{p.target_title}</span>
                <div className="evidence" style={{ marginTop: 4 }}>{p.rationale}</div>
              </span>
              <Confidence value={p.confidence} />
              <span className="path">{p.id}</span>
            </div>
          ))}
          {filtered.length === 0 && <div className="empty">No proposed links match.</div>}
        </div>
      </div>
    </main>
  );
}

// ─── Reports ───────────────────────────────────────────────────────────────
function ReportsView({ navigate }) {
  const { REPORTS } = window.WikiData;
  return (
    <main className="main" id="main" tabIndex="-1">
      <div className="page-h">
        <div>
          <div className="breadcrumb">wiki / reports</div>
          <h1>Reports</h1>
          <div className="sub">Phase reports, retros, and research notes — workspace-relative paths.</div>
        </div>
      </div>
      <div className="panel">
        <div className="list">
          {REPORTS.map(r => (
            <div key={r.id} className="list-row" style={{ gridTemplateColumns: '1fr 1fr 80px 80px' }}
                 onClick={() => navigate('pages', { id: r.id })}>
              <span className="title truncate">{r.title}</span>
              <span className="path truncate">{r.path}</span>
              <span className="meta">{r.words.toLocaleString()}w</span>
              <span className="meta">{r.updated}</span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

// ─── Health ────────────────────────────────────────────────────────────────
function HealthView({ actions }) {
  const { HEALTH } = window.WikiData;
  const ok   = HEALTH.filter(h => h.status === 'ok').length;
  const warn = HEALTH.filter(h => h.status === 'warn').length;
  const err  = HEALTH.filter(h => h.status === 'err').length;
  return (
    <main className="main" id="main" tabIndex="-1">
      <div className="page-h">
        <div>
          <div className="breadcrumb">wiki / health</div>
          <h1>Workspace Health</h1>
          <div className="sub">Graph schema, freshness, alias hygiene, and proposal drift.</div>
        </div>
        <div className="page-actions">
          <button className="btn ghost" onClick={() => actions && actions.openRecheck()}><Icon name="refresh" />re-check</button>
          <button className="btn primary" onClick={() => actions && actions.openRebuild()}><Icon name="bolt" />rebuild graph</button>
        </div>
      </div>

      <div className="cols-3">
        <div className="tile"><div className="label">Healthy</div><div className="value">{ok}</div><div className="delta up">checks passing</div></div>
        <div className="tile"><div className="label">Warnings</div><div className="value">{warn}</div><div className="delta flat" style={{ color: 'var(--warn)' }}>review recommended</div></div>
        <div className="tile"><div className="label">Errors</div><div className="value">{err}</div><div className="delta flat">none</div></div>
      </div>

      <div className="panel" style={{ marginBottom: 12 }}>
        <div className="panel__h"><h2>Checks</h2><span className="meta">last run · 14:02 today</span></div>
        <div>
          {HEALTH.map(h => (
            <div key={h.id} className="health-row">
              <div className={'status ' + h.status}>
                {h.status === 'ok'   && <Icon name="check" />}
                {h.status === 'warn' && <Icon name="bolt"  />}
                {h.status === 'err'  && <Icon name="x"     />}
              </div>
              <div>
                <div className="label">{h.label}</div>
                <div className="desc">{h.desc}</div>
              </div>
              <div className={'status ' + h.status} style={{ justifyContent: 'flex-end' }}>{h.status}</div>
              <div className="val">{h.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="panel__h"><h2>Last rebuild log</h2><span className="meta">graph_a91c · 24.3s</span></div>
        <div style={{ padding: 12 }}>
<pre className="logblock">
<span className="dim">[14:02:01]</span> rebuild-graph --workspace ~/AI_V2/team_memory_wiki
<span className="dim">[14:02:01]</span> graph schema v1.3 · loaded
<span className="dim">[14:02:02]</span> scanning durable pages…
<span className="dim">[14:02:09]</span> parsed 142 pages · 4 skipped (frontmatter-only)
<span className="dim">[14:02:14]</span> resolved 264 entity aliases · <span className="warn">2 ambiguous (Atlas, Catalog)</span>
<span className="dim">[14:02:18]</span> created 318 edges (links_to=141, mentions=63, belongs_to=114)
<span className="dim">[14:02:21]</span> generated 17 proposals · 12 ≥ 0.94, 5 ≥ 0.90
<span className="dim">[14:02:24]</span> <span className="ok">success</span> · run graph_a91c · 24.3s · 0 markdown writes
</pre>
        </div>
      </div>
    </main>
  );
}

Object.assign(window, { OverviewView, PagesView, EntitiesView, ProposalsView, ReportsView, HealthView, PageDetailView, EntityDetailView });
