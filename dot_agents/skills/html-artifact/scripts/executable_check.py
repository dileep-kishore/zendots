#!/usr/bin/env python3
"""Validate an html-artifact page: single file, allowlisted hosts, pinned libraries and fonts, TOC-able headings,
and well-formed interactive figures and widgets.

Usage: check.py FILE
Exit 0 when there are no errors, 1 otherwise. Warnings never fail the check.
"""
import argparse
import json
import math
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
        # Widget roots and their direct-child JSON scripts, tied through the open-element stack.
        self.widget_roots, self.widgets, self.raw_widget, self.stack = [], [], False, []
        self.raw_tag = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if "viz" in (attrs.get("class") or "").split():
            self.viz_roots.append(attrs.get("id"))
        parent = self.stack[-1][1] if self.stack else None
        root = None
        if tag == "div" and "widget" in (attrs.get("class") or "").split():
            root = len(self.widget_roots)
            self.widget_roots.append(attrs.get("id"))
        if tag not in VOID:
            self.stack.append((tag, root))
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
            self.raw_widget = tag == "script" and attrs.get("type") == "application/json" and parent is not None
            if self.raw_widget:
                self.widgets.append([parent, ""])
            if attrs.get("id") in {"viz-css", "viz-js"}:
                self.runtime.add((tag, attrs["id"]))
            self.raw_js = tag == "script" and (attrs.get("type") or "text/javascript") in JS_TYPES

    def handle_endtag(self, tag):
        if tag == self.raw_tag:
            self.raw_tag = None
        if any(t == tag for t, _ in self.stack):
            while self.stack and self.stack.pop()[0] != tag:
                pass

    def handle_data(self, data):
        if self.raw_tag == "style":
            self.css.append(data)
        elif self.raw_tag == "script":
            self.scripts.append(data)
            if self.raw_js:
                self.code.append(data)
            if self.raw_lanes:
                self.lanes[-1] += data
            if self.raw_widget:
                self.widgets[-1][1] += data


OPS = (">=", ">", "<=", "<", "==", "!=", "contains")
STAT_OPS = ("count", "missing", "mean", "median", "min", "max", "sum")
# Each widget component's arguments, True when required. Row and Sources take a list. Mirrors viz-js checkWidget.
ARGS = {
    "Stat": {"label": True, "rows": True, "op": True, "field": False, "where": False},
    "Slider": {"label": True, "min": True, "max": True, "step": True, "value": True},
    "Select": {"label": True, "options": True, "value": True},
    "Table": {"rows": True, "columns": False, "where": False, "sort": False, "limit": False},
    "Chart": {"rows": True, "spec": True, "where": False, "params": False},
}
REF = re.compile(r"^\$[A-Za-z_]\w*$")
URL_VALUE = re.compile(r"url\s*\(", re.I)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def is_obj(v) -> bool:
    return isinstance(v, dict)


