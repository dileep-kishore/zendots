import { ICON_SIZE, LINE, nodeBox, sizeNode, text, textBox, type Measure, type Pt, type SItem, specError } from '../scene';
import { isText, TONES, type Kind } from './types';

interface Lane { id: string; label: string }
interface Step { id: string; lane: string; title: string; detail?: string; tone?: string; icon?: string; style?: string }
interface Edge { from: string; to: string; label?: string; style?: string; back?: boolean }
type Box = { x: number; y: number; w: number; h: number };
// An along-axis position: a box side, or a track inside the gap after column k (k = -1 is the leading gap).
interface Seg { k: number; c1: number; c2: number; track: number }
type ARef = { t: 'far' | 'near'; s: string } | { t: 'gap'; seg: Seg };
interface Way { a: ARef; c: number }

const BASE_PAD = 22, CORR0 = 9, CORR_STEP = 8, TRACK = 10, TRACK_EDGE = 14, LABEL_ZONE = 22;
const SUB_GAP = 14, CHANNEL0 = 24, GUTTER_PAD = 16, HEADER = 38, END = 16;

function check(g: any): { errors: string[]; warns: string[] } {
  const errors: string[] = [], warns: string[] = [];
  if (g.direction !== undefined && g.direction !== 'RIGHT' && g.direction !== 'DOWN') errors.push('direction must be RIGHT or DOWN for a swimlane');
  const lanes = new Set<string>();
  if (!Array.isArray(g.lanes) || !g.lanes.length) errors.push('lanes must be a nonempty array');
  else for (const l of g.lanes) {
    if (!isText(l?.id) || lanes.has(l.id)) errors.push(`lane id missing or duplicated: ${l?.id}`);
    else if (l.id.includes('|')) errors.push(`lane ${l.id}: ids may not contain "|"`);
    if (!isText(l?.label)) errors.push(`lane ${l?.id} needs a label`);
    lanes.add(l?.id);
  }
  const steps = new Set<string>();
  let accents = 0;
  if (!Array.isArray(g.steps) || !g.steps.length) errors.push('steps must be a nonempty array');
  else for (const s of g.steps) {
    if (!isText(s?.id) || steps.has(s.id)) errors.push(`step id missing or duplicated: ${s?.id}`);
    else if (lanes.has(s.id)) errors.push(`step ${s.id}: id is also a lane id; give them distinct ids`);
    if (!isText(s?.title)) errors.push(`step ${s?.id} needs a title`);
    if (!lanes.has(s?.lane)) errors.push(`step ${s?.id}: unknown lane ${s?.lane}`);
    if (s?.detail !== undefined && !isText(s.detail)) errors.push(`step ${s?.id}: detail must be text`);
    if (s?.tone !== undefined && !TONES.has(s.tone)) errors.push(`step ${s?.id}: unknown tone ${s.tone}`);
    if (s?.style !== undefined && s.style !== 'dashed') errors.push(`step ${s?.id}: style must be "dashed"`);
    if (s?.tone === 'accent') accents++;
    steps.add(s?.id);
  }
  if (!Array.isArray(g.edges)) errors.push('edges must be an array; use [] for a swimlane without arrows');
  else for (const e of g.edges) {
    const name = `edge ${e?.from} -> ${e?.to}`;
    // Without a steps list every reference would fail; the steps error already names the problem.
    if (Array.isArray(g.steps) && !steps.has(e?.from)) errors.push(`${name}: unknown step ${e?.from}`);
    if (Array.isArray(g.steps) && !steps.has(e?.to)) errors.push(`${name}: unknown step ${e?.to}`);
    if (e?.label !== undefined && !isText(e.label)) errors.push(`${name}: label must be text`);
    if (e?.style !== undefined && e.style !== 'dashed') errors.push(`${name}: style must be "dashed"`);
    if (e?.back !== undefined && typeof e.back !== 'boolean') errors.push(`${name}: back must be true or false`);
  }
  if (accents > 1) warns.push(`${accents} accent steps; keep one, the step the reader must notice.`);
  if (Array.isArray(g.lanes) && g.lanes.length > 5) warns.push(`${g.lanes.length} lanes; above 5 a swimlane stops reading at a glance. Merge lanes or split the process.`);
  if (Array.isArray(g.steps) && g.steps.length > 12) warns.push(`${g.steps.length} steps; above 12 a swimlane stops reading at a glance. Split it into an overview and parts.`);
  return { errors, warns };
}

