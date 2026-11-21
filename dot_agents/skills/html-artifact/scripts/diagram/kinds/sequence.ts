import { nodeBox, sizeNode, stroke, text, textBox, type Measure, type SItem, type SText } from '../scene';
import { isText, TONES, type Kind } from './types';

const TYPES = new Set(['call', 'return', 'async']);
const OPS = new Set(['opt', 'alt', 'loop']);
const MAX_ACTORS = 6, MAX_MESSAGES = 16;
// Label offset from its source lifeline, self-loop size, frame inset from its outermost lifelines.
const PAD = 8, LOOP_W = 30, LOOP_H = 18, INSET = 14, NEST = 8, ACTOR_GAP = 32;

interface Frame { i: number; op: string; guard: string; start: number; end: number; else?: number; elseGuard?: string; parent?: Frame; depth: number }

const isIndex = (v: unknown, n: number): v is number => Number.isInteger(v) && (v as number) >= 0 && (v as number) < n;
const list = (g: any, key: string): any[] => Array.isArray(g[key]) ? g[key] : [];

// The smallest frame that holds f; equal ranges nest by array order, the earlier frame outside.
function parentOf(f: Frame, all: Frame[]): Frame | undefined {
  let best: Frame | undefined;
  for (const o of all) {
    if (o === f || o.start > f.start || o.end < f.end) continue;
    if (o.start === f.start && o.end === f.end && o.i > f.i) continue;
    if (!best || o.end - o.start < best.end - best.start || (o.end - o.start === best.end - best.start && o.i > best.i)) best = o;
  }
  return best;
}

function framesOf(g: any): Frame[] {
  const all: Frame[] = list(g, 'frames').map((f: any, i: number) => ({ i, op: f.op, guard: f.guard, start: f.start, end: f.end, else: f.else, elseGuard: f.elseGuard, depth: 0 }));
  for (const f of all) f.parent = parentOf(f, all);
  for (const f of all) { let d = 0; for (let p = f.parent; p; p = p.parent) d++; f.depth = d; }
  return all;
}

