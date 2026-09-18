import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmdirSync, writeFileSync, unlinkSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';

const args = process.argv.slice(2);
if (args.length !== 2) {
  console.error('Usage: bun run scripts/excalidraw.ts INPUT.json OUTPUT_PREFIX');
  process.exit(1);
}
const [input, output] = args.map(path => resolve(path));
const source = join(import.meta.dir, 'excalidraw');
const files = ['package.json', 'bun.lock', 'export.ts', 'browser.ts'];
const hash = createHash('sha256').update(`${Bun.version}:${process.platform}:${process.arch}`);
for (const name of files) hash.update(name).update(readFileSync(join(source, name)));
const cache = join(process.env.XDG_CACHE_HOME || join(homedir(), '.cache'), 'html-artifact', 'excalidraw');
const runtime = join(cache, hash.digest('hex').slice(0, 16));
const ready = join(runtime, '.ready');
const lock = `${runtime}.lock`;
const options = {
  cwd: runtime, stdio: 'inherit' as const, timeout: 300_000,
  env: { ...process.env, PLAYWRIGHT_BROWSERS_PATH: join(cache, 'browsers') },
};
try {
  mkdirSync(cache, { recursive: true });
  const deadline = Date.now() + 300_000;
  while (!existsSync(ready)) {
    try {
      mkdirSync(lock);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'EEXIST') throw error;
      if (Date.now() >= deadline) throw new Error(`Timed out waiting for setup. Check the process in ${lock}/pid before removing a stale lock.`);
      await delay(250);
      continue;
    }
    try {
      writeFileSync(join(lock, 'pid'), String(process.pid));
      // A previous initializer may have finished just before we acquired the lock.
      if (!existsSync(ready)) {
        console.log(`Preparing shared Excalidraw runtime: ${runtime}`);
        mkdirSync(runtime, { recursive: true });
        for (const name of files) copyFileSync(join(source, name), join(runtime, name));
        execFileSync(process.execPath, ['install', '--frozen-lockfile', '--ignore-scripts'], options);
        execFileSync(process.execPath, ['node_modules/playwright/cli.js', 'install', 'chromium', '--only-shell'], options);
        writeFileSync(ready, 'ready\n');
      }
    } finally {
      if (existsSync(join(lock, 'pid'))) unlinkSync(join(lock, 'pid'));
      rmdirSync(lock);
    }
  }
  console.log(`Using shared Excalidraw runtime: ${runtime}`);
  execFileSync(process.execPath, ['run', 'export.ts', input, output], options);
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  console.error(`Excalidraw runtime retained for diagnosis: ${runtime}`);
  process.exitCode = 1;
}
