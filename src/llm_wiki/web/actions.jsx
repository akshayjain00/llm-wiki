/* global React, Icon */
// Action wiring layer — real API calls behind every button.
// Each modal is driven by server SSE/JSON; client-side fallbacks remain
// so the UI stays usable if the server is an older build.
const { useState, useEffect, useRef, createContext, useContext, useCallback } = React;

// ─── Toasts ────────────────────────────────────────────────────────────────
const ToastCtx = createContext(null);
function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const idRef = useRef(0);
  const push = useCallback((msg, opts = {}) => {
    const id = ++idRef.current;
    const it = { id, msg, kind: opts.kind || 'info', detail: opts.detail, ttl: opts.ttl ?? 4500 };
    setItems(xs => [...xs, it]);
    if (it.ttl) setTimeout(() => setItems(xs => xs.filter(x => x.id !== id)), it.ttl);
    return id;
  }, []);
  const dismiss = useCallback(id => setItems(xs => xs.filter(x => x.id !== id)), []);
  return (
    <ToastCtx.Provider value={{ push, dismiss }}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        {items.map(it => (
          <div key={it.id} className={'toast t-' + it.kind}>
            <div className="toast__icon">
              {it.kind === 'ok'   ? <Icon name="check" /> :
               it.kind === 'warn' ? <Icon name="bolt"  /> :
               it.kind === 'err'  ? <Icon name="x"     /> : <Icon name="info" />}
            </div>
            <div className="toast__body">
              <div className="toast__msg">{it.msg}</div>
              {it.detail && <div className="toast__detail">{it.detail}</div>}
            </div>
            <button className="toast__x" onClick={() => dismiss(it.id)} aria-label="Dismiss">×</button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
function useToast() { return useContext(ToastCtx); }

// ─── Modal shell ───────────────────────────────────────────────────────────
function Modal({ open, onClose, title, sub, children, footer, width = 560 }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = e => { if (e.key === 'Escape' && onClose) onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="modal-scrim" onClick={onClose} role="dialog" aria-modal="true" aria-label={title}>
      <div className="modal" style={{ width }} onClick={e => e.stopPropagation()}>
        <div className="modal__h">
          <div>
            <h2>{title}</h2>
            {sub && <p>{sub}</p>}
          </div>
          <button className="modal__x" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="modal__b">{children}</div>
        {footer && <div className="modal__f">{footer}</div>}
      </div>
    </div>
  );
}

// ─── Rebuild graph progress modal ──────────────────────────────────────────
// SSE event step IDs match server output exactly; UI state is driven by events.
const REBUILD_STEPS = [
  { id: 'scan',    label: 'Scanning durable pages',           detail: 'walking wiki/**/*.md' },
  { id: 'parse',   label: 'Parsing frontmatter & headings',   detail: 'pyyaml · markdown-it' },
  { id: 'alias',   label: 'Resolving entity aliases',         detail: 'entity_aliases · candidates' },
  { id: 'edges',   label: 'Materialising edges',              detail: 'links_to · mentions · belongs_to_project' },
  { id: 'propose', label: 'Generating link proposals',        detail: 'rule-based + cosine threshold 0.88' },
  { id: 'commit',  label: 'Writing state/index.db',           detail: 'transaction commit · 0 markdown writes' },
];

function RebuildModal({ open, onClose, onDone }) {
  const [step, setStep]       = useState(0);    // index of last completed step + 1
  const [done, setDone]       = useState(false);
  const [doneData, setDoneData] = useState(null);
  const [error, setError]     = useState(null);
  const toast = useToast();

  useEffect(() => {
    if (!open) { setStep(0); setDone(false); setDoneData(null); setError(null); return undefined; }
    setStep(0); setDone(false); setDoneData(null); setError(null);

    let aborted = false;

    fetch('/api/graph/rebuild', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force: false }),
    }).then(async res => {
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.error || `HTTP ${res.status}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      while (true) {
        const { done: rdone, value } = await reader.read();
        if (rdone || aborted) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split('\n');
        buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          let evt;
          try { evt = JSON.parse(line.slice(6)); } catch { continue; }
          if (evt.step === 'done') {
            setStep(REBUILD_STEPS.length);
            setDone(true);
            setDoneData(evt);
            onDone && onDone(evt);
          } else {
            const idx = REBUILD_STEPS.findIndex(s => s.id === evt.step);
            if (idx >= 0) setStep(idx + 1);
          }
        }
      }
    }).catch(err => {
      if (!aborted) {
        setError(err.message);
        toast && toast.push('Rebuild failed: ' + err.message, { kind: 'err' });
      }
    });

    return () => { aborted = true; };
  }, [open]);  // eslint-disable-line react-hooks/exhaustive-deps

  const doneSummary = doneData
    ? `${doneData.pages} pages · ${doneData.edges} edges · ${doneData.proposals} proposals · ${doneData.duration_ms}ms · ${doneData.markdown_writes} markdown writes`
    : 'Rebuild complete · 0 markdown writes';

  return (
    <Modal open={open} onClose={onClose} title="Rebuild graph"
           sub="Re-derives state/index.db from current markdown. Read-only against the wiki — no markdown is mutated."
           footer={
             <>
               <span className="mono dim">
                 {doneData ? `run ${doneData.run_id}` : error ? 'failed' : 'running…'} · workspace ~/AI_V2/team_memory_wiki
               </span>
               <button className={'btn ' + (done || error ? 'primary' : 'ghost')}
                       onClick={onClose} disabled={!done && !error}>
                 {done || error ? 'Close' : 'Working…'}
               </button>
             </>
           }>
      <ol className="rebuild-steps">
        {REBUILD_STEPS.map((s, i) => {
          const state = i < step ? 'ok' : (i === step && !done ? 'run' : 'idle');
          return (
            <li key={i} className={'r-step is-' + state}>
              <span className="r-icn">
                {state === 'ok'  ? <Icon name="check" /> :
                 state === 'run' ? <span className="spin" /> :
                 <span className="dot" />}
              </span>
              <span className="r-lbl">{s.label}</span>
              <span className="r-detail mono">{s.detail}</span>
            </li>
          );
        })}
      </ol>
      {done && (
        <div className="rebuild-done">
          <Icon name="check" /> {doneSummary}
        </div>
      )}
      {error && (
        <div style={{ marginTop: 12, padding: '10px 12px', borderRadius: 8, fontSize: '12.5px',
                      background: 'color-mix(in srgb, var(--err) 10%, var(--surface))',
                      border: '1px solid color-mix(in srgb, var(--err) 30%, var(--hairline))',
                      color: 'var(--err)' }}>
          Error: {error}
        </div>
      )}
    </Modal>
  );
}

// ─── New Project modal ─────────────────────────────────────────────────────
const PROJECT_TEMPLATES = [
  { id: 'standard', name: 'Standard project',    desc: 'overview · decisions · runbook · open-questions' },
  { id: 'eng',      name: 'Engineering project', desc: 'overview · architecture · adr · runbook · changelog' },
  { id: 'research', name: 'Research note',       desc: 'overview · prior-art · experiments · findings' },
  { id: 'minimal',  name: 'Minimal',             desc: 'overview only' },
];
const OWNERS = ['Akshay Jain', 'Data Team', 'Eng / Knowledge', 'ML Platform', 'Internal Tools'];

function slugify(s) {
  return s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
}
function templatePages(id) {
  switch (id) {
    case 'eng':      return ['overview', 'architecture', 'adr', 'runbook', 'changelog'];
    case 'research': return ['overview', 'prior-art', 'experiments', 'findings'];
    case 'minimal':  return ['overview'];
    default:         return ['overview', 'decisions', 'runbook', 'open-questions'];
  }
}

function NewProjectModal({ open, onClose, navigate }) {
  const toast = useToast();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({ name: '', slug: '', owner: 'Akshay Jain', template: 'standard', description: '', seedFromPath: '' });
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open) { setStep(0); setError(null); setForm(f => ({ ...f, name: '', slug: '', description: '', seedFromPath: '' })); }
  }, [open]);

  const update = (k, v) => setForm(f => {
    const next = { ...f, [k]: v };
    if (k === 'name') next.slug = slugify(v);
    return next;
  });

  const pages = templatePages(form.template);
  const canNext = step === 0 ? form.name.trim().length > 0 : true;

  const handleCreate = async () => {
    setStep(3); setError(null);
    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name.trim(), slug: form.slug, owner: form.owner,
          description: form.description || undefined, template: form.template,
          seed_from: form.seedFromPath || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        const msg = data.error === 'writes_disabled'
          ? 'Server write-protection is on — restart llm-wiki serve with --allow-writes.'
          : data.error === 'slug_exists'
          ? `Slug "${form.slug}" already exists (${data.existing}).`
          : data.error || `Error ${res.status}`;
        setError(msg); setStep(2);
        toast && toast.push(msg, { kind: 'err' });
        return;
      }
      toast && toast.push(`Project created · ${form.name}`, {
        kind: 'ok',
        detail: `projects/${data.node_id.split(':')[1] || form.slug}/ · ${(data.pages || []).length} pages · graph rebuild queued`,
      });
      onClose();
      // Short delay so the toast renders before reload
      setTimeout(() => { window.location.reload(); }, 600);
    } catch (err) {
      setError(err.message); setStep(2);
      toast && toast.push(err.message, { kind: 'err' });
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="New project"
           sub="Scaffolds a project folder under ~/AI_V2/team_memory_wiki/projects/ and triggers the standard project flow: page templates, entity registration, and a graph rebuild."
           width={640}
           footer={
             <>
               <span className="mono dim">step {Math.min(step + 1, 3)} of 3</span>
               <span style={{ display: 'flex', gap: 8 }}>
                 <button className="btn ghost" onClick={onClose}>Cancel</button>
                 {step > 0 && step < 3 && <button className="btn ghost" onClick={() => setStep(s => s - 1)}>Back</button>}
                 {step < 2 && <button className="btn primary" disabled={!canNext} onClick={() => setStep(s => s + 1)}>Continue</button>}
                 {step === 2 && <button className="btn primary" onClick={handleCreate}>Create project</button>}
               </span>
             </>
           }>

      {step === 0 && (
        <div className="form">
          <div className="field">
            <label>Project name</label>
            <input autoFocus value={form.name} onChange={e => update('name', e.target.value)} placeholder="e.g. Linear Importer" />
          </div>
          <div className="field">
            <label>Slug <span className="mono dim">— folder + entity id</span></label>
            <input value={form.slug} onChange={e => update('slug', slugify(e.target.value))} placeholder="linear-importer" />
            <div className="hint">Becomes <span className="mono">~/AI_V2/team_memory_wiki/projects/{form.slug || '…'}/</span> and <span className="mono">project:{form.slug || '…'}</span>.</div>
          </div>
          <div className="field">
            <label>Owner</label>
            <div className="chip-group">
              {OWNERS.map(o => (
                <button key={o} type="button" className={'chip-btn' + (form.owner === o ? ' is-on' : '')} onClick={() => update('owner', o)}>{o}</button>
              ))}
            </div>
          </div>
          <div className="field">
            <label>One-line description <span className="mono dim">— optional</span></label>
            <input value={form.description} onChange={e => update('description', e.target.value)} placeholder="What is this project for?" />
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="form">
          <div className="field">
            <label>Template</label>
            <div className="tpl-list">
              {PROJECT_TEMPLATES.map(p => (
                <button key={p.id} type="button" className={'tpl-row' + (form.template === p.id ? ' is-on' : '')} onClick={() => update('template', p.id)}>
                  <span className="tpl-row__radio" />
                  <span>
                    <div className="tpl-row__name">{p.name}</div>
                    <div className="tpl-row__desc mono">{p.desc}</div>
                  </span>
                </button>
              ))}
            </div>
          </div>
          <div className="field">
            <label>Seed from existing folder <span className="mono dim">— optional</span></label>
            <input value={form.seedFromPath} onChange={e => update('seedFromPath', e.target.value)} placeholder="~/repos/linear-importer" />
            <div className="hint">If set, the LLM will scan this path on first rebuild and pre-populate the project's overview page.</div>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="form">
          <div className="confirm">
            <h3>Will create</h3>
            <ul className="path-list">
              <li><span className="mono">projects/{form.slug}/</span> <span className="dim">— project folder</span></li>
              {pages.map(p => <li key={p}><span className="mono">projects/{form.slug}/{p}.md</span> <span className="dim">— from <span className="mono">{form.template}</span> template</span></li>)}
            </ul>
            <h3 style={{ marginTop: 16 }}>And register</h3>
            <ul className="path-list">
              <li><span className="mono">project:{form.slug}</span> <span className="dim">— canonical entity, owner: {form.owner}</span></li>
              <li><span className="mono">graph rebuild</span> <span className="dim">— queued; ~25s; 0 markdown writes outside this project</span></li>
              {form.seedFromPath && <li><span className="mono">seed scan</span> <span className="dim">— {form.seedFromPath} → page proposals</span></li>}
            </ul>
            <div className="callout">
              <Icon name="bolt" className="icon" />
              <span>This is the only flow in the UI that <b>writes</b> to the workspace. Page edits and link approvals still happen out-of-band.</span>
            </div>
            {error && (
              <div style={{ marginTop: 12, padding: '10px 12px', borderRadius: 8, fontSize: '12.5px',
                            background: 'color-mix(in srgb, var(--err) 10%, var(--surface))',
                            border: '1px solid color-mix(in srgb, var(--err) 30%, var(--hairline))',
                            color: 'var(--err)' }}>
                {error}
              </div>
            )}
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="form" style={{ alignItems: 'center', textAlign: 'center', padding: '32px 0' }}>
          <div className="spin" style={{ width: 28, height: 28, borderWidth: 3 }} />
          <div style={{ marginTop: 16, color: 'var(--ink-1)' }}>Creating <b>{form.name}</b>…</div>
          <div className="mono dim" style={{ marginTop: 4, fontSize: 11 }}>scaffolding {pages.length} pages · registering entity · queueing rebuild</div>
        </div>
      )}
    </Modal>
  );
}

// ─── Re-check progress (health) ────────────────────────────────────────────
function RecheckModal({ open, onClose }) {
  const [result, setResult] = useState(null);
  const [error, setError]   = useState(null);
  const toast = useToast();

  useEffect(() => {
    if (!open) { setResult(null); setError(null); return undefined; }
    fetch('/api/health/recheck', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      .then(res => {
        if (!res.ok) return res.json().then(d => { throw new Error(d.error || `HTTP ${res.status}`); });
        return res.json();
      })
      .then(data => setResult(data))
      .catch(err => {
        setError(err.message);
        toast && toast.push('Health check failed: ' + err.message, { kind: 'err' });
      });
  }, [open]);  // eslint-disable-line react-hooks/exhaustive-deps

  const done = !!(result || error);

  return (
    <Modal open={open} onClose={onClose} title="Re-check workspace health"
           sub="Runs diagnostic checks against state/index.db and the live filesystem."
           footer={<button className="btn primary" onClick={onClose} disabled={!done}>{done ? 'Close' : 'Checking…'}</button>}>
      <div style={{ padding: '12px 0' }}>
        {!done && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="spin" />
            <span className="mono dim">running checks · verifying graph schema · alias hygiene · proposal drift…</span>
          </div>
        )}
        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--err)' }}>
            <Icon name="x" /><span>Check failed: {error}</span>
          </div>
        )}
        {result && result.checks && result.checks.map(c => (
          <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0',
                                   borderBottom: '1px solid var(--hairline)' }}>
            <span style={{ color: c.status === 'ok' ? 'var(--ok)' : c.status === 'warn' ? 'var(--warn)' : 'var(--err)', flexShrink: 0 }}>
              {c.status === 'ok' ? <Icon name="check" /> : c.status === 'warn' ? <Icon name="bolt" /> : <Icon name="x" />}
            </span>
            <span style={{ flex: 1, fontSize: '12.5px', color: 'var(--ink-1)' }}>{c.id.replace(/_/g, ' ')}</span>
            <span className="mono" style={{ fontSize: 11, color: 'var(--ink-4)' }}>{c.value}</span>
          </div>
        ))}
      </div>
    </Modal>
  );
}

Object.assign(window, { ToastProvider, useToast, Modal, RebuildModal, NewProjectModal, RecheckModal });
