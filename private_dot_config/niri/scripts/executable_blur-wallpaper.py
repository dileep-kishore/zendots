#!/usr/bin/env python3

import json
import os
import subprocess

wallpapers_cache_path = os.path.expanduser("~/.cache/swww/")
events_of_interest = ["Workspace focused", "Window opened", "Window closed"]


def get_niri_msg_output(msg):
    output = subprocess.check_output(["niri", "msg", "-j", msg])
    output = json.loads(output)
    return output


def get_current_wallpaper(monitor):
    with open(os.path.join(wallpapers_cache_path, monitor)) as f:
        wallpaper_string = str(f.readlines()[-1].strip())
        wallpaper = "/home/dileep" + wallpaper_string.split("/home/dileep")[-1]
        print(f"Current wallpaper for {monitor} is {wallpaper}")
        return wallpaper


def set_wallpaper(monitor, wallpaper):
    print(f"Setting wallpaper for {monitor} to {wallpaper}")
    subprocess.run(
        [
            "swww",
            "img",
            "--transition-type",
            "grow",
            "-o",
            monitor,
            wallpaper,
        ]
    )


def change_wallpaper_on_event():
    workspaces = get_niri_msg_output("workspaces")
    active_workspaces = [
        workspace for workspace in workspaces if workspace["is_active"]
    ]
    for active_workspace in active_workspaces:
        active_workspace_is_empty = active_workspace["active_window_id"] is None
        active_workspace_monitor = active_workspace["output"]
        current_wallpaper = get_current_wallpaper(active_workspace_monitor)
        unblurred_wallpaper = current_wallpaper.replace("-blurred", "")
        blurred_wallpaper = unblurred_wallpaper.split(".png")[0] + "-blurred.png"
        if active_workspace_is_empty:
            wallpaper = unblurred_wallpaper
        else:
            print("Workspace is not empty, using blurred wallpaper")
            wallpaper = blurred_wallpaper
            if not os.path.exists(wallpaper):
                print(f"Blurred wallpaper {wallpaper} does not exist, using unblurred")
                wallpaper = unblurred_wallpaper
        if current_wallpaper != wallpaper:
            print(f"Setting wallpaper to {wallpaper}")
            set_wallpaper(active_workspace_monitor, wallpaper)


def main():
    event_stream = subprocess.Popen(
        ["niri", "msg", "event-stream"], stdout=subprocess.PIPE
    )
    for line in iter(event_stream.stdout.readline, ""):
        print(line.decode().strip())
        if any(event in line.decode() for event in events_of_interest):
            change_wallpaper_on_event()


if __name__ == "__main__":
    main()
