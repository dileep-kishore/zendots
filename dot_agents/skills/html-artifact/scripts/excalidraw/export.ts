import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';

const [input, prefix] = process.argv.slice(2);
const file = Bun.file(input);
if (file.size > 2_000_000) throw new Error('Diagram input exceeds 2 MB');
const diagram = await file.json();
if (!diagram || typeof diagram.alt !== 'string' || !diagram.alt.trim() || !Array.isArray(diagram.elements) || !diagram.elements.length) {
  throw new Error('Expected { alt: "description", elements: [Excalidraw element skeletons] }');
}
const types = new Set(['rectangle', 'ellipse', 'diamond', 'text', 'arrow', 'line']);
const ids = new Set<string>();
for (const [index, el] of diagram.elements.entries()) {
  if (!el || !types.has(el.type) || !Number.isFinite(el.x) || !Number.isFinite(el.y)) throw new Error('Every element needs a supported type and finite x/y');
  if (el.type === 'text' && typeof el.text !== 'string') throw new Error('Text elements need a string text field');
  if (el.label != null && typeof el.label.text !== 'string') throw new Error('Element labels need a string text field');
  for (const key of ['width', 'height', 'fontSize']) {
    if (el[key] !== undefined && (!Number.isFinite(el[key]) || el[key] < 0)) throw new Error(`Invalid ${key}`);
  }
  const id = el.id ?? `element-${index}`;
  if (typeof id !== 'string' || !id || ids.has(id)) throw new Error('Element IDs must be unique nonempty strings');
  ids.add(id);
}
for (const el of diagram.elements) {
  for (const end of [el.start, el.end]) {
    if (end?.id && !ids.has(end.id)) throw new Error(`Arrow references missing element: ${end.id}`);
  }
}
const bundle = await Bun.build({ entrypoints: [join(import.meta.dir, 'browser.ts')], target: 'browser', minify: true, define: { 'process.env.NODE_ENV': '"production"' } });
if (!bundle.success) throw new Error(bundle.logs.join('\n'));
const fonts = join(import.meta.dir, 'node_modules/@excalidraw/excalidraw/dist/prod/fonts');
const assets = new Map<string, string>();
for await (const name of new Bun.Glob('**/*.woff2').scan(fonts)) assets.set(`/fonts/${name}`, join(fonts, name));
const server = Bun.serve({ hostname: '127.0.0.1', port: 0, fetch(request) {
  const path = new URL(request.url).pathname;
  if (path === '/') return new Response('<!doctype html><meta charset="utf-8"><script>window.EXCALIDRAW_ASSET_PATH="/";</script><script type="module" src="/bundle.js"></script>', { headers: { 'content-type': 'text/html' } });
  if (path === '/bundle.js') return new Response(bundle.outputs[0], { headers: { 'content-type': 'text/javascript' } });
  if (assets.has(path)) return new Response(Bun.file(assets.get(path)!));
  return new Response('Not found', { status: 404 });
} });
let browser: Awaited<ReturnType<typeof chromium.launch>> | undefined;
let timedOut = false;
const deadline = setTimeout(() => { timedOut = true; void browser?.close(); server.stop(true); }, 60_000);
try {
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('pageerror', error => console.error(error.message));
  const origin = server.url.origin;
  await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  await page.goto(origin);
  await page.waitForFunction(() => typeof window.exportDiagram === 'function');
  const result = await page.evaluate(data => window.exportDiagram(data), diagram);
  for (const svg of [result.light, result.dark]) {
    if (!svg.startsWith('<svg') || (svg.includes('<text') && !svg.includes('data:font/'))) throw new Error('Export is missing SVG or embedded fonts');
  }
  const escape = (value: string) => value.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  const images = ['<div class="excalidraw-images" tabindex="0" role="group" aria-label="Scrollable diagram">'];
  await mkdir(dirname(prefix), { recursive: true });
  for (const mode of ['light', 'dark'] as const) {
    await writeFile(`${prefix}.${mode}.svg`, result[mode]);
    images.push(`<img class="excalidraw-${mode}" src="data:image/svg+xml;base64,${Buffer.from(result[mode]).toString('base64')}" alt="${escape(diagram.alt)}">`);
  }
  images.push('</div>');
  const fragment = images.join('\n') + '\n';
  await writeFile(`${prefix}.images.html`, fragment);
  await writeFile(`${prefix}.excalidraw`, result.scene + '\n');
  console.log(`Exported ${prefix}.{light.svg,dark.svg,images.html,excalidraw}`);
  console.log(`Embedded diagram: ${Buffer.byteLength(fragment)} bytes (page limit: 2,000,000 bytes)`);
} catch (error) {
  if (timedOut) throw new Error('Excalidraw export timed out after 60 seconds', { cause: error });
  throw error;
} finally {
  clearTimeout(deadline);
  await browser?.close();
  server.stop(true);
}
