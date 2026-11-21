import { ICONS } from './icons';

// A laid-out drawing in final SVG units. Kind layouts build one; geometry.ts checks it and render() draws it.
export type Pt = [number, number];
export type Role = 'title' | 'titleMono' | 'detail' | 'edge' | 'group' | 'legend' | 'note';
export type Measure = (text: string, role: Role) => { w: number; h: number };
export interface SRect { t: 'rect'; x: number; y: number; w: number; h: number; rx?: number; style: string; role: 'box' | 'zone' | 'backing' | 'band'; id?: string }
export interface SPath { t: 'path'; pts: Pt[]; style: string; role: 'connector' | 'lifeline' | 'frame' | 'leader' | 'axis' | 'divider'; marker?: 'arrow' | 'open'; start?: 'arrow'; r?: number; id?: string; owner?: string }
export interface SText { t: 'text'; x: number; y: number; text: string; role: Role; anchor?: 'start' | 'middle' | 'end'; style: string; w: number; h: number; owner?: string; backed?: boolean; id?: string }
export interface SDot { t: 'dot'; cx: number; cy: number; r: number; style: string; id?: string }
export interface SIcon { t: 'icon'; x: number; y: number; name: string; owner?: string }
export type SItem = SRect | SPath | SText | SDot | SIcon;
export interface Scene { W: number; H: number; items: SItem[] }

// Same faces and sizes as browser.ts draws graph diagrams with.
export const DRAW: Record<Role, string> = {
  title: '600 15px var(--font-display)', titleMono: '500 14px var(--font-mono)', detail: '400 12.5px var(--font-mono)',
  edge: '400 12px var(--font-mono)', group: '500 11px var(--font-mono)', legend: '400 12px var(--font-mono)',
  note: 'italic 400 13px var(--font-text)',
};
export const LINE: Record<Role, number> = { title: 19, titleMono: 18, detail: 16, edge: 15, group: 14, legend: 15, note: 18 };
export const ICON_SIZE = 18, ICON_GAP = 8;
const SOFT = new Set(['blue', 'green', 'teal', 'peach', 'red']);
export const stroke = (t?: string) => t && t !== 'ink' ? `var(--${t})` : 'var(--ink-3)';
export const tint = (t?: string) => t === 'accent' ? 'var(--accent-soft)' : t && SOFT.has(t) ? `var(--${t}-soft)` : 'var(--surface-2)';
export const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const f = (v: number) => +v.toFixed(1);
/** An error the spec's author can fix; export.ts reports these as a rejected layout and anything else as a crash. */
export const specError = (message: string) => new Error(`[spec] ${message}`);

/** The box a text item occupies: baseline y, measured width, line height. */
export function textBox(t: SText) {
  const x0 = t.anchor === 'middle' ? t.x - t.w / 2 : t.anchor === 'end' ? t.x - t.w : t.x;
  return { x: x0, y: t.y - t.h + 5, w: t.w, h: t.h };
}

export function text(x: number, y: number, s: string, role: Role, m: Measure, extra: Partial<SText> = {}, fill = 'var(--ink-3)'): SText {
  const { w, h } = m(s, role);
  const spacing = role === 'group' ? ';letter-spacing:.08em' : '';
  return { t: 'text', x, y, text: s, role, style: `font:${DRAW[role]}${spacing};fill:${fill}`, w, h, ...extra };
}

/** Box size for a titled node, sized from measured text like the graph kind, plus room for an icon. */
export function sizeNode(m: Measure, n: { title: string; detail?: string; mono?: boolean; icon?: string; kind?: string }, padY = 12, minW = 150) {
  const t = m(n.title, n.mono ? 'titleMono' : 'title');
  const d = n.detail ? m(n.detail, 'detail') : undefined;
  const padX = n.kind === 'actor' ? 30 : 22;
  const head = t.w + (n.icon ? ICON_SIZE + ICON_GAP : 0);
  const w = Math.max(minW, Math.ceil(Math.max(head, d?.w || 0) + 2 * padX));
  const h = Math.ceil(padY + t.h + (d ? 4 + d.h : 0) + padY);
  return { w, h, t, d };
}

/** Draws a node the way the graph kind does: canvas box, tone stroke, accent wash, centred title and detail. */
export function nodeBox(out: SItem[], m: Measure, b: { x: number; y: number; w: number; h: number }, n: { id: string; title: string; detail?: string; tone?: string; mono?: boolean; style?: string; kind?: string; icon?: string }) {
  const focal = n.tone === 'accent', rx = n.kind === 'actor' ? b.h / 2 : 6;
  out.push({ t: 'rect', ...b, rx, role: 'box', id: n.id, style: `fill:var(--ground);stroke:${stroke(n.tone)};stroke-width:${focal ? 2 : 1.4}${n.style === 'dashed' ? ';stroke-dasharray:5 4' : ''}` });
  if (focal) out.push({ t: 'rect', ...b, rx, role: 'backing', style: 'fill:var(--accent-soft)' });
  const role: Role = n.mono ? 'titleMono' : 'title';
  const tm = m(n.title, role), dm = n.detail ? m(n.detail, 'detail') : undefined;
  const contentH = tm.h + (dm ? 2 + dm.h : 0), top = b.y + (b.h - contentH) / 2, cx = b.x + b.w / 2;
  const ty = top + tm.h - 5;
  if (n.icon) {
    const x0 = cx - (ICON_SIZE + ICON_GAP + tm.w) / 2;
    out.push({ t: 'icon', x: x0, y: ty - ICON_SIZE + 4, name: n.icon, owner: n.id });
    out.push(text(x0 + ICON_SIZE + ICON_GAP, ty, n.title, role, m, { anchor: 'start', owner: n.id }, 'var(--ink)'));
  } else out.push(text(cx, ty, n.title, role, m, { anchor: 'middle', owner: n.id }, 'var(--ink)'));
  if (n.detail) out.push(text(cx, top + tm.h + 2 + dm!.h - 4, n.detail, 'detail', m, { anchor: 'middle', owner: n.id }));
}