export const sequence: Kind = {
  check(g) {
    const errors: string[] = [], warns: string[] = [];
    const actorList = g.actors;
    const ids = new Set<string>();
    if (!Array.isArray(actorList) || !actorList.length) errors.push('actors must be a nonempty array');
    else actorList.forEach((a: any, i: number) => {
      if (!isText(a?.id) || ids.has(a.id)) errors.push(`actors[${i}]: id missing or duplicated: ${a?.id}`);
      else ids.add(a.id);
      if (!isText(a?.title)) errors.push(`actors[${i}] needs a title`);
      if (a?.detail !== undefined && !isText(a.detail)) errors.push(`actors[${i}]: detail must be a nonempty string`);
      if (a?.tone !== undefined && !TONES.has(a.tone)) errors.push(`actors[${i}]: unknown tone ${a.tone}`);
    });
    const actors = new Set(ids);
    const msgList = g.messages;
    const n = Array.isArray(msgList) ? msgList.length : 0;
    if (!Array.isArray(msgList) || !msgList.length) errors.push('messages must be a nonempty array');
    else msgList.forEach((msg: any, i: number) => {
      for (const end of ['from', 'to'] as const) if (!actors.has(msg?.[end])) errors.push(`messages[${i}]: ${end} ${JSON.stringify(msg?.[end])} is not an actor id`);
      if (!isText(msg?.label)) errors.push(`messages[${i}] needs a label`);
      if (msg?.type !== undefined && !TYPES.has(msg.type)) errors.push(`messages[${i}]: type must be one of ${[...TYPES].join(', ')}`);
      if (msg?.tone !== undefined && !TONES.has(msg.tone)) errors.push(`messages[${i}]: unknown tone ${msg.tone}`);
      if (msg?.id !== undefined) {
        if (!isText(msg.id) || ids.has(msg.id)) errors.push(`messages[${i}]: id missing or duplicated: ${msg.id}`);
        else ids.add(msg.id);
      }
    });
    if (g.frames !== undefined && !Array.isArray(g.frames)) errors.push('frames must be an array');
    let framesOk = true;
    list(g, 'frames').forEach((f: any, i: number) => {
      const bad = (s: string) => { errors.push(`frames[${i}]: ${s}`); framesOk = false; };
      if (!OPS.has(f?.op)) bad(`op must be one of ${[...OPS].join(', ')}`);
      if (!isText(f?.guard)) bad('needs a guard');
      if (!isIndex(f?.start, n) || !isIndex(f?.end, n) || f.start > f.end) bad(`start and end must be message indexes with start <= end (0 to ${n - 1})`);
      if (f?.op === 'alt') {
        if (!Number.isInteger(f.else) || !(f.start < f.else && f.else <= f.end)) bad('alt needs an else index with start < else <= end');
        if (f.elseGuard !== undefined && !isText(f.elseGuard)) bad('elseGuard must be a nonempty string');
      } else if (f?.else !== undefined || f?.elseGuard !== undefined) bad('else and elseGuard apply only to alt');
    });
    if (framesOk) {
      const all = framesOf(g);
      for (const a of all) for (const b of all) {
        if (a.i < b.i && ((a.start < b.start && b.start <= a.end && a.end < b.end) || (b.start < a.start && a.start <= b.end && b.end < a.end)))
          errors.push(`frames[${a.i}] and frames[${b.i}] partly overlap; a frame must hold another whole or not at all`);
      }
      for (const f of all) {
        if (f.depth > 1) errors.push(`frames[${f.i}] is nested ${f.depth} levels deep; frames nest at most one level, so split the diagram`);
        const p = f.parent;
        if (p?.op === 'alt' && f.start < p.else! && p.else! <= f.end) errors.push(`frames[${f.i}] crosses the else divider of frames[${p.i}]`);
      }
    }
    if (Array.isArray(actorList) && actorList.length > MAX_ACTORS) warns.push(`${actorList.length} actors; above ${MAX_ACTORS} lifelines a sequence stops reading at a glance. Split it.`);
    if (n > MAX_MESSAGES) warns.push(`${n} messages; above ${MAX_MESSAGES} split the flow into an overview and a detail diagram.`);
    const accents = [...(Array.isArray(actorList) ? actorList : []), ...(Array.isArray(msgList) ? msgList : [])].filter((x: any) => x?.tone === 'accent').length;
    if (accents > 1) warns.push(`${accents} accent actors and messages; keep one, the step the reader must notice.`);
    return { errors, warns };
  },

  ids(g) {
    return [...list(g, 'actors'), ...list(g, 'messages')].map((x: any) => x?.id).filter(isText);
  },

  layout(g, m: Measure) {
    const actors: any[] = g.actors, msgs: any[] = g.messages, frames = framesOf(g);
    const col = new Map<string, number>(actors.map((a, i) => [a.id, i]));
    const sizes = actors.map(a => sizeNode(m, { title: a.title, detail: a.detail, icon: a.icon }, 12, 120));
    const boxH = Math.max(...sizes.map(s => s.h));
    const nA = actors.length;
    const label = (s: string) => m(s, 'edge').w;
    const head = (f: Frame) => Math.max(m(f.op.toUpperCase(), 'group').w + 16, label(`[${f.guard}]`), f.op === 'alt' ? label(`[${f.elseGuard ?? 'else'}]`) : 0) + 2 * PAD;

    // Horizontal: constraints cx[j] - cx[i] >= d with i < j, solved left to right as a longest path.
    const cons: [number, number, number][] = [];
    for (let i = 0; i + 1 < nA; i++) cons.push([i, i + 1, sizes[i].w / 2 + sizes[i + 1].w / 2 + ACTOR_GAP]);
    const selfReach = (k: number) => Math.max(LOOP_W, PAD + label(msgs[k].label));
    msgs.forEach((msg, k) => {
      const a = col.get(msg.from)!, b = col.get(msg.to)!, need = label(msg.label) + 2 * PAD;
      if (a < b) cons.push([a, a + 1, need]);
      else if (a > b) cons.push([a - 1, a, need]);
      else if (a + 1 < nA) cons.push([a, a + 1, selfReach(k) + 2 * PAD]);
    });
    const span = new Map<Frame, { a: number; b: number; lx: number; rx: number }>();
    for (const f of [...frames].sort((p, q) => q.depth - p.depth || p.i - q.i)) {
      let a = Infinity, b = -Infinity;
      for (let k = f.start; k <= f.end; k++) for (const c of [col.get(msgs[k].from)!, col.get(msgs[k].to)!]) { a = Math.min(a, c); b = Math.max(b, c); }
      let lx = INSET, rx = INSET;
      for (let k = f.start; k <= f.end; k++) if (msgs[k].from === msgs[k].to && col.get(msgs[k].from) === b) rx = Math.max(rx, selfReach(k) + INSET);
      for (const c of frames) if (c.parent === f) {
        const s = span.get(c)!;
        if (s.a === a) lx = Math.max(lx, s.lx + NEST);
        if (s.b === b) rx = Math.max(rx, s.rx + NEST);
      }
      if (a === b) rx = Math.max(rx, head(f) - lx);
      else cons.push([a, b, head(f) - lx - rx]);
      if (b + 1 < nA) cons.push([b, b + 1, rx + 2 * PAD]);
      if (a > 0) cons.push([a - 1, a, lx + 2 * PAD]);
      span.set(f, { a, b, lx, rx });
    }
    const cx = new Array<number>(nA).fill(0);
    for (let j = 1; j < nA; j++) cx[j] = Math.max(...cons.filter(c => c[1] === j).map(([i, , d]) => cx[i] + d));

    // Vertical: one row per message, with room for frame headers, else dividers and frame bottoms.
    const top = new Map<Frame, number>(), bottom = new Map<Frame, number>(), divider = new Map<Frame, number>();
    const rows: number[] = [];
    let y = boxH + 24;
    msgs.forEach((msg, k) => {
      for (const f of frames.filter(f => f.start === k).sort((p, q) => p.depth - q.depth || p.i - q.i)) { y += 4; top.set(f, y); y += 44; }
      for (const f of frames.filter(f => f.op === 'alt' && f.else === k)) { divider.set(f, y + 2); y += 28; }
      rows.push(y);
      y += 19 + (msg.from === msg.to ? LOOP_H : 0) + 14;
      for (const f of frames.filter(f => f.end === k).sort((p, q) => q.depth - p.depth || q.i - p.i)) { bottom.set(f, y); y += 10; }
    });
    const lifeEnd = y + 8;

    const out: SItem[] = [], texts: SItem[] = [];
    // A text drawn on an opaque patch of the figure colour, so lines behind it break cleanly.
    const backed = (t: SText) => {
      const b = textBox(t);
      texts.push({ t: 'rect', x: b.x - 3, y: b.y, w: b.w + 6, h: b.h, role: 'backing', style: 'fill:var(--surface)' }, t);
    };
    actors.forEach((_, i) => out.push({ t: 'path', pts: [[cx[i], boxH], [cx[i], lifeEnd]], r: 0, role: 'lifeline', style: 'stroke:var(--line-strong);stroke-width:1;stroke-dasharray:3 4' }));
    for (const f of frames) {
      const s = span.get(f)!, x0 = cx[s.a] - s.lx, x1 = cx[s.b] + s.rx, y0 = top.get(f)!, y1 = bottom.get(f)!;
      const mid = (x0 + x1) / 2;
      out.push({ t: 'path', pts: [[mid, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0], [mid, y0]], r: 4, role: 'frame', style: 'stroke:var(--line-strong);stroke-width:1' });
      const op = text(x0 + PAD, y0 + 13, f.op.toUpperCase(), 'group', m, { anchor: 'start', backed: true }, 'var(--ink-2)');
      texts.push({ t: 'rect', x: x0, y: y0, w: op.w + 2 * PAD, h: 18, rx: 2, role: 'backing', style: 'fill:var(--surface);stroke:var(--line-strong);stroke-width:1' }, op);
      backed(text(x0 + PAD, y0 + 32, `[${f.guard}]`, 'edge', m, { anchor: 'start', backed: true }));
      const dy = divider.get(f);
      if (dy !== undefined) {
        out.push({ t: 'path', pts: [[x0, dy], [x1, dy]], r: 0, role: 'divider', style: 'stroke:var(--line-strong);stroke-width:1;stroke-dasharray:4 3' });
        backed(text(x0 + PAD, dy + 16, `[${f.elseGuard ?? 'else'}]`, 'edge', m, { anchor: 'start', backed: true }));
      }
    }
    msgs.forEach((msg, k) => {
      const a = col.get(msg.from)!, b = col.get(msg.to)!, ay = rows[k] + 19;
      const type = msg.type ?? 'call', focal = msg.tone === 'accent';
      const style = `stroke:${stroke(msg.tone)};stroke-width:${focal ? 2 : 1.4}${type === 'call' ? '' : ';stroke-dasharray:5 4'}`;
      const pts: [number, number][] = a === b
        ? [[cx[a], ay], [cx[a] + LOOP_W, ay], [cx[a] + LOOP_W, ay + LOOP_H], [cx[a] + 1, ay + LOOP_H]]
        : [[cx[a], ay], [cx[b], ay]];
      out.push({ t: 'path', pts, r: a === b ? 6 : 0, role: 'connector', marker: type === 'async' ? 'open' : 'arrow', style, id: msg.id, owner: msg.id ?? `msg:${k}` });
      const left = a > b;
      backed(text(left ? cx[a] - PAD : cx[a] + PAD, rows[k] + 10, msg.label, 'edge', m, { anchor: left ? 'end' : 'start', backed: true, owner: msg.id ?? `msg:${k}` }, focal ? 'var(--ink)' : 'var(--ink-2)'));
    });
    out.push(...texts);
    actors.forEach((act, i) => nodeBox(out, m, { x: cx[i] - sizes[i].w / 2, y: 0, w: sizes[i].w, h: boxH }, { id: act.id, title: act.title, detail: act.detail, tone: act.tone, icon: act.icon }));
    return out;
  },
};
