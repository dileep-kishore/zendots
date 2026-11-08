#!/usr/bin/env python3
"""Print a CSV, TSV or JSON table as the JSON rows a widget block embeds.

Cells follow the BERIL Workbench reader (apps/api/beril_api/widgets.py `_cell`): "", NA, NaN, nan, null and
None become null; numeric text becomes a number; a leading-zero token ("007") and an integer past 2**53 stay
strings, because they are identifiers or would lose digits as JSON numbers.

The output escapes "<" as \\u003c, so it can be pasted into a <script type="application/json"> block as is.

Usage: rows.py FILE [--columns a,b,c] [--limit N]
"""
import argparse
import csv
import io
import json
import math
import re
import sys
from pathlib import Path

MISSING = frozenset({"", "NA", "NaN", "nan", "null", "None"})
SAFE_INT = 2**53 - 1


def cell(value):
    """Return a CSV cell as a number when it is one, None when it is missing."""
    if value is None:
        return None
    text = str(value).strip()
    if text in MISSING:
        return None
    if re.fullmatch(r"-?0\d+", text):
        return text
    if re.fullmatch(r"-?\d+", text):
        return int(text) if abs(int(text)) <= SAFE_INT else text
    try:
        number = float(text)
    except ValueError:
        return text
    if math.isnan(number) or math.isinf(number):
        return text
    return int(number) if number.is_integer() and "." not in text else number


def json_cell(value):
    # Python's JSON reader accepts NaN and Infinity; the browser's JSON.parse refuses them.
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, str) and value.strip() in MISSING:
        return None
    return value


def read(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    suffix = path.suffix.lower()
    if suffix == ".json":
        loaded = json.loads(text)
        rows = loaded.get("rows") if isinstance(loaded, dict) else loaded
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            sys.exit("rows.py: JSON must be a list of objects or {rows: [...]}")
        return [{str(k): json_cell(v) for k, v in r.items()} for r in rows]
    if suffix not in (".csv", ".tsv"):
        sys.exit(f"rows.py: expected .csv, .tsv or .json, got {suffix or 'no suffix'}")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t" if suffix == ".tsv" else ",")
    rows = []
    for r in reader:
        if None in r:
            sys.exit(f"rows.py: line {reader.line_num} has more fields than the header")
        rows.append({str(k): cell(v) for k, v in r.items()})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--columns", help="comma-separated fields to keep, in this order")
    ap.add_argument("--limit", type=int, help="keep the first N rows")
    args = ap.parse_args()
    rows = read(args.file)
    if args.columns:
        keep = [c.strip() for c in args.columns.split(",") if c.strip()]
        absent = [c for c in keep if rows and not any(c in r for r in rows)]
        if absent:
            sys.exit(f"rows.py: no row has {', '.join(absent)}")
        rows = [{c: r.get(c) for c in keep} for r in rows]
    if args.limit is not None:
        rows = rows[: args.limit]
    # "<" escaped so a cell holding "</script>" cannot end the <script> block the rows are pasted into.
    sys.stdout.write(json.dumps(rows, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c"))
    sys.stderr.write(f"rows.py: {len(rows)} rows\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
