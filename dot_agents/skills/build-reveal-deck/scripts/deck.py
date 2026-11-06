#!/usr/bin/env python3
"""Create, check and export reveal.js decks built from this skill's templates.

Commands
--------
new     Copy a template into a new deck folder.
check   Screenshot every slide in its final state and report layout problems.
steps   Screenshot one slide at every fragment step, to review animation order.
pdf     Write a PDF with one page per slide, each in its final state.
bundle  Write one self-contained HTML file (for Notion or email).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / "assets"
RUNTIME_SRC = SKILL / "scripts" / "runtime"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "build-reveal-deck"
# html-artifact pins the same Playwright, so its Chromium download is reused when present
SHARED_BROWSERS = Path.home() / ".cache" / "html-artifact" / "diagram" / "browsers"


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def guard_untracked(dest: Path, files: list[Path]) -> None:
    """Refuse a deck folder where git would track any file ``new`` writes.

    Parameters
    ----------
    dest : Path
        Deck folder, which may not exist yet.
    files : list of Path
        Paths relative to ``dest`` that ``new`` will create.
    """
    probe = dest
    while not probe.exists():
        probe = probe.parent
    top = subprocess.run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode != 0:
        return
    wanted = [str(dest / f) for f in files]
    res = subprocess.run(["git", "-C", top.stdout.strip(), "check-ignore", "--no-index", "--stdin"],
                         input="\n".join(wanted), capture_output=True, text=True)
    ignored = {Path(line).resolve() for line in res.stdout.splitlines() if line}
    tracked = [str(f) for f in files if (dest / f).resolve() not in ignored]
    if tracked:
        fail(f"git would track {len(tracked)} file(s) in {dest}, e.g. {', '.join(tracked[:3])}. Use the project's "
             "ignored artifact folder (docs/superpowers/ or docs/drafts/), add the whole folder to the file "
             "`git rev-parse --git-path info/exclude` names, or pass --tracked to commit it")


def cmd_new(a: argparse.Namespace) -> None:
    tdir = ASSETS / "templates" / a.template
    if not tdir.is_dir():
        fail(f"unknown template {a.template!r}; choose from {', '.join(p.name for p in (ASSETS / 'templates').iterdir())}")
    dest = Path(a.dest).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()):
        fail(f"{dest} is not empty; pick a new folder so an existing deck is never overwritten")
    if not a.tracked:
        made = ["index.html", "brief.md", "deck.css", "base.css", "deck.js", "theme.css"]
        made += [f"lib/{f.relative_to(ASSETS / 'lib')}" for f in (ASSETS / "lib").rglob("*") if f.is_file()]
        if (tdir / "assets").is_dir():
            made += [f"assets/{f.relative_to(tdir / 'assets')}" for f in (tdir / "assets").rglob("*") if f.is_file()]
        guard_untracked(dest, [Path(m) for m in made])
    cfg = json.loads((tdir / "template.json").read_text())
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ASSETS / "lib", dest / "lib")
    shutil.copy(ASSETS / "base.css", dest / "base.css")
    shutil.copy(ASSETS / "deck.js", dest / "deck.js")
    shutil.copy(tdir / "theme.css", dest / "theme.css")
    if (tdir / "assets").is_dir():
        shutil.copytree(tdir / "assets", dest / "assets")
    (dest / "deck.css").write_text("/* Styles for this deck only. Shared components live in base.css, colours in theme.css. */\n")
    html = (ASSETS / "starter.html").read_text()
    for key, val in {"TITLE": a.title, "FONTS": cfg["fonts"], "TITLE_LOGO": cfg["title_logo"],
                     "PRESENTER": a.presenter, "DATE": a.date}.items():
        html = html.replace("{{" + key + "}}", val)
    (dest / "index.html").write_text(html)
    (dest / "brief.md").write_text(f"""# Brief: {a.title}

Answers from the interview (references/interview.md). Update when one changes.