const ids = (g: any): string[] => [...(Array.isArray(g.lanes) ? g.lanes : []), ...(Array.isArray(g.steps) ? g.steps : [])].map((x: any) => x?.id).filter(isText);

/** Return edges: every edge marked back, then each edge that closes a cycle in a depth-first walk in spec order. */
function returnEdges(steps: Step[], edges: Edge[]) {
  const ret = edges.map(e => e.back === true);
  const state = new Map<string, number>();
  const visit = (u: string) => {
    state.set(u, 1);
    edges.forEach((e, i) => {
      if (ret[i] || e.from !== u) return;
      const st = state.get(e.to) ?? 0;
      if (st === 1) ret[i] = true;
      else if (st === 0) visit(e.to);
    });
    state.set(u, 2);
  };
  for (const s of steps) if (!state.get(s.id)) visit(s.id);
  return ret;
}

/** Longest-path rank over the forward edges, which form a DAG once return edges are removed. */
function ranks(steps: Step[], edges: Edge[], ret: boolean[]) {
  const rank = new Map(steps.map(s => [s.id, 0]));
  const indeg = new Map(steps.map(s => [s.id, 0]));
  edges.forEach((e, i) => { if (!ret[i]) indeg.set(e.to, indeg.get(e.to)! + 1); });
  const queue = steps.filter(s => !indeg.get(s.id)).map(s => s.id);
  while (queue.length) {
    const u = queue.shift()!;
    edges.forEach((e, i) => {
      if (ret[i] || e.from !== u) return;
      rank.set(e.to, Math.max(rank.get(e.to)!, rank.get(u)! + 1));
      indeg.set(e.to, indeg.get(e.to)! - 1);
      if (!indeg.get(e.to)) queue.push(e.to);
    });
  }
  return rank;
}

const meets = (a: Box, b: Box, pad = 0) => a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;
function hits(b: Box, p: Pt, q: Pt) {
  if (Math.abs(p[1] - q[1]) < 0.5) return p[1] > b.y && p[1] < b.y + b.h && Math.max(p[0], q[0]) > b.x && Math.min(p[0], q[0]) < b.x + b.w;
  return p[0] > b.x && p[0] < b.x + b.w && Math.max(p[1], q[1]) > b.y && Math.min(p[1], q[1]) < b.y + b.h;
}

