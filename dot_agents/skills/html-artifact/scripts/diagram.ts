import { resolve } from 'node:path';
import { ensureFonts, ensureRuntime } from './runtime';

const paths = process.argv.slice(2);
if (paths.length !== 2) {
  console.error('Usage: bun run scripts/diagram.ts SPEC.json OUTPUT_PREFIX');
  process.exit(1);
}
const [input, output] = paths.map(path => resolve(path));

const TONES = new Set(['ink', 'blue', 'green', 'teal', 'peach', 'yellow', 'red', 'accent']);
const LAYOUTS = new Set(['layered', 'ring', 'ring-v']);
const DIRECTIONS = new Set(['RIGHT', 'DOWN', 'LEFT', 'UP']);

function validate(g: any): string[] {
  const errors: string[] = [];
  const text = (v: unknown) => typeof v === 'string' && v.trim().length > 0;
  if (!g || typeof g !== 'object') return ['spec must be a JSON object'];
  if (!text(g.id) || !/^[a-z][a-z0-9-]*$/.test(g.id)) errors.push('id must be a lowercase slug, unique on the page (it prefixes SVG ids)');
  if (!text(g.alt)) errors.push('alt must describe the diagram for screen readers');
  if (g.layout !== undefined && !LAYOUTS.has(g.layout)) errors.push(`layout must be one of ${[...LAYOUTS].join(', ')}`);
  if (g.direction !== undefined && !DIRECTIONS.has(g.direction)) errors.push(`direction must be one of ${[...DIRECTIONS].join(', ')}`);
  for (const key of ['nodeGap', 'layerGap']) if (g[key] !== undefined && !(Number.isFinite(g[key]) && g[key] > 0)) errors.push(`${key} must be a positive number`);
  const groups = new Set<string>();
  for (const grp of g.groups ?? []) {
    if (!text(grp?.id) || groups.has(grp.id)) errors.push(`group id missing or duplicated: ${grp?.id}`);
    if (!text(grp?.label)) errors.push(`group ${grp?.id} needs a label`);
    if (grp?.tone !== undefined && !TONES.has(grp.tone)) errors.push(`group ${grp.id}: unknown tone ${grp.tone}`);
    groups.add(grp?.id);
  }
  if (!Array.isArray(g.nodes) || !g.nodes.length) errors.push('nodes must be a nonempty array');
  const nodes = new Set<string>();
  for (const n of g.nodes ?? []) {
    if (!text(n?.id) || nodes.has(n.id)) errors.push(`node id missing or duplicated: ${n?.id}`);
    else if (n.id.startsWith('group:')) errors.push(`node id ${n.id}: the group: prefix is reserved for groups`);
    if (!text(n?.title)) errors.push(`node ${n?.id} needs a title`);
    if (n?.group !== undefined && !groups.has(n.group)) errors.push(`node ${n.id}: unknown group ${n.group}`);
    if (n?.tone !== undefined && !TONES.has(n.tone)) errors.push(`node ${n.id}: unknown tone ${n.tone}`);
    nodes.add(n?.id);
  }
  if (g.layout?.startsWith('ring') && (g.groups ?? []).some((grp: any) => !(g.nodes ?? []).some((n: any) => n.group === grp.id))) errors.push('every group in a ring layout needs at least one node');
  if (!Array.isArray(g.edges)) errors.push('edges must be an array; use [] for a diagram without arrows');
  if (g.layout?.startsWith('ring') && (g.nodeGap !== undefined || g.layerGap !== undefined)) errors.push('nodeGap and layerGap apply only to the layered layout');
  for (const e of g.edges ?? []) {
    if (!nodes.has(e?.from) || !nodes.has(e?.to)) errors.push(`edge ${e?.from} -> ${e?.to} names a missing node`);
  }
  for (const item of g.legend ?? []) {
    if (!Array.isArray(item) || !text(item[0]) || !(TONES.has(item[1]) || item[1] === 'dashed')) errors.push(`legend entries are [text, tone or "dashed"]: ${JSON.stringify(item)}`);
  }
  return errors;
}

let runtime = '';
try {
  const graph = await Bun.file(input).json();
  const errors = validate(graph);
  if (errors.length) throw new Error(`Invalid diagram spec ${input}:\n- ${errors.join('\n- ')}`);
  if (graph.nodes.length > 12) console.log(`WARN: ${graph.nodes.length} nodes; above about 9 a diagram stops reading at a glance. Split it into an overview and parts.`);
  const accents = graph.nodes.filter((n: any) => n.tone === 'accent').length;
  if (accents > 1) console.log(`WARN: ${accents} accent nodes; keep one, the node the reader must notice.`);
  const fonts = await ensureFonts();
  const rt = await ensureRuntime();
  runtime = rt.dir;
  rt.run(['run', 'export.ts', input, output], { DIAGRAM_FONTS: fonts });
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  if (runtime) console.error(`Diagram runtime retained for diagnosis: ${runtime}`);
  process.exitCode = 1;
}
