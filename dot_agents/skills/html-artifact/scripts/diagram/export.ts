import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';

// Usage (from diagram.ts): bun run export.ts SPEC.json PREFIX; DIAGRAM_FONTS names the font directory.
const [input, prefix] = process.argv.slice(2);
const graph = await Bun.file(input).json();
const opts = {
  layout: graph.layout || 'layered', dir: graph.direction || '', placement: 'NETWORK_SIMPLEX',
  layerGap: String(graph.layerGap ?? 56), nodeGap: String(graph.nodeGap ?? 32),
};
const fontDir = process.env.DIAGRAM_FONTS!;
const bundle = await Bun.build({ entrypoints: [join(import.meta.dir, 'browser.ts')], target: 'browser', minify: true });
if (!bundle.success) throw new Error(bundle.logs.join('\n'));
const assets = new Map<string, string>([['/fonts/display.ttf', join(fontDir, 'display.ttf')], ['/fonts/mono.ttf', join(fontDir, 'mono.ttf')]]);
const noteFont = process.env.DIAGRAM_NOTE_FONT;
if (noteFont) assets.set('/fonts/note.ttf', noteFont);
const faces = '<style>@font-face{font-family:"Diagram Display";src:url(/fonts/display.ttf);font-weight:200 900}@font-face{font-family:"Diagram Mono";src:url(/fonts/mono.ttf);font-weight:400 700}'
  + (noteFont ? '@font-face{font-family:"Diagram Note";src:url(/fonts/note.ttf);font-weight:400 700;font-style:italic}' : '') + '</style>';
const server = Bun.serve({ hostname: '127.0.0.1', port: 0, fetch(request) {
  const path = new URL(request.url).pathname;
  if (path === '/') return new Response(`<!doctype html><meta charset="utf-8">${faces}<script type="module" src="/bundle.js"></script>`, { headers: { 'content-type': 'text/html' } });
  if (path === '/bundle.js') return new Response(bundle.outputs[0], { headers: { 'content-type': 'text/javascript' } });
  if (assets.has(path)) return new Response(Bun.file(assets.get(path)!));
  return new Response('Not found', { status: 404 });
} });
let browser: Awaited<ReturnType<typeof chromium.launch>> | undefined;
let rejected = false;
const deadline = setTimeout(() => { void browser?.close(); server.stop(true); console.error('Diagram export timed out after 60 seconds'); process.exit(1); }, 60_000);
try {
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('pageerror', error => console.error(error.message));
  const origin = server.url.origin;
  await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  await page.goto(origin);
  await mkdir(dirname(prefix), { recursive: true });
  await page.waitForFunction(() => typeof (window as any).renderDiagram === 'function');
  let res;
  try {
    res = await page.evaluate(([g, o]) => (window as any).renderDiagram(g, o), [graph, opts] as const);
  } catch (error) {
    // Layouts mark the specs they cannot draw with [spec]; report those as a rejection, and anything else as a crash.
    const message = error instanceof Error ? error.message : String(error);
    const at = message.indexOf('[spec] ');
    if (at < 0) throw error;
    throw Object.assign(new Error(message.slice(at + 7).split('\n    at ')[0]), { spec: true });
  }
  const found = res.violations.map((v: { rule: string; what: string }) => `${v.rule}: ${v.what}`);
  if (res.strict && found.length) {
    console.error(`Layout self-check failed for ${graph.kind} diagram ${graph.id}; nothing was written:\n- ${found.join('\n- ')}`);
    rejected = true;
  } else {
    // Inline overflow keeps the fragment scrolling on pages copied from a template older than the .diagram rule.
    const fragment = `<div class="diagram" style="overflow-x:auto" tabindex="0" role="group" aria-label="Scrollable diagram">\n${res.svg}\n</div>\n`;
    await writeFile(`${prefix}.diagram.html`, fragment);
    console.log(`Exported ${prefix}.diagram.html: viewBox ${res.W}x${res.H}, ${Buffer.byteLength(fragment)} bytes`);
    if (res.W > 1100) console.log(`WARN: drawing is ${res.W} units wide; above about 1100 its labels shrink below reading size. Try direction DOWN, layout ring-v, or split the diagram.`);
    for (const f of found) console.log(`WARN: layout self-check: ${f}`);
  }
} catch (error) {
  if (!(error as { spec?: boolean }).spec) throw error;
  console.error((error as Error).message);
  rejected = true;
} finally {
  clearTimeout(deadline);
  await browser?.close();
  server.stop(true);
}
// Exit 3 tells diagram.ts the spec was rejected, not that the runtime broke.
if (rejected) process.exit(3);
