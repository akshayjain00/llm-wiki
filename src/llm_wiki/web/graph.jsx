/* global React, Icon, Pill, Confidence */
const { useState, useEffect, useMemo, useRef } = React;

// ─── Graph view ────────────────────────────────────────────────────────────
// Builds a small local neighborhood around a center node using a deterministic
// pseudo-force layout (all in SVG, no external lib). Three layouts:
//   force        — concentric rings of decreasing density
//   radial       — single ring around center
//   hierarchical — center on left, neighbors fanning right by hop
//
// The graph is paired with an adjacency list panel (right side, fixed) so that
// every visible relationship is also accessible as text.

function buildNeighborhood(centerId, depth = 1) {
  const { EDGES, byId } = window.WikiData;
  const nodes = new Map();
  const links = [];
  const visit = (id, hop) => {
    if (nodes.has(id)) return;
    const n = byId(id);
    if (!n) return;
    nodes.set(id, { id, hop, n });
    if (hop >= depth) return;
    for (const e of EDGES) {
      if (e.src === id) { visit(e.tgt, hop + 1); links.push({ ...e, hop }); }
      if (e.tgt === id) { visit(e.src, hop + 1); links.push({ ...e, hop }); }
    }
  };
  visit(centerId, 0);
  // Add a couple of inferred (proposed) edges from PROPOSALS so the dashed
  // lines for candidate links surface visually.
  const { PROPOSALS } = window.WikiData;
  for (const p of PROPOSALS) {
    if (nodes.has(p.target_node_id)) {
      const sourcePage = window.WikiData.PAGES.find(pg => pg.path === p.source_path);
      if (sourcePage && nodes.has(sourcePage.id)) {
        links.push({ src: sourcePage.id, tgt: p.target_node_id, type: 'proposed', evidence: p.original_text });
      }
    }
  }
  return { nodes: [...nodes.values()], links };
}

function nodeKind(node) {
  const n = node.n;
  if (node.id.startsWith('page:')) {
    if (n.kind === 'report') return 'report';
    if (n.kind === 'decisions') return 'page';
    return 'page';
  }
  if (n.type === 'project') return 'project';
  if (n.type === 'concept') return 'concept';
  if (n.type === 'person') return 'entity';
  return 'entity';
}

function radialLayout(nodes, w, h) {
  const cx = w / 2, cy = h / 2;
  const center = nodes.find(n => n.hop === 0);
  const ring1 = nodes.filter(n => n.hop === 1);
  const ring2 = nodes.filter(n => n.hop >= 2);
  const pos = new Map();
  if (center) pos.set(center.id, { x: cx, y: cy });
  const r1 = Math.min(w, h) * 0.27;
  ring1.forEach((n, i) => {
    const a = (i / ring1.length) * Math.PI * 2 - Math.PI / 2;
    pos.set(n.id, { x: cx + Math.cos(a) * r1, y: cy + Math.sin(a) * r1 });
  });
  const r2 = Math.min(w, h) * 0.42;
  ring2.forEach((n, i) => {
    const a = (i / Math.max(ring2.length, 1)) * Math.PI * 2 - Math.PI / 2 + 0.18;
    pos.set(n.id, { x: cx + Math.cos(a) * r2, y: cy + Math.sin(a) * r2 });
  });
  return pos;
}

function forceLayout(nodes, w, h) {
  // Deterministic pseudo-force: place node i at radius ~ hop*r0 with a
  // hash-based jitter so multiple re-renders give the same map.
  const cx = w / 2, cy = h / 2;
  const pos = new Map();
  const center = nodes.find(n => n.hop === 0);
  if (center) pos.set(center.id, { x: cx, y: cy });
  const others = nodes.filter(n => n.hop > 0);
  others.forEach((n, i) => {
    const seed = hashStr(n.id);
    const baseR = 90 + n.hop * 110;
    const jitter = ((seed % 60) - 30);
    const r = baseR + jitter;
    const a = ((seed % 360) / 360) * Math.PI * 2 + i * 0.07;
    pos.set(n.id, { x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r });
  });
  return pos;
}

function hierarchicalLayout(nodes, w, h) {
  const pos = new Map();
  const byHop = {};
  nodes.forEach(n => { (byHop[n.hop] = byHop[n.hop] || []).push(n); });
  const hops = Object.keys(byHop).map(Number).sort();
  const xstep = w / (hops.length + 1);
  hops.forEach((hop, hi) => {
    const arr = byHop[hop];
    arr.forEach((n, ni) => {
      const x = (hi + 1) * xstep;
      const y = ((ni + 1) / (arr.length + 1)) * h;
      pos.set(n.id, { x, y });
    });
  });
  return pos;
}

