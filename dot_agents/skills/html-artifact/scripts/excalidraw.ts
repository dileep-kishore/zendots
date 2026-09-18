import { execFileSync } from 'node:child_process';
import { copyFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const args = process.argv.slice(2);
if (args.length !== 2) {
  console.error('Usage: bun run scripts/excalidraw.ts INPUT.json OUTPUT_PREFIX');
  process.exit(1);
}
const [input, output] = args.map(path => resolve(path));
const runtime = mkdtempSync(join(tmpdir(), 'html-artifact-excalidraw-'));
for (const name of ['package.json', 'bun.lock', 'export.ts', 'browser.ts']) {
  copyFileSync(join(import.meta.dir, 'excalidraw', name), join(runtime, name));
}
try {
  const options = { cwd: runtime, stdio: 'inherit' as const, timeout: 300_000 };
  execFileSync(process.execPath, ['install', '--frozen-lockfile', '--ignore-scripts'], options);
  execFileSync(process.execPath, ['node_modules/playwright/cli.js', 'install', 'chromium', '--only-shell'], options);
  execFileSync(process.execPath, ['run', 'export.ts', input, output], options);
  rmSync(runtime, { recursive: true });
} catch (error) {
  // Retain the workspace on failure, including when a child exceeded its timeout.
  console.error(`Excalidraw export failed. Diagnostic workspace: ${runtime}`);
  process.exitCode = 1;
}
