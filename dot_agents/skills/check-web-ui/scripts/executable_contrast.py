#!/usr/bin/env python3
"""Print the WCAG 2.x contrast ratio of a foreground and background color.

Usage:
    contrast.py FOREGROUND BACKGROUND

Colors are hex (#RRGGBB, RRGGBB, or #RGB). Reports the ratio and AA verdicts
for normal text (4.5:1), and for large text and UI components (3:1). Exits 0
only when the pair passes 4.5:1.

Examples:
    contrast.py "#777777" "#ffffff"
    contrast.py 555 000
"""

import argparse
import re
import sys


def luminance(hex_color):
    value = hex_color.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        raise ValueError(f"expected a hex color like #1A2B3C, got {hex_color!r}")
    channels = []
    for i in (0, 2, 4):
        c = int(value[i : i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("foreground")
    parser.add_argument("background")
    args = parser.parse_args()
    try:
        lighter, darker = sorted((luminance(args.foreground), luminance(args.background)))[::-1]
    except ValueError as exc:
        parser.error(str(exc))
    ratio = (lighter + 0.05) / (darker + 0.05)
    print(f"ratio: {ratio:.2f}:1")
    print(f"normal text (4.5): {'PASS' if ratio >= 4.5 else 'FAIL'}")
    print(f"large text / UI (3.0): {'PASS' if ratio >= 3 else 'FAIL'}")
    return 0 if ratio >= 4.5 else 1


if __name__ == "__main__":
    sys.exit(main())
