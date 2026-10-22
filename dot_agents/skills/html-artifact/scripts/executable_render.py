#!/usr/bin/env python3
"""Wrap one interactive-figure fragment in the html-artifact runtime as a self-contained page.

The runtime (<style id="viz-css"> and <script id="viz-js">) is copied from assets/template.html,
its only source. Without --page the output suits T3's html_render: no background or padding of its
own, and T3 supplies the theme tokens. With --page it is a centred standalone page whose Catppuccin
fallback tokens follow the operating system's light or dark setting, carrying the favicon of the
repository OUT is written into (see favicon.py).

Usage: render.py FRAGMENT OUT [--title TITLE] [--page]
"""
import argparse
import re
import subprocess
import sys
from html import escape
from html.parser import HTMLParser
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "template.html"
FAVICON = Path(__file__).resolve().parent / "favicon.py"
DOCUMENT = re.compile(r"<!doctype\s|<\s*(?:html|head|body)[\s>]", re.IGNORECASE)
INLINE_LIMIT = 512_000  # html_render's maximum document length


class VizRoot(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and "viz" in (attrs.get("class") or "").split() and attrs.get("id"):
            self.found = True


def block(template: str, tag: str, ident: str) -> str:
    match = re.search(rf'<{tag} id="{ident}">.*?</{tag}>', template, re.DOTALL)
    if not match:
        sys.exit(f'render.py: {TEMPLATE} has no <{tag} id="{ident}"> block')
    return match.group(0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fragment", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--title", help="document title; defaults to the fragment's file name")
    ap.add_argument("--page", action="store_true", help="standalone page with its own background and margins")
    args = ap.parse_args()

    fragment = args.fragment.read_text(encoding="utf-8").strip()
    if DOCUMENT.search(fragment):
        sys.exit("render.py: FRAGMENT must be a fragment, not a whole document")
    root = VizRoot()
    root.feed(fragment)
    if not root.found:
        sys.exit('render.py: FRAGMENT needs a root <div class="viz" id="...">')

    template = TEMPLATE.read_text(encoding="utf-8")
    title = args.title or args.fragment.stem.replace("-", " ").capitalize()
    body_css = (
        "body { margin: 0 auto; max-width: 980px; padding: 32px 20px; background: var(--background); }"
        if args.page
        else "body { margin: 0; }"
    )
    favicon = []
    if args.page:
        made = subprocess.run(
            [sys.executable, str(FAVICON), "--dir", str(args.out.resolve().parent)],
            capture_output=True, text=True, check=False,
        )
        if made.returncode:
            sys.exit(made.stderr.strip() or "render.py: favicon.py failed")
        favicon = [made.stdout.strip()]
    out = "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{escape(title)}</title>",
        *favicon,
        block(template, "style", "viz-css"),
        f"<style>{body_css}</style>",
        block(template, "script", "viz-js"),
        "</head>",
        "<body>",
        fragment,
        "</body>",
        "</html>",
        "",
    ])
    args.out.write_text(out, encoding="utf-8")
    size = len(out)
    print(f"{args.out.resolve()} ({size} characters)")
    if not args.page and size > INLINE_LIMIT:
        print(f"WARN: above html_render's {INLINE_LIMIT}-character limit; downsample the inline data", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
