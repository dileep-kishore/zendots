import { LINE, stroke, text, textBox, type Measure, type Pt, type SItem, type SPath, type SText } from '../scene';
import { isText, TONES, type Kind } from './types';

type Box = { x: number; y: number; w: number; h: number };
interface Dot { id: string; title: string; tone?: string; cx: number; cy: number; r: number; q: number; Q: Box }

const BASE = 480, GROW = 60, MAX = 780, TIP = 16, EDGE = 8, GAP = 7, CH = 5;
const PITCH = LINE.detail + 2;
const EPS = 1.5;

const meets = (a: Box, b: Box) => a.x < b.x + b.w - EPS && b.x < a.x + a.w - EPS && a.y < b.y + b.h - EPS && b.y < a.y + a.h - EPS;
const inside = (a: Box, b: Box) => a.x >= b.x - EPS && a.y >= b.y - EPS && a.x + a.w <= b.x + b.w + EPS && a.y + a.h <= b.y + b.h + EPS;
const grow = (b: Box, d: number): Box => ({ x: b.x - d, y: b.y - d, w: b.w + 2 * d, h: b.h + 2 * d });
const dotBox = (d: Dot): Box => ({ x: d.cx - d.r, y: d.cy - d.r, w: 2 * d.r, h: 2 * d.r });

// Same rule as geometry.ts: an orthogonal segment through the inside of the box.
function hits(b: Box, [x0, y0]: Pt, [x1, y1]: Pt) {
  const ix = b.x + EPS, iy = b.y + EPS, ax = b.x + b.w - EPS, ay = b.y + b.h - EPS;
  if (Math.abs(y0 - y1) < 0.5) return y0 > iy && y0 < ay && Math.max(x0, x1) > ix && Math.min(x0, x1) < ax;
  if (Math.abs(x0 - x1) < 0.5) return x0 > ix && x0 < ax && Math.max(y0, y1) > iy && Math.min(y0, y1) < ay;
  return false;
}
const segs = (p: SPath) => p.pts.slice(1).map((b, i) => [p.pts[i], b] as [Pt, Pt]);
function crosses([a, b]: [Pt, Pt], [c, d]: [Pt, Pt]) {
  const ah = Math.abs(a[1] - b[1]) < 0.5, ch = Math.abs(c[1] - d[1]) < 0.5;
  const within = (v: number, p: number, q: number) => v > Math.min(p, q) + 0.5 && v < Math.max(p, q) - 0.5;
  if (ah && !ch) return within(c[0], a[0], b[0]) && within(a[1], c[1], d[1]);
  if (!ah && ch) return within(a[0], c[0], d[0]) && within(c[1], a[1], b[1]);
  // Collinear leaders that overlap read as one line.
  if (ah) return Math.abs(a[1] - c[1]) < 2 && Math.max(a[0], b[0]) > Math.min(c[0], d[0]) && Math.max(c[0], d[0]) > Math.min(a[0], b[0]);
  return Math.abs(a[0] - c[0]) < 2 && Math.max(a[1], b[1]) > Math.min(c[1], d[1]) && Math.max(c[1], d[1]) > Math.min(a[1], b[1]);
}

/** Slots at least `pitch` apart, each run of crowded labels centred on the mean of where its labels want to be. */
function spread(want: number[], pitch: number) {
  const groups: { start: number; n: number; sum: number }[] = [];
  want.forEach((w, i) => {
    let g = { start: i, n: 1, sum: w };
    while (groups.length) {
      const p = groups[groups.length - 1];
      if (p.sum / p.n + p.n * pitch <= g.sum / g.n) break;
      groups.pop();
      g = { start: p.start, n: p.n + g.n, sum: p.sum + g.sum - g.n * p.n * pitch };
    }
    groups.push(g);
  });
  const out: number[] = [];
  for (const g of groups) for (let k = 0; k < g.n; k++) out.push(g.sum / g.n + k * pitch);
  return out;
}

