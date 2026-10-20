#!/usr/bin/env python3
"""Render a unified diff (git diff, or diff -u) as an html-artifact diff figure.

The lines come from the real diff, so the page cannot drift from what changed. Notes pin
numbered markers to lines. A notes file maps keys to text: PATH:N pins new-side line N,
PATH:-N pins a deleted line by its old-side number, and PATH may be any suffix of the
file's path. A note that matches no shown line is an error, so none silently disappears.

Usage: git diff BASE -- PATHS | diff.py --caption "<b>Title.</b> Legend. Takeaway." [--notes notes.json] [--max-lines 300] [-o OUT]
"""
import argparse
import json
import re
import sys
from html import escape
from pathlib import Path

HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@ ?(.*)")


def unquote(path: str) -> str:
    """Decode Git's C-style quoting, which it applies to names with spaces escaped or non-ASCII bytes."""
    if len(path) > 1 and path[0] == path[-1] == '"':
        path = path[1:-1].encode("latin-1", "backslashreplace").decode("unicode_escape").encode("latin-1").decode("utf-8", "replace")
    return path


def header_path(line: str) -> str | None:
    path = unquote(line[4:].split("\t")[0].strip())
    return None if path == "/dev/null" else re.sub(r"^[ab]/", "", path)


def parse(text: str) -> list[dict]:
    files: list[dict] = []
    cur = None
    old_left = new_left = 0  # lines still owed to the open hunk; a "--- " inside one is content
    o = n = 0

    def start() -> dict:
        files.append({"path": "", "old": None, "lines": [], "binary": False, "renamed": None, "meta": []})
        return files[-1]

    for line in text.splitlines():
        if old_left or new_left:
            tag, body = line[:1], line[1:]
            if tag == "\\":
                continue
            if tag in " ":
                cur["lines"].append((" ", o, n, body)); o += 1; n += 1; old_left -= 1; new_left -= 1
            elif tag == "-":
                cur["lines"].append(("-", o, None, body)); o += 1; old_left -= 1
            elif tag == "+":
                cur["lines"].append(("+", None, n, body)); n += 1; new_left -= 1
            continue
        if line.startswith("diff "):
            cur = start()
            if line.startswith("diff --git "):
                tail = line.rsplit(' "b/', 1)
                cur["path"] = unquote('"b/' + tail[1]) if len(tail) == 2 else line.rsplit(" b/", 1)[-1]
                cur["path"] = re.sub(r"^b/", "", cur["path"])
        elif line.startswith("--- "):
            if cur is None or cur["lines"]:
                cur = start()
            cur["old"] = header_path(line)
        elif line.startswith("+++ ") and cur is not None:
            cur["path"] = header_path(line) or cur["old"] or cur["path"]
        elif line.startswith("rename from ") and cur is not None:
            cur["renamed"] = unquote(line[len("rename from "):])
        elif line.startswith("rename to ") and cur is not None:
            cur["path"] = unquote(line[len("rename to "):])
        elif line.startswith(("old mode ", "new mode ", "new file mode ", "deleted file mode ")) and cur is not None:
            cur["meta"].append(line)
        elif line.startswith("Binary files ") and cur is not None:
            cur["binary"] = True
        elif (m := HUNK.match(line)) and cur is not None:
            o, n = int(m[1]), int(m[3])
            old_left = int(m[2]) if m[2] is not None else 1
            new_left = int(m[4]) if m[4] is not None else 1
            cur["lines"].append(("@", None, None, line))
    return [f for f in files if f["path"] or f["old"]]


def render(files: list[dict], caption: str, notes: dict[str, str], max_lines: int) -> tuple[str, list[str]]:
    used, pin, out = set(), 0, []
    adds = sum(1 for f in files for line in f["lines"] if line[0] == "+")
    dels = sum(1 for f in files for line in f["lines"] if line[0] == "-")
    out.append('<figure class="diff">')
    out.append(f'  <div class="diff-sum">{len(files)} file{"s" if len(files) != 1 else ""} changed · '
               f'<span class="add">+{adds}</span> <span class="del">−{dels}</span></div>')
    for f in files:
        path = f["path"] or f["old"]
        a = sum(1 for line in f["lines"] if line[0] == "+")
        d = sum(1 for line in f["lines"] if line[0] == "-")
        label = escape(path) + (f" <span>(renamed from {escape(f['renamed'])})</span>" if f["renamed"] else "")
        out.append(f'  <details class="diff-file" open><summary><code>{label}</code>'
                   f'<span><span class="add">+{a}</span> <span class="del">−{d}</span></span></summary>')
        out.append('    <div class="diff-lines">')
        file_notes, first_pin = [], pin + 1
        for meta in f["meta"]:
            out.append(f'      <div class="gap">{escape(meta[0].upper() + meta[1:])}</div>')
        if f["binary"]:
            out.append('      <div class="gap">Binary file changed</div>')
        for tag, old, new, body in f["lines"][:max_lines]:
            if tag == "@":
                out.append(f'      <div class="h">{escape(body)}</div>')
                continue
            key = None
            for k in notes:
                kpath, _, num = k.rpartition(":")
                hit = (num.startswith("-") and tag == "-" and old == int(num[1:])) or (not num.startswith("-") and new is not None and tag != "-" and new == int(num))
                if hit and path.endswith(kpath) and k not in used:
                    key = k
                    break
            marker = ""
            if key:
                used.add(key); pin += 1; file_notes.append(notes[key])
                marker = f'<b class="pin">{pin}</b>'
            cls = {"+": ' class="a"', "-": ' class="r"', " ": ""}[tag]
            out.append(f'      <div{cls}><span>{old or ""}</span><span>{new or ""}</span>'
                       f'<code>{escape(tag + body)}{marker}</code></div>')
        if len(f["lines"]) > max_lines:
            out.append(f'      <div class="gap">… {len(f["lines"]) - max_lines} more lines not shown</div>')
        out.append("    </div>")
        if file_notes:
            items = "".join(f"<li>{escape(n)}</li>" for n in file_notes)
            out.append(f'    <ol class="diff-notes" start="{first_pin}">{items}</ol>')
        out.append("  </details>")
    out.append(f"  <figcaption>{caption}</figcaption>")
    out.append("</figure>")
    return "\n".join(out) + "\n", [k for k in notes if k not in used]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("diff", nargs="?", type=Path, help="diff file; reads stdin when omitted")
    ap.add_argument("--caption", required=True, help="figcaption HTML, starting with a <b> title sentence")
    ap.add_argument("--notes", type=Path, help="JSON object mapping PATH:N or PATH:-N to note text")
    ap.add_argument("--max-lines", type=int, default=300, help="lines shown per file before truncating")
    ap.add_argument("-o", "--out", type=Path, help="write here instead of stdout")
    args = ap.parse_args()

    text = args.diff.read_text(encoding="utf-8") if args.diff else sys.stdin.read()
    files = parse(text)
    if not files:
        sys.exit("diff.py: no file changes found in the input")
    notes = json.loads(args.notes.read_text(encoding="utf-8")) if args.notes else {}
    bad = [k for k in notes if not re.fullmatch(r".+:-?\d+", k)]
    if bad:
        sys.exit("diff.py: note keys must be PATH:N or PATH:-N: " + ", ".join(bad))
    html, missed = render(files, args.caption, notes, args.max_lines)
    if missed:
        sys.exit("diff.py: no shown line matches these notes: " + ", ".join(missed))
    if args.out:
        args.out.write_text(html, encoding="utf-8")
    else:
        sys.stdout.write(html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