- Audience:
- Goal (what they should do after):
- How the deck is used (live, projected, sent):
- Slot length and discussion time:
- The one sentence to remember:
- The hardest question, and the slide that answers it:
- Evidence sources:
- Sensitive points:
- Template and motion: {a.template}
- Assumptions made without asking:
""")
    print(dest / "index.html")


def runtime() -> tuple[Path, dict[str, str]]:
    h = hashlib.sha256()
    for name in ("package.json", "bun.lock", "shoot.mjs"):
        h.update(name.encode())
        h.update((RUNTIME_SRC / name).read_bytes())
    rdir = CACHE / h.hexdigest()[:16]
    browsers = SHARED_BROWSERS if SHARED_BROWSERS.is_dir() else CACHE / "browsers"
    env = {**os.environ, "PLAYWRIGHT_BROWSERS_PATH": str(browsers)}
    if not (rdir / ".ready").exists():
        if not shutil.which("bun") or not shutil.which("node"):
            fail("bun and node are needed for screenshots; install them with Homebrew or Paru")
        print(f"Preparing runtime in {rdir} (first run only)", file=sys.stderr)
        rdir.mkdir(parents=True, exist_ok=True)
        for name in ("package.json", "bun.lock", "shoot.mjs"):
            shutil.copy(RUNTIME_SRC / name, rdir / name)
        subprocess.run(["bun", "install", "--frozen-lockfile", "--ignore-scripts"], cwd=rdir, env=env, check=True)
        subprocess.run(["node", "node_modules/playwright/cli.js", "install", "chromium", "--only-shell"], cwd=rdir, env=env, check=True)
        (rdir / ".ready").write_text("ready\n")
    return rdir, env


def deck_index(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    p = p / "index.html" if p.is_dir() else p
    if not p.is_file():
        fail(f"no deck at {p}")
    return p


def shoot(mode: str, a: argparse.Namespace, extra: list[str] | None = None) -> dict:
    idx = deck_index(a.deck)
    # screenshots stay out of the deck folder, which may be synced
    tag = hashlib.sha256(str(idx).encode()).hexdigest()[:8]
    out = Path(a.out).expanduser().resolve() if a.out else CACHE / "shots" / f"{idx.parent.name}-{tag}"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("slide-*.png"):
        old.unlink()
    rdir, env = runtime()
    w, h = (int(x) for x in getattr(a, "size", "1600x900").lower().split("x"))
    res = subprocess.run(["node", "shoot.mjs", mode, str(idx), str(out), *(extra or [])],
                         cwd=rdir, env={**env, "DECK_VIEWPORT": f"{w}x{h}"}, capture_output=True, text=True, timeout=900)
    if res.returncode != 0:
        fail(res.stderr.strip() or res.stdout.strip())
    return json.loads(res.stdout)


def cmd_check(a: argparse.Namespace) -> None:
    r = shoot("check", a)
    problems = [f"slide {s['slide']} ({s['title'][:40]}): {i}" for s in r["report"] for i in s["issues"]]
    problems += [f"page error: {e}" for e in r["pageErrors"]] + [f"failed to load: {u}" for u in r["failedRequests"]]
    print(f"{r['slides']} slides; fonts loaded: {', '.join(r['fontsLoaded']) or 'none'}")
    print(f"screenshots: {Path(r['shots'][0]).parent}" if r["shots"] else "no screenshots")
    print("\n".join(problems) if problems else "no layout problems found")
    sys.exit(1 if problems else 0)


def cmd_steps(a: argparse.Namespace) -> None:
    r = shoot("steps", a, [str(a.slide)])
    print("\n".join(r["shots"]))


def cmd_pdf(a: argparse.Namespace) -> None:
    idx = deck_index(a.deck)
    target = Path(a.pdf).expanduser().resolve() if a.pdf else idx.parent / f"{idx.parent.name}.pdf"
    a.out = None
    r = shoot("pdf", a)
    shutil.move(Path(r["shots"][0]).parent / "deck.pdf", target)
    print(target)


def data_uri(p: Path) -> str:
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


REMOTE = ("data:", "http:", "https:", "//", "#", "mailto:", "javascript:")
CSS_URL = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")
# a start tag in either quote style, or an inlined <script>/<style> block left untouched
LINK_CSS = re.compile(r"""<link\b[^>]*\brel=(['"])stylesheet\1[^>]*>""", re.I)
SCRIPT_SRC = re.compile(r"""<script\b[^>]*\bsrc=(['"])([^'"]+)\1[^>]*>\s*</script>""", re.I)
ATTR = re.compile(r"""\b(src|href|poster)=(['"])([^'"]*)\2""", re.I)
STYLE_ATTR = re.compile(r"""\bstyle=(['"])(.*?)\1""", re.I | re.S)
CODE_BLOCK = re.compile(r"(<(script|style)\b[^>]*>.*?</\2>)", re.I | re.S)


def inline_css_urls(text: str, base: Path, missing: list[str]) -> str:
    """Replace local ``url(...)`` references in CSS with data URIs."""

    def sub(m: re.Match) -> str:
        ref = m.group(2).strip()
        if ref.startswith(REMOTE):
            return m.group(0)
        f = (base / ref.split("#")[0].split("?")[0]).resolve()
        if not f.is_file():
            missing.append(ref)
            return m.group(0)
        return f"url({data_uri(f)})"

    return CSS_URL.sub(sub, text)


def cmd_bundle(a: argparse.Namespace) -> None:
    idx = deck_index(a.deck)
    root = idx.parent
    html = idx.read_text()
    missing: list[str] = []
    # an embedded copy should not rewrite the host page's URL; older decks configure Reveal inline
    html = re.sub(r"hash:\s*true", "hash: false", html)

    def css(m: re.Match) -> str:
        href = re.search(r"""\bhref=(['"])([^'"]+)\1""", m.group(0))
        if not href or href.group(2).startswith(REMOTE):
            return m.group(0)
        f = root / href.group(2)
        return f"<style>{inline_css_urls(f.read_text(), f.parent, missing)}</style>"

    def js(m: re.Match) -> str:
        if m.group(2).startswith(REMOTE):
            return m.group(0)
        text = re.sub(r"hash:\s*true", "hash: false", (root / m.group(2)).read_text())
        return "<script>" + text.replace("</script", "<\\/script") + "</script>"

    html = SCRIPT_SRC.sub(js, LINK_CSS.sub(css, html))

    def attr(m: re.Match) -> str:
        ref = m.group(3)
        if not ref or ref.startswith(REMOTE):
            return m.group(0)
        # an href is a navigation link unless it points at an image (SVG <image>, favicon)
        if m.group(1).lower() == "href" and not re.search(r"\.(png|jpe?g|gif|svg|webp|ico)$", ref.split("?")[0], re.I):
            return m.group(0)
        f = (root / ref.split("#")[0].split("?")[0]).resolve()
        if not f.is_file():
            missing.append(ref)
            return m.group(0)
        return f"{m.group(1)}={m.group(2)}{data_uri(f)}{m.group(2)}"

    parts = CODE_BLOCK.split(html)
    out_parts = []
    i = 0
    while i < len(parts):
        markup = parts[i]
        markup = STYLE_ATTR.sub(lambda m: f"style={m.group(1)}{inline_css_urls(m.group(2), root, missing)}{m.group(1)}", markup)
        out_parts.append(ATTR.sub(attr, markup))
        if i + 1 < len(parts):
            block = parts[i + 1]
            if block[:6].lower() == "<style":
                block = inline_css_urls(block, root, missing)
            out_parts.append(block)
        i += 3
    if missing:
        fail(f"local files not found while bundling: {sorted(set(missing))}")
    html = "".join(out_parts)
    out = Path(a.out).expanduser().resolve() if a.out else root / f"{root.name}.bundle.html"
    out.write_text(html)
    print(f"{out} ({out.stat().st_size // 1024} KB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="copy a template into a new deck folder")
    n.add_argument("dest")
    n.add_argument("--template", default="default", help="default or kbase")
    n.add_argument("--title", required=True)
    n.add_argument("--presenter", default="Dileep Kishore")
    n.add_argument("--date", default=date.today().strftime("%-d %B %Y"))
    n.add_argument("--tracked", action="store_true", help="allow a folder git would track")
    for name, helptext in (("check", "screenshot and audit every slide"), ("pdf", "write a PDF"), ("bundle", "write one HTML file")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("deck", help="deck folder or its index.html")
        s.add_argument("--out", help="screenshot folder (check) or output file (bundle)")
        if name == "check":
            s.add_argument("--size", default="1600x900", help="browser window WIDTHxHEIGHT, e.g. 1280x960 for a 4:3 projector")
        if name == "pdf":
            s.add_argument("--pdf", help="output PDF path; default <deck folder>/<folder name>.pdf")
    st = sub.add_parser("steps", help="screenshot one slide at every fragment step")
    st.add_argument("deck")
    st.add_argument("slide", type=int, help="slide number, starting at 1")
    st.add_argument("--out")
    st.add_argument("--size", default="1600x900", help="browser window WIDTHxHEIGHT")
    a = ap.parse_args()
    {"new": cmd_new, "check": cmd_check, "steps": cmd_steps, "pdf": cmd_pdf, "bundle": cmd_bundle}[a.cmd](a)


if __name__ == "__main__":
    main()
