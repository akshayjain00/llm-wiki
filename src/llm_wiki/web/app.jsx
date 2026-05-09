/* global React, ReactDOM, useTweaks, TweaksPanel, TweakSection, TweakRadio, TweakColor, TweakToggle, TweakSelect,
          ToastProvider, RebuildModal, NewProjectModal, RecheckModal */
const { useState, useEffect, useMemo, useCallback } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "density": "roomy",
  "accent": "blue",
  "aesthetic": "editorial",
  "layout": "force",
  "showRightPanel": true
}/*EDITMODE-END*/;

const ACCENTS = {
  blue:  { '--accent': '#2862e6', '--accent-soft': '#e3ecff', '--accent-line': '#b9cdfb', '--accent-ink': '#1849c2' },
  green: { '--accent': '#1f8a5b', '--accent-soft': '#dff5ea', '--accent-line': '#a4e0c4', '--accent-ink': '#106443' },
  mono:  { '--accent': '#1e2536', '--accent-soft': '#eef0f6', '--accent-line': '#cfd5e2', '--accent-ink': '#0b1220' },
};

function applyTweaks(t) {
  const root = document.documentElement;
  root.dataset.theme = t.theme;
  root.dataset.density = t.density;
  root.dataset.aesthetic = t.aesthetic;
  const a = ACCENTS[t.accent] || ACCENTS.blue;
  for (const [k, v] of Object.entries(a)) root.style.setProperty(k, v);
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  useEffect(() => applyTweaks(t), [t]);

  const [route, setRoute]             = useState('overview');
  const [routeParams, setRouteParams] = useState({});
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [filters, setFilters]         = useState({
    project: null,
    types: ['project', 'person', 'concept'],
    edges: ['links_to', 'mentions', 'belongs_to_project'],
  });

  // Modal state
  const [rebuildOpen, setRebuildOpen]     = useState(false);
  const [newProjOpen, setNewProjOpen]     = useState(false);
  const [recheckOpen, setRecheckOpen]     = useState(false);

  // Actions object passed down to views that need it
  const actions = {
    openRebuild:    () => setRebuildOpen(true),
    openNewProject: () => setNewProjOpen(true),
    openRecheck:    () => setRecheckOpen(true),
  };
  window.WikiActions = actions;

  const setFilter = useCallback((k, v) => setFilters(f => ({ ...f, [k]: v })), []);
  const navigate  = useCallback((r, params = {}) => {
    setRoute(r); setRouteParams(params); window.scrollTo(0, 0);
  }, []);

  // Selection drives the right context panel
  const selectionId = routeParams.id || (route === 'overview'
    ? ('project:' + (window.WikiData.PROJECTS[0] ? window.WikiData.PROJECTS[0].slug : 'team-memory-wiki'))
    : null);

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = e => {
      const inField = e.target.matches('input, textarea, select, [contenteditable=""], [contenteditable="true"]');
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault(); setPaletteOpen(true); return;
      }
      if (inField) return;
      if (e.key === 'g') { window.__g = true; setTimeout(() => { window.__g = false; }, 800); return; }
      if (window.__g) {
        const map = { o: 'overview', p: 'pages', e: 'entities', l: 'proposals', g: 'graph', h: 'health', r: 'reports' };
        if (map[e.key]) { e.preventDefault(); navigate(map[e.key]); window.__g = false; }
      }
      if (e.key === '/') { e.preventDefault(); setPaletteOpen(true); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [navigate]);

  const counts = useMemo(() => ({ proposals: window.WikiData.PROPOSALS.length }), []);

  // Derive freshness from most recent page update
  const freshness = useMemo(() => {
    const dates = window.WikiData.PAGES.map(p => p.updated).filter(Boolean).sort().reverse();
    if (!dates.length) return '—';
    return dates[0].slice(5); // MM-DD
  }, []);

  const view = (() => {
    switch (route) {
      case 'overview':  return <OverviewView navigate={navigate} actions={actions} />;
      case 'pages':     return <PagesView navigate={navigate} selectedId={routeParams.id} filters={filters} setFilter={setFilter} />;
      case 'entities':  return <EntitiesView navigate={navigate} selectedId={routeParams.id} filters={filters} />;
      case 'proposals': return <ProposalsView navigate={navigate} selectedId={routeParams.id} />;
      case 'graph':     return (
        <main className="main main--graph" id="main" tabIndex="-1">
          <div className="page-h">
            <div>
              <div className="breadcrumb">wiki / graph</div>
              <h1>Local Graph</h1>
              <div className="sub">
                Neighborhood view around <b>{(window.WikiData.byId(selectionId) || {}).name || (window.WikiData.byId(selectionId) || {}).title || 'workspace'}</b>.
                Center node is selected; depth-2 fan-out. Solid edges are materialized; dashed are proposed.
              </div>
            </div>
          </div>
          <GraphView centerId={selectionId || (window.WikiData.PROJECTS[0] ? 'project:' + window.WikiData.PROJECTS[0].slug : 'project:team-memory-wiki')}
                     layout={t.layout}
                     onLayoutChange={v => setTweak('layout', v)}
                     onSelect={id => setRouteParams({ id })}
                     navigate={navigate} />
        </main>
      );
      case 'reports':   return <ReportsView navigate={navigate} />;
      case 'health':    return <HealthView actions={actions} />;
      default:          return <OverviewView navigate={navigate} actions={actions} />;
    }
  })();

  return (
    <ToastProvider>
      <a href="#main" className="skip-link">Skip to main content</a>
      <div className={'shell' + (t.showRightPanel ? '' : ' no-right')}>
        <TopBar onOpenPalette={() => setPaletteOpen(true)}
                freshness={freshness}
                propsCount={counts.proposals}
                onNewProject={() => setNewProjOpen(true)} />
        <Sidebar route={route} navigate={navigate} counts={counts}
                 filters={filters} setFilter={setFilter} />
        {view}
        {t.showRightPanel && <RightPanel selection={selectionId} navigate={navigate} />}
      </div>

      <TweaksPanel title="Tweaks">
        <TweakSection label="Theme" />
        <TweakRadio label="Mode" value={t.theme} options={['light', 'dark']}
                    onChange={v => setTweak('theme', v)} />
        <TweakColor label="Accent" value={t.accent}
                    options={['blue', 'green', 'mono']}
                    onChange={v => setTweak('accent', v)}
                    swatches={{ blue: '#2862e6', green: '#1f8a5b', mono: '#1e2536' }} />

        <TweakSection label="Density" />
        <TweakRadio label="Spacing" value={t.density} options={['roomy', 'dense']}
                    onChange={v => setTweak('density', v)} />

        <TweakSection label="Aesthetic" />
        <TweakSelect label="Direction" value={t.aesthetic}
                     options={['editorial', 'terminal', 'paper']}
                     onChange={v => setTweak('aesthetic', v)} />

        <TweakSection label="Graph" />
        <TweakSelect label="Layout" value={t.layout}
                     options={['force', 'radial', 'hierarchical']}
                     onChange={v => setTweak('layout', v)} />

        <TweakSection label="Layout" />
        <TweakToggle label="Right context panel" value={t.showRightPanel}
                     onChange={v => setTweak('showRightPanel', v)} />
      </TweaksPanel>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} navigate={navigate} />

      <RebuildModal open={rebuildOpen} onClose={() => setRebuildOpen(false)} />
      <NewProjectModal open={newProjOpen} onClose={() => setNewProjOpen(false)} navigate={navigate} />
      <RecheckModal open={recheckOpen} onClose={() => setRecheckOpen(false)} />
    </ToastProvider>
  );
}

