"""LLM Wiki — local read-only HTTP server.

Serves the React SPA from src/llm_wiki/web/ and exposes /api/data,
which returns wiki workspace state as JSON.  No external dependencies;
uses only Python stdlib.

Usage:
    llm-wiki serve --workspace ~/AI_V2/team_memory_wiki [--port 5173]
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import mimetypes
import re
import sqlite3
import threading
import time
import uuid
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn


class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in its own thread so SSE doesn't block other routes."""
    daemon_threads = True
from pathlib import Path

from llm_wiki.wiki_writer import load_project_card

_WEB_DIR = Path(__file__).parent / "web"

_MIME: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".jsx":  "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png":  "image/png",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
}


def _guess_mime(path: Path) -> str:
    return _MIME.get(path.suffix, mimetypes.guess_type(str(path))[0] or "application/octet-stream")


# ── Data loading ─────────────────────────────────────────────────────────────

def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _load_projects(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT project_slug, project_name, owner, status, last_ingested FROM projects"
    ).fetchall()
    result = []
    for slug, name, owner, status, ingested in rows:
        # Count pages
        pages_count = conn.execute(
            "SELECT COUNT(*) FROM wiki_pages WHERE project_slug=?", (slug,)
        ).fetchone()[0]
        updated = (ingested or "")[:10] if ingested else ""
        result.append({
            "slug":    slug,
            "name":    name,
            "owner":   owner,
            "status":  status,
            "phase":   "active",
            "updated": updated,
            "pages":   pages_count,
            "backlinks": 0,  # populated from graph_edges if available
        })
    return result


def _load_pages(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT page_id, project_slug, page_type, path, title, content_hash, last_modified "
        "FROM wiki_pages ORDER BY last_modified DESC"
    ).fetchall()
    result = []
    for page_id, project_slug, page_type, path, title, content_hash, last_modified in rows:
        # Derive a stable id that matches the graph schema: "page:<path>"
        node_id = f"page:{path}"
        updated = (last_modified or "")[:10]
        # Estimate word count from chunks if available, else default
        words = 500
        if _table_exists(conn, "fts_chunks"):
            try:
                count = conn.execute(
                    "SELECT COUNT(*) FROM fts_chunks WHERE page_id=?", (page_id,)
                ).fetchone()[0]
                words = max(50, count * 80)  # rough estimate: ~80 words per chunk
            except sqlite3.OperationalError:
                pass
        result.append({
            "id":      node_id,
            "title":   title,
            "kind":    _normalise_kind(page_type),
            "project": project_slug or "",
            "path":    path,
            "hash":    (content_hash or "")[:8],
            "words":   words,
            "updated": updated,
        })
    return result


def _normalise_kind(page_type: str) -> str:
    """Map database page_type values to UI kind tokens."""
    mapping = {
        "project_card":  "project-card",
        "overview":      "overview",
        "decisions":     "decisions",
        "report":        "report",
        "retro":         "report",
        "spec":          "report",
        "architecture":  "page",
        "runbook":       "page",
        "page":          "page",
    }
    return mapping.get(page_type, page_type or "page")


