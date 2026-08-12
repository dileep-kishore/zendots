#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools"]
# ///
"""Build a single "Monaspace Mixed" family out of four Monaspace faces.

Ghostty and kitty take a separate font-family per style, so they can use Neon
for roman, Krypton for bold and Radon for italic. Apps that accept only one
family name -- Orca's xterm.js terminal, anything else built on a browser
engine -- cannot express that.

Relabelling the four faces into one family gives those apps the same result.
The italic slots deliberately use Radon's *upright* faces, matching ghostty's
font-style-italic = "Light": Radon's handwriting shapes are the distinction,
and its true italics come out slanted twice over. They are flagged italic in
OS/2 and head so the browser engine treats them as a real italic face -- given
an unflagged one it applies a synthetic skew of its own, which is what a
fontconfig alias cannot prevent.

Usage:
    ./make_monaspace_mixed.py [family-name]
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

FAMILY = sys.argv[1] if len(sys.argv) > 1 else "Monaspace Mixed"

IS_MAC = platform.system() == "Darwin"

# (source filename, subfamily, usWeightClass, italic slot)
# Weights are relabelled to 400/700 so a request for any normal weight lands on
# the Light faces rather than falling back to a heavier one. macOS keeps the
# working Frozen build; Linux uses terminal-sized Nerd Font glyphs for Orca.
FACES = (
    [
        ("MonaspaceNeonFrozen-Light.ttf", "Regular", 400, False),
        ("MonaspaceRadonFrozen-Light.ttf", "Italic", 400, True),
        ("MonaspaceKryptonFrozen-Bold.ttf", "Bold", 700, False),
        ("MonaspaceRadonFrozen-Bold.ttf", "Bold Italic", 700, True),
    ]
    if IS_MAC
    else [
        ("MonaspiceNeNerdFont-Light.otf", "Regular", 400, False),
        ("MonaspiceRnNerdFont-Light.otf", "Italic", 400, True),
        ("MonaspiceKrNerdFont-Bold.otf", "Bold", 700, False),
        ("MonaspiceRnNerdFont-Bold.otf", "Bold Italic", 700, True),
    ]
)
SEARCH_DIRS = (
    [Path.home() / "Library/Fonts", Path("/Library/Fonts")]
    if IS_MAC
    else [Path.home() / ".local/share/fonts", Path("/usr/share/fonts")]
)
# macOS ignores fonts nested in subdirectories of ~/Library/Fonts
OUT_DIR = (
    Path.home() / "Library/Fonts"
    if IS_MAC
    else Path.home() / ".local/share/fonts/monaspace-mixed"
)

# nameIDs holding family/style strings. 16/17 (typographic) and 21/22 (WWS)
# regroup a face under its original family, so they are dropped rather than set.
RENAMED = {1: None, 2: None, 3: None, 4: None, 6: None}
DROPPED = (16, 17, 21, 22)


def find_source(filename: str) -> Path:
    for root in SEARCH_DIRS:
        if root.is_dir():
            for hit in root.rglob(filename):
                return hit
    sys.exit(
        f"error: {filename} not found under {', '.join(str(d) for d in SEARCH_DIRS)}\n"
        + (
            "Install Monaspace Frozen from monaspace.githubnext.com."
            if IS_MAC
            else "Install Monaspice Nerd Font (Arch: otf-monaspace-nerd)."
        )
    )


def build(filename: str, subfamily: str, weight: int, italic: bool) -> Path:
    font = TTFont(find_source(filename))
    name = font["name"]
    postscript = f"{FAMILY.replace(' ', '')}-{subfamily.replace(' ', '')}"
    full = f"{FAMILY} {subfamily}"

    for record in list(name.names):
        if record.nameID in DROPPED or record.nameID in RENAMED:
            name.names.remove(record)
    for nid, value in ((1, FAMILY), (2, subfamily), (3, full), (4, full), (6, postscript)):
        name.setName(value, nid, 3, 1, 0x409)

    os2, head = font["OS/2"], font["head"]
    os2.usWeightClass = weight
    # fsSelection bit 0 italic / 5 bold / 6 regular are mutually exclusive
    selection = os2.fsSelection & ~0b1100001
    mac_style = head.macStyle & ~0b11
    if italic:
        selection |= 1 << 0
        mac_style |= 1 << 1
    if weight >= 700:
        selection |= 1 << 5
        mac_style |= 1 << 0
    elif not italic:
        selection |= 1 << 6
    os2.fsSelection, head.macStyle = selection, mac_style
    # glyphs are upright even in the italic slots, so italicAngle stays 0

    out = OUT_DIR / f"{postscript}{Path(filename).suffix}"
    font.save(out)
    return out


if OUT_DIR.name == "monaspace-mixed" and OUT_DIR.exists():
    shutil.rmtree(OUT_DIR)
OUT_DIR.mkdir(parents=True, exist_ok=True)

for face in FACES:
    print(f"  {build(*face).name}")

if not IS_MAC and shutil.which("fc-cache"):
    subprocess.run(["fc-cache", "-f", str(OUT_DIR)], check=True)

print(f'\nBuilt "{FAMILY}" in {OUT_DIR}')
print(f'Set it as the font family in Orca (Settings -> Terminal -> Font Family), then restart Orca.')
