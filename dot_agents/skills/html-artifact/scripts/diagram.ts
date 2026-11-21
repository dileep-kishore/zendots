import { resolve } from 'node:path';
import { ICON_NAMES } from './diagram/icons';
import { KINDS } from './diagram/kinds';
import { NOTE_LINES, NOTE_MAX, wrapNote } from './diagram/notes';
import { ensureFonts, ensureNoteFont, ensureRuntime } from './runtime';

const paths = process.argv.slice(2);
if (paths.length !== 2) {
  console.error('Usage: bun run scripts/diagram.ts SPEC.json OUTPUT_PREFIX');
  process.exit(1);
}
const [input, output] = paths.map(path => resolve(path));

const TONES = new Set(['ink', 'blue', 'green', 'teal', 'peach', 'yellow', 'red', 'accent']);
const LAYOUTS = new Set(['layered', 'ring', 'ring-v']);
const DIRECTIONS = new Set(['RIGHT', 'DOWN', 'LEFT', 'UP']);
const KIND_NAMES = ['graph', ...Object.keys(KINDS)];
const text = (v: unknown) => typeof v === 'string' && v.trim().length > 0;
// A collection that is present but not an array is reported once and then skipped, never iterated.
const list = (g: any, key: string, errors: string[]): any[] => {
  if (g[key] === undefined) return [];
  if (Array.isArray(g[key])) return g[key];
  errors.push(`${key} must be an array`);
  return [];
};

function validateGraph(g: any): string[] {
  const errors: string[] = [];
  if (g.layout !== undefined && !LAYOUTS.has(g.layout)) errors.push(`layout must be one of ${[...LAYOUTS].join(', ')}`);
  if (g.direction !== undefined && !DIRECTIONS.has(g.direction)) errors.push(`direction must be one of ${[...DIRECTIONS].join(', ')}`);
  for (const key of ['nodeGap', 'layerGap']) if (g[key] !== undefined && !(Number.isFinite(g[key]) && g[key] > 0)) errors.push(`${key} must be a positive number`);
  const groups = new Set<string>();
  for (const grp of list(g, 'groups', errors)) {
    if (!text(grp?.id) || groups.has(grp.id)) errors.push(`group id missing or duplicated: ${grp?.id}`);
    if (!text(grp?.label)) errors.push(`group ${grp?.id} needs a label`);
    if (grp?.tone !== undefined && !TONES.has(grp.tone)) errors.push(`group ${grp.id}: unknown tone ${grp.tone}`);
    groups.add(grp?.id);
  }
  const nodeList: any[] = Array.isArray(g.nodes) ? g.nodes : [];
  if (!nodeList.length) errors.push('nodes must be a nonempty array');
  const nodes = new Set<string>();
  for (const n of nodeList) {
    if (!text(n?.id) || nodes.has(n.id)) errors.push(`node id missing or duplicated: ${n?.id}`);
    else if (n.id.startsWith('group:')) errors.push(`node id ${n.id}: the group: prefix is reserved for groups`);
    if (!text(n?.title)) errors.push(`node ${n?.id} needs a title`);
    if (n?.group !== undefined && !groups.has(n.group)) errors.push(`node ${n.id}: unknown group ${n.group}`);
    if (n?.tone !== undefined && !TONES.has(n.tone)) errors.push(`node ${n.id}: unknown tone ${n.tone}`);
    nodes.add(n?.id);
  }
  if (g.layout?.startsWith('ring') && (Array.isArray(g.groups) ? g.groups : []).some((grp: any) => !nodeList.some((n: any) => n?.group === grp?.id))) errors.push('every group in a ring layout needs at least one node');
  const edgeList: any[] = Array.isArray(g.edges) ? g.edges : [];
  if (!Array.isArray(g.edges)) errors.push('edges must be an array; use [] for a diagram without arrows');
  if (g.layout?.startsWith('ring') && (g.nodeGap !== undefined || g.layerGap !== undefined)) errors.push('nodeGap and layerGap apply only to the layered layout');
  for (const e of edgeList) {
    if (!nodes.has(e?.from) || !nodes.has(e?.to)) errors.push(`edge ${e?.from} -> ${e?.to} names a missing node`);
  }
  return errors;
}

// Every id a spec declares, in any collection; duplicates make a note target ambiguous.
function declaredIds(g: any): string[] {
  if ((g.kind ?? 'graph') !== 'graph') return KINDS[g.kind].ids(g);
  return [...(Array.isArray(g.nodes) ? g.nodes : []), ...(Array.isArray(g.groups) ? g.groups : [])].map((x: any) => x?.id).filter(text);
}