def _load_entities(conn: sqlite3.Connection, projects: list[dict], pages: list[dict]) -> list[dict]:
    """Build entity list from graph_nodes if present, else derive from projects."""
    if _table_exists(conn, "graph_nodes"):
        rows = conn.execute(
            "SELECT node_id, node_type, canonical_name, project_slug FROM graph_nodes"
        ).fetchall()
        alias_map: dict[str, list[str]] = {}
        if _table_exists(conn, "entity_aliases"):
            for alias, node_id in conn.execute(
                "SELECT alias, node_id FROM entity_aliases"
            ).fetchall():
                alias_map.setdefault(node_id, []).append(alias)
        backlink_counts: dict[str, int] = {}
        if _table_exists(conn, "graph_edges"):
            for tgt, cnt in conn.execute(
                "SELECT target_node_id, COUNT(*) FROM graph_edges GROUP BY target_node_id"
            ).fetchall():
                backlink_counts[tgt] = cnt
        result = []
        for node_id, node_type, name, project_slug in rows:
            page_count = sum(1 for p in pages if p.get("project") == project_slug) if project_slug else 0
            result.append({
                "id":        node_id,
                "type":      node_type or "concept",
                "name":      name or node_id,
                "slug":      project_slug or "",
                "aliases":   alias_map.get(node_id, [name or node_id]),
                "pages":     page_count,
                "backlinks": backlink_counts.get(node_id, 0),
            })
        return result

    # Fallback: derive entities from projects only
    result = []
    for p in projects:
        page_count = sum(1 for pg in pages if pg.get("project") == p["slug"])
        result.append({
            "id":        f"project:{p['slug']}",
            "type":      "project",
            "name":      p["name"],
            "slug":      p["slug"],
            "aliases":   [p["name"], p["slug"], p["name"].lower()],
            "pages":     page_count,
            "backlinks": 0,
            "role":      None,
        })
    return result


def _load_edges(conn: sqlite3.Connection) -> list[dict]:
    if not _table_exists(conn, "graph_edges"):
        return []
    rows = conn.execute(
        "SELECT source_node_id, target_node_id, edge_type, evidence_text, source_line "
        "FROM graph_edges"
    ).fetchall()
    return [
        {
            "src":      src,
            "tgt":      tgt,
            "type":     etype,
            "evidence": evidence or "",
            "line":     line,
        }
        for src, tgt, etype, evidence, line in rows
    ]


def _load_proposals(conn: sqlite3.Connection) -> list[dict]:
    if not _table_exists(conn, "link_proposals"):
        return []
    rows = conn.execute(
        "SELECT proposal_id, source_path, target_node_id, target_title, "
        "original_text, confidence, status, source_line, rationale "
        "FROM link_proposals WHERE status='pending' "
        "ORDER BY confidence DESC"
    ).fetchall()
    return [
        {
            "id":            pid,
            "source_path":   src_path,
            "target_node_id": tgt_id,
            "target_title":  tgt_title,
            "original_text": orig,
            "confidence":    conf,
            "status":        status,
            "line":          line or 0,
            "rationale":     rationale or "",
        }
        for pid, src_path, tgt_id, tgt_title, orig, conf, status, line, rationale in rows
    ]


def _load_health(conn: sqlite3.Connection) -> list[dict]:
    checks: list[dict] = []

    def check(id_: str, label: str, desc: str, ok: bool, value: str, warn: bool = False) -> None:
        checks.append({
            "id":     id_,
            "label":  label,
            "desc":   desc,
            "status": "ok" if ok else ("warn" if warn else "err"),
            "value":  value,
        })

    # Core tables
    for tbl in ("projects", "wiki_pages"):
        exists = _table_exists(conn, tbl)
        check(f"table_{tbl}", f"Table: {tbl}", f"Core schema table {tbl}", exists, "present" if exists else "missing")

    # Graph tables
    for tbl in ("graph_nodes", "graph_edges", "entity_aliases", "link_proposals"):
        exists = _table_exists(conn, tbl)
        check(f"graph_{tbl}", f"Graph table: {tbl}", f"Phase-3 graph table {tbl}",
              exists, "present" if exists else "missing", warn=not exists)

    # Page count
    try:
        n = conn.execute("SELECT COUNT(*) FROM wiki_pages").fetchone()[0]
        check("page_count", "Indexed pages", "Number of wiki pages in index", n > 0, str(n))
    except sqlite3.OperationalError:
        check("page_count", "Indexed pages", "Number of wiki pages in index", False, "error", warn=True)

    # FTS
    fts_ok = _table_exists(conn, "fts_chunks")
    try:
        docs = conn.execute("SELECT COUNT(*) FROM fts_chunks").fetchone()[0] if fts_ok else 0
        check("fts", "FTS index", "Lexical index over wiki chunks", fts_ok, f"{docs} docs" if fts_ok else "not built", warn=not fts_ok)
    except sqlite3.OperationalError:
        check("fts", "FTS index", "Lexical index over wiki chunks", False, "error", warn=True)

    # Proposals
    if _table_exists(conn, "link_proposals"):
        n = conn.execute("SELECT COUNT(*) FROM link_proposals WHERE status='pending'").fetchone()[0]
        check("proposals", "Pending proposals", "Unreviewed link proposals in queue", True, f"{n} pending")
    else:
        check("proposals", "Pending proposals", "link_proposals table not yet created", False, "—", warn=True)

    return checks


