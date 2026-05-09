/* global React */
// SVG icon set — restrained, 16px line icons, no emoji.
// Each renders as a 16×16 svg with stroke-currentColor so it inherits color.

const __ICON_PATHS = {
  graph: 'M5 11a2 2 0 1 1 0-4 2 2 0 0 1 0 4Zm6-4a2 2 0 1 1 0-4 2 2 0 0 1 0 4Zm0 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4ZM6.4 6.7l3.2-1.8M6.4 9.3l3.2 1.8',
  search: 'M11 11 14 14 M11 7.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0Z',
  page:   'M4 2h6l3 3v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z M9 2v4h4',
  pages:  'M5 3h6l3 3v8H5z M3 5v9a1 1 0 0 0 1 1h7',
  entity: 'M8 4.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4Z M3.5 13c0-2.2 2-3.5 4.5-3.5S12.5 10.8 12.5 13',
  entities: 'M5 6a1.6 1.6 0 1 1 0-3 1.6 1.6 0 0 1 0 3Zm6 0a1.6 1.6 0 1 1 0-3 1.6 1.6 0 0 1 0 3ZM3 12c0-1.7 1-2.5 2-2.5S7 10.3 7 12 M9 12c0-1.7 1-2.5 2-2.5s2 .8 2 2.5',
  link:   'M7 9.5 5.5 11a2.5 2.5 0 0 1-3.5-3.5l2-2a2.5 2.5 0 0 1 3.5 0 M9 6.5 10.5 5a2.5 2.5 0 0 1 3.5 3.5l-2 2a2.5 2.5 0 0 1-3.5 0',
  proposal:'M3 4l5 7 5-7 M8 11v3',
  health: 'M2 8h3l1.5-4 3 8L11 6.5l1 1.5h2',
  reports:'M3 3h10v10H3z M5 6h6 M5 8.5h6 M5 11h4',
  decision:'M8 2v12 M3 8h10',
  overview:'M3 3h4v5H3z M9 3h4v3H9z M9 8h4v5H9z M3 10h4v3H3z',
  arrow:  'M5 8h6 M9 5l3 3-3 3',
  arrowR: 'M3 8h8 M9 5l3 3-3 3',
  arrowD: 'M8 3v8 M5 8l3 3 3-3',
  cmd:    'M5 5a1.5 1.5 0 1 1 0 3v0a1.5 1.5 0 1 1 0-3Zm0 0h6a1.5 1.5 0 1 1 0 3H5z M5 8h6 M11 8a1.5 1.5 0 1 1 0 3v0a1.5 1.5 0 1 1 0-3Z',
  filter: 'M2 3h12 L9 9v4l-2 1V9z',
  layers: 'M8 2 14 5 8 8 2 5z M2 8l6 3 6-3 M2 11l6 3 6-3',
  external:'M9 3h4v4 M13 3 7 9 M11 9v4H3V5h4',
  copy:   'M5 5h7v8H5z M3 3h7v2 M5 5v8h-2V5z',
  open:   'M3 3h4 M3 3v4 M13 13h-4 M13 13v-4 M3 3l4 4 M13 13l-4-4',
  hash:   'M6 3v10 M10 3v10 M3 6h10 M3 10h10',
  star:   'M8 2.5 9.6 6.2 13.5 6.6 10.6 9.2 11.5 13 8 11 4.5 13 5.4 9.2 2.5 6.6 6.4 6.2z',
  clock:  'M8 4v4l2.5 2.5 M14 8a6 6 0 1 1-12 0 6 6 0 0 1 12 0Z',
  bolt:   'M9 2 4 9h4l-1 5 5-7H8z',
  check:  'M3 8.5 6.5 12 13 4',
  x:      'M4 4l8 8 M12 4l-8 8',
  caretD: 'M4 6l4 4 4-4',
  caretR: 'M6 4l4 4-4 4',
  refresh:'M3 8a5 5 0 0 1 8.5-3.5 M13 8a5 5 0 0 1-8.5 3.5 M11 4v3h-3 M5 12V9h3',
  enter:  'M3 8h9 M9 5l3 3-3 3 M12 3v5',
  esc:    'M5 5h6v6H5z M5 5l6 6',
  dots:   'M4 8h.01 M8 8h.01 M12 8h.01',
  nodemcp:'M2 5h12 v6 H2z M5 5V3 M11 5V3 M5 11v2 M11 11v2',
  prop:   'M2 8h6 M8 5l3 3-3 3',
  tableico:'M2 4h12v8H2z M2 7h12 M6 4v8',
  graphList:'M3 4h10 M3 8h10 M3 12h10',
  cmdkey: 'M5 5a1.5 1.5 0 1 1 0 3v0a1.5 1.5 0 1 1 0-3Zm0 0h6a1.5 1.5 0 1 1 0 3H5z',
  plus:   'M8 3v10 M3 8h10',
  info:   'M8 7v5 M8 5.5v.5',
};

function Icon({ name, size = 14 }) {
  const d = __ICON_PATHS[name];
  if (!d) return null;
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 16 16"
         fill="none" stroke="currentColor" strokeWidth="1.4"
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {d.split(' M').map((seg, i) => (
        <path key={i} d={(i === 0 ? '' : 'M') + seg} />
      ))}
    </svg>
  );
}

window.Icon = Icon;
