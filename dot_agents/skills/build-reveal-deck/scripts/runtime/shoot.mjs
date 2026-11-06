// Usage: node shoot.mjs <check|pdf|steps> <deck index.html> <out dir> [slide number for steps]
import { chromium } from "playwright";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [mode, html, outDir, stepSlide] = process.argv.slice(2);
const SETTLE_MS = 2600; // longest fragment transition (draw 1100 ms) plus arrowhead timers
const b = await chromium.launch();
const [vw, vh] = (mode === "pdf" ? "1600x900" : process.env.DECK_VIEWPORT || "1600x900").split("x").map(Number);
const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: mode === "pdf" ? 2 : 1 });
const errs = []; p.on("pageerror", e => errs.push(String(e)));
const failed = [];
p.on("requestfailed", r => failed.push(r.url()));
p.on("response", r => { if (r.status() >= 400) failed.push(`${r.status()} ${r.url()}`); });
await p.goto(pathToFileURL(html).href);
await p.waitForFunction(() => window.Reveal && Reveal.isReady(), null, { timeout: 15000 });
await p.waitForTimeout(1500);
if (mode === "pdf") await p.addStyleTag({ content: ".reveal .controls,.reveal .slide-number,.reveal .progress{display:none!important}" });
// leaf slides in reading order; a vertical stack counts each child, so slide i is not always Reveal.slide(i)
const coords = await p.evaluate(() => Reveal.getSlides().map(s => { const { h, v } = Reveal.getIndices(s); return { h, v: v || 0 }; }));
const n = coords.length;
const go = (i, f) => p.evaluate(([c, f]) => Reveal.slide(c.h, c.v, f), [coords[i], f]);
const pad = i => String(i).padStart(2, "0");

const visibleBoxes = () => [...Reveal.getCurrentSlide().querySelectorAll(".box, .col, .lim .bad, .lim .good, .window, .term")]
  .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && e.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true }); }).length;

const audit = () => {
  const s = Reveal.getCurrentSlide();
  const sr = s.getBoundingClientRect(), k = sr.width / 1600;
  const label = e => (e.querySelector?.("h4,h3")?.textContent || e.textContent || e.getAttribute("class") || e.tagName).trim().replace(/\s+/g, " ").slice(0, 50);
  const issues = [];
  const h2 = s.querySelector("h2");
  if (h2) {
    const lh = parseFloat(getComputedStyle(h2).lineHeight) * k;
    if (h2.scrollWidth > h2.clientWidth + 1) issues.push(`title wider than the slide: "${label(h2)}"`);
    else if (h2.getBoundingClientRect().height > lh * 1.5) issues.push(`title runs over one line: "${label(h2)}"`);
  }
  s.querySelectorAll(".box, .col, .lim .bad, .lim .good, .window, .term, .callout").forEach(e => {
    if (e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1) issues.push(`text overflows its box: "${label(e)}"`);
  });
  const shown = e => e.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true });
  const inside = r => r.left >= sr.left - 2 && r.top >= sr.top - 2 && r.right <= sr.right + 2 && r.bottom <= sr.bottom + 2;
  const off = [...s.querySelectorAll("*")].filter(e => {
    if (e.closest("aside.notes, defs, marker") || e.tagName === "BR") return false;
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && shown(e) && !inside(r);
  });
  // report the outermost element that leaves the slide, not each of its children
  off.filter(e => !off.some(o => o !== e && o.contains(e))).forEach(e => issues.push(`off the slide: "${label(e)}"`));
  const deco = s.parentElement.matches(".slides") ? s : s.parentElement;  // theme logos sit on the top-level section
  const after = getComputedStyle(deco, "::after");
  if (after.content && after.content !== "none") {
    const dr = deco.getBoundingClientRect();
    const w = parseFloat(after.width) * k, h = parseFloat(after.height) * k;
    const right = dr.right - parseFloat(after.right) * k, bottom = dr.bottom - parseFloat(after.bottom) * k;
    const foot = { left: right - w, right, top: bottom - h, bottom };
    // text lines are measured by their glyphs, since a list item's box spans the full width
    const lineRects = e => { const rg = document.createRange(); rg.selectNodeContents(e); return [...rg.getClientRects()]; };
    const hits = r => r.width && r.left < foot.right && r.right > foot.left && r.top < foot.bottom && r.bottom > foot.top;
    const textSel = ".takeaway li, .source, .bullets li, .prose p";
    s.querySelectorAll(`${textSel}, .box, .col, .term, .window`).forEach(e => {
      const rects = e.matches(textSel) ? lineRects(e) : [e.getBoundingClientRect()];
      if (rects.some(hits)) issues.push(`covers the footer logos: "${label(e)}"`);
    });
  }
  const arrows = [...s.querySelectorAll("[data-marker]")];
  const noHead = arrows.filter(e => !e.getAttribute("marker-end")).length;
  if (noHead) issues.push(`${noHead} arrowhead(s) missing after the last fragment`);
  const badRef = [...new Set(arrows.map(e => e.dataset.marker).filter(id => document.getElementById(id)?.tagName.toLowerCase() !== "marker"))];
  if (badRef.length) issues.push(`data-marker names no <marker>: ${badRef.join(", ")}`);
  s.querySelectorAll("img").forEach(img => { if (img.complete && img.naturalWidth === 0) issues.push(`image did not load: ${img.getAttribute("src")?.slice(0, 60)}`); });
  return { title: (h2?.textContent || s.querySelector("h1")?.textContent || "").trim().replace(/\s+/g, " "), fragments: s.querySelectorAll(".fragment").length, issues };
};

