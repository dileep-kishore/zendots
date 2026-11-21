import { bounds, LINE, text, textBox, type Measure, type Pt, type SItem } from './scene';

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

// Everything a leader must not pass through: boxes, dots and text that do not belong to the target.
function obstacles(items: SItem[], id: string): Box[] {
  const out: Box[] = [];
  for (const it of items) {
    if (it.t === 'rect' && it.role === 'box' && it.id !== id) out.push(it);
    else if (it.t === 'dot' && it.id !== id) out.push({ x: it.cx - it.r, y: it.cy - it.r, w: 2 * it.r, h: 2 * it.r });
    else if (it.t === 'text' && it.owner !== id) out.push(textBox(it));
  }
  return out;
}
const clear = (obs: Box[], a: Pt, b: Pt) => {
  const x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]), y0 = Math.min(a[1], b[1]), y1 = Math.max(a[1], b[1]);
  return !obs.some(o => x1 > o.x && x0 < o.x + o.w && y1 > o.y && y0 < o.y + o.h);
};

/**
 * Places each note on the first side of its target (right, left, below) whose straight leader reaches the
 * drawing's edge without crossing anything else, and grows the drawing on that side. Mutates items.
 */
export function placeNotes(items: SItem[], notes: Note[], m: Measure, extent: { x0: number; y0: number; x1: number; y1: number }) {
  const ext = { ...extent };
  const placed: SItem[] = [];
  let rightY = -Infinity, leftY = -Infinity, belowX = -Infinity;
  for (const [i, note] of notes.entries()) {
    const owner = `note:${i}`;
    const tb = targetBox(items, note.target);
    if (!tb) throw new Error(`note ${i + 1}: target ${note.target} is not drawn in this diagram`);
    const lines = wrapNote(note.text);
    const sizes = lines.map(l => m(l, 'note'));
    const w = Math.max(...sizes.map(s => s.w)), h = lines.length * LINE.note;
    const obs = obstacles([...items, ...placed], note.target);
    const cy = tb.y + tb.h / 2, cx = tb.x + tb.w / 2;
    const block = (x: number, top: number, anchor: 'start' | 'end') =>
      lines.map((l, k) => text(x, top + (k + 1) * LINE.note - 4, l, 'note', m, { anchor, owner }, 'var(--ink-2)'));
    const leader = (a: Pt, b: Pt): SItem => ({ t: 'path', pts: [a, b], r: 0, role: 'leader', owner, style: 'stroke:var(--ink-3);stroke-width:1;stroke-dasharray:3 3' });
    const right: [Pt, Pt] = [[tb.x + tb.w + INSET, cy], [ext.x1 + GAP - 6, cy]];
    const left: [Pt, Pt] = [[tb.x - INSET, cy], [ext.x0 - GAP + 6, cy]];
    const below: [Pt, Pt] = [[cx, tb.y + tb.h + INSET], [cx, ext.y1 + GAP - 6]];
    if (clear(obs, ...right)) {
      const top = Math.max(cy - h / 2, rightY + 8);
      placed.push(leader(...right), ...block(ext.x1 + GAP, top, 'start'));
      rightY = top + h;
    } else if (clear(obs, ...left)) {
      const top = Math.max(cy - h / 2, leftY + 8);
      placed.push(leader(...left), ...block(ext.x0 - GAP, top, 'end'));
      leftY = top + h;
    } else if (clear(obs, ...below)) {
      const x = Math.max(cx - w / 2, belowX + 16);
      placed.push(leader(...below), ...block(x, ext.y1 + GAP, 'start'));
      belowX = x + w;
    } else throw new Error(`note ${i + 1}: no side of ${note.target} has a clear path to the edge of the drawing; target a node on the outside, or drop the note`);
  }
  items.push(...placed);
}
