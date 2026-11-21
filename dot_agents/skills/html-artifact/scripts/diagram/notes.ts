import { bounds, LINE, specError, text, textBox, type Measure, type Pt, type SItem } from './scene';

export interface Note { target: string; text: string }
export const NOTE_MAX = 2, NOTE_CHARS = 28, NOTE_LINES = 3;

/** Greedy word wrap by characters, so diagram.ts can reject an over-long note before anything is measured. */
export function wrapNote(s: string): string[] {
  const lines: string[] = [];
  let cur = '';
  for (const word of s.trim().split(/\s+/)) {
    if (cur && cur.length + 1 + word.length > NOTE_CHARS) { lines.push(cur); cur = word; }
    else cur = cur ? `${cur} ${word}` : word;
  }
  if (cur) lines.push(cur);
  return lines;
}

type Box = { x: number; y: number; w: number; h: number };
const GAP = 22, INSET = 4;

function targetBox(items: SItem[], id: string): Box | undefined {
  const own = items.filter(it => (it.t === 'rect' || it.t === 'dot' || it.t === 'path') && it.id === id);
  if (!own.length) return undefined;
  const b = bounds(own);
  return { x: b.x0, y: b.y0, w: b.x1 - b.x0, h: b.y1 - b.y0 };
}

// Everything a leader must not pass through: boxes, dots, and text other than the target's own text inside its box.
// A quadrant label belongs to its item but sits outside the dot, so it still blocks that side.
function obstacles(items: SItem[], id: string, tb: Box): Box[] {
  const out: Box[] = [];
  const within = (b: Box) => b.x >= tb.x - 1 && b.y >= tb.y - 1 && b.x + b.w <= tb.x + tb.w + 1 && b.y + b.h <= tb.y + tb.h + 1;
  for (const it of items) {
    if (it.t === 'rect' && it.role === 'box' && it.id !== id) out.push(it);
    else if (it.t === 'dot' && it.id !== id) out.push({ x: it.cx - it.r, y: it.cy - it.r, w: 2 * it.r, h: 2 * it.r });
    else if (it.t === 'text' && !(it.owner === id && within(textBox(it)))) out.push(textBox(it));
  }
  return out;
}
const clear = (obs: Box[], a: Pt, b: Pt) => {
  const x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]), y0 = Math.min(a[1], b[1]), y1 = Math.max(a[1], b[1]);
  return !obs.some(o => x1 > o.x && x0 < o.x + o.w && y1 > o.y && y0 < o.y + o.h);
};

type Side = 'right' | 'left' | 'below';
interface Plan { i: number; owner: string; tb: Box; lines: string[]; w: number; h: number; side: Side }

/**
 * Places each note on the first side of its target (right, left, below) whose straight leader reaches the
 * drawing's edge without crossing anything else, and grows the drawing on that side. Notes sharing a side
 * stack in the order of their targets; a displaced note's leader jogs in the margin to meet it. Mutates items.
 */
export function placeNotes(items: SItem[], notes: Note[], m: Measure, ext: { x0: number; y0: number; x1: number; y1: number }) {
  const plans: Plan[] = [];
  for (const [i, note] of notes.entries()) {
    const tb = targetBox(items, note.target);
    if (!tb) throw specError(`note ${i + 1}: target ${note.target} is not drawn in this diagram`);
    const lines = wrapNote(note.text);
    const w = Math.max(...lines.map(l => m(l, 'note').w)), h = lines.length * LINE.note;
    const obs = obstacles(items, note.target, tb);
    const cy = tb.y + tb.h / 2, cx = tb.x + tb.w / 2;
    const side: Side | undefined =
      clear(obs, [tb.x + tb.w + INSET, cy], [ext.x1 + GAP, cy]) ? 'right'
      : clear(obs, [tb.x - INSET, cy], [ext.x0 - GAP, cy]) ? 'left'
      : clear(obs, [cx, tb.y + tb.h + INSET], [cx, ext.y1 + GAP]) ? 'below' : undefined;
    if (!side) throw specError(`note ${i + 1}: no side of ${note.target} has a clear path to the edge of the drawing; target a node on the outside, or drop the note`);
    plans.push({ i, owner: `note:${i}`, tb, lines, w, h, side });
  }
  const style = 'stroke:var(--ink-3);stroke-width:1;stroke-dasharray:3 3';
  const leader = (owner: string, pts: Pt[]): SItem => ({ t: 'path', pts, r: 0, role: 'leader', owner, style });
  const block = (p: Plan, x: number, top: number, anchor: 'start' | 'end') =>
    p.lines.map((l, k) => text(x, top + (k + 1) * LINE.note - 4, l, 'note', m, { anchor, owner: p.owner }, 'var(--ink-2)'));
  const placed: SItem[] = [];
  for (const side of ['right', 'left'] as const) {
    let water = -Infinity;
    const dir = side === 'right' ? 1 : -1, edge = side === 'right' ? ext.x1 : ext.x0;
    for (const p of plans.filter(q => q.side === side).sort((a, b) => (a.tb.y + a.tb.h / 2) - (b.tb.y + b.tb.h / 2))) {
      const cy = p.tb.y + p.tb.h / 2, top = Math.max(cy - p.h / 2, water + 8), mid = top + p.h / 2;
      const from: Pt = [side === 'right' ? p.tb.x + p.tb.w + INSET : p.tb.x - INSET, cy], end = edge + dir * (GAP - 6);
      const jog = edge + dir * 8;
      placed.push(leader(p.owner, Math.abs(mid - cy) < 1 ? [from, [end, cy]] : [from, [jog, cy], [jog, mid], [end, mid]]));
      placed.push(...block(p, edge + dir * GAP, top, side === 'right' ? 'start' : 'end'));
      water = top + p.h;
    }
  }
  let water = -Infinity;
  for (const p of plans.filter(q => q.side === 'below').sort((a, b) => (a.tb.x + a.tb.w / 2) - (b.tb.x + b.tb.w / 2))) {
    const cx = p.tb.x + p.tb.w / 2, x = Math.max(cx - p.w / 2, water + 16), mid = x + p.w / 2;
    const from: Pt = [cx, p.tb.y + p.tb.h + INSET], end = ext.y1 + GAP - 6, jog = ext.y1 + 8;
    placed.push(leader(p.owner, Math.abs(mid - cx) < 1 ? [from, [cx, end]] : [from, [cx, jog], [mid, jog], [mid, end]]));
    placed.push(...block(p, x, ext.y1 + GAP, 'start'));
    water = x + p.w;
  }
  items.push(...placed);
}