function layout(g: any, m: Measure): SItem[] {
  const down = g.direction === 'DOWN';
  const lanes: Lane[] = g.lanes, steps: Step[] = g.steps, edges: Edge[] = g.edges;
  const laneIx = new Map(lanes.map((l, i) => [l.id, i]));
  const step = new Map(steps.map(s => [s.id, s]));
  const size = new Map(steps.map(s => {
    const z = sizeNode(m, s, 12, 120);
    return [s.id, { w: z.w, h: z.h, A: down ? z.h : z.w, C: down ? z.w : z.h }];
  }));
  const ret = returnEdges(steps, edges);
  const rank = ranks(steps, edges, ret);
  const R = Math.max(...rank.values()) + 1;
  const laneLabels = lanes.map(l => text(0, 0, l.label.toUpperCase(), 'group', m, {}, 'var(--ink-2)'));
  const subGap = down ? 16 : SUB_GAP;

  // Lane-local across positions: each cell's stack is centred in the lane's content band.
  const cells = new Map<string, Step[]>();
  for (const s of steps) {
    const key = `${s.lane}|${rank.get(s.id)}`;
    cells.set(key, [...(cells.get(key) ?? []), s]);
  }
  const stackC = (ss: Step[]) => ss.reduce((t, s) => t + size.get(s.id)!.C, 0) + (ss.length - 1) * subGap;
  const content = lanes.map(l => Math.max(0, ...[...cells.entries()].filter(([k]) => k.startsWith(`${l.id}|`)).map(([, ss]) => stackC(ss))));
  const local = new Map<string, number>();
  for (const ss of cells.values()) {
    let c = (content[laneIx.get(ss[0].lane)!] - stackC(ss)) / 2;
    for (const s of ss) { local.set(s.id, c); c += size.get(s.id)!.C + subGap; }
  }
  const mid = (id: string) => local.get(id)! + size.get(id)!.C / 2;

  // Ports: edges sharing a box side get evenly spaced attach points, ordered by where the other end lies.
  const portC = new Map<string, number>();
  const sides = new Map<string, { key: [number, number]; port: string }[]>();
  edges.forEach((e, i) => {
    const out = ret[i] ? [Infinity, i] : [laneIx.get(step.get(e.to)!.lane)!, mid(e.to)];
    const inn = ret[i] ? [Infinity, i] : [laneIx.get(step.get(e.from)!.lane)!, mid(e.from)];
    sides.set(`${e.from}>`, [...(sides.get(`${e.from}>`) ?? []), { key: out as [number, number], port: `${i}>` }]);
    sides.set(`${e.to}<`, [...(sides.get(`${e.to}<`) ?? []), { key: inn as [number, number], port: `${i}<` }]);
  });
  for (const [side, list] of sides) {
    const id = side.slice(0, -1), C = size.get(id)!.C;
    list.sort((a, b) => a.key[0] - b.key[0] || a.key[1] - b.key[1]);
    list.forEach((p, j) => portC.set(p.port, local.get(id)! + C * (j + 1) / (list.length + 1)));
  }
  // A lone port slides to meet its partner in the same lane, so the arrow runs straight instead of jogging.
  const within = (id: string, c: number) => c >= local.get(id)! + 8 && c <= local.get(id)! + size.get(id)!.C - 8;
  edges.forEach((e, i) => {
    if (ret[i] || step.get(e.from)!.lane !== step.get(e.to)!.lane) return;
    const cs = portC.get(`${i}>`)!, ct = portC.get(`${i}<`)!;
    if (sides.get(`${e.to}<`)!.length === 1 && within(e.to, cs)) portC.set(`${i}<`, cs);
    else if (sides.get(`${e.from}>`)!.length === 1 && within(e.from, ct)) portC.set(`${i}>`, ct);
  });

  // Route shapes, decided in lane-local coordinates so corridor padding can be sized before lanes are placed.
  const clearAt = (lane: string, c: number, r0: number, r1: number) => !steps.some(x => {
    const r = rank.get(x.id)!, c0 = local.get(x.id)!;
    return x.lane === lane && r > r0 && r < r1 && c > c0 - 6 && c < c0 + size.get(x.id)!.C + 6;
  });
  type Shape = 'straight' | 'early' | 'late' | 'corr' | 'ret';
  const shape: Shape[] = [], corr: { side: string; track: number }[] = [];
  const corrUse = new Map<string, [number, number][][]>();
  edges.forEach((e, i) => {
    const S = step.get(e.from)!, T = step.get(e.to)!, rs = rank.get(S.id)!, rt = rank.get(T.id)!;
    const cs = portC.get(`${i}>`)!, ct = portC.get(`${i}<`)!, same = S.lane === T.lane && Math.abs(cs - ct) < 0.5;
    if (ret[i]) shape[i] = 'ret';
    else if (same && clearAt(S.lane, cs, rs, rt)) shape[i] = 'straight';
    else if (rt === rs + 1) shape[i] = 'early';
    else if (clearAt(S.lane, cs, rs, rt)) shape[i] = 'late';
    else if (clearAt(T.lane, ct, rs, rt)) shape[i] = 'early';
    else {
      shape[i] = 'corr';
      const ls = laneIx.get(S.lane)!, lt = laneIx.get(T.lane)!;
      const end = ls < lt || (ls === lt && (cs + ct) / 2 > content[ls] / 2);
      const side = `${S.lane}|${end ? 'end' : 'start'}`;
      const tracks = corrUse.get(side) ?? [];
      let t = tracks.findIndex(ivs => ivs.every(([a, b]) => b < rs || a > rt - 1));
      if (t < 0) { t = tracks.length; tracks.push([]); }
      tracks[t].push([rs, rt - 1]);
      corrUse.set(side, tracks);
      corr[i] = { side, track: t };
    }
  });

  // Global across positions of lanes, steps, corridors and the return channel.
  const pad = (lane: string, side: string) => {
    const n = corrUse.get(`${lane}|${side}`)?.length ?? 0;
    return n ? Math.max(BASE_PAD, CORR0 + CORR_STEP * (n - 1) + 13) : BASE_PAD;
  };
  const laneC: { cs: number; ce: number; c0: number }[] = [];
  let cur = 0;
  lanes.forEach((l, i) => {
    const ps = pad(l.id, 'start'), pe = pad(l.id, 'end');
    const min = down ? Math.max(160, laneLabels[i].w + 28) : 60;
    const L = Math.max(ps + content[i] + pe, min);
    laneC.push({ cs: cur, ce: cur + L, c0: cur + ps + (L - ps - content[i] - pe) / 2 });
    cur += L;
  });
  const gc = (id: string) => laneC[laneIx.get(step.get(id)!.lane)!].c0 + local.get(id)!;
  const gport = (i: number, dir: '>' | '<') => {
    const e = edges[i];
    return laneC[laneIx.get(step.get(dir === '>' ? e.from : e.to)!.lane)!].c0 + portC.get(`${i}${dir}`)!;
  };
  const corrC = (i: number) => {
    const [lane, side] = corr[i].side.split('|'), lc = laneC[laneIx.get(lane)!];
    const off = CORR0 + CORR_STEP * corr[i].track;
    return side === 'start' ? lc.cs + off : lc.ce - off;
  };
  const chanBase = laneC[laneC.length - 1].ce + CHANNEL0;
  const retOrder = edges.map((_, i) => i).filter(i => ret[i]);

  // Routes with along positions still symbolic; across segments in gaps are collected for track assignment.
  const gapSegs: Seg[][] = Array.from({ length: R + 1 }, () => []);
  const seg = (k: number, c1: number, c2: number): ARef => {
    const s: Seg = { k, c1, c2, track: 0 };
    gapSegs[k + 1].push(s);
    return { t: 'gap', seg: s };
  };
  const routes: Way[][] = edges.map((e, i) => {
    const rs = rank.get(e.from)!, rt = rank.get(e.to)!, cs = gport(i, '>'), ct = gport(i, '<');
    const far: ARef = { t: 'far', s: e.from }, near: ARef = { t: 'near', s: e.to };
    const via = (k: number, c1: number, c2: number): Way[] => { const a = seg(k, c1, c2); return [{ a, c: c1 }, { a, c: c2 }]; };
    if (shape[i] === 'straight') return [{ a: far, c: cs }, { a: near, c: ct }];
    if (shape[i] === 'early') return [{ a: far, c: cs }, ...via(rs, cs, ct), { a: near, c: ct }];
    if (shape[i] === 'late') return [{ a: far, c: cs }, ...via(rt - 1, cs, ct), { a: near, c: ct }];
    const mid = shape[i] === 'corr' ? corrC(i) : chanBase + TRACK * retOrder.indexOf(i);
    return [{ a: far, c: cs }, ...via(rs, cs, mid), ...via(rt - 1, mid, ct), { a: near, c: ct }];
  });

  // Track 0 sits nearest the next column; this order keeps same-direction turns from crossing each other.
  const trackCount = gapSegs.map(list => {
    const downs = list.filter(s => s.c2 > s.c1).sort((a, b) => a.c1 - b.c1);
    const ups = list.filter(s => s.c2 <= s.c1).sort((a, b) => b.c1 - a.c1);
    const tracks: Seg[][] = [];
    for (const s of [...downs, ...ups]) {
      const lo = Math.min(s.c1, s.c2), hi = Math.max(s.c1, s.c2);
      let t = tracks.findIndex(ts => ts.every(o => Math.max(lo, Math.min(o.c1, o.c2)) > Math.min(hi, Math.max(o.c1, o.c2)) + 12));
      if (t < 0) { t = tracks.length; tracks.push([]); }
      tracks[t].push(s);
      s.track = t;
    }
    return tracks.length;
  });

  // Along positions: gaps sized for their tracks plus the labels that sit on exits into them.
  const labelAlong = (e: Edge) => e.label ? (down ? LINE.edge : m(e.label, 'edge').w) : 0;
  const gutter = down ? HEADER : Math.max(...laneLabels.map(t => t.w)) + 2 * GUTTER_PAD;
  const colA = Array.from({ length: R }, (_, r) => Math.max(...steps.filter(s => rank.get(s.id) === r).map(s => size.get(s.id)!.A)));
  const zoneable = (i: number) => shape[i] === 'early' || shape[i] === 'corr';
  // Labels first try the room the routes leave; an exit gap widens only for a label that found no clear spot.
  const build = (zoned: Set<number>): { items: SItem[]; need: number[] } => {
    const zone = Array.from({ length: R + 1 }, () => 0);
    edges.forEach((e, i) => {
      if (e.label && (zoned.has(i) || (shape[i] === 'straight' && rank.get(e.to)! === rank.get(e.from)! + 1))) {
        const k = rank.get(e.from)! + 1;
        zone[k] = Math.max(zone[k], labelAlong(e) + LABEL_ZONE + (shape[i] === 'straight' ? 10 : 0));
      }
    });
    const gapW = trackCount.map((n, k) => {
      const tz = n ? 2 * TRACK_EDGE + (n - 1) * TRACK : 0;
      if (k === 0) return n ? tz : down ? 12 : 16;
      if (k === R) return tz;
      return Math.max(down ? 40 : 44, zone[k] + tz);
    });
    const gapStart: number[] = [], colStart: number[] = [];
    let a = gutter;
    for (let k = 0; k <= R; k++) {
      gapStart[k] = a; a += gapW[k];
      if (k < R) { colStart[k] = a; a += colA[k]; }
    }
    const endA = a + END;
    const a0 = (id: string) => colStart[rank.get(id)!] + (colA[rank.get(id)!] - size.get(id)!.A) / 2;
    const along = (r: ARef) => r.t === 'far' ? a0(r.s) + size.get(r.s)!.A : r.t === 'near' ? a0(r.s) : gapStart[r.seg.k + 1] + gapW[r.seg.k + 1] - TRACK_EDGE - r.seg.track * TRACK;
    const xy = (al: number, ac: number): Pt => down ? [ac, al] : [al, ac];

    const items: SItem[] = [];
    const tinted = (i: number) => i % 2 === 0;
    lanes.forEach((l, i) => {
      const { cs, ce } = laneC[i];
      const b = down ? { x: cs, y: 0, w: ce - cs, h: endA } : { x: 0, y: cs, w: endA, h: ce - cs };
      items.push({ t: 'rect', ...b, role: 'band', id: l.id, style: tinted(i) ? 'fill:var(--surface-2);fill-opacity:.4' : 'fill:var(--surface)' });
    });
    for (const c of [laneC[0].cs, ...laneC.map(l => l.ce)]) items.push({ t: 'path', pts: [xy(0, c), xy(endA, c)], r: 0, role: 'divider', style: 'stroke:var(--line);stroke-width:1' });
    lanes.forEach((l, i) => {
      const { cs, ce } = laneC[i], t = laneLabels[i];
      items.push(down ? { ...t, x: (cs + ce) / 2, y: HEADER / 2 + 4, anchor: 'middle', owner: l.id } : { ...t, x: GUTTER_PAD, y: (cs + ce) / 2 + 4, anchor: 'start', owner: l.id });
    });
    const paths = routes.map((ways, i) => {
      const pts: Pt[] = [];
      for (const w of ways) {
        const p = xy(along(w.a), w.c), q = pts[pts.length - 1];
        if (!q || Math.abs(q[0] - p[0]) > 0.01 || Math.abs(q[1] - p[1]) > 0.01) pts.push(p);
      }
      const dashed = ret[i] || edges[i].style === 'dashed';
      return { t: 'path' as const, pts, role: 'connector' as const, marker: 'arrow' as const, owner: `~edge${i}`, style: `stroke:var(--ink-3);stroke-width:1.4${dashed ? ';stroke-dasharray:5 4' : ''}` };
    });
    items.push(...paths);
    for (const s of steps) {
      const z = size.get(s.id)!, al = a0(s.id), ac = gc(s.id);
      nodeBox(items, m, down ? { x: ac, y: al, w: z.w, h: z.h } : { x: al, y: ac, w: z.w, h: z.h }, s);
    }

    // Edge labels: the clear spot beside a segment that crosses the fewest other lines, preferring the exit.
    const obst: Box[] = [];
    for (const it of items) {
      if (it.t === 'text') obst.push(textBox(it));
      else if (it.t === 'rect' && it.role === 'box') obst.push(it);
      else if (it.t === 'icon') obst.push({ x: it.x, y: it.y, w: ICON_SIZE, h: ICON_SIZE });
    }
    const lines = items.filter((it): it is Extract<SItem, { t: 'path' }> => it.t === 'path');
    const labelled: SItem[] = [], need: number[] = [];
    edges.forEach((e, i) => {
      if (!e.label) return;
      const pts = paths[i].pts, { w, h } = m(e.label, 'edge');
      let best: { box: Box; score: number } | undefined;
      for (let k = 0; k + 1 < pts.length; k++) {
        const [p, q] = [pts[k], pts[k + 1]], last = k + 2 === pts.length;
        const pref = ret[i] ? (k === 2 ? 0 : 2) : k === 0 ? 0 : last ? 1 : 2;
        const boxes: Box[] = [];
        if (Math.abs(p[1] - q[1]) < 0.5) {
          const xa = Math.min(p[0], q[0]), xb = Math.max(p[0], q[0]) - (last ? 10 : 0);
          if (w + 16 > xb - xa) continue;
          for (const x of [xa + 8, (xa + xb - w) / 2, xb - 8 - w]) for (const y of [p[1] - 2 - h, p[1] + 3]) boxes.push({ x, y, w, h });
        } else {
          const ya = Math.min(p[1], q[1]), yb = Math.max(p[1], q[1]) - (last ? 10 : 0);
          if (h + 12 > yb - ya) continue;
          for (const y of [ya + 6, (ya + yb - h) / 2, yb - 6 - h]) for (const x of [p[0] + 7, p[0] - 7 - w]) boxes.push({ x, y, w, h });
        }
        for (const box of boxes) {
          if (obst.some(o => meets(box, o, 3))) continue;
          let score = pref * 3;
          for (const ln of lines) {
            if (ln.owner === paths[i].owner) continue;
            for (let j = 1; j < ln.pts.length; j++) if (hits(box, ln.pts[j - 1], ln.pts[j])) { score += ln.role === 'divider' ? 1 : 10; break; }
          }
          if (!best || score < best.score) best = { box, score };
        }
      }
      if ((!best || best.score >= 10) && zoneable(i) && !zoned.has(i)) { need.push(i); return; }
      if (!best) throw specError(`edge ${e.from} -> ${e.to}: no clear place beside the arrow for its label "${e.label}"; shorten it`);
      const { box } = best;
      obst.push(box);
      const bk = { x: box.x - 3, y: box.y, w: box.w + 6, h: box.h };
      labelled.push({ t: 'rect', ...bk, role: 'backing', style: 'fill:var(--surface)' });
      // A label straddling a lane edge gets each band's tint only over its own part.
      for (const band of items) {
        if (band.t !== 'rect' || band.role !== 'band' || !tinted(laneIx.get(band.id!)!)) continue;
        const x0 = Math.max(bk.x, band.x), x1 = Math.min(bk.x + bk.w, band.x + band.w), y0 = Math.max(bk.y, band.y), y1 = Math.min(bk.y + bk.h, band.y + band.h);
        if (x1 > x0 && y1 > y0) labelled.push({ t: 'rect', x: x0, y: y0, w: x1 - x0, h: y1 - y0, role: 'backing', style: band.style });
      }
      labelled.push(text(box.x, box.y + h - 5, e.label, 'edge', m, { anchor: 'start', owner: paths[i].owner, backed: true }));
    });
    items.push(...labelled);
    return { items, need };
  };
  const zoned = new Set<number>();
  for (;;) {
    const res = build(zoned);
    if (!res.need.length) return res.items;
    res.need.forEach(i => zoned.add(i));
  }
}

export const swimlane: Kind = { check, ids, layout };
