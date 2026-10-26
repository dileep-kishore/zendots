import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, renameSync, rmdirSync, unlinkSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';

const source = join(import.meta.dir, 'diagram');
const files = ['package.json', 'bun.lock', 'layout.ts', 'browser.ts', 'export.ts'];
const cache = join(process.env.XDG_CACHE_HOME || join(homedir(), '.cache'), 'html-artifact', 'diagram');
// The same pinned faces the template's @font-face rules load, so measured widths match the page.
const FONTS = {
  'display.ttf': 'https://cdn.jsdelivr.net/gh/supernotes/sn-pro@e025ac475535/fonts/variable/SNPro%5Bwght%5D.ttf',
  'mono.ttf': 'https://cdn.jsdelivr.net/gh/iaolo/iA-Fonts@f32c04c3058a/iA%20Writer%20Mono/Variable/iAWriterMonoV.ttf',
};

export interface Runtime { dir: string; run: (args: string[], env?: Record<string, string>) => void }

/** Installs the locked packages and Chromium once per revision, then returns a runner inside that runtime. */
export async function ensureRuntime(): Promise<Runtime> {
  const hash = createHash('sha256').update(`${Bun.version}:${process.platform}:${process.arch}`);
  for (const name of files) hash.update(name).update(readFileSync(join(source, name)));
  const dir = join(cache, hash.digest('hex').slice(0, 16));
  const ready = join(dir, '.ready');
  const lock = `${dir}.lock`;
  const options = {
    cwd: dir, stdio: 'inherit' as const, timeout: 300_000,
    env: { ...process.env, PLAYWRIGHT_BROWSERS_PATH: join(cache, 'browsers') },
  };
  mkdirSync(cache, { recursive: true });
  const deadline = Date.now() + 610_000;
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
        console.log(`Preparing shared diagram runtime: ${dir}`);
        mkdirSync(dir, { recursive: true });
        for (const name of files) copyFileSync(join(source, name), join(dir, name));
        execFileSync(process.execPath, ['install', '--frozen-lockfile', '--ignore-scripts'], options);
        execFileSync(process.execPath, ['node_modules/playwright/cli.js', 'install', 'chromium', '--only-shell'], options);
        writeFileSync(ready, 'ready\n');
      }
    } finally {
      if (existsSync(join(lock, 'pid'))) unlinkSync(join(lock, 'pid'));
      rmdirSync(lock);
    }
  }
  console.log(`Using shared diagram runtime: ${dir}`);
  return { dir, run: (args, env = {}) => execFileSync(process.execPath, args, { ...options, env: { ...options.env, ...env } }) };
}

/** Downloads the measuring fonts once into the cache and returns their directory. */
export async function ensureFonts(): Promise<string> {
  const dir = join(cache, 'fonts', createHash('sha256').update(JSON.stringify(FONTS)).digest('hex').slice(0, 16));
  mkdirSync(dir, { recursive: true });
  for (const [name, url] of Object.entries(FONTS)) {
    const path = join(dir, name);
    if (existsSync(path)) continue;
    const response = await fetch(url, { signal: AbortSignal.timeout(60_000) });
    if (!response.ok) throw new Error(`Font download failed (${response.status}): ${url}`);
    // A per-process temporary file renamed into place: no truncated font, and concurrent first runs never collide.
    const part = `${path}.${process.pid}.${Math.random().toString(36).slice(2)}.part`;
    writeFileSync(part, new Uint8Array(await response.arrayBuffer()));
    renameSync(part, path);
  }
  return dir;
}