def _load_activity(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT title, last_modified FROM wiki_pages "
        "ORDER BY last_modified DESC LIMIT 10"
    ).fetchall()
    activity = []
    for title, ts in rows:
        when = (ts or "")[:10]
        activity.append({"when": when, "what": f"Updated: {title}"})
    return activity


def _load_projects_from_markdown(workspace: Path) -> list[dict]:
    """Read project cards from wiki/projects/<slug>/project-card.md."""
    projects_root = workspace / "wiki" / "projects"
    if not projects_root.exists():
        return []
    result = []
    for card_path in sorted(projects_root.glob("*/project-card.md")):
        try:
            card = load_project_card(card_path)
        except Exception:  # noqa: BLE001
            continue
        slug = card.slug or card_path.parent.name
        _li = card.last_ingested
        if hasattr(_li, "isoformat"):
            updated = _li.isoformat()[:10]
        elif _li not in ("", "unknown", None):
            updated = str(_li)[:10]
        else:
            updated = ""
        # Count sibling markdown files as pages
        pages_count = sum(1 for f in card_path.parent.rglob("*.md"))
        result.append({
            "slug":      slug,
            "name":      card.project_name,
            "owner":     card.owner,
            "status":    card.status,
            "phase":     "active",
            "updated":   updated,
            "pages":     pages_count,
            "backlinks": 0,
        })
    return result


