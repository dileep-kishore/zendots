import { layoutGraph, type Graph, type Opts } from './layout';
import { checkScene, type Violation } from './geometry';
import { KINDS } from './kinds';
import { placeNotes } from './notes';
import { bounds, esc, iconSvg, ICON_GAP, ICON_SIZE, itemSvg, legendRows, legendSvg, shift, stroke, tint, type Role, type SItem } from './scene';

declare global { interface Window { renderDiagram: (g: Graph, o: Opts) => Promise<{ svg: string; W: number; H: number; violations: Violation[]; strict: boolean; items: SItem[] }> } }

// Measured with the template's own faces, served by diagram-export.ts under these names.
const MEASURE = {
  title: '600 15px "Diagram Display"', titleMono: '500 14px "Diagram Mono"', detail: '400 12.5px "Diagram Mono"',
  edge: '400 12px "Diagram Mono"', group: '500 11px "Diagram Mono"', legend: '400 12px "Diagram Mono"',
  note: 'italic 400 13px "Diagram Note"',
};
// Drawn with the page's font stacks, so the SVG follows whatever the page resolved.
const DRAW = {
  title: '600 15px var(--font-display)', titleMono: '500 14px var(--font-mono)', detail: '400 12.5px var(--font-mono)',
  edge: '400 12px var(--font-mono)', group: '500 11px var(--font-mono)', legend: '400 12px var(--font-mono)',
};
const LINE = { title: 19, titleMono: 18, detail: 16, edge: 15, group: 14, legend: 15, note: 18 };
// Fallback faces run wider than SN Pro and iA Writer; the slack keeps text inside its box.
const SLACK = 1.06;

// The graph kind keeps its original grey marker; newer kinds colour each head like its line where context-stroke works.
function markers(id: string, open: boolean, matchStroke = false) {
  const fill = matchStroke ? 'fill:var(--ink-3);fill:context-stroke' : 'fill:var(--ink-3)';
  const arrow = `<marker id="${id}-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" style="${fill}"/></marker>`;
  const hollow = `<marker id="${id}-open" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9" style="fill:none;stroke:var(--ink-3);stroke:context-stroke;stroke-width:1.4"/></marker>`;
  return `<defs>${arrow}${open ? hollow : ''}</defs>`;
}

