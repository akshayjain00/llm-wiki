/* global React */
// LLM Wiki — live data loader
// Fetches workspace data from /api/data and wires up window.WikiData with
// the same shape the rest of the frontend expects.  app.jsx defers its
// ReactDOM.render call until this promise resolves.

window.WikiDataPromise = fetch('/api/data')
  .then(function(r) {
    if (!r.ok) throw new Error('API error ' + r.status);
    return r.json();
  })
  .then(function(raw) {
    var PAGES     = raw.PAGES     || [];
    var ENTITIES  = raw.ENTITIES  || [];
    var EDGES     = raw.EDGES     || [];
    var PROPOSALS = raw.PROPOSALS || [];

    window.WikiData = {
      PROJECTS:  raw.PROJECTS  || [],
      PEOPLE:    raw.PEOPLE    || [],
      CONCEPTS:  raw.CONCEPTS  || [],
      PAGES:     PAGES,
      REPORTS:   PAGES.filter(function(p) { return p.kind === 'report'; }),
      ENTITIES:  ENTITIES,
      EDGES:     EDGES,
      PROPOSALS: PROPOSALS,
      ACTIVITY:  raw.ACTIVITY  || [],
      HEALTH:    raw.HEALTH    || [],

      backlinksFor: function(targetId, edgeTypes) {
        return EDGES
          .filter(function(e) {
            return e.tgt === targetId && (!edgeTypes || edgeTypes.includes(e.type));
          })
          .map(function(e) {
            var srcPage = PAGES.find(function(p) { return p.id === e.src; });
            return {
              source_node_id: e.src,
              source_title:   srcPage ? srcPage.title : e.src,
              source_path:    srcPage ? srcPage.path  : null,
              edge_type:      e.type,
              evidence:       e.evidence || '',
              line:           e.line,
            };
          });
      },

      outboundFor: function(sourceId) {
        var allNodes = ENTITIES.concat(PAGES);
        return EDGES
          .filter(function(e) { return e.src === sourceId; })
          .map(function(e) {
            var tgtEnt = allNodes.find(function(n) { return n.id === e.tgt; });
            return Object.assign({}, e, {
              target_title: tgtEnt ? (tgtEnt.name || tgtEnt.title) : e.tgt,
            });
          });
      },

      byId: function(id) {
        return ENTITIES.find(function(e) { return e.id === id; })
            || PAGES.find(function(p) { return p.id === id; });
      },
    };
  });
