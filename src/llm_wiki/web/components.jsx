/* global React, Icon */
const { useState, useEffect, useRef, useMemo } = React;

// ── TopBar ─────────────────────────────────────────────────────────────────
function TopBar({ onOpenPalette, freshness, propsCount, onNewProject }) {
  return (
    <header className="topbar" role="banner">
      <div className="topbar__brand">
        <span className="dot">w</span>
        <span>llm-wiki</span>
        <span className="topbar__path">· <b>~/AI_V2/team_memory_wiki</b></span>
      </div>
      <button className="topbar__search" onClick={onOpenPalette} aria-label="Open search palette (Cmd+K)">
        <Icon name="search" />
        <span>Search pages, entities, proposals…</span>
        <kbd>⌘K</kbd>
      </button>
      <div className="topbar__chips">
        <span className="chip is-ok"><span className="dot-sm" />graph: fresh · {freshness}</span>
        <span className="chip is-warn"><span className="dot-sm" />{propsCount} pending</span>
        <span className="chip is-accent"><span className="dot-sm" />mcp: ready · stdio</span>
        <button className="btn primary btn-sm" onClick={onNewProject}>
          <Icon name="plus" /> new project
        </button>
      </div>
    </header>
  );
}

// ── Sidebar ────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { route: 'overview',  label: 'Overview',       icon: 'overview' },
  { route: 'pages',     label: 'Pages',          icon: 'pages' },
  { route: 'entities',  label: 'Entities',       icon: 'entities' },
  { route: 'proposals', label: 'Proposed Links', icon: 'proposal', badgeKey: 'proposals' },
  { route: 'graph',     label: 'Graph',          icon: 'graph' },
  { route: 'reports',   label: 'Reports',        icon: 'reports' },
  { route: 'health',    label: 'Health',         icon: 'health' },
];

function Sidebar({ route, navigate, counts, filters, setFilter }) {
  const { PROJECTS } = window.WikiData;
  return (
    <nav className="sidebar" aria-label="Workspace">
      <div className="sidebar__section">
        <div className="sidebar__label">Workspace</div>
        {NAV_ITEMS.map(item => (
          <div key={item.route}
               className={'nav-item' + (route === item.route ? ' is-active' : '')}
               role="link" tabIndex="0"
               onClick={() => navigate(item.route)}
               onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && navigate(item.route)}>
            <Icon name={item.icon} />
            <span>{item.label}</span>
            {item.badgeKey && <span className="badge">{counts[item.badgeKey]}</span>}
          </div>
        ))}
      </div>

      <div className="sidebar__section">
        <div className="sidebar__label">Projects <span className="count">{PROJECTS.length}</span></div>
        {PROJECTS.slice(0, 8).map(p => (
          <div key={p.slug}
               className={'nav-item' + (filters.project === p.slug ? ' is-active' : '')}
               role="link" tabIndex="0"
               onClick={() => { setFilter('project', filters.project === p.slug ? null : p.slug); navigate('pages'); }}>
            <span className="icon" style={{
              width: 8, height: 8, borderRadius: 2,
              background: p.status === 'active' ? 'var(--ok)' : p.status === 'paused' ? 'var(--warn)' : 'var(--ink-5)',
              display: 'inline-block', flexShrink: 0,
            }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
            <span className="badge">{p.pages}</span>
          </div>
        ))}
        <div className="nav-item" style={{ color: 'var(--ink-4)' }} onClick={() => navigate('pages')}>
          <span className="icon" />
          <span>Show all…</span>
        </div>
      </div>

      <div className="sidebar__section sidebar__filters">
        <div className="sidebar__label">Entity Type</div>
        {['project','person','concept'].map(t => (
          <label key={t} className="filter-row">
            <input type="checkbox"
                   checked={filters.types.includes(t)}
                   onChange={() => {
                     const next = filters.types.includes(t)
                       ? filters.types.filter(x => x !== t)
                       : [...filters.types, t];
                     setFilter('types', next);
                   }} />
            <span className="swatch" style={{
              background: t === 'project' ? 'var(--accent)' : t === 'person' ? '#2c8a92' : '#d24f7c'
            }} />
            <span style={{ textTransform: 'capitalize' }}>{t}s</span>
            <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', color: 'var(--ink-5)' }}>
              {window.WikiData.ENTITIES.filter(e => e.type === t).length}
            </span>
          </label>
        ))}
      </div>

      <div className="sidebar__section sidebar__filters">
        <div className="sidebar__label">Edge Type</div>
        {[
          { id: 'links_to', label: 'links_to', color: 'var(--accent)' },
          { id: 'mentions', label: 'mentions', color: '#7a5ae0' },
          { id: 'belongs_to_project', label: 'belongs_to', color: 'var(--ink-5)' },
        ].map(e => (
          <label key={e.id} className="filter-row">
            <input type="checkbox"
                   checked={filters.edges.includes(e.id)}
                   onChange={() => {
                     const next = filters.edges.includes(e.id)
                       ? filters.edges.filter(x => x !== e.id)
                       : [...filters.edges, e.id];
                     setFilter('edges', next);
                   }} />
            <span className="swatch" style={{ background: e.color }} />
            <span className="mono" style={{ fontFamily: 'var(--font-mono)' }}>{e.label}</span>
          </label>
        ))}
      </div>
    </nav>
  );
}