window.renderDiagram = async (g, o) => {
  const fonts = Object.entries(MEASURE).filter(([role]) => role !== 'note' || (g.notes?.length ?? 0) > 0).map(([, f]) => f);
  await Promise.all(fonts.map(f => document.fonts.load(f, 'Ag')));
  const required = ['15px "Diagram Display"', '12px "Diagram Mono"', ...(g.notes?.length ? ['italic 13px "Diagram Note"'] : [])];
  for (const f of required) if (!document.fonts.check(f)) throw new Error(`Measuring font did not load: ${f}`);
  const ctx = document.createElement('canvas').getContext('2d')!;
  const width = (text: string, font: string, spacing = 0) => { ctx.font = font; return ctx.measureText(text).width * SLACK + spacing * text.length; };
  const m = (text: string, role: Role) => ({ w: width(text, MEASURE[role], role === 'group' ? 0.9 : 0), h: LINE[role] });
  const id = g.id;
  const pad = 16;
  const legendW = Math.max(0, ...(g.legend || []).map(([text]) => 25 + width(text, MEASURE.legend)));
  const header = (W: number, H: number) => [
    `<svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="${id}-t ${id}-d" style="width:100%;height:auto;max-width:${W}px;min-width:${Math.min(W, 600)}px">`,
    `<title id="${id}-t">${esc(g.title || g.id)}</title><desc id="${id}-d">${esc(g.alt)}</desc>`,
  ];

  if (g.kind && g.kind !== 'graph') {
    const items: SItem[] = KINDS[g.kind].layout(g, m);
    if (g.notes?.length) placeNotes(items, g.notes, m, bounds(items));
    const b = bounds(items);
    shift(items, pad - b.x0, pad - b.y0);
    const W = Math.ceil(Math.max(b.x1 - b.x0, legendW) + 2 * pad);
    const rows = legendRows(g.legend || [], W, pad, t => width(t, MEASURE.legend));
    const legendH = rows.length ? 18 + rows.length * 22 : 0;
    const H = Math.ceil(b.y1 - b.y0 + 2 * pad + legendH);
    const violations = checkScene({ W, H, items });
    const open = items.some(it => it.t === 'path' && it.marker === 'open');
    const out = [...header(W, H), markers(id, open, true), ...items.map(it => itemSvg(it, id)), ...legendSvg(rows, H - legendH, DRAW.legend), '</svg>'];
    return { svg: out.join('\n'), W, H, violations, strict: true, items };
  }

  // The graph kind below keeps its original drawing code, so specs without notes or icons render byte-for-byte as before.
  const L = await layoutGraph(g, { ...o, padY: 12 }, m as any);
  const { pos, sizes, groupBoxes, edgePaths } = L;
  let ox = pad - L.bounds.x0, oy = pad - L.bounds.y0;
  const X = (x: number) => +(x + ox).toFixed(1), Y = (y: number) => +(y + oy).toFixed(1);
  const contentW = L.bounds.x1 - L.bounds.x0, contentH = L.bounds.y1 - L.bounds.y0;
  // ELK coordinates carry sub-pixel noise; snap so collinear bends stay straight and corners stay square.
  const sgn = (v: number) => Math.abs(v) < 0.01 ? 0 : Math.sign(v);
  for (const ep of edgePaths) for (let i = 1; i < ep.pts.length; i++) {
    const [px, py] = ep.pts[i - 1], q = ep.pts[i];
    if (Math.abs(q[0] - px) < 3) q[0] = px;
    if (Math.abs(q[1] - py) < 3) q[1] = py;
  }

  // The same drawing as plain geometry, for the self-check and for placing notes.
  const geom: SItem[] = [];
  const tbox = (x: number, y: number, s: string, role: Role, anchor: 'start' | 'middle', owner?: string, backed?: boolean) =>
    geom.push({ t: 'text', x, y, text: s, role, anchor, style: '', ...m(s, role), owner, backed });
  for (const grp of g.groups || []) {
    const b = groupBoxes.get(grp.id)!;
    geom.push({ t: 'rect', x: X(b.x), y: Y(b.y), w: b.w, h: b.h, role: 'zone', style: '', id: grp.id });
    tbox(X(b.x) + 14, Y(b.y) + 20, grp.label, 'group', 'start', grp.id, true);
  }
  edgePaths.forEach(({ e, pts, label }, i) => {
    geom.push({ t: 'path', pts: pts.map(([x, y]) => [X(x), Y(y)]), role: 'connector', style: '', owner: `edge:${i}` });
    if (label && e.label) tbox(X(label.x), Y(label.y) + 11, e.label, 'edge', 'start', `edge:${i}`);
  });
  for (const n of g.nodes) {
    const b = pos.get(n.id)!, s = sizes.get(n.id)!, x = X(b.x), y = Y(b.y);
    geom.push({ t: 'rect', x, y, w: b.w, h: b.h, role: 'box', style: '', id: n.id });
    const contentH = s.t.h + (s.d ? 2 + s.d.h : 0), top = y + (b.h - contentH) / 2;
    tbox(x + b.w / 2, top + s.t.h - 5, n.title, n.mono ? 'titleMono' : 'title', 'middle', n.id);
    if (s.d && n.detail) tbox(x + b.w / 2, top + s.t.h + 2 + s.d.h - 4, n.detail, 'detail', 'middle', n.id);
  }
  const notesAt = geom.length;
  let left = 0, right = 0, topGrow = 0, bottom = 0;
  if (g.notes?.length) {
    placeNotes(geom, g.notes, m, { x0: pad, y0: pad, x1: pad + contentW, y1: pad + contentH });
    const b = bounds(geom);
    left = Math.max(0, Math.ceil(pad - b.x0)); topGrow = Math.max(0, Math.ceil(pad - b.y0));
    right = Math.max(0, Math.ceil(b.x1 + pad - (contentW + 2 * pad))); bottom = Math.max(0, Math.ceil(b.y1 + pad - (contentH + 2 * pad)));
    if (left || topGrow) { shift(geom, left, topGrow); ox += left; oy += topGrow; }
  }

  // Wide enough for the widest single legend entry, which cannot wrap.
  const W = Math.ceil(Math.max(contentW + left + right, legendW) + 2 * pad);
  // Legend entries wrap onto further rows rather than running past a narrow drawing's right edge.
  const legendRowsOut: { text: string; t: string; x: number }[][] = [];
  for (const [text, t] of g.legend || []) {
    const w = 25 + width(text, MEASURE.legend);
    const row = legendRowsOut[legendRowsOut.length - 1];
    const end = row?.length ? row[row.length - 1].x + 25 + width(row[row.length - 1].text, MEASURE.legend) + 22 : pad;
    if (!row || (row.length && end + w > W - pad)) legendRowsOut.push([{ text, t, x: pad }]);
    else row.push({ text, t, x: end });
  }
  const legendH = legendRowsOut.length ? 18 + legendRowsOut.length * 22 : 0;
  const H = Math.ceil(contentH + topGrow + bottom + 2 * pad + legendH);
  const out: string[] = [];
  // Narrow screens scroll the wrapper instead of shrinking labels below reading size.
  out.push(...header(W, H));
  out.push(markers(id, false));
  for (const grp of g.groups || []) {
    const b = groupBoxes.get(grp.id)!;
    out.push(`<rect x="${X(b.x)}" y="${Y(b.y)}" width="${b.w}" height="${b.h}" rx="10" style="fill:${tint(grp.tone)};${grp.tone ? '' : 'fill-opacity:.55;'}stroke:${grp.tone ? stroke(grp.tone) : 'var(--line-strong)'};stroke-opacity:.6;stroke-dasharray:4 4"/>`);
  }
  for (const { e, pts } of edgePaths) {
    let d = `M${X(pts[0][0])},${Y(pts[0][1])}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const [px, py] = pts[i - 1], [cx, cy] = pts[i], [nx, ny] = pts[i + 1];
      const r = Math.min(6, Math.hypot(cx - px, cy - py) / 2, Math.hypot(nx - cx, ny - cy) / 2);
      const ax = cx - sgn(cx - px) * r, ay = cy - sgn(cy - py) * r, bx = cx + sgn(nx - cx) * r, by = cy + sgn(ny - cy) * r;
      d += ` L${X(ax)},${Y(ay)} Q${X(cx)},${Y(cy)} ${X(bx)},${Y(by)}`;
    }
    const [ex, ey] = pts[pts.length - 1];
    d += ` L${X(ex)},${Y(ey)}`;
    out.push(`<path d="${d}" marker-end="url(#${id}-arrow)" style="fill:none;stroke:var(--ink-3);stroke-width:1.4${e.style === 'dashed' ? ';stroke-dasharray:5 4' : ''}"/>`);
  }
  for (const { e, label } of edgePaths) {
    if (!label || !e.label) continue;
    out.push(`<text x="${X(label.x)}" y="${Y(label.y) + 11}" style="font:${DRAW.edge};fill:var(--ink-3)">${esc(e.label)}</text>`);
  }
  for (const grp of g.groups || []) {
    const b = groupBoxes.get(grp.id)!, w = width(grp.label, MEASURE.group, 0.9);
    // Canvas colour under the group's own tint, so edges pass behind the label without a visible patch.
    out.push(`<rect x="${X(b.x) + 8}" y="${Y(b.y) + 7}" width="${(w + 12).toFixed(1)}" height="18" style="fill:var(--surface)"/>`);
    out.push(`<rect x="${X(b.x) + 8}" y="${Y(b.y) + 7}" width="${(w + 12).toFixed(1)}" height="18" style="fill:${tint(grp.tone)};${grp.tone ? '' : 'fill-opacity:.55'}"/>`);
    out.push(`<text x="${X(b.x) + 14}" y="${Y(b.y) + 20}" style="font:${DRAW.group};letter-spacing:.08em;fill:${grp.tone ? stroke(grp.tone) : 'var(--ink-3)'}">${esc(grp.label)}</text>`);
  }
  for (const n of g.nodes) {
    const b = pos.get(n.id)!, s = sizes.get(n.id)!, x = X(b.x), y = Y(b.y);
    const focal = n.tone === 'accent', rx = n.kind === 'actor' ? b.h / 2 : 6;
    out.push(`<rect x="${x}" y="${y}" width="${b.w}" height="${b.h}" rx="${rx}" style="fill:var(--ground);stroke:${stroke(n.tone)};stroke-width:${focal ? 2 : 1.4}${n.style === 'dashed' ? ';stroke-dasharray:5 4' : ''}"/>`);
    if (focal) out.push(`<rect x="${x}" y="${y}" width="${b.w}" height="${b.h}" rx="${rx}" style="fill:var(--accent-soft)"/>`);
    const contentH = s.t.h + (s.d ? 2 + s.d.h : 0), top = y + (b.h - contentH) / 2, cx = x + b.w / 2;
    const ty = (top + s.t.h - 5).toFixed(1);
    if (n.icon) {
      const x0 = cx - (ICON_SIZE + ICON_GAP + s.t.w) / 2;
      out.push(iconSvg(n.icon, x0, +ty - ICON_SIZE + 4));
      out.push(`<text x="${(x0 + ICON_SIZE + ICON_GAP).toFixed(1)}" y="${ty}" style="font:${n.mono ? DRAW.titleMono : DRAW.title};fill:var(--ink)">${esc(n.title)}</text>`);
    } else out.push(`<text x="${cx}" y="${ty}" text-anchor="middle" style="font:${n.mono ? DRAW.titleMono : DRAW.title};fill:var(--ink)">${esc(n.title)}</text>`);
    if (s.d && n.detail) out.push(`<text x="${cx}" y="${(top + s.t.h + 2 + s.d.h - 4).toFixed(1)}" text-anchor="middle" style="font:${DRAW.detail};fill:var(--ink-3)">${esc(n.detail)}</text>`);
  }
  for (const it of geom.slice(notesAt)) out.push(itemSvg(it, id));
  legendRowsOut.forEach((row, r) => {
    const ly = H - legendH + 12 + r * 22;
    for (const { text, t, x: lx } of row) {
      const dashed = t === 'dashed';
      out.push(`<rect x="${lx.toFixed(1)}" y="${ly}" width="18" height="12" rx="3" style="fill:${t === 'accent' ? 'var(--accent-soft)' : 'var(--ground)'};stroke:${dashed ? 'var(--ink-3)' : stroke(t)};stroke-width:1.4${dashed ? ';stroke-dasharray:3 2' : ''}"/>`);
      out.push(`<text x="${(lx + 25).toFixed(1)}" y="${ly + 10.5}" style="font:${DRAW.legend};fill:var(--ink-3)">${esc(text)}</text>`);
    }
  });
  out.push('</svg>');
  return { svg: out.join('\n'), W, H, violations: checkScene({ W, H, items: geom }), strict: false, items: geom };
};
