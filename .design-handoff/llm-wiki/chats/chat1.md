# Team Memory Wiki

_Started 2026-05-09 14:15 UTC_

---

## User

The goal is to build an LLM-maintained team memory workspace that compiles understanding from those artifacts into a durable, inspectable wiki rather than re-discovering context from raw files on every question.
Those roots include a mix of project repos, docs, specs, notes, screenshots, exports, and operational artifacts. The current state makes it hard to answer a simple project-orientation question quickly and reliably:

- What is this project?
- Who owns it?
- What is its current status?
- What should happen next?
Primary goal
Build a Karpathy-aligned layered LLM wiki at:
`/Users/akshay.jain/Desktop/AI_V2/team_memory_wiki`
UI must:

- read from `state/index.db` and markdown pages
- avoid markdown mutation
- show graph summary, search, pages, entities, backlinks, and proposed links
- expose graph visualization plus accessible list/table fallback
- bind to localhost by default

## Assistant

_[tool: read_file]_

_[tool: list_files]_

_[tool: local_ls]_

_[tool: view_image]_

_[tool: list_files]_

_[tool: list_files]_

_[tool: questions_v2]_

## User

Questions answered:
- fidelity: Decide for me
- scope: Overview (/), Entities list + Entity detail, Decide for me — wire them all
- graph_treatment: Decide for me
- aesthetic: Show me 2–3 variants as Tweaks
- density: Roomy — Linear/Mem-style breathing room
- theme: Decide for me
- command_palette: Decide for me
- data_seed: Generate a richer fictional team-memory workspace (12+ projects, 40+ entities, 100+ pages)
- tweaks: Graph layout (radial / force / hierarchical), Density (roomy/dense), Theme (light/dark), Accent color (blue / green / monochrome), Decide for me
- accessibility_emphasis: Decide for me
- anything_else: inspired from https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2

 Most Relevant References for inspiration

  - Obsidian Graph View (https://obsidian.md/help/plugins/graph): best reference for full/local graph, filters, node sizing, link thickness, and graph navigation.
  - Dendron Backlinks Panel (https://wiki.dendron.so/notes/yxkn87ohgomk0tgs12dppur/): strongest pattern for explicit backlinks plus “candidate backlinks,” which maps directly to our proposed-link queue.
  - Dendron Graph View (https://wiki.dendron.so/notes/587e6d62-3c5b-49b0-aedc-02f62f0448e6/): useful for local vs full graph, depth filters, edge toggles, and graph metadata.
  - Mem Search (https://help.mem.ai/features/search): good model for fast typeahead, full search results, and “describe what you remember” search.
  - InfraNodus (https://infranodus.com/): useful inspiration for graph gaps, clusters, and analysis-first graph UX.
  - Linkurious Knowledge Graph (https://linkurious.com/knowledge-graphs-solution/): good reminder that graph tools fail when they are not searchable, filterable, and explainable.

## Assistant

_[tool: update_todos]_

_[tool: copy_starter_component]_

_[tool: snip]_

_[tool: read_file]_

_[tool: snip]_

_[tool: write_file]_

Now let me build this. I'll start with the shell and styles so I can preview, then layer in data and views.

_[tool: snip]_

Now data and icons:

_[tool: write_file]_

_[tool: write_file]_

_[tool: snip]_

_[tool: write_file]_

_[tool: snip]_

_[tool: write_file]_

_[tool: snip]_

_[tool: write_file]_

_[tool: list_files]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: snip]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: update_todos]_

_[tool: write_file]_

## Assistant

_[tool: write_file]_

_[tool: write_file]_

_[tool: snip]_

_[tool: update_todos]_

_[tool: done]_

_[tool: update_todos]_

_[tool: fork_verifier_agent]_

The LLM Wiki prototype is live at **LLM Wiki.html** — a Karpathy-style local read-only graph browser over `~/AI_V2/team_memory_wiki`.

**What's there**
- **Overview** — workspace tiles, project list, recent activity, top entities, high-confidence proposals
- **Pages** — searchable/filterable page index + markdown preview with proposed-link highlights
- **Entities** — projects/people/concepts list with detail view (backlinks, co-mentioned, owned pages)
- **Proposed Links** — Dendron-style candidate-link queue with confidence + rationale
- **Graph** — local neighborhood (force / radial / hierarchical) with paired adjacency-list fallback
- **Reports / Health** — phase reports + graph-rebuild diagnostics
- **Command palette** (⌘K or `/`) and `g o/p/e/l/g/h/r` keyboard nav

**Tweaks**
- Theme (light / dark), Accent (blue / green / mono), Density (roomy / dense)
- Aesthetic direction (editorial / terminal / paper)
- Graph layout (force / radial / hierarchical)
- Right context panel toggle

Mock data: 14 projects, 40+ entities, 100+ pages, 17 proposals — all read from in-memory mock structures shaped like `state/index.db`.

## User

Verifier agent check completed

## Assistant

_[tool: grep]_

_[tool: snip]_

_[tool: read_file]_

_[tool: str_replace_edit]_

_[tool: snip]_

_[tool: done]_

_[tool: fork_verifier_agent]_

_[tool: snip]_

Fixed the layout bug — the topbar is now nested inside the shell grid so the main content row gets the rest of the viewport height. Verifier re-running in the background.

## User

within thw gaprh section from left hand panel, force radial and hamburger menu are currently not working also whats the purpose of adjacency list, also its blocking current gaph view even in full screen view
please evalaute and fix

## Assistant

_[tool: read_file]_

_[tool: grep]_

_[tool: snip]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

I'll fix three things: wire the layout buttons, make the adjacency list collapsible (it's an a11y fallback that shouldn't always block the canvas), and add a tooltip explaining its purpose.

_[tool: str_replace_edit]_

_[tool: snip]_

_[tool: done]_

Fixed three things in the Graph view:

1. **Layout buttons now work** — force / radial / hierarchy are wired to the layout tweak, so clicking them reflows the graph (and stays in sync with the Tweaks panel).
2. **Adjacency list is now opt-in** — collapsed by default with a toolbar toggle (`adjacency list`). It no longer covers the canvas; full-screen graph is unobstructed.
3. **Purpose is documented** — hover the toolbar button for a tooltip, and the panel itself explains: it's the accessible text fallback (every visible edge as source → target), useful for screen readers, keyboard navigation, or scanning relationships as plain text.