def is_num(v) -> bool:
    # bool is an int subclass, and JSON true is not a number to the runtime.
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def check_widget(spec, errors: list, warns: list) -> None:
    """The widget refusals viz-js checkWidget makes at runtime, moved to check time."""
    if not is_obj(spec):
        errors.append("widget JSON must be an object")
        return
    for k in spec:
        if k not in ("state", "rows", "where", "view"):
            errors.append(f'widget has unknown top-level key "{k}"')
    for k in ("state", "rows", "where"):
        if k in spec and not is_obj(spec[k]):
            errors.append(f"widget {k} must be an object")
    state = spec["state"] if is_obj(spec.get("state")) else {}
    rows = spec["rows"] if is_obj(spec.get("rows")) else {}
    named = spec["where"] if is_obj(spec.get("where")) else {}
    good = {}
    for k, v in rows.items():
        if isinstance(v, list) and all(is_obj(r) for r in v):
            good[k] = v
            if not v:
                warns.append(f'widget rows "{k}" is empty; its field names are not checked')
        else:
            errors.append(f'widget rows "{k}" must be a list of objects')

    def ref(v, at):
        if isinstance(v, str) and REF.match(v) and v[1:] not in state:
            errors.append(f"widget {at} reads {v}, which state does not declare")

    def has_field(dataset, field, at):
        data = good.get(dataset)
        if data and not any(field in r for r in data):
            errors.append(f'widget {at} names field "{field}", which no row of "{dataset}" has')

    def cond_list(where, dataset, at):
        for c in where if isinstance(where, list) else [where]:
            if not is_obj(c) or not isinstance(c.get("field"), str):
                errors.append(f"widget {at} has a condition that is not {{field, op, value}}")
                continue
            for k in c:
                if k not in ("field", "op", "value"):
                    errors.append(f'widget {at} condition has unknown key "{k}"')
            if c.get("op") not in OPS:
                errors.append(f'widget {at} uses op "{c.get("op")}"; use one of {" ".join(OPS)}')
            ref(c.get("value"), at)
            if dataset:
                has_field(dataset, c["field"], at)

    # A named set holds conditions, never another name, so the runtime resolves each name exactly once.
    for k, v in named.items():
        if isinstance(v, str):
            errors.append(f'widget where "{k}" must hold conditions, not another name')

    def conds(where, dataset, at):
        if where is None:
            return
        if isinstance(where, str):
            if where not in named:
                errors.append(f'widget {at} uses where "{where}", which is not declared')
            elif not isinstance(named[where], str):
                cond_list(named[where], dataset, at)
            return
        cond_list(where, dataset, at)

    def forbid(v, at):
        if isinstance(v, list):
            for x in v:
                forbid(x, at)
        elif isinstance(v, str):
            if URL_VALUE.search(v):
                errors.append(f"widget {at} spec has a url(...) value, which would load a file")
        elif is_obj(v):
            for k, x in v.items():
                if k in ("url", "data", "datasets"):
                    errors.append(f'widget {at} spec has a "{k}" key; a widget chart draws only its rows')
                if k == "mark" and (x == "image" or (is_obj(x) and x.get("type") == "image")):
                    errors.append(f"widget {at} spec has an image mark, which would load files")
                forbid(x, at)

    def option(o) -> bool:
        if o is None or isinstance(o, str) or is_num(o):
            return True
        return is_obj(o) and isinstance(o.get("label"), str) and (o.get("value") is None or isinstance(o.get("value"), str) or is_num(o.get("value")))

    def node(n, path):
        if not (is_obj(n) and len(n) == 1):
            errors.append(f"widget {path} must be an object with one component name")
            return
        name, a = next(iter(n.items()))
        at = f"{path} {name}"
        if name == "Row":
            if not isinstance(a, list):
                errors.append(f"widget {at} takes a list of components")
            else:
                for i, k in enumerate(a):
                    node(k, f"{at}[{i}]")
            return
        if name == "Sources":
            if not (isinstance(a, list) and all(isinstance(x, str) for x in a)):
                errors.append(f"widget {at} takes a list of strings")
            return
        if name not in ARGS:
            errors.append(f"widget {at} is not a component; use Row, Stat, Slider, Select, Table, Chart or Sources")
            return
        if not is_obj(a):
            errors.append(f"widget {at} takes an object of arguments")
            return
        for k in a:
            if k not in ARGS[name]:
                errors.append(f'widget {at} has unknown argument "{k}"')
        for k, required in ARGS[name].items():
            if required and k not in a:
                errors.append(f'widget {at} needs "{k}"')
        if "label" in a and not isinstance(a["label"], str):
            errors.append(f"widget {at} label must be a string")
        if "rows" in a and not (isinstance(a["rows"], str) and isinstance(rows.get(a["rows"]), list)):
            errors.append(f'widget {at} reads rows "{a["rows"]}", which is not declared')
        dataset = a["rows"] if isinstance(a.get("rows"), str) and a["rows"] in good else None
        conds(a.get("where"), dataset, at)
        if name == "Stat":
            if a.get("op") not in STAT_OPS:
                errors.append(f'widget {at} uses op "{a.get("op")}"; use one of {" ".join(STAT_OPS)}')
            elif a["op"] != "count" and not isinstance(a.get("field"), str):
                errors.append(f'widget {at} op "{a["op"]}" needs a field')
            if dataset and isinstance(a.get("field"), str):
                has_field(dataset, a["field"], at)
        if name in ("Slider", "Select"):
            v = a.get("value")
            if not (isinstance(v, str) and REF.match(v)):
                errors.append(f'widget {at} value must be a "$name" from state')
            else:
                ref(v, at)
        if name == "Slider":
            for k in ("min", "max", "step"):
                if k in a and not is_num(a[k]):
                    errors.append(f"widget {at} {k} must be a number")
        if name == "Select":
            opts = a.get("options")
            if not (isinstance(opts, list) and opts and all(option(o) for o in opts)):
                errors.append(f"widget {at} options must be a non-empty list of strings, numbers, null or {{value, label}}")
        if name == "Table":
            cols = a.get("columns")
            if "columns" in a and not (isinstance(cols, list) and all(isinstance(c, str) for c in cols)):
                errors.append(f"widget {at} columns must be a list of field names")
            elif dataset:
                for c in cols or []:
                    has_field(dataset, c, at)
            sort = a.get("sort")
            if "sort" in a and not (is_obj(sort) and isinstance(sort.get("field"), str)):
                errors.append(f"widget {at} sort must be {{field, desc}}")
            elif sort and dataset:
                has_field(dataset, sort["field"], at)
            if "limit" in a and not (is_num(a["limit"]) and a["limit"] > 0):
                errors.append(f"widget {at} limit must be a positive number")
        if name == "Chart":
            if not is_obj(a.get("spec")):
                errors.append(f"widget {at} spec must be a Vega-Lite object")
            else:
                forbid(a["spec"], at)
            params = a.get("params")
            if "params" in a and not is_obj(params):
                errors.append(f"widget {at} params must be an object")
            else:
                for v in (params or {}).values():
                    ref(v, at)

    view = spec.get("view")
    if not isinstance(view, list):
        errors.append("widget view must be a list of components")
    else:
        for i, n in enumerate(view):
            node(n, f"view[{i}]")

def reject_constant(name):
    """NaN and Infinity are Python JSON extensions; the browser's JSON.parse refuses them."""
    raise ValueError(f"{name} is not valid JSON")


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
    if page.viz_roots or page.widget_roots:
        if page.runtime != {("style", "viz-css"), ("script", "viz-js")}:
            errors.append("interactive figure but no viz runtime; copy viz-css and viz-js from the template")
        if not all(page.viz_roots):
            errors.append('interactive figure root without an id: <div class="viz" id="...">')
        if not all(page.widget_roots):
            errors.append('widget root without an id: <div class="widget" id="...">')
    sources = [idx for idx, _ in page.widgets]
    for idx, wid in enumerate(page.widget_roots):
        if sources.count(idx) != 1:
            errors.append(f'widget root "{wid}" needs exactly one direct-child <script type="application/json">')
    for _, spec in page.widgets:
        try:
            check_widget(json.loads(spec, parse_constant=reject_constant), errors, warns)
        except (json.JSONDecodeError, ValueError) as e:
            errors.append(f"widget JSON is not valid: {e}")
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