// ── Right context panel ────────────────────────────────────────────────────
function RightPanel({ selection, navigate }) {
  const { byId, backlinksFor, outboundFor, PROPOSALS } = window.WikiData;
  if (!selection) return <RightDefault navigate={navigate} />;
  const ent = byId(selection);
  if (!ent) return <RightDefault navigate={navigate} />;

  const isPage = selection.startsWith('page:');
  const backlinks = backlinksFor(selection);
  const outbound = outboundFor(selection).filter(e => e.type !== 'belongs_to_project');
  const proposals = PROPOSALS.filter(p => p.target_node_id === selection || p.source_path === ent.path);

  return (
    <aside className="right" aria-label="Context">
      <div className="right__section right__title">
        <span className={'pill t-' + (isPage ? (ent.kind === 'report' ? 'report' : 'page') : ent.type)}>
          {isPage ? (ent.kind === 'report' ? 'report' : 'page') : ent.type}
        </span>
        <h2 style={{ marginTop: 6 }}>{ent.title || ent.name}</h2>
        {ent.path && <div className="path">{ent.path}</div>}

        <dl className="kv" style={{ marginTop: 14 }}>
          {!isPage && ent.aliases && <><dt>Aliases</dt><dd>{ent.aliases.join(', ')}</dd></>}
          {ent.role && <><dt>Role</dt><dd>{ent.role}</dd></>}
          {ent.project && <><dt>Project</dt><dd>{ent.project}</dd></>}
          {ent.hash && <><dt>Hash</dt><dd>{ent.hash}</dd></>}
          {ent.words != null && <><dt>Words</dt><dd>{ent.words.toLocaleString()}</dd></>}
          {ent.updated && <><dt>Updated</dt><dd>{ent.updated}</dd></>}
          <dt>Backlinks</dt><dd>{backlinks.length}</dd>
          <dt>Outbound</dt><dd>{outbound.length}</dd>
        </dl>
      </div>

      <div className="right__section">
        <div className="right__h"><h3>Backlinks</h3><span className="count">{backlinks.length}</span></div>
        {backlinks.length === 0
          ? <div style={{ color: 'var(--ink-4)', fontSize: 12 }}>No inbound references yet.</div>
          : <div className="linklist">
              {backlinks.slice(0, 6).map((b, i) => (
                <a key={i} onClick={() => navigate('pages', { id: b.source_node_id })}>
                  <Icon name="link" />
                  <span className="truncate">{b.source_title}</span>
                  <span className="why mono">{b.edge_type}</span>
                </a>
              ))}
            </div>}
      </div>

      {outbound.length > 0 && (
        <div className="right__section">
          <div className="right__h"><h3>Outbound</h3><span className="count">{outbound.length}</span></div>
          <div className="linklist">
            {outbound.slice(0, 6).map((o, i) => (
              <a key={i} onClick={() => navigate(o.tgt.startsWith('page:') ? 'pages' : 'entities', { id: o.tgt })}>
                <Icon name="arrow" />
                <span className="truncate">{o.target_title}</span>
                <span className="why mono">{o.type}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {proposals.length > 0 && (
        <div className="right__section">
          <div className="right__h">
            <h3>Proposed Links</h3>
            <span className="count">{proposals.length}</span>
          </div>
          {proposals.slice(0, 4).map(p => (
            <div key={p.id} style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--ink-2)' }}>
                <Confidence value={p.confidence} />
                <span style={{ marginLeft: 'auto', color: 'var(--ink-4)', fontFamily: 'var(--font-mono)', fontSize: 10.5 }}>{p.id}</span>
              </div>
              <div className="evidence" style={{ marginTop: 4 }}>
                {p.original_text} → <em>{p.target_title}</em>
              </div>
              <div style={{ fontSize: 11, color: 'var(--ink-4)', marginTop: 2 }}>{p.rationale}</div>
            </div>
          ))}
        </div>
      )}

      <div className="right__section">
        <div className="right__h"><h3>Actions</h3></div>
        <div className="linklist">
          <span className="row"><Icon name="open" /><span className="truncate">Open page</span></span>
          <span className="row"><Icon name="copy" /><span className="truncate">Copy MCP URI</span><span className="why mono">wiki://{selection}</span></span>
          <span className="row"><Icon name="external" /><span className="truncate">View citations</span></span>
        </div>
      </div>
    </aside>
  );
}

function RightDefault({ navigate }) {
  const { ACTIVITY } = window.WikiData;
  return (
    <aside className="right" aria-label="Context">
      <div className="right__section">
        <div className="right__h"><h3>MCP</h3><span className="count">stdio</span></div>
        <dl className="kv">
          <dt>Status</dt><dd style={{ color: 'var(--ok)' }}>● ready</dd>
          <dt>Tools</dt><dd>6 read-only</dd>
          <dt>Clients</dt><dd>claude-code · codex</dd>
          <dt>Schema</dt><dd>v1.3</dd>
        </dl>
      </div>
      <div className="right__section">
        <div className="right__h"><h3>Recent Activity</h3></div>
        <div className="timeline" style={{ marginTop: 4 }}>
          {ACTIVITY.slice(0, 6).map((a, i) => (
            <div key={i} className="item" style={{ padding: '6px 0', borderBottom: '1px solid var(--hairline-2)' }}>
              <div className="when">{a.when}</div>
              <div className="what">{a.what}</div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

// ── Confidence ─────────────────────────────────────────────────────────────
function Confidence({ value }) {
  const cls = value >= 0.94 ? 'is-high' : value >= 0.88 ? 'is-mid' : 'is-low';
  return (
    <span className={'conf ' + cls}>
      <span className="conf__bar"><i style={{ width: `${Math.round(value * 100)}%` }} /></span>
      <span>{value.toFixed(2)}</span>
    </span>
  );
}

// ── Pill ───────────────────────────────────────────────────────────────────
function Pill({ kind, children }) {
  return <span className={'pill t-' + kind}>{children}</span>;
}

// ── Command Palette ────────────────────────────────────────────────────────
function CommandPalette({ open, onClose, navigate }) {
  const [q, setQ] = useState('');
  const [active, setActive] = useState(0);
  const inputRef = useRef(null);
  useEffect(() => { if (open) { setQ(''); setActive(0); setTimeout(() => inputRef.current && inputRef.current.focus(), 0); } }, [open]);

  const { ENTITIES, PAGES, PROPOSALS } = window.WikiData;
  const results = useMemo(() => {
    const ql = q.trim().toLowerCase();
    const cmds = [
      { kind: 'cmd', title: 'Go to Overview',       route: 'overview',  meta: 'g o' },
      { kind: 'cmd', title: 'Go to Pages',          route: 'pages',     meta: 'g p' },
      { kind: 'cmd', title: 'Go to Entities',       route: 'entities',  meta: 'g e' },
      { kind: 'cmd', title: 'Go to Proposed Links', route: 'proposals', meta: 'g l' },
      { kind: 'cmd', title: 'Go to Graph',          route: 'graph',     meta: 'g g' },
      { kind: 'cmd', title: 'Go to Health',         route: 'health',    meta: 'g h' },
      { kind: 'cmd', title: 'Rebuild graph',        route: 'health',    meta: '⌘ R' },
    ];
    const ents = ENTITIES.map(e => ({ kind: 'entity', title: e.name, type: e.type, route: 'entities', id: e.id, meta: e.id }));
    const pgs  = PAGES.map(p => ({ kind: 'page', title: p.title, route: 'pages', id: p.id, meta: p.path }));
    const props = PROPOSALS.map(p => ({ kind: 'proposal', title: `${p.original_text} → ${p.target_title}`, route: 'proposals', id: p.id, meta: p.source_path }));
    if (!ql) {
      return [
        { group: 'Commands', items: cmds.slice(0, 6) },
        { group: 'Entities', items: ents.slice(0, 6) },
        { group: 'Pages',    items: pgs.slice(0, 5) },
      ];
    }
    const match = a => a.title.toLowerCase().includes(ql) || (a.meta || '').toLowerCase().includes(ql);
    return [
      { group: 'Commands', items: cmds.filter(match).slice(0, 4) },
      { group: 'Entities', items: ents.filter(match).slice(0, 8) },
      { group: 'Pages',    items: pgs.filter(match).slice(0, 8) },
      { group: 'Proposals', items: props.filter(match).slice(0, 4) },
    ].filter(g => g.items.length > 0);
  }, [q]);

  const flat = results.flatMap(g => g.items);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = e => {
      if (e.key === 'Escape') { e.preventDefault(); onClose(); }
      else if (e.key === 'ArrowDown') { e.preventDefault(); setActive(a => Math.min(a + 1, flat.length - 1)); }
      else if (e.key === 'ArrowUp')   { e.preventDefault(); setActive(a => Math.max(a - 1, 0)); }
      else if (e.key === 'Enter')     {
        e.preventDefault();
        const r = flat[active];
        if (r) { navigate(r.route, r.id ? { id: r.id } : undefined); onClose(); }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, flat, active, navigate, onClose]);

  if (!open) return null;

  let runIdx = -1;
  return (
    <div className="palette-scrim" onClick={onClose} role="dialog" aria-modal="true" aria-label="Command palette">
      <div className="palette" onClick={e => e.stopPropagation()}>
        <div className="palette__input">
          <Icon name="search" size={16} />
          <input ref={inputRef} value={q} onChange={e => { setQ(e.target.value); setActive(0); }}
                 placeholder="Search the wiki — pages, entities, proposed links, commands…" />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--ink-4)' }}>{flat.length} matches</span>
        </div>
        <div className="palette__list">
          {results.map((g, gi) => (
            <div key={gi}>
              <div className="palette__group">{g.group}</div>
              {g.items.map(r => {
                runIdx += 1;
                const isActive = runIdx === active;
                const i = runIdx;
                return (
                  <div key={r.title + i}
                       className={'palette__row' + (isActive ? ' is-active' : '')}
                       onMouseEnter={() => setActive(i)}
                       onClick={() => { navigate(r.route, r.id ? { id: r.id } : undefined); onClose(); }}>
                    <Icon name={
                      r.kind === 'cmd' ? 'cmd' :
                      r.kind === 'entity' ? (r.type === 'project' ? 'entity' : r.type === 'person' ? 'entity' : 'hash') :
                      r.kind === 'proposal' ? 'proposal' : 'page'
                    } />
                    <span className="title" dangerouslySetInnerHTML={{ __html: highlight(r.title, q) }} />
                    <span className="path" dangerouslySetInnerHTML={{ __html: highlight(r.meta || '', q) }} />
                  </div>
                );
              })}
            </div>
          ))}
          {flat.length === 0 && (
            <div style={{ padding: '24px 20px', color: 'var(--ink-4)', fontSize: 13, textAlign: 'center' }}>
              No matches for "{q}"
            </div>
          )}
        </div>
        <div className="palette__hint">
          <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
          <span><kbd>↵</kbd> open</span>
          <span><kbd>esc</kbd> close</span>
          <span style={{ marginLeft: 'auto' }}>read-only · MCP-aligned</span>
        </div>
      </div>
    </div>
  );
}

function highlight(text, q) {
  if (!q) return escape(text);
  const idx = text.toLowerCase().indexOf(q.toLowerCase());
  if (idx === -1) return escape(text);
  return escape(text.slice(0, idx)) + '<mark>' + escape(text.slice(idx, idx + q.length)) + '</mark>' + escape(text.slice(idx + q.length));
}
function escape(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

Object.assign(window, { TopBar, Sidebar, RightPanel, RightDefault, CommandPalette, Confidence, Pill });