const shots = [], slides = [], boxes = [];
if (mode === "steps") {
  const i = Number(stepSlide) - 1;
  if (!(i >= 0 && i < n)) { console.error(`slide ${stepSlide} does not exist; the deck has ${n} slides`); process.exit(2); }
  await go(i, -1);
  await p.waitForTimeout(SETTLE_MS);
  for (let step = 0; ; step++) {
    const f = `${outDir}/slide-${pad(i + 1)}-step-${pad(step)}.png`;
    await p.screenshot({ path: f }); shots.push(f);
    if (!(await p.evaluate(() => Reveal.availableFragments().next))) break;
    await p.evaluate(() => Reveal.nextFragment());
    await p.waitForTimeout(SETTLE_MS);
  }
} else {
  for (let i = 0; i < n; i++) {
    await go(i, 999);
    await p.waitForTimeout(SETTLE_MS);
    const f = `${outDir}/slide-${pad(i + 1)}.png`;
    await p.screenshot({ path: f }); shots.push(f);
    if (mode === "check") {
      slides.push({ slide: i + 1, ...(await p.evaluate(audit)) });
      boxes.push(await p.evaluate(visibleBoxes));
    }
  }
}
// A slide visited a second time must look the same; auto-animate can leave boxes hidden.
if (mode === "check") {
  for (let i = 0; i + 1 < n; i++) {
    await go(i, 999); await p.waitForTimeout(400);
    await go(i + 1, 0); await p.waitForTimeout(1300);
    await go(i, 999); await p.waitForTimeout(SETTLE_MS);
    const now = await p.evaluate(visibleBoxes);
    if (now < boxes[i]) slides[i].issues.push(`${boxes[i] - now} box(es) invisible after leaving and returning`);
  }
}
const fonts = await p.evaluate(() => [...new Set([...document.fonts].filter(f => f.status === "loaded").map(f => f.family.replace(/"/g, "")))]);
if (mode === "pdf") {
  const doc = await b.newPage();
  const imgs = shots.map(f => `<img src="data:image/png;base64,${readFileSync(f).toString("base64")}">`).join("");
  await doc.setContent(`<style>@page{size:1600px 900px;margin:0}body{margin:0}img{display:block;width:1600px;height:900px;page-break-after:always}</style>${imgs}`);
  await doc.pdf({ path: `${outDir}/deck.pdf`, width: "1600px", height: "900px", printBackground: true });
}
console.log(JSON.stringify({ slides: n, pageErrors: errs, failedRequests: failed, fontsLoaded: fonts, shots, report: slides }, null, 2));
await b.close();