// TweakColor with named swatches support
const _TweakColor = TweakColor;
window.TweakColor = function ColorWithSwatches({ swatches, options, value, onChange, ...rest }) {
  if (swatches) {
    return (
      <div className="twk-row">
        <div className="twk-lbl"><span>{rest.label}</span><span className="twk-val">{value}</span></div>
        <div style={{ display: 'flex', gap: 6 }}>
          {options.map(opt => (
            <button key={opt} onClick={() => onChange(opt)} title={opt} aria-label={opt}
                    style={{ width: 28, height: 28, borderRadius: 7, background: swatches[opt],
                             border: value === opt ? '2px solid #1849c2' : '1px solid rgba(0,0,0,.15)',
                             cursor: 'default' }} />
          ))}
        </div>
      </div>
    );
  }
  return <_TweakColor options={options} value={value} onChange={onChange} {...rest} />;
};

// Defer render until WikiData is ready
window.WikiDataPromise
  .then(function() {
    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  })
  .catch(function(err) {
    document.getElementById('root').innerHTML =
      '<div style="padding:40px;font-family:\'Fira Code\',monospace;color:#b03240;background:#fbdfe2;border-radius:8px;margin:40px;border:1px solid #e26674">' +
      '<b>LLM Wiki — failed to load workspace data</b><br><br>' +
      (err.message || String(err)) +
      '<br><br><code>llm-wiki serve --workspace PATH</code>' +
      '</div>';
  });
