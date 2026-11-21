import { ICON_SIZE, textBox, type Scene, type SItem, type SText } from './scene';

// The layout self-check. Pure, so a scratch script can import it and feed it a mutated scene.
export interface Violation { rule: 'diagonal' | 'overlap' | 'crossing' | 'bounds'; what: string }
type Box = { x: number; y: number; w: number; h: number };

// Text boxes include line leading; two lines a few units apart are not a collision.
const EPS = 1.5;
const meets = (a: Box, b: Box) => a.x < b.x + b.w - EPS && b.x < a.x + a.w - EPS && a.y < b.y + b.h - EPS && b.y < a.y + a.h - EPS;
const inside = (a: Box, b: Box) => a.x >= b.x - EPS && a.y >= b.y - EPS && a.x + a.w <= b.x + b.w + EPS && a.y + a.h <= b.y + b.h + EPS;
const name = (t: SText) => JSON.stringify(t.text.length > 40 ? t.text.slice(0, 40) + '…' : t.text);

function segmentHits(b: Box, [x0, y0]: [number, number], [x1, y1]: [number, number]) {
  // Orthogonal segments only; diagonals are reported by their own rule. A line along the box edge does not cross it.
  const ix = b.x + EPS, iy = b.y + EPS, ax = b.x + b.w - EPS, ay = b.y + b.h - EPS;
  if (Math.abs(y0 - y1) < 0.5) return y0 > iy && y0 < ay && Math.max(x0, x1) > ix && Math.min(x0, x1) < ax;
  if (Math.abs(x0 - x1) < 0.5) return x0 > ix && x0 < ax && Math.max(y0, y1) > iy && Math.min(y0, y1) < ay;
  return false;
}

/** Every way the scene breaks the four layout rules; an empty list means it may be written. */
export function checkScene(scene: Scene): Violation[] {
  const out: Violation[] = [];
  const texts = scene.items.filter((i): i is SText => i.t === 'text');
  const boxes = scene.items.filter(i => i.t === 'rect' && i.role === 'box') as Extract<SItem, { t: 'rect' }>[];
  const dots = scene.items.filter(i => i.t === 'dot') as Extract<SItem, { t: 'dot' }>[];
  const paths = scene.items.filter(i => i.t === 'path') as Extract<SItem, { t: 'path' }>[];
  const tb = texts.map(textBox);

  for (const p of paths) for (let i = 1; i < p.pts.length; i++) {
    const [a, b] = [p.pts[i - 1], p.pts[i]];
    if (Math.abs(a[0] - b[0]) > 0.5 && Math.abs(a[1] - b[1]) > 0.5) {
      out.push({ rule: 'diagonal', what: `${p.role}${p.id ? ` ${p.id}` : ''} runs diagonally from ${a.map(Math.round)} to ${b.map(Math.round)}` });
      break;
    }
  }
  for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
    if (meets(tb[i], tb[j])) out.push({ rule: 'overlap', what: `text ${name(texts[i])} overlaps text ${name(texts[j])}` });
  }
  for (let i = 0; i < texts.length; i++) {
    const t = texts[i];
    for (const b of boxes) {
      if (b.id !== undefined && b.id === t.owner) continue;
      if (meets(tb[i], b)) out.push({ rule: 'overlap', what: `text ${name(t)} overlaps box ${b.id ?? '(unnamed)'}` });
    }
    for (const d of dots) {
      if (d.id !== undefined && d.id === t.owner) continue;
      if (meets(tb[i], { x: d.cx - d.r, y: d.cy - d.r, w: 2 * d.r, h: 2 * d.r })) out.push({ rule: 'overlap', what: `text ${name(t)} overlaps dot ${d.id ?? ''}` });
    }
    if (t.backed) continue;
    for (const p of paths) {
      if (p.owner !== undefined && p.owner === t.owner) continue;
      for (let k = 1; k < p.pts.length; k++) {
        if (segmentHits(tb[i], p.pts[k - 1], p.pts[k])) { out.push({ rule: 'crossing', what: `text ${name(t)} crosses ${p.role}${p.id ? ` ${p.id}` : ''}` }); break; }
      }
    }
  }
  const view: Box = { x: 0, y: 0, w: scene.W, h: scene.H };
  const outside = (b: Box, what: string) => { if (!inside(b, view)) out.push({ rule: 'bounds', what: `${what} lies outside the ${scene.W}x${scene.H} viewBox` }); };
  texts.forEach((t, i) => outside(tb[i], `text ${name(t)}`));
  for (const b of boxes) outside(b, `box ${b.id ?? ''}`);
  for (const d of dots) outside({ x: d.cx - d.r, y: d.cy - d.r, w: 2 * d.r, h: 2 * d.r }, `dot ${d.id ?? ''}`);
  for (const it of scene.items) if (it.t === 'icon') outside({ x: it.x, y: it.y, w: ICON_SIZE, h: ICON_SIZE }, `icon ${it.name}`);
  for (const p of paths) for (const [x, y] of p.pts) if (x < -EPS || y < -EPS || x > scene.W + EPS || y > scene.H + EPS) { outside({ x, y, w: 0, h: 0 }, `${p.role} point`); break; }
  return out;
}
