import { ICON_GAP, ICON_SIZE, LINE, stroke, text, type Measure, type Role, type SItem } from '../scene';
import { isText, TONES, type Kind } from './types';

const MIN_LAYERS = 2, MAX_LAYERS = 7;
const PAD_X = 24, PAD_Y = 18, MIN_H = 60, MIN_W = 640, TAG_GAP = 24, MID_GAP = 56;
const TITLE_MAX = 300, DETAIL_MAX = 340, AXIS_GAP = 28;
// Toned outlines sit inside the band so neighbours never share a stroke with each other or the frame.
const INSET = 3;
const GENERATED = /^layer-\d+$/;

const layerList = (g: any): any[] => Array.isArray(g.layers) ? g.layers : [];
const layerId = (l: any, i: number): string => isText(l?.id) ? l.id : `layer-${i + 1}`;

/** Greedy word wrap by measured width; a single word wider than max keeps its own line. */
function wrap(s: string, role: Role, max: number, m: Measure): string[] {
  const lines: string[] = [];
  let cur = '';
  for (const word of s.trim().split(/\s+/)) {
    const next = cur ? `${cur} ${word}` : word;
    if (cur && m(next, role).w > max) { lines.push(cur); cur = word; }
    else cur = next;
  }
  if (cur) lines.push(cur);
  return lines;
}

/** Splits "abstraction ↑" into its label and direction; no glyph means up. */
function parseAxis(s: string): { label: string; up: boolean } {
  const hit = s.match(/\s*([↑↓])\s*$/);
  return { label: (hit ? s.slice(0, hit.index) : s).trim(), up: hit?.[1] !== '↓' };
}