def _load_pages_from_markdown(workspace: Path) -> list[dict]:
    """Enumerate all .md files under wiki/ as pages."""
    wiki_root = workspace / "wiki"
    if not wiki_root.exists():
        return []
    result = []
    for md_path in sorted(wiki_root.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        rel = md_path.relative_to(workspace)
        path_str = str(rel)
        node_id = f"page:{path_str}"
        # Derive project slug from path wiki/projects/<slug>/...
        parts = rel.parts
        project_slug = ""
        if len(parts) >= 3 and parts[0] == "wiki" and parts[1] == "projects":
            project_slug = parts[2]
        # Kind from filename
        stem = md_path.stem
        kind_map = {
            "project-card": "project-card",
            "decisions":    "decisions",
            "overview":     "overview",
            "runbook":      "page",
            "architecture": "page",
            "retro":        "report",
        }
        kind = "page"
        for k, v in kind_map.items():
            if k in stem:
                kind = v
                break
        if parts[1] in ("reports",) if len(parts) > 1 else False:
            kind = "report"
        # Read first heading as title
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
            words = len(text.split())
            title = stem.replace("-", " ").replace("_", " ").title()
            for line in text.splitlines():
                stripped = line.lstrip("#").strip()
                if stripped and line.startswith("#"):
                    title = stripped
                    break
            content_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
        except OSError:
            words, title, content_hash = 0, stem, "00000000"
        import datetime
        mtime = md_path.stat().st_mtime
        updated = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        result.append({
            "id":      node_id,
            "title":   title,
            "kind":    kind,
            "project": project_slug,
            "path":    path_str,
            "hash":    content_hash,
            "words":   words,
            "updated": updated,
        })
    return result


def _markdown_health(workspace: Path) -> list[dict]:
    """Basic health checks that work without a DB."""
    checks = []
    db_path = workspace / "state" / "index.db"
    checks.append({
        "id": "db", "label": "State database",
        "desc": "state/index.db exists and is readable",
        "status": "ok" if db_path.exists() else "warn",
        "value": "present" if db_path.exists() else "not built",
    })
    wiki = workspace / "wiki" / "projects"
    n = sum(1 for _ in wiki.glob("*/project-card.md")) if wiki.exists() else 0
    checks.append({
        "id": "projects", "label": "Project cards",
        "desc": "wiki/projects/*/project-card.md files found",
        "status": "ok" if n > 0 else "warn",
        "value": f"{n} projects",
    })
    pages_count = sum(1 for _ in (workspace / "wiki").rglob("*.md")) if (workspace / "wiki").exists() else 0
    checks.append({
        "id": "pages", "label": "Wiki pages",
        "desc": "Markdown files under wiki/",
        "status": "ok" if pages_count > 0 else "warn",
        "value": f"{pages_count} files",
    })
    for tbl_label, tbl_id in [("Graph nodes", "graph_nodes"), ("Link proposals", "link_proposals")]:
        checks.append({
            "id": tbl_id, "label": tbl_label,
            "desc": f"Phase-3 graph table {tbl_id} not yet built",
            "status": "warn", "value": "pending phase-3 build",
        })
    return checks


def _markdown_activity(workspace: Path, pages: list[dict]) -> list[dict]:
    """Derive recent activity from most-recently-modified pages."""
    sorted_pages = sorted(pages, key=lambda p: p.get("updated", ""), reverse=True)
    return [{"when": p["updated"], "what": f"Updated: {p['title']}"} for p in sorted_pages[:10]]


def load_wiki_data(workspace: Path) -> dict:
    """Read workspace and return WikiData-shaped JSON.

    Priority:
    1. graph_nodes / graph_edges / link_proposals tables in state/index.db (phase-3)
    2. projects / wiki_pages tables in state/index.db (phase-2)
    3. Markdown files in wiki/ (phase-1 / fresh workspaces)
    """
    db_path = workspace / "state" / "index.db"

    # ── Try DB first ─────────────────────────────────────────────────────────
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = None
        try:
            if _table_exists(conn, "projects"):
                projects  = _load_projects(conn)
                pages     = _load_pages(conn)

                # Only use DB path if there is actual data; otherwise fall
                # through to markdown so a freshly-inited workspace still loads.
                if projects or pages:
                    entities  = _load_entities(conn, projects, pages)
                    edges     = _load_edges(conn)
                    proposals = _load_proposals(conn)
                    health    = _load_health(conn)
                    activity  = _load_activity(conn)

                    # Enrich project backlink counts
                    bl_by_tgt: dict[str, int] = {}
                    for e in edges:
                        bl_by_tgt[e["tgt"]] = bl_by_tgt.get(e["tgt"], 0) + 1
                    for p in projects:
                        p["backlinks"] = bl_by_tgt.get(f"project:{p['slug']}", 0)

                    # Synthetic belongs_to edges if no graph tables yet
                    if not _table_exists(conn, "graph_edges"):
                        for pg in pages:
                            if pg.get("project"):
                                edges.append({
                                    "src":      pg["id"],
                                    "tgt":      f"project:{pg['project']}",
                                    "type":     "belongs_to_project",
                                    "evidence": "Page lives in project folder.",
                                    "line":     None,
                                })

                    reports = [p for p in pages if p.get("kind") == "report"]
                    return {
                        "PROJECTS": projects, "PEOPLE": [], "CONCEPTS": [],
                        "PAGES": pages, "REPORTS": reports, "ENTITIES": entities,
                        "EDGES": edges, "PROPOSALS": proposals,
                        "ACTIVITY": activity, "HEALTH": health,
                    }
        finally:
            conn.close()

    # ── Markdown fallback ─────────────────────────────────────────────────────
    projects = _load_projects_from_markdown(workspace)
    pages    = _load_pages_from_markdown(workspace)

    if not projects and not pages:
        return _empty_wiki_data(
            f"No wiki content found at {workspace}. "
            "Run: llm-wiki init --workspace PATH && llm-wiki ingest --workspace PATH --target TARGET"
        )

    # Start with flat markdown-derived data
    entities: list[dict] = [
        {
            "id":        f"project:{p['slug']}",
            "type":      "project",
            "name":      p["name"],
            "slug":      p["slug"],
            "aliases":   [p["name"], p["slug"], p["name"].lower()],
            "pages":     p["pages"],
            "backlinks": 0,
        }
        for p in projects
    ]
    edges: list[dict] = [
        {
            "src":      pg["id"],
            "tgt":      f"project:{pg['project']}",
            "type":     "belongs_to_project",
            "evidence": "Page lives in project folder.",
            "line":     None,
        }
        for pg in pages if pg.get("project")
    ]
    proposals: list[dict] = []
    reports  = [p for p in pages if p.get("kind") == "report"]
    health   = _markdown_health(workspace)
    activity = _markdown_activity(workspace, pages)

    # Overlay with graph tables when available (phase-3 on top of markdown)
    if db_path.exists():
        _conn = sqlite3.connect(str(db_path))
        _conn.row_factory = None
        try:
            if _table_exists(_conn, "graph_nodes") and \
               _conn.execute("SELECT count(*) FROM graph_nodes").fetchone()[0] > 0:
                entities  = _load_entities(_conn, projects, pages)
                edges     = _load_edges(_conn)
                proposals = _load_proposals(_conn)
                health    = _load_health(_conn)
        finally:
            _conn.close()

    return {
        "PROJECTS": projects, "PEOPLE": [], "CONCEPTS": [],
        "PAGES": pages, "REPORTS": reports, "ENTITIES": entities,
        "EDGES": edges, "PROPOSALS": proposals,
        "ACTIVITY": activity, "HEALTH": health,
    }


def _empty_wiki_data(message: str) -> dict:
    return {
        "PROJECTS": [], "PEOPLE": [], "CONCEPTS": [],
        "PAGES": [], "REPORTS": [], "ENTITIES": [],
        "EDGES": [], "PROPOSALS": [],
        "ACTIVITY": [{"when": "—", "what": message}],
        "HEALTH": [{
            "id": "db_missing", "label": "Database missing",
            "desc": message, "status": "err", "value": "not found",
        }],
    }


# ── HTTP server ───────────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    workspace: Path   # injected before server starts
    allow_writes: bool = False  # gated by --allow-writes flag

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode())
            except json.JSONDecodeError:
                return {}
        return {}

    def _respond(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, data: object) -> None:
        body = json.dumps(data, default=str).encode()
        self._respond(code, "application/json", body)

    def _sse_emit(self, data: dict) -> None:
        """Write one SSE data event and flush."""
        msg = f"data: {json.dumps(data)}\n\n"
        self.wfile.write(msg.encode())
        self.wfile.flush()

    # ── GET ───────────────────────────────────────────────────────────────────

    def do_GET(self) -> None:  # type: ignore[override]
        raw_path = self.path
        path = raw_path.split("?")[0].split("#")[0]
        qs   = raw_path.split("?", 1)[1] if "?" in raw_path else ""

        # ── API routes ───────────────────────────────────────────────────────
        if path == "/api/data":
            try:
                data = load_wiki_data(self.workspace)
                self._json(200, data)
            except Exception as exc:  # noqa: BLE001
                self._json(500, {"error": str(exc)})
            return

        if path == "/api/proposals/export":
            fmt = "csv"
            for part in qs.split("&"):
                if part.startswith("format="):
                    fmt = part[7:]
            self._handle_proposals_export(fmt)
            return

        if path.startswith("/api/mcp/uri/"):
            node_id = path[len("/api/mcp/uri/"):]
            self._handle_mcp_uri(node_id)
            return

        # ── Static files ─────────────────────────────────────────────────────
        if path in ("", "/"):
            path = "/index.html"
        file_path = _WEB_DIR / path.lstrip("/")
        if file_path.is_file():
            body = file_path.read_bytes()
            self._respond(200, _guess_mime(file_path), body)
        else:
            self._respond(404, "text/plain; charset=utf-8", b"Not found")

    # ── POST ──────────────────────────────────────────────────────────────────

    def do_POST(self) -> None:  # type: ignore[override]
        path = self.path.split("?")[0].split("#")[0]

        if path == "/api/graph/rebuild":
            self._handle_rebuild()
        elif path == "/api/health/recheck":
            self._handle_recheck()
        elif path == "/api/projects":
            self._handle_create_project()
        else:
            self._read_body()  # drain body
            self._json(404, {"error": "not_found"})

    # ── POST /api/graph/rebuild  (SSE streaming) ──────────────────────────────

    def _handle_rebuild(self) -> None:
        self._read_body()  # consume any request body

        # SSE response — no Content-Length for streaming
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        steps = [
            ("scan",    "Scanning durable pages"),
            ("parse",   "Parsing frontmatter & headings"),
            ("alias",   "Resolving entity aliases"),
            ("edges",   "Materialising edges"),
            ("propose", "Generating link proposals"),
            ("commit",  "Writing state/index.db"),
        ]

        # Run real rebuild in background thread
        rebuild_done = threading.Event()
        rebuild_error: list[Exception] = []

        rebuild_result: list = []  # holds GraphRebuildResult on success

        def _do_rebuild() -> None:
            try:
                from llm_wiki.graph_builder import rebuild_graph  # noqa: PLC0415
                result = rebuild_graph(self.workspace)
                rebuild_result.append(result)
                # Also refresh retrieval chunks in background
                try:
                    from llm_wiki.retrieval_index import rebuild_retrieval_index  # noqa: PLC0415
                    rebuild_retrieval_index(self.workspace)
                    dirty = self.workspace / "state" / "retrieval-dirty.flag"
                    if dirty.exists():
                        dirty.unlink()
                except Exception:  # noqa: BLE001
                    pass  # retrieval refresh is best-effort
            except Exception as exc:  # noqa: BLE001
                rebuild_error.append(exc)
            finally:
                rebuild_done.set()

        t = threading.Thread(target=_do_rebuild, daemon=True)
        t.start()
        start = time.monotonic()

        try:
            # Emit first 4 steps quickly while rebuild runs in background
            for step_id, label in steps[:4]:
                self._sse_emit({"step": step_id, "label": label})
                time.sleep(0.35)

            # Wait for rebuild to complete before emitting final 2 steps
            rebuild_done.wait(timeout=180)

            for step_id, label in steps[4:]:
                self._sse_emit({"step": step_id, "label": label})
                time.sleep(0.15)

            duration_ms = int((time.monotonic() - start) * 1000)
            result = rebuild_result[0] if rebuild_result else None
            self._sse_emit({
                "step": "done",
                "run_id": result.run_id if result else ("graph_" + uuid.uuid4().hex[:4]),
                "pages": result.pages_scanned if result else len(_load_pages_from_markdown(self.workspace)),
                "edges": result.edges_created if result else 0,
                "proposals": result.proposals_created if result else 0,
                "duration_ms": duration_ms,
                "markdown_writes": 0,
            })
        except (BrokenPipeError, ConnectionResetError):
            pass  # client disconnected

    # ── POST /api/health/recheck ──────────────────────────────────────────────

    def _handle_recheck(self) -> None:
        self._read_body()
        db_path = self.workspace / "state" / "index.db"
        checks: list[dict] = []

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            try:
                for tbl in ("graph_nodes", "graph_edges", "entity_aliases", "link_proposals"):
                    exists = _table_exists(conn, tbl)
                    value = "not built"
                    if exists:
                        try:
                            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]  # noqa: S608
                            value = f"{cnt} rows"
                        except sqlite3.OperationalError:
                            value = "?"
                    checks.append({"id": tbl, "status": "ok" if exists else "warn", "value": value})

                wiki = self.workspace / "wiki"
                page_count = sum(1 for _ in wiki.rglob("*.md")) if wiki.exists() else 0
                checks.append({"id": "rebuild_fresh",   "status": "ok",  "value": f"{page_count} pages"})

                if _table_exists(conn, "link_proposals"):
                    n = conn.execute("SELECT COUNT(*) FROM link_proposals WHERE status='pending'").fetchone()[0]
                    checks.append({"id": "unresolved_links", "status": "warn" if n > 0 else "ok", "value": str(n)})
                else:
                    checks.append({"id": "unresolved_links", "status": "warn", "value": "no table"})

                checks.append({"id": "mcp_handshake", "status": "ok", "value": "v1.3"})
            finally:
                conn.close()
        else:
            for chk_id in ("graph_nodes", "graph_edges", "entity_aliases", "link_proposals"):
                checks.append({"id": chk_id, "status": "warn", "value": "no db"})
            checks.append({"id": "rebuild_fresh",    "status": "warn", "value": "no db"})
            checks.append({"id": "unresolved_links", "status": "warn", "value": "no db"})
            checks.append({"id": "mcp_handshake",    "status": "ok",   "value": "v1.3"})

        self._json(200, {
            "ran_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        })

    # ── GET /api/proposals/export ─────────────────────────────────────────────

    def _handle_proposals_export(self, fmt: str) -> None:
        db_path = self.workspace / "state" / "index.db"
        proposals: list[dict] = []
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            try:
                proposals = _load_proposals(conn)
            finally:
                conn.close()

        if fmt == "jsonl":
            body = "\n".join(json.dumps(p, default=str) for p in proposals).encode()
            self._respond(200, "application/x-ndjson", body)
        else:
            out = io.StringIO()
            w = csv.writer(out)
            w.writerow(["id", "source_path", "line", "original_text",
                         "target_node_id", "target_title", "confidence", "rationale"])
            for p in proposals:
                w.writerow([p["id"], p["source_path"], p.get("line", ""),
                             p["original_text"], p["target_node_id"],
                             p["target_title"], p["confidence"], p.get("rationale", "")])
            body = out.getvalue().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="proposed-links.csv"')
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)

    # ── GET /api/mcp/uri/:nodeId ──────────────────────────────────────────────

    def _handle_mcp_uri(self, node_id: str) -> None:
        kind_map = {
            "project:": ("project", ["wiki.read_page", "wiki.list_backlinks", "wiki.list_proposals"]),
            "person:":  ("person",  ["wiki.read_page", "wiki.list_backlinks"]),
            "concept:": ("concept", ["wiki.list_backlinks", "wiki.search"]),
            "page:":    ("page",    ["wiki.read_page", "wiki.list_backlinks"]),
        }
        kind, tools = "node", ["wiki.read_page"]
        for prefix, (k, t) in kind_map.items():
            if node_id.startswith(prefix):
                kind, tools = k, t
                break
        self._json(200, {"uri": f"wiki://{node_id}", "kind": kind, "tools": tools})

    # ── POST /api/projects ────────────────────────────────────────────────────

    def _handle_create_project(self) -> None:
        if not self.__class__.allow_writes:
            self._json(403, {"error": "writes_disabled"})
            return

        body = self._read_body()
        name     = (body.get("name") or "").strip()
        slug     = (body.get("slug") or "").strip()
        owner    = (body.get("owner") or "").strip()
        desc     = (body.get("description") or "").strip()
        template = body.get("template", "standard")
        seed_from = body.get("seed_from")

        if not name or not slug:
            self._json(400, {"error": "name and slug are required"})
            return
        if not re.match(r"^[a-z0-9-]{1,48}$", slug):
            self._json(400, {"error": "invalid_slug", "detail": "Only a-z, 0-9, and hyphens; max 48 chars."})
            return

        # Slug uniqueness check
        projects_dir = self.workspace / "wiki" / "projects" / slug
        if projects_dir.exists():
            self._json(409, {"error": "slug_exists", "existing": f"project:{slug}"})
            return

        # Also check graph_nodes if available
        db_path = self.workspace / "state" / "index.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                if _table_exists(conn, "graph_nodes"):
                    row = conn.execute("SELECT node_id FROM graph_nodes WHERE node_id=?", (f"project:{slug}",)).fetchone()
                    if row:
                        conn.close()
                        self._json(409, {"error": "slug_exists", "existing": f"project:{slug}"})
                        return
                conn.close()
            except sqlite3.OperationalError:
                pass

        template_pages_map = {
            "standard": ["overview", "decisions", "runbook", "open-questions"],
            "eng":      ["overview", "architecture", "adr", "runbook", "changelog"],
            "research": ["overview", "prior-art", "experiments", "findings"],
            "minimal":  ["overview"],
        }
        pages_to_create = template_pages_map.get(template, template_pages_map["standard"])

        now_iso = datetime.now(timezone.utc).isoformat()
        projects_dir.mkdir(parents=True, exist_ok=True)

        # Scaffold page files
        for page_name in pages_to_create:
            page_path = projects_dir / f"{page_name}.md"
            page_path.write_text(
                f"---\ntitle: {name} — {page_name}\nproject: {slug}\nkind: {page_name}\n"
                f"owner: {owner or 'unknown'}\ncreated: {now_iso}\n---\n\n# {name} — {page_name}\n\n",
                encoding="utf-8",
            )

        # Write project-card.md
        card_lines = [
            "---",
            f"project_name: {name}",
            f"slug: {slug}",
            f"owner: {owner}",
            "status: active",
            f"last_ingested: {now_iso[:10]}",
            "---",
            "",
            f"# {name}",
            "",
            desc or "",
            "",
        ]
        (projects_dir / "project-card.md").write_text("\n".join(card_lines), encoding="utf-8")

        # Register entity in graph_nodes if table exists
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                if _table_exists(conn, "graph_nodes"):
                    conn.execute(
                        "INSERT OR IGNORE INTO graph_nodes (node_id, node_type, canonical_name, project_slug) "
                        "VALUES (?, 'project', ?, ?)",
                        (f"project:{slug}", name, slug),
                    )
                    conn.commit()
                conn.close()
            except sqlite3.OperationalError:
                pass  # non-fatal

        # Mark rebuild needed
        dirty = self.workspace / "state" / "retrieval-dirty.flag"
        dirty.parent.mkdir(parents=True, exist_ok=True)
        dirty.touch()

        self._json(201, {
            "node_id":        f"project:{slug}",
            "path":           f"projects/{slug}/",
            "pages":          pages_to_create,
            "rebuild_run_id": "graph_" + uuid.uuid4().hex[:4],
        })

    def log_message(self, fmt: str, *args: object) -> None:  # type: ignore[override]
        # Suppress per-request noise; keep errors.
        if args and str(args[1]) not in ("200", "201", "304"):
            super().log_message(fmt, *args)


def serve(workspace: Path, port: int = 5173, open_browser: bool = True, allow_writes: bool = False) -> None:
    """Start the LLM Wiki HTTP server on localhost:port."""
    if not workspace.exists():
        raise FileNotFoundError(f"Workspace not found: {workspace}")

    _Handler.workspace    = workspace
    _Handler.allow_writes = allow_writes

    server = _ThreadedHTTPServer(("127.0.0.1", port), _Handler)
    url = f"http://localhost:{port}"
    print(f"LLM Wiki  →  {url}")
    print(f"Workspace →  {workspace}")
    if allow_writes:
        print("Write mode  →  enabled (--allow-writes)")
    print("Press Ctrl+C to stop.\n")

    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
