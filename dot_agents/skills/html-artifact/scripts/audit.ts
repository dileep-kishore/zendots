import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { ensureRuntime } from './runtime';

const USAGE = 'Usage: bun scripts/audit.ts PAGE.html [--width 390,1280] [--theme light,dark] [--timezone ZONE] [--select CSS]';
const args = process.argv.slice(2);
const opts: Record<string, string> = { width: '390,1280', theme: 'light,dark', timezone: '', select: '' };
let page = '';
for (let i = 0; i < args.length; i++) {
  const flag = args[i].match(/^--(width|theme|timezone|select)$/);
  if (flag && i + 1 < args.length) opts[flag[1]] = args[++i];
  else if (!args[i].startsWith('--') && !page) page = resolve(args[i]);
  else { console.error(USAGE); process.exit(2); }
}
const bad = !page || !existsSync(page)
  || !opts.width.split(',').every(w => /^\d+$/.test(w) && +w >= 240)
  || !opts.theme.split(',').every(t => t === 'light' || t === 'dark');
if (bad) { console.error(page && !existsSync(page) ? `No such page: ${page}` : USAGE); process.exit(2); }

let runtime = '';
try {
  const rt = await ensureRuntime();
  runtime = rt.dir;
  rt.run(['run', 'audit-run.ts', page, opts.width, opts.theme, opts.timezone, opts.select]);
} catch (error) {
  // The runner exits 1 when a pass is not ok; anything else is a failure to audit at all.
  const status = (error as { status?: number }).status;
  if (status === 1) process.exit(1);
  console.error(error instanceof Error ? error.message : error);
  if (runtime) console.error(`Audit runtime retained for diagnosis: ${runtime}`);
  process.exit(2);
}