function hashStr(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function GraphView({ centerId, layout, onLayoutChange, onSelect, navigate }) {
  const [size, setSize] = useState({ w: 1000, h: 700 });
  const [adjOpen, setAdjOpen] = useState(false);
  const wrapRef = useRef(null);
  useEffect(() => {
    if (!wrapRef.current) return undefined;
    const update = () => {
      const r = wrapRef.current.getBoundingClientRect();
      const adjW = adjOpen ? 340 : 0;
      setSize({ w: Math.max(400, r.width - adjW), h: Math.max(400, r.height) });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, [adjOpen]);

  const { nodes, links } = useMemo(() => buildNeighborhood(centerId, 2), [centerId]);
  const pos = useMemo(() => {
    if (layout === 'radial') return radialLayout(nodes, size.w, size.h);
    if (layout === 'hierarchical') return hierarchicalLayout(nodes, size.w, size.h);
    return forceLayout(nodes, size.w, size.h);
  }, [nodes, layout, size]);

  const center = nodes.find(n => n.hop === 0);
  const adjEntries = useMemo(() => {
    const seen = new Set();
    return links.filter(l => {
      const k = `${l.src}|${l.type}|${l.tgt}`;
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  }, [links]);

  return (
    <div className={'graph-wrap' + (adjOpen ? ' has-adj' : '')} ref={wrapRef}>
      <div className="graph-toolbar" role="toolbar" aria-label="Graph controls">
        <button type="button" className={layout === 'force' ? 'is-on' : ''}
                onClick={() => onLayoutChange && onLayoutChange('force')}
                aria-pressed={layout === 'force'}><Icon name="graph" />force</button>
        <button type="button" className={layout === 'radial' ? 'is-on' : ''}
                onClick={() => onLayoutChange && onLayoutChange('radial')}
                aria-pressed={layout === 'radial'}><Icon name="layers" />radial</button>
        <button type="button" className={layout === 'hierarchical' ? 'is-on' : ''}
                onClick={() => onLayoutChange && onLayoutChange('hierarchical')}
                aria-pressed={layout === 'hierarchical'}><Icon name="graphList" />hierarchy</button>
        <span style={{ width: 1, background: 'var(--hairline)', margin: '4px 4px' }} />
        <button type="button" disabled>depth: 2</button>
        <button type="button" disabled>nodes: {nodes.length}</button>
        <span style={{ width: 1, background: 'var(--hairline)', margin: '4px 4px' }} />
        <button type="button" className={adjOpen ? 'is-on' : ''}
                onClick={() => setAdjOpen(o => !o)}
                aria-pressed={adjOpen}
                title="Accessible text fallback for the graph — every visible edge as a screen-reader-friendly source → target list. Off by default; toggle on for keyboard navigation or to read relationships as text.">
          <Icon name="graphList" />adjacency list {adjOpen ? '✓' : ''}
        </button>
      </div>

      <svg className="graph-svg" viewBox={`0 0 ${size.w} ${size.h}`} preserveAspectRatio="xMidYMid meet"
           role="img" aria-label="Local graph neighborhood">
        <g>
          {links.map((l, i) => {
            const a = pos.get(l.src), b = pos.get(l.tgt);
            if (!a || !b) return null;
            const isCenter = l.src === centerId || l.tgt === centerId;
            return (
              <line key={i}
                    className={'edge' + (l.type === 'proposed' ? ' proposed' : '') + (isCenter ? ' is-active' : '')}
                    x1={a.x} y1={a.y} x2={b.x} y2={b.y} />
            );
          })}
        </g>
        <g>
          {nodes.map(n => {
            const p = pos.get(n.id);
            if (!p) return null;
            const k = nodeKind(n);
            const r = n.hop === 0 ? 18 : n.hop === 1 ? 11 : 7;
            const label = (n.n.title || n.n.name || n.id).replace(/^[a-z]+:/, '').slice(0, 28);
            return (
              <g key={n.id}
                 className={`node t-${k}` + (n.hop === 0 ? ' is-center' : '')}
                 transform={`translate(${p.x},${p.y})`}
                 onClick={() => { onSelect(n.id); }}
                 style={{ cursor: 'default' }}>
                <circle r={r} />
                <text y={r + 12} textAnchor="middle">{label}</text>
              </g>
            );
          })}
        </g>
      </svg>

      {adjOpen && (
      <aside className="adj-fallback" aria-label="Adjacency list">
        <h3>
          Adjacency list
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-5)' }}>{adjEntries.length}</span>
            <button type="button" onClick={() => setAdjOpen(false)}
                    aria-label="Close adjacency list"
                    style={{ appearance: 'none', border: 0, background: 'transparent', cursor: 'default', color: 'var(--ink-4)', padding: 2, lineHeight: 1, fontSize: 14 }}>×</button>
          </span>
        </h3>
        <p style={{ margin: 0, padding: '0 var(--pad-4) var(--pad-3)', fontSize: 11, color: 'var(--ink-4)', lineHeight: 1.4 }}>
          Text fallback — every visible edge in the graph, in source → target form. Click any row to focus that node.
        </p>
        <ul>
          {adjEntries.map((l, i) => {
            const a = window.WikiData.byId(l.src);
            const b = window.WikiData.byId(l.tgt);
            return (
              <li key={i} onClick={() => onSelect(l.tgt)}>
                <span className="src">{(a?.name || a?.title || l.src).slice(0, 22)}</span>
                <span className="arrow mono">{l.type === 'proposed' ? '⇢' : '→'}</span>
                <span className="tgt">{(b?.name || b?.title || l.tgt).slice(0, 26)}</span>
              </li>
            );
          })}
        </ul>
      </aside>
      )}

      <div className="graph-legend">
        <span className="lg-item"><span className="lg-dot" style={{ background: 'var(--accent)' }} /> project</span>
        <span className="lg-item"><span className="lg-dot" style={{ background: '#7a5ae0' }} /> entity</span>
        <span className="lg-item"><span className="lg-dot" style={{ background: '#d24f7c' }} /> concept</span>
        <span className="lg-item"><span className="lg-dot" style={{ background: 'var(--ink-5)' }} /> page</span>
        <span className="lg-item"><span style={{ width: 18, height: 1, borderTop: '1px dashed var(--warn)' }} /> proposed</span>
      </div>
    </div>
  );
}

window.GraphView = GraphView;