function validate(g: any): { errors: string[]; warns: string[] } {
  if (!g || typeof g !== 'object' || Array.isArray(g)) return { errors: ['spec must be a JSON object'], warns: [] };
  const errors: string[] = [], warns: string[] = [];
  if (!text(g.id) || !/^[a-z][a-z0-9-]*$/.test(g.id)) errors.push('id must be a lowercase slug, unique on the page (it prefixes SVG ids)');
  if (!text(g.alt)) errors.push('alt must describe the diagram for screen readers');
  const kind = g.kind ?? 'graph';
  if (!KIND_NAMES.includes(kind)) return { errors: [...errors, `kind must be one of ${KIND_NAMES.join(', ')}`], warns };
  if (kind === 'graph') errors.push(...validateGraph(g));
  else { const r = KINDS[kind].check(g); errors.push(...r.errors); warns.push(...r.warns); }
  for (const item of list(g, 'legend', errors)) {
    if (!Array.isArray(item) || !text(item[0]) || !(TONES.has(item[1]) || item[1] === 'dashed')) errors.push(`legend entries are [text, tone or "dashed"]: ${JSON.stringify(item)}`);
  }
  if (!errors.length) {
    // Graph specs may reuse an id for a node and its group; that is ambiguous only as a note target.
    const ids = declaredIds(g), count = new Map<string, number>();
    for (const i of ids) count.set(i, (count.get(i) ?? 0) + 1);
    const notes = list(g, 'notes', errors);
    if (notes.length > NOTE_MAX) errors.push(`notes: at most ${NOTE_MAX} callouts per diagram, found ${notes.length}`);
    notes.forEach((n: any, i: number) => {
      if (!text(n?.text)) errors.push(`notes[${i}] needs text`);
      else if (wrapNote(n.text).length > NOTE_LINES) errors.push(`notes[${i}]: text wraps to more than ${NOTE_LINES} lines of about 28 characters; shorten it`);
      const c = count.get(n?.target) ?? 0;
      if (!c) errors.push(`notes[${i}]: target ${n?.target} is not an id in this spec`);
      else if (c > 1) errors.push(`notes[${i}]: target ${n.target} names more than one element; give them distinct ids`);
    });
  }
  const iconHosts = kind === 'graph' ? (Array.isArray(g.nodes) ? g.nodes : []) : kind === 'sequence' ? (Array.isArray(g.actors) ? g.actors : []) : kind === 'swimlane' ? (Array.isArray(g.steps) ? g.steps : []) : kind === 'layers' ? (Array.isArray(g.layers) ? g.layers : []) : [];
  for (const h of iconHosts) if (h?.icon !== undefined && !ICON_NAMES.includes(h.icon)) errors.push(`${h.id ?? h.title}: unknown icon ${JSON.stringify(h.icon)}; known icons: ${ICON_NAMES.join(', ')}`);
  return { errors, warns };
}

let runtime = '';
try {
  const graph = await Bun.file(input).json();
  const { errors, warns } = validate(graph);
  if (errors.length) throw new Error(`Invalid diagram spec ${input}:\n- ${errors.join('\n- ')}`);
  for (const w of warns) console.log(`WARN: ${w}`);
  if ((graph.kind ?? 'graph') === 'graph') {
    if (graph.nodes.length > 12) console.log(`WARN: ${graph.nodes.length} nodes; above about 9 a diagram stops reading at a glance. Split it into an overview and parts.`);
    const accents = graph.nodes.filter((n: any) => n.tone === 'accent').length;
    if (accents > 1) console.log(`WARN: ${accents} accent nodes; keep one, the node the reader must notice.`);
  }
  const fonts = await ensureFonts();
  const env: Record<string, string> = { DIAGRAM_FONTS: fonts };
  if (graph.notes?.length) env.DIAGRAM_NOTE_FONT = await ensureNoteFont();
  const rt = await ensureRuntime();
  runtime = rt.dir;
  rt.run(['run', 'export.ts', input, output], env);
} catch (error) {
  // Exit 3 is a rejected layout: export.ts has already printed why, and the runtime is not at fault.
  const rejected = (error as { status?: number }).status === 3;
  if (!rejected) console.error(error instanceof Error ? error.message : error);
  if (runtime && !rejected) console.error(`Diagram runtime retained for diagnosis: ${runtime}`);
  process.exitCode = 1;
}