/** SVG path data with rounded corners, the same corner rule the graph kind uses. */
export function pathD(pts: Pt[], radius = 6) {
  const sgn = (v: number) => Math.abs(v) < 0.01 ? 0 : Math.sign(v);
  let d = `M${f(pts[0][0])},${f(pts[0][1])}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const [px, py] = pts[i - 1], [cx, cy] = pts[i], [nx, ny] = pts[i + 1];
    const r = Math.min(radius, Math.hypot(cx - px, cy - py) / 2, Math.hypot(nx - cx, ny - cy) / 2);
    const ax = cx - sgn(cx - px) * r, ay = cy - sgn(cy - py) * r, bx = cx + sgn(nx - cx) * r, by = cy + sgn(ny - cy) * r;
    d += ` L${f(ax)},${f(ay)} Q${f(cx)},${f(cy)} ${f(bx)},${f(by)}`;
  }
  const [ex, ey] = pts[pts.length - 1];
  return d + ` L${f(ex)},${f(ey)}`;
}

export function iconSvg(name: string, x: number, y: number) {
  // 24-unit Tabler glyph at 0.75 scale: 18 units, stroke 1.5.
  return `<g transform="translate(${f(x)} ${f(y)}) scale(0.75)" style="fill:none;stroke:var(--ink-2);stroke-width:2;stroke-linecap:round;stroke-linejoin:round">${ICONS[name]}</g>`;
}

export function itemSvg(it: SItem, id: string): string {
  if (it.t === 'rect') return `<rect x="${f(it.x)}" y="${f(it.y)}" width="${f(it.w)}" height="${f(it.h)}"${it.rx ? ` rx="${f(it.rx)}"` : ''} style="${it.style}"/>`;
  if (it.t === 'dot') return `<circle cx="${f(it.cx)}" cy="${f(it.cy)}" r="${it.r}" style="${it.style}"/>`;
  if (it.t === 'icon') return iconSvg(it.name, it.x, it.y);
  if (it.t === 'text') return `<text x="${f(it.x)}" y="${f(it.y)}"${it.anchor && it.anchor !== 'start' ? ` text-anchor="${it.anchor}"` : ''} style="${it.style}">${esc(it.text)}</text>`;
  const d = it.r === 0 ? `M${it.pts.map(([x, y]) => `${f(x)},${f(y)}`).join(' L')}` : pathD(it.pts, it.r ?? 6);
  const mk = it.marker ? ` marker-end="url(#${id}-${it.marker})"` : '';
  const ms = it.start ? ` marker-start="url(#${id}-arrow)"` : '';
  return `<path d="${d}"${mk}${ms} style="fill:none;${it.style}"/>`;
}

/** Legend rows that wrap within the drawing's width, as the graph kind lays them out. */
export function legendRows(legend: [string, string][], W: number, pad: number, width: (s: string) => number) {
  const rows: { text: string; t: string; x: number }[][] = [];
  for (const [label, t] of legend) {
    const w = 25 + width(label);
    const row = rows[rows.length - 1];
    const end = row?.length ? row[row.length - 1].x + 25 + width(row[row.length - 1].text) + 22 : pad;
    if (!row || (row.length && end + w > W - pad)) rows.push([{ text: label, t, x: pad }]);
    else row.push({ text: label, t, x: end });
  }
  return rows;
}

export function legendSvg(rows: ReturnType<typeof legendRows>, top: number, draw: string) {
  const out: string[] = [];
  rows.forEach((row, r) => {
    const ly = top + 12 + r * 22;
    for (const { text: label, t, x: lx } of row) {
      const dashed = t === 'dashed';
      out.push(`<rect x="${lx.toFixed(1)}" y="${ly}" width="18" height="12" rx="3" style="fill:${t === 'accent' ? 'var(--accent-soft)' : 'var(--ground)'};stroke:${dashed ? 'var(--ink-3)' : stroke(t)};stroke-width:1.4${dashed ? ';stroke-dasharray:3 2' : ''}"/>`);
      out.push(`<text x="${(lx + 25).toFixed(1)}" y="${ly + 10.5}" style="font:${draw};fill:var(--ink-3)">${esc(label)}</text>`);
    }
  });
  return out;
}

export function bounds(items: SItem[]) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const add = (x: number, y: number, w = 0, h = 0) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x + w); y1 = Math.max(y1, y + h); };
  for (const it of items) {
    if (it.t === 'rect') add(it.x, it.y, it.w, it.h);
    else if (it.t === 'dot') add(it.cx - it.r, it.cy - it.r, 2 * it.r, 2 * it.r);
    else if (it.t === 'icon') add(it.x, it.y, ICON_SIZE, ICON_SIZE);
    else if (it.t === 'text') { const b = textBox(it); add(b.x, b.y, b.w, b.h); }
    else for (const [x, y] of it.pts) add(x, y);
  }
  return { x0, y0, x1, y1 };
}

export function shift(items: SItem[], dx: number, dy: number) {
  for (const it of items) {
    if (it.t === 'rect' || it.t === 'text' || it.t === 'icon') { it.x += dx; it.y += dy; }
    else if (it.t === 'dot') { it.cx += dx; it.cy += dy; }
    else it.pts = it.pts.map(([x, y]) => [x + dx, y + dy] as Pt);
  }
}
