import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

// Usage (from audit.ts): bun run audit-run.ts PAGE WIDTHS THEMES TIMEZONE SELECT; empty strings for unset options.
const [page, widthsArg, themesArg, timezone, select] = process.argv.slice(2);
const widths = widthsArg.split(',').map(Number);
const themes = themesArg.split(',') as ('light' | 'dark')[];
const source = readFileSync(join(import.meta.dir, 'audit.js'), 'utf8').trim();

const browser = await chromium.launch({ headless: true });
let failed = false;
try {
  for (const width of widths) {
    for (const theme of themes) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: theme, ...(timezone ? { timezoneId: timezone } : {}) });
      const tab = await context.newPage();
      // Listening before navigation hears errors thrown while the page first draws.
      const heard: { figure: string; text: string }[] = [];
      tab.on('pageerror', error => heard.push({ figure: 'page', text: error.message }));
      tab.on('console', message => { if (message.type() === 'error') heard.push({ figure: 'console', text: message.text() }); });
      await tab.goto('file://' + page, { waitUntil: 'load' });
      // Settled: no figure is empty without an error and the SVG count held for 500 ms, or 5 s passed.
      const start = Date.now();
      let last = -1, steadySince = Date.now();
      while (Date.now() - start < 5000) {
        const { svgs, pending } = await tab.evaluate(`(() => { const r = (${source})(); return { svgs: document.querySelectorAll('svg').length, pending: r.empty.length }; })()`) as { svgs: number; pending: number };
        if (svgs !== last) { last = svgs; steadySince = Date.now(); }
        if (!pending && Date.now() - steadySince >= 500) break;
        await tab.waitForTimeout(250);
      }
      const result = await tab.evaluate(`(${source})()`) as { errors: { figure: string; text: string }[]; empty: string[]; clipped: unknown[]; overflow: boolean; ok: boolean };
      result.errors.push(...heard);
      result.ok = result.ok && heard.length === 0;
      const out: Record<string, unknown> = { width, theme, ...result };
      if (select) out.selected = await tab.$$eval(select, els => els.map(el => ({ text: (el.textContent || '').trim(), tooltip: el.getAttribute('data-tooltip') })));
      console.log(JSON.stringify(out));
      failed ||= !result.ok;
      await context.close();
    }
  }
} finally {
  await browser.close();
}
process.exitCode = failed ? 1 : 0;
