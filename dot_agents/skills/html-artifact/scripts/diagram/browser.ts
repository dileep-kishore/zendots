import { layoutGraph, type Graph, type Opts } from './layout';

declare global { interface Window { renderDiagram: (g: Graph, o: Opts) => Promise<{ svg: string; W: number; H: number }> } }

// Measured with the template's own faces, served by diagram-export.ts under these names.
const MEASURE = {
  title: '600 15px "Diagram Display"', titleMono: '500 14px "Diagram Mono"', detail: '400 12.5px "Diagram Mono"',
  edge: '400 12px "Diagram Mono"', group: '500 11px "Diagram Mono"', legend: '400 12px "Diagram Mono"',
};
// Drawn with the page's font stacks, so the SVG follows whatever the page resolved.
const DRAW = {
  title: '600 15px var(--font-display)', titleMono: '500 14px var(--font-mono)', detail: '400 12.5px var(--font-mono)',
  edge: '400 12px var(--font-mono)', group: '500 11px var(--font-mono)', legend: '400 12px var(--font-mono)',
};
const LINE = { title: 19, titleMono: 18, detail: 16, edge: 15, group: 14, legend: 15 };
// Fallback faces run wider than SN Pro and iA Writer; the slack keeps text inside its box.
const SLACK = 1.06;
const SOFT = new Set(['blue', 'green', 'teal', 'peach', 'red']);
const stroke = (t?: string) => t && t !== 'ink' ? `var(--${t})` : 'var(--ink-3)';
const tint = (t?: string) => t === 'accent' ? 'var(--accent-soft)' : t && SOFT.has(t) ? `var(--${t}-soft)` : 'var(--surface-2)';
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

window.renderDiagram = async (g, o) => {
  await Promise.all(Object.values(MEASURE).map(f => document.fonts.load(f, 'Ag')));
  for (const f of ['15px "Diagram Display"', '12px "Diagram Mono"']) if (!document.fonts.check(f)) throw new Error(`Measuring font did not load: ${f}`);
  const ctx = document.createElement('canvas').getContext('2d')!;
  const width = (text: string, font: string, spacing = 0) => { ctx.font = font; return ctx.measureText(text).width * SLACK + spacing * text.length; };
  const m = (text: string, role: keyof typeof LINE) => ({ w: width(text, MEASURE[role], role === 'group' ? 0.9 : 0), h: LINE[role] });
  const L = await layoutGraph(g, { ...o, padY: 12 }, m as any);
  const { pos, sizes, groupBoxes, edgePaths } = L;
  const pad = 16;
  const ox = pad - L.bounds.x0, oy = pad - L.bounds.y0;
  // Wide enough for the widest single legend entry, which cannot wrap.
  const legendW = Math.max(0, ...(g.legend || []).map(([text]) => 25 + width(text, MEASURE.legend)));
  const W = Math.ceil(Math.max(L.bounds.x1 - L.bounds.x0, legendW) + 2 * pad);
  // Legend entries wrap onto further rows rather than running past a narrow drawing's right edge.
  const legendRows: { text: string; t: string; x: number }[][] = [];
  for (const [text, t] of g.legend || []) {
    const w = 25 + width(text, MEASURE.legend);
    const row = legendRows[legendRows.length - 1];
    const end = row?.length ? row[row.length - 1].x + 25 + width(row[row.length - 1].text, MEASURE.legend) + 22 : pad;
    if (!row || (row.length && end + w > W - pad)) legendRows.push([{ text, t, x: pad }]);
    else row.push({ text, t, x: end });
  }
  const legendH = legendRows.length ? 18 + legendRows.length * 22 : 0;
  const H = Math.ceil(L.bounds.y1 - L.bounds.y0 + 2 * pad + legendH);
  const X = (x: number) => +(x + ox).toFixed(1), Y = (y: number) => +(y + oy).toFixed(1);
  const id = g.id;
  const out: string[] = [];
  // Narrow screens scroll the wrapper instead of shrinking labels below reading size.
  out.push(`<svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="${id}-t ${id}-d" style="width:100%;height:auto;max-width:${W}px;min-width:${Math.min(W, 600)}px">`);
  out.push(`<title id="${id}-t">${esc(g.title || g.id)}</title><desc id="${id}-d">${esc(g.alt)}</desc>`);
  out.push(`<defs><marker id="${id}-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" style="fill:var(--ink-3)"/></marker></defs>`);
  for (const grp of g.groups || []) {
    const b = groupBoxes.get(grp.id)!;
    out.push(`<rect x="${X(b.x)}" y="${Y(b.y)}" width="${b.w}" height="${b.h}" rx="10" style="fill:${tint(grp.tone)};${grp.tone ? '' : 'fill-opacity:.55;'}stroke:${grp.tone ? stroke(grp.tone) : 'var(--line-strong)'};stroke-opacity:.6;stroke-dasharray:4 4"/>`);
  }
  // ELK coordinates carry sub-pixel noise; snap so collinear bends stay straight and corners stay square.
  const sgn = (v: number) => Math.abs(v) < 0.01 ? 0 : Math.sign(v);
  for (const ep of edgePaths) for (let i = 1; i < ep.pts.length; i++) {
    const [px, py] = ep.pts[i - 1], q = ep.pts[i];
    if (Math.abs(q[0] - px) < 3) q[0] = px;
    if (Math.abs(q[1] - py) < 3) q[1] = py;
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
    out.push(`<text x="${cx}" y="${(top + s.t.h - 5).toFixed(1)}" text-anchor="middle" style="font:${n.mono ? DRAW.titleMono : DRAW.title};fill:var(--ink)">${esc(n.title)}</text>`);
    if (s.d && n.detail) out.push(`<text x="${cx}" y="${(top + s.t.h + 2 + s.d.h - 4).toFixed(1)}" text-anchor="middle" style="font:${DRAW.detail};fill:var(--ink-3)">${esc(n.detail)}</text>`);
  }
  legendRows.forEach((row, r) => {
    const ly = H - legendH + 12 + r * 22;
    for (const { text, t, x: lx } of row) {
      const dashed = t === 'dashed';
      out.push(`<rect x="${lx.toFixed(1)}" y="${ly}" width="18" height="12" rx="3" style="fill:${t === 'accent' ? 'var(--accent-soft)' : 'var(--ground)'};stroke:${dashed ? 'var(--ink-3)' : stroke(t)};stroke-width:1.4${dashed ? ';stroke-dasharray:3 2' : ''}"/>`);
      out.push(`<text x="${(lx + 25).toFixed(1)}" y="${ly + 10.5}" style="font:${DRAW.legend};fill:var(--ink-3)">${esc(text)}</text>`);
    }
  });
  out.push('</svg>');
  return { svg: out.join('\n'), W, H };
};
