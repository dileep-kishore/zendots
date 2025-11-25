#!/usr/bin/env python3

import subprocess
import time
from itertools import cycle
from pathlib import Path

WALLPAPERS_DIR = Path("~/Pictures/swww/").expanduser()
WALLPAPERS = []
for file in WALLPAPERS_DIR.iterdir():
    if file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        if "-blurred" not in file.stem:
            WALLPAPERS.append(file)


def set_wallpaper(wallpaper):
    subprocess.run(
        [
            "swww",
            "img",
            wallpaper,
            "--transition-type",
            "grow",
        ]
    )


def main():
    wallpaper_cycle = cycle(WALLPAPERS)
    for wallpaper in wallpaper_cycle:
        print(f"Setting wallpaper to {wallpaper}")
        set_wallpaper(wallpaper)
        time.sleep(900)


if __name__ == "__main__":
    main()