export const layers: Kind = {
  check(g) {
    const errors: string[] = [], warns: string[] = [];
    if (!Array.isArray(g.layers)) return { errors: ['layers must be an array of 2 to 7 layers, top to bottom'], warns };
    const ls = g.layers as any[];
    if (ls.length < MIN_LAYERS) errors.push(`layers needs at least ${MIN_LAYERS} entries, found ${ls.length}; one layer is a box, not a stack`);
    if (ls.length > MAX_LAYERS) warns.push(`${ls.length} layers; above ${MAX_LAYERS} a stack stops reading at a glance. Merge layers or split the stack.`);
    const seen = new Set<string>();
    ls.forEach((l, i) => {
      const at = `layers[${i}]`;
      if (!l || typeof l !== 'object' || Array.isArray(l)) { errors.push(`${at} must be an object with a title`); return; }
      if (!isText(l.title)) errors.push(`${at} needs a title`);
      if (l.id !== undefined) {
        if (!isText(l.id)) errors.push(`${at}: id must be a nonempty string`);
        else if (seen.has(l.id)) errors.push(`${at}: id ${l.id} is duplicated`);
        else if (GENERATED.test(l.id) && l.id !== `layer-${i + 1}`) errors.push(`${at}: id ${l.id} clashes with the id generated for another layer; pick another`);
      }
      seen.add(layerId(l, i));
      for (const key of ['tag', 'detail'] as const) if (l[key] !== undefined && !isText(l[key])) errors.push(`${at}: ${key} must be a nonempty string`);
      if (l.tone !== undefined && !TONES.has(l.tone)) errors.push(`${at}: unknown tone ${JSON.stringify(l.tone)}; use one of ${[...TONES].join(', ')}`);
    });
    if (g.axis !== undefined && !isText(g.axis)) errors.push('axis must be a nonempty string such as "abstraction ↑"');
    const accents = ls.filter(l => l?.tone === 'accent').length;
    if (accents > 1) warns.push(`${accents} accent layers; keep one, the layer the reader must notice.`);
    return { errors, warns };
  },

  ids: g => layerList(g).map(l => l?.id).filter(isText),

  layout(g, m) {
    const ls = layerList(g);
    const rows = ls.map((l, i) => ({
      id: layerId(l, i), tone: l.tone as string | undefined, icon: l.icon as string | undefined,
      tag: isText(l.tag) ? l.tag : undefined,
      title: wrap(l.title, 'title', TITLE_MAX, m),
      detail: isText(l.detail) ? wrap(l.detail, 'detail', DETAIL_MAX, m) : [],
    }));
    const widest = (lines: string[], role: Role) => Math.max(0, ...lines.map(s => m(s, role).w));
    const tagW = Math.max(0, ...rows.map(r => r.tag ? m(r.tag, 'group').w : 0));
    // One icon column for every row, so titles start at the same x whether or not their layer has an icon.
    const iconCol = rows.some(r => r.icon) ? ICON_SIZE + ICON_GAP : 0;
    const titleW = iconCol + Math.max(...rows.map(r => widest(r.title, 'title')));
    const detailW = Math.max(0, ...rows.map(r => widest(r.detail, 'detail')));
    const titleX = PAD_X + (tagW ? tagW + TAG_GAP : 0);
    const W = Math.ceil(Math.max(MIN_W, titleX + titleW + (detailW ? MID_GAP + detailW : 0) + PAD_X));
    const contentH = Math.max(...rows.map(r => Math.max(r.title.length * LINE.title, r.detail.length * LINE.detail, r.icon ? ICON_SIZE : 0)));
    const H = Math.max(MIN_H, Math.ceil(contentH + 2 * PAD_Y));
    const total = H * rows.length;

    const fills: SItem[] = [{ t: 'rect', x: 0, y: 0, w: W, h: total, rx: 6, role: 'band', style: 'fill:var(--ground)' }];
    const lines: SItem[] = [], boxes: SItem[] = [], labels: SItem[] = [];
    // Baselines for a block of n lines centred on cy, matching textBox's top = baseline - lineHeight + 5.
    const block = (n: number, lh: number, cy: number) => Array.from({ length: n }, (_, k) => cy - (n * lh) / 2 + (k + 1) * lh - 5);
    rows.forEach((r, i) => {
      const y = i * H, cy = y + H / 2, focal = r.tone === 'accent';
      const toned = !!r.tone && r.tone !== 'ink';
      const inner = { x: INSET, y: y + INSET, w: W - 2 * INSET, h: H - 2 * INSET, rx: 4 };
      if (focal) fills.push({ t: 'rect', ...inner, role: 'backing', style: 'fill:var(--accent-soft)' });
      if (i > 0) lines.push({ t: 'path', pts: [[0, y], [W, y]], r: 0, role: 'divider', style: 'stroke:var(--line);stroke-width:1' });
      if (toned) boxes.push({ t: 'rect', ...inner, role: 'box', id: r.id, style: `fill:none;stroke:${stroke(r.tone)};stroke-width:${focal ? 2 : 1.4}` });
      else boxes.push({ t: 'rect', x: 0, y, w: W, h: H, role: 'box', id: r.id, style: 'fill:none;stroke:none' });
      if (r.tag) labels.push(text(PAD_X, block(1, LINE.group, cy)[0], r.tag, 'group', m, { anchor: 'start', owner: r.id }, focal ? 'var(--accent)' : 'var(--ink-3)'));
      const tx = titleX + iconCol;
      const tb = block(r.title.length, LINE.title, cy);
      if (r.icon) labels.push({ t: 'icon', x: titleX, y: tb[0] - ICON_SIZE + 4, name: r.icon, owner: r.id });
      r.title.forEach((s, k) => labels.push(text(tx, tb[k], s, 'title', m, { anchor: 'start', owner: r.id }, 'var(--ink)')));
      const db = block(r.detail.length, LINE.detail, cy);
      r.detail.forEach((s, k) => labels.push(text(W - PAD_X, db[k], s, 'detail', m, { anchor: 'end', owner: r.id })));
    });
    const frame: SItem = { t: 'rect', x: 0, y: 0, w: W, h: total, rx: 6, role: 'band', style: `fill:none;stroke:${stroke()};stroke-width:1.4` };

    const axis: SItem[] = [];
    if (isText(g.axis)) {
      const { label, up } = parseAxis(g.axis);
      const colW = label ? m(label, 'group').w : 12, ax = -AXIS_GAP - colW / 2, cy = total / 2, half = LINE.group / 2;
      const top: [number, number] = [ax, 4], bottom: [number, number] = [ax, total - 4];
      const style = 'stroke:var(--ink-3);stroke-width:1.2';
      if (!label) axis.push({ t: 'path', pts: up ? [bottom, top] : [top, bottom], r: 0, role: 'axis', marker: 'arrow', style });
      else {
        const above: [number, number] = [ax, cy - half - 8], below: [number, number] = [ax, cy + half + 8];
        axis.push({ t: 'path', pts: up ? [above, top] : [below, bottom], r: 0, role: 'axis', marker: 'arrow', style });
        axis.push({ t: 'path', pts: up ? [bottom, below] : [top, above], r: 0, role: 'axis', style });
        axis.push(text(ax, cy - half + LINE.group - 5, label, 'group', m, { anchor: 'middle' }));
      }
    }
    return [...fills, ...lines, frame, ...boxes, ...axis, ...labels];
  },
};
