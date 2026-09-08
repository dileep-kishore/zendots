#!/usr/bin/env python3
"""Validate an html-artifact page: single file, allowlisted hosts, pinned libraries and fonts, TOC-able headings.

Usage: check.py FILE [--screenshot]
Exit 0 when there are no errors, 1 otherwise. Warnings never fail the check.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ALLOWED_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net"}
WARN_BYTES, MAX_BYTES = 1_000_000, 2_000_000
PINNED = re.compile(r"@(\d+\.\d+\.\d+|[0-9a-f]{7,40})/")


def check(path: Path, screenshot: bool, window: str = "1400,2400") -> int:
    html = path.read_text(encoding="utf-8")
    errors, warns = [], []

    size = path.stat().st_size
    if size > MAX_BYTES:
        errors.append(f"size {size} bytes exceeds {MAX_BYTES}")
    elif size > WARN_BYTES:
        warns.append(f"size {size} bytes above {WARN_BYTES}")

    for url in re.findall(r'(?:src|href)="(https?://[^"]+)"', html):
        host = re.match(r"https?://([^/]+)", url).group(1)
        if host not in ALLOWED_HOSTS:
            errors.append(f"external host not allowed: {host}")
        if host == "cdn.jsdelivr.net" and not PINNED.search(url):
            errors.append(f"unpinned library: {url}")
    for url in re.findall(r"(?:import|loadScript)\('(https?://[^']+)'\)", html):
        if not PINNED.search(url):
            errors.append(f"unpinned library: {url}")

    for tag in re.findall(r"<h2\b[^>]*>", html):
        if ' id="' not in tag:
            errors.append(f"h2 without id: {tag}")
    for chunk in re.split(r"<h2\b", html)[1:]:
        heading, _, rest = chunk.partition(">")
        body = rest.split("</main>", 1)[0]
        if not re.sub(r"<[^>]+>", "", body).strip():
            errors.append("empty section: " + re.sub(r"<[^>]+>", "", rest.split("</h2>", 1)[0])[:40])

    for spec in re.findall(
        r'<div class="vega[^"]*">\s*<script type="application/json">(.*?)</script>', html, re.S
    ):
        try:
            json.loads(spec)
        except json.JSONDecodeError as e:
            errors.append(f"vega spec is not valid JSON: {e}")

    if "<!-- SLOT:" in html:
        errors.append("unfilled SLOT comment remains")

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

    if screenshot:
        chrome = next(
            (c for c in ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser") if shutil.which(c)),
            None,
        )
        if chrome:
            out = Path(tempfile.mkdtemp()) / "artifact.png"
            # virtual-time-budget lets Mermaid and Vega arrive from the CDN before the capture.
            subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                 f"--user-data-dir={out.parent / 'profile'}", "--virtual-time-budget=15000",
                 f"--screenshot={out}", f"--window-size={window}", path.resolve().as_uri()],
                check=False, capture_output=True, timeout=90,
            )
            print(f"screenshot: {out}" if out.exists() else "WARN: screenshot failed")
        else:
            print("WARN: no Chrome/Chromium found; visual check skipped")

    for w in warns:
        print("WARN:", w)
    for e in errors:
        print("ERROR:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--screenshot", action="store_true", help="render with a local Chrome and print the PNG path")
    ap.add_argument("--size", default="1400,2400", help="screenshot window as WIDTH,HEIGHT (default 1400,2400; use 1400,900 for a one-screen check)")
    a = ap.parse_args()
    sys.exit(check(a.file, a.screenshot, a.size))