function check(g: any) {
  const errors: string[] = [], warns: string[] = [];
  const ax = g.axes;
  if (!ax || typeof ax !== 'object' || Array.isArray(ax)) errors.push('axes must be an object {"x": [low, high], "y": [low, high]} of single words');
  else for (const k of ['x', 'y']) {
    const p = ax[k];
    if (!Array.isArray(p) || p.length !== 2 || !p.every((w: unknown) => isText(w) && /^\S+$/.test(w.trim()))) errors.push(`axes.${k} must be two single words, [low, high]`);
  }
  if (g.quadrants !== undefined && !(Array.isArray(g.quadrants) && g.quadrants.length === 4 && g.quadrants.every(isText))) {
    errors.push('quadrants must be four short labels in reading order: top left, top right, bottom left, bottom right');
  }
  if (!Array.isArray(g.items) || !g.items.length) { errors.push('items must be a nonempty array'); return { errors, warns }; }
  const ids = new Set<string>(), at = new Map<string, string>();
  g.items.forEach((it: any, i: number) => {
    const name = isText(it?.id) ? it.id : `items[${i}]`;
    if (!isText(it?.id) || ids.has(it.id)) errors.push(`item id missing or duplicated: ${it?.id}`);
    else ids.add(it.id);
    if (!isText(it?.title)) errors.push(`item ${name} needs a title`);
    if (it?.tone !== undefined && !TONES.has(it.tone)) errors.push(`item ${name}: unknown tone ${it.tone}`);
    const bad = ['x', 'y'].map(k => {
      const v = it?.[k];
      if (typeof v !== 'number' || !Number.isFinite(v)) return `item ${name}: ${k} must be a number from 0 to 1`;
      if (v < 0 || v > 1) return `item ${name}: ${k} ${v} is outside 0 to 1`;
      if (v === 0.5) return `item ${name}: ${k} 0.5 sits on the axis, between two quadrants; move it to one side`;
      return '';
    }).filter(Boolean);
    errors.push(...bad);
    if (bad.length) return;
    const key = `${it.x},${it.y}`;
    if (at.has(key)) errors.push(`items ${at.get(key)} and ${name} sit at the same point (${it.x}, ${it.y}); separate them`);
    else at.set(key, name);
  });
  if (g.items.length > 12) warns.push(`${g.items.length} items; above about 12 a quadrant stops reading at a glance. Cluster related items or split the chart.`);
  const accents = g.items.filter((it: any) => it?.tone === 'accent').length;
  if (accents > 1) warns.push(`${accents} accent items; keep one, the item the reader must act on.`);
  return { errors, warns };
}

