#!/usr/bin/env python3
"""Validate an html-artifact page: single file, allowlisted hosts, pinned libraries and fonts, TOC-able headings,
and well-formed interactive figures.

Usage: check.py FILE
Exit 0 when there are no errors, 1 otherwise. Warnings never fail the check.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net"}
WARN_BYTES, MAX_BYTES = 1_000_000, 2_000_000
PINNED = re.compile(r"@(\d+\.\d+\.\d+|[0-9a-f]{7,40})/")
def substitutions(m: re.Match) -> str:
    """Drop a literal or comment but keep a template literal's ${...} parts, which execute."""
    text = m.group(0)
    return " ".join(re.findall(r"\$\{(.*?)\}", text, re.DOTALL)) if text.startswith("`") else ""


JS_TYPES = {"text/javascript", "application/javascript", "module"}
# String literals and comments, so a mention of fetch( in text is not taken for a call.
LITERALS = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`|/\*.*?\*/|//[^\n]*", re.DOTALL)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources, self.headings, self.css, self.scripts = [], [], [], []
        self.ids, self.viz_roots, self.code = [], [], []
        self.runtime, self.raw_js = set(), False
        self.lanes, self.last_div, self.raw_lanes = [], [], False
        self.raw_tag = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if "viz" in (attrs.get("class") or "").split():
            self.viz_roots.append(attrs.get("id"))
        if tag == "h2":
            self.headings.append(attrs.get("id"))
        for key in ("src", "poster"):
            if attrs.get(key):
                self.resources.append(attrs[key])
        if tag in {"link", "image", "use"}:
            for key in ("href", "xlink:href"):
                if attrs.get(key):
                    self.resources.append(attrs[key])
        if attrs.get("style"):
            self.css.append(attrs["style"])
        if tag == "div":
            self.last_div = (attrs.get("class") or "").split()
        if tag in {"style", "script"}:
            self.raw_tag = tag
            self.raw_lanes = tag == "script" and attrs.get("type") == "application/json" and "lanes" in self.last_div
            if self.raw_lanes:
                self.lanes.append("")
            if attrs.get("id") in {"viz-css", "viz-js"}:
                self.runtime.add((tag, attrs["id"]))
            self.raw_js = tag == "script" and (attrs.get("type") or "text/javascript") in JS_TYPES

    def handle_endtag(self, tag):
        if tag == self.raw_tag:
            self.raw_tag = None

    def handle_data(self, data):
        if self.raw_tag == "style":
            self.css.append(data)
        elif self.raw_tag == "script":
            self.scripts.append(data)
            if self.raw_js:
                self.code.append(data)
            if self.raw_lanes:
                self.lanes[-1] += data


def check(path: Path) -> int:
    html = path.read_text(encoding="utf-8")
    errors, warns = [], []

    size = path.stat().st_size
    if size > MAX_BYTES:
        errors.append(f"size {size} bytes exceeds {MAX_BYTES}")
    elif size > WARN_BYTES:
        warns.append(f"size {size} bytes above {WARN_BYTES}")

    page = Page()
    page.feed(html)
    for _, url in re.findall(r"url\(\s*(['\"]?)(.*?)\1\s*\)", "\n".join(page.css)):
        page.resources.append(url)
    for _, url in re.findall(r"(?:import|loadScript)\(\s*(['\"])(.*?)\1\s*\)", "\n".join(page.scripts)):
        page.resources.append(url)
    for url in page.resources:
        url = url.strip()
        if url.startswith(("data:", "#")):
            continue
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            errors.append(f"resource must be embedded, not linked: {url}")
            continue
        host = parsed.hostname
        if host not in ALLOWED_HOSTS:
            errors.append(f"external host not allowed: {host}")
        if host == "cdn.jsdelivr.net" and not PINNED.search(url):
            errors.append(f"unpinned library: {url}")

    seen = set()
    for heading_id in page.headings:
        if not heading_id or not heading_id.strip():
            errors.append("h2 without id")
        elif heading_id in seen:
            errors.append(f"duplicate h2 id: {heading_id}")
        seen.add(heading_id)
    for chunk in re.split(r"<h2\b", html)[1:]:
        heading, _, rest = chunk.partition(">")
        body = rest.partition("</h2>")[2].split("</main>", 1)[0]
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        if not re.sub(r"<[^>]+>", "", body).strip() and not re.search(r"<(?:img|svg|canvas)\b", body):
            errors.append("empty section: " + re.sub(r"<[^>]+>", "", rest.split("</h2>", 1)[0])[:40])

    for spec in re.findall(
        r'<div class="vega[^"]*">\s*<script type="application/json">(.*?)</script>', html, re.S
    ):
        try:
            json.loads(spec)
        except json.JSONDecodeError as e:
            errors.append(f"vega spec is not valid JSON: {e}")

    dupes = sorted({i for i in page.ids if page.ids.count(i) > 1})
    if dupes:
        errors.append("duplicate id: " + ", ".join(dupes))
    if page.viz_roots:
        if page.runtime != {("style", "viz-css"), ("script", "viz-js")}:
            errors.append("interactive figure but no viz runtime; copy viz-css and viz-js from the template")
        if not all(page.viz_roots):
            errors.append('interactive figure root without an id: <div class="viz" id="...">')
    if re.search(r"\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(", LITERALS.sub(substitutions, "\n".join(page.code))):
        errors.append("script makes a network request; inline the data instead")

    for spec in page.lanes:
        try:
            data = json.loads(spec)
            for lane in data["lanes"]:
                lane["name"]
                for span in lane["spans"]:
                    span["start"], span["end"]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            errors.append(f"lanes data needs lanes[].name and spans[].start/end: {e!r}")

    if "<!-- SLOT:" in html:
        errors.append("unfilled SLOT comment remains")

    for diagram in re.findall(r'<pre\b[^>]*class=["\'][^"\']*\bmermaid\b[^"\']*["\'][^>]*>(.*?)</pre>', html, re.S):
        if not re.search(r"look\s*:\s*handDrawn\b", diagram):
            warns.append("Mermaid lacks handDrawn configuration; confirm the user chose this renderer")

    for fig in re.findall(r"<figure\b.*?</figure>", html, re.S):
        cap = re.search(r"<figcaption>(.*?)</figcaption>", fig, re.S)
        if not cap:
            errors.append("figure without figcaption: " + re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fig))[:50])
            continue
        text = re.sub(r"<[^>]+>", "", cap.group(1)).strip()
        if re.match(r"(Figure|Fig\.?|Table)\s*\d", text, re.I):
            warns.append("caption carries its own number; the template numbers it: " + text[:40])
        if "<b>" not in cap.group(1) and "<strong>" not in cap.group(1):
            warns.append("caption lacks a bold title sentence: " + text[:40])

    for w in warns:
        print("WARN:", w)
    for e in errors:
        print("ERROR:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    a = ap.parse_args()
    sys.exit(check(a.file))