/** One attempt at plot size S; returns the scene, or the ids whose labels found no room. */
function attempt(g: any, m: Measure, S: number): { items?: SItem[]; fail: string[] } {
  const H = S / 2;
  const quads: Box[] = [
    { x: 0, y: 0, w: H - EDGE, h: H - EDGE }, { x: H + EDGE, y: 0, w: H - EDGE, h: H - EDGE },
    { x: 0, y: H + EDGE, w: H - EDGE, h: H - EDGE }, { x: H + EDGE, y: H + EDGE, w: H - EDGE, h: H - EDGE },
  ];
  const dots: Dot[] = g.items.map((it: any) => {
    const cx = it.x * S, cy = (1 - it.y) * S, q = (cy < H ? 0 : 2) + (cx < H ? 0 : 1);
    return { id: it.id, title: it.title, tone: it.tone, cx, cy, r: it.tone === 'accent' ? 6 : 5, q, Q: quads[q] };
  });
  const axisStyle = 'stroke:var(--ink-3);stroke-width:1.2';
  const axes: SPath[] = [
    { t: 'path', pts: [[0, H], [S + TIP, H]], role: 'axis', marker: 'arrow', r: 0, style: axisStyle },
    { t: 'path', pts: [[H, S], [H, -TIP]], role: 'axis', marker: 'arrow', r: 0, style: axisStyle },
  ];
  const word = (x: number, y: number, s: string, anchor: 'start' | 'middle' | 'end') => text(x, y, s.trim().toUpperCase(), 'group', m, { anchor }, 'var(--ink-2)');
  const fixed: SText[] = [
    word(-10, H + 4, g.axes.x[0], 'end'), word(S + TIP + 10, H + 4, g.axes.x[1], 'start'),
    word(H, -TIP - 10, g.axes.y[1], 'middle'), word(H, S + 19, g.axes.y[0], 'middle'),
  ];

  // Corner labels: the outer corner first, then the other corners of the quadrant, wherever no dot sits.
  if (Array.isArray(g.quadrants)) {
    for (let q = 0; q < 4; q++) {
      const Q = quads[q], right = q % 2 === 1, bottom = q >= 2;
      const s = String(g.quadrants[q]).trim().toUpperCase();
      const ox = right ? Q.x + Q.w : Q.x, ix = right ? Q.x : Q.x + Q.w;
      const oy = bottom ? Q.y + Q.h - 5 : Q.y + 11, iy = bottom ? Q.y + 11 : Q.y + Q.h - 5;
      const spots: [number, number, 'start' | 'end'][] = [[ox, oy, right ? 'end' : 'start'], [ix, oy, right ? 'start' : 'end'], [ox, iy, right ? 'end' : 'start'], [ix, iy, right ? 'start' : 'end']];
      const pick = spots.map(([x, y, a]) => text(x, y, s, 'group', m, { anchor: a }, 'var(--ink-3)'))
        .find(t => inside(textBox(t), Q) && !dots.some(d => meets(grow(textBox(t), 4), dotBox(d))));
      if (!pick) return { fail: [`quadrants[${q}]`] };
      fixed.push(pick);
    }
  }

  const labels = new Map<string, SText>(), leaders = new Map<string, SPath>();
  const byId = new Map(dots.map(d => [d.id, d]));
  const label = (d: Dot, x: number, c: number, anchor: 'start' | 'end') =>
    text(x, c + 4, d.title, 'detail', m, { anchor, owner: d.id }, d.tone === 'accent' ? 'var(--ink)' : 'var(--ink-2)');

  // Hard conflicts stop a placement; `taken` lists placed labels in the way, which a column may absorb.
  type Verdict = { hard: boolean; taken: string[]; soft: number };
  const judge = (newLabels: SText[], newLeaders: SPath[], skip: Set<string>): Verdict => {
    const v: Verdict = { hard: false, taken: [], soft: 0 };
    const placedLabels = [...labels.values()].filter(t => !skip.has(t.owner!));
    const placedLeaders = [...leaders.values()].filter(p => !skip.has(p.owner!));
    for (const t of newLabels) {
      const b = textBox(t), d = byId.get(t.owner!)!;
      if (!inside(b, d.Q) || fixed.some(f => meets(b, textBox(f))) || dots.some(o => o.id !== d.id && meets(b, dotBox(o)))) v.hard = true;
      if (placedLeaders.some(p => segs(p).some(([a, c]) => hits(b, a, c)))) v.hard = true;
      for (const o of placedLabels) if (meets(b, textBox(o))) v.taken.push(o.owner!);
    }
    for (const p of newLeaders) for (const [a, c] of segs(p)) {
      for (const t of [...fixed, ...newLabels]) if (t.owner !== p.owner && hits(textBox(t), a, c)) v.hard = true;
      for (const o of placedLabels) if (hits(textBox(o), a, c)) v.taken.push(o.owner!);
      for (const o of dots) if (o.id !== p.owner && hits(grow(dotBox(o), 1), a, c)) v.soft++;
      for (const o of [...placedLeaders, ...newLeaders]) if (o !== p && segs(o).some(s => crosses([a, c], s))) v.soft++;
    }
    return v;
  };

  // Right of the dot, else left; the accent item chooses first.
  const order = [...dots].sort((a, b) => Number(b.tone === 'accent') - Number(a.tone === 'accent'));
  const pending: Dot[] = [];
  for (const d of order) {
    const cands = [label(d, d.cx + d.r + GAP, d.cy, 'start'), label(d, d.cx - d.r - GAP, d.cy, 'end')];
    const ok = cands.find(t => { const v = judge([t], [], new Set()); return !v.hard && !v.taken.length; });
    if (ok) labels.set(d.id, ok); else pending.push(d);
  }

  // Clusters: crowded dots of one quadrant, linked when they sit within three lines of each other.
  const clusters: Dot[][] = [];
  for (const d of pending) {
    const near = clusters.filter(c => c[0].q === d.q && c.some(o => Math.hypot(o.cx - d.cx, o.cy - d.cy) <= 3 * PITCH));
    const merged = [d, ...near.flat()];
    for (const c of near) clusters.splice(clusters.indexOf(c), 1);
    clusters.push(merged);
  }

  type Mode = 'beside' | 'below' | 'above';
  type Plan = { labels: SText[]; leaders: SPath[] };
  const leader = (owner: string, pts: Pt[]): SPath => ({ t: 'path', pts, role: 'leader', owner, r: 3, style: 'stroke:var(--ink-3);stroke-width:0.8' });
  const far = (d: Dot, t: SText) => {
    const b = textBox(t);
    return Math.hypot(Math.max(b.x - d.cx, 0, d.cx - b.x - b.w), Math.max(b.y - d.cy, 0, d.cy - b.y - b.h)) - d.r > LINE.detail;
  };
  // beside: labels level with their dots, leaders run out sideways to their own lane.
  // below/above: labels stacked past the cluster in x order, leaders drop straight then turn, so none cross.
  const plan = (C: Dot[], side: 'L' | 'R', mode: Mode, k: number, jog: number): Plan | undefined => {
    const Q = C[0].Q, top = Q.y + 7, bottom = Q.y + Q.h - 9, sgn = side === 'L' ? -1 : 1;
    const edge = side === 'L' ? Math.min(...C.map(d => d.cx - d.r)) : Math.max(...C.map(d => d.cx + d.r));
    const ls: SText[] = [], ps: SPath[] = [];
    const anchor = side === 'L' ? 'end' : 'start';
    if (mode !== 'beside') {
      const dir = mode === 'below' ? 1 : -1, rMax = Math.max(...C.map(d => d.r));
      const lo = Math.max(...C.map(d => d.cy)), hi = Math.min(...C.map(d => d.cy));
      // A dot straight below (or above) another would sit on its leader; a jog steps that leader past it.
      const vx = new Map<string, number>();
      for (const d of C) {
        const block = jog ? C.find(o => o !== d && Math.abs(o.cx - d.cx) < o.r + 2 && (o.cy - d.cy) * dir > 0) : undefined;
        const v = block ? block.cx + jog * (block.r + 3) : d.cx;
        if (v < Q.x || v > Q.x + Q.w) return undefined;
        vx.set(d.id, v);
      }
      const outward = (a: Dot, b: Dot) => sgn * (vx.get(b.id)! - vx.get(a.id)!) || a.cy - b.cy;
      const sorted = [...C].sort(mode === 'below' ? outward : (a, b) => outward(b, a));
      const n = sorted.length, x = (side === 'L' ? Math.min(edge, ...vx.values()) : Math.max(edge, ...vx.values())) + sgn * GAP;
      const c0 = mode === 'below' ? lo + rMax + 11 + k * PITCH : hi - rMax - 13 - k * PITCH - (n - 1) * PITCH;
      if (c0 < top || c0 + (n - 1) * PITCH > bottom) return undefined;
      sorted.forEach((d, i) => {
        const c = c0 + i * PITCH, t = label(d, x, c, anchor), v = vx.get(d.id)!;
        ls.push(t);
        if (!far(d, t)) return;
        const head: Pt[] = v === d.cx ? [[v, d.cy + dir * (d.r + 2)]] : [[d.cx + Math.sign(v - d.cx) * (d.r + 2), d.cy], [v, d.cy]];
        ps.push(leader(d.id, [...head, [v, c], [x - sgn * 4, c]]));
      });
      return { labels: ls, leaders: ps };
    }
    const sorted = [...C].sort((a, b) => a.cy - b.cy || a.cx - b.cx);
    let cs = spread(sorted.map(d => d.cy + k * PITCH), PITCH);
    if (cs[cs.length - 1] - cs[0] > bottom - top) return undefined;
    if (cs[0] < top) cs = cs.map(c => c + top - cs[0]);
    if (cs[cs.length - 1] > bottom) cs = cs.map(c => c - (cs[cs.length - 1] - bottom));
    const up = sorted.filter((d, i) => cs[i] < d.cy - 0.5), down = sorted.filter((d, i) => cs[i] > d.cy + 0.5).reverse();
    const lanes = Math.max(up.length, down.length);
    const x = edge + sgn * (GAP + (lanes ? 6 + CH * lanes : 0));
    const rank = new Map<string, number>([...up.map((d, i) => [d.id, i] as const), ...down.map((d, i) => [d.id, i] as const)]);
    sorted.forEach((d, i) => {
      const t = label(d, x, cs[i], anchor);
      ls.push(t);
      if (!far(d, t)) return;
      const from: Pt = [d.cx + sgn * (d.r + 2), d.cy], to: Pt = [x - sgn * 4, cs[i]];
      const lane = edge + sgn * (6 + CH * (rank.get(d.id) ?? 0));
      ps.push(leader(d.id, Math.abs(cs[i] - d.cy) <= 0.5 ? [from, [to[0], d.cy]] : [from, [lane, d.cy], [lane, cs[i]], to]));
    });
    return { labels: ls, leaders: ps };
  };

  const tries: [Mode, number, number][] = [];
  for (let k = 0; k <= 10; k++) {
    if (k) tries.push(['beside', -k, 1], ['beside', k, 1]); else tries.push(['beside', 0, 1]);
    for (const mode of ['below', 'above'] as const) tries.push([mode, k, 0], [mode, k, -1], [mode, k, 1]);
  }
  for (const cluster of clusters) {
    let C = cluster, saved: { p: Plan; soft: number; labels: Map<string, SText>; leaders: Map<string, SPath> } | undefined;
    let chosen: Plan | undefined;
    for (let round = 0; round <= dots.length && !chosen; round++) {
      const ids = new Set(C.map(d => d.id));
      const Q = C[0].Q, minX = Math.min(...C.map(d => d.cx)), maxX = Math.max(...C.map(d => d.cx));
      const sides: ('L' | 'R')[] = minX - Q.x >= Q.x + Q.w - maxX ? ['L', 'R'] : ['R', 'L'];
      let best: { p: Plan; soft: number } | undefined;
      let absorb: string[] | undefined;
      search: for (const [mode, k, jog] of tries) for (const side of sides) {
        const p = plan(C, side, mode, k, jog);
        if (!p) continue;
        const v = judge(p.labels, p.leaders, ids);
        if (v.hard) continue;
        const taken = [...new Set(v.taken)].filter(id => byId.get(id)!.q === C[0].q);
        if (v.taken.length) { if (taken.length === new Set(v.taken).size && (!absorb || taken.length < absorb.length)) absorb = taken; continue; }
        if (!best || v.soft < best.soft) best = { p, soft: v.soft };
        if (v.soft === 0) break search;
      }
      // A leader through a dot or another leader may clear by pulling neighbours into the column; keep the better of the two.
      if (best && (best.soft === 0 || !absorb)) chosen = best.p;
      if (best && !chosen && (!saved || best.soft < saved.soft)) saved = { ...best, labels: new Map(labels), leaders: new Map(leaders) };
      if (saved && (!best || saved.soft <= best.soft) && (chosen || !absorb)) {
        labels.clear(); leaders.clear();
        for (const [k, v] of saved.labels) labels.set(k, v);
        for (const [k, v] of saved.leaders) leaders.set(k, v);
        chosen = saved.p;
      }
      if (!chosen && absorb) {
        for (const id of absorb) { labels.delete(id); leaders.delete(id); }
        C = [...C, ...absorb.map(id => byId.get(id)!)];
      }
    }
    if (!chosen) return { fail: C.map(d => d.id) };
    for (const t of chosen.labels) labels.set(t.owner!, t);
    for (const p of chosen.leaders) leaders.set(p.owner!, p);
  }

  const out: SItem[] = [...axes, ...fixed, ...leaders.values()];
  for (const d of dots) {
    const fill = d.tone === 'accent' ? 'var(--accent)' : d.tone ? stroke(d.tone) : 'var(--ink-2)';
    out.push({ t: 'dot', cx: d.cx, cy: d.cy, r: d.r, id: d.id, style: `fill:${fill};stroke:var(--ground);stroke-width:1.5` });
  }
  for (const d of dots) out.push(labels.get(d.id)!);
  return { items: out, fail: [] };
}

export const quadrant: Kind = {
  check,
  ids: (g: any) => (Array.isArray(g.items) ? g.items : []).map((it: any) => it?.id).filter(isText),
  layout(g: any, m: Measure) {
    let fail: string[] = [];
    for (let S = BASE; S <= MAX; S += GROW) {
      const r = attempt(g, m, S);
      if (r.items) return r.items;
      fail = r.fail;
    }
    throw new Error(`quadrant ${g.id}: no room for the labels of ${fail.join(', ')} even in a ${MAX}-unit plot; shorten those titles, spread the items, or drop some`);
  },
};
