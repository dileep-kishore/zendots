# OmniWM on macOS

OmniWM's Hyper chord is Control+Option+Command, leaving Shift available for
moving windows to workspaces. `systemHyperTrigger = "None"` keeps key remapping
independent of the window manager.

The Go60 setup expects its existing Hyper key to send Right GUI, which macOS
sees as Right Command. Configure Karabiner separately to translate that key
into Control+Option+Command for every app, preserving an additional physical
Shift. This repo installs Karabiner through the Brewfile but does not ship the
remapping or keyboard firmware. A four-modifier firmware Hyper key will not
match these three-modifier bindings. Linux's Right GUI/Super behavior is
independent of this macOS configuration.

## Setup

1. Install with `brew install --cask omniwm` if missing; it is also listed in
   `pkgs/Brewfile`. Upstream currently requires macOS 26+ on Apple Silicon.
2. Turn off Stage Manager in System Settings > Desktop & Dock. Keep
   Displays have separate Spaces enabled under Mission Control. If you change
   that setting, log out and back in. Start with one native macOS Space.
3. Quit other window managers before starting OmniWM.
4. Preview `chezmoi diff -r ~/.config/omniwm`, then apply only the two managed
   files after approval:
   `chezmoi apply ~/.config/omniwm/settings.toml ~/.config/omniwm/shell/shell.toml`.
5. Open OmniWM. Grant Accessibility and Input Monitoring. Screen Recording is
   optional and enables Overview thumbnails. Click Start OmniWM or Continue
   Without Screen Recording in its permissions window.
6. Try the shortcuts below with two ordinary windows. Check that Hyper+2 and
   Hyper+1 switch workspaces, focusing scrolls the layout, and Hyper+Period
   cycles widths. Enable Start at Login after the trial works.

## Shortcuts

| Hold Hyper and press | Action |
| --- | --- |
| 1–9 | Switch to workspace 1–9 |
| Shift+1–9 | Move the focused window to workspace 1–9 |
| H / L | Focus left / right |
| J / K | Focus down / up; switch to next / previous workspace at the edge |
| Arrow keys | Move in that direction |
| Tab | Toggle between current and last-used workspace |
| Space | Raycast, configured separately in Raycast |
| P | OmniWM command palette |
| Return | Toggle the Quake Terminal (Ghostty) |
| O | Overview |
| Period / Comma | Cycle column width forward / backward |
| C | Center the column |
| V | Toggle floating |
| F | Jump between floating and tiled windows |
| M / Shift+M | Name the focused window with a mark / remove a mark |
| T | Toggle tabbed column |

Hyper excludes Shift, so Hyper+Shift+number is distinct from Hyper+number.
J/K use `focusWindowOrWorkspaceDown` / `focusWindowOrWorkspaceUp`, matching
Niri's Mod+J/K behavior. Workspace switching at the edge does not wrap.
All other keyboard bindings are Unassigned, preserving ordinary Option
shortcuts for apps. The remapper must keep the additional physical Shift
modifier when the WM key is held.

Hyper+F works in both directions. From a tiled window it raises the
workspace's floating windows and focuses the last-focused one; from a floating
window it returns to the last tiled window. Hyper+M prompts for a name. Marks
last until the window closes or OmniWM quits. To jump to a marked window, type
its name in the Hyper+P palette, where marks sort first, or run
`omniwmctl window mark focus <name>`.

Reserve Hyper+Space for Raycast by setting its hotkey to
Control+Option+Command+Space. On the Go60, press Right Command+Space.
OmniWM's `openCommandPalette` uses Hyper+P, or Right Command+P on the Go60,
keeping Hyper+Space free for Raycast.

The config uses Niri scrolling and ten workspaces. Workspaces 2, 3, and 10 are
pinned to the ASUS VG289 when it is connected, and the rest use the main
monitor. It sets 25/50/75/100% column widths (50% by default, 100% on the
MacBook's built-in display), and a 6-point gap with no outer gaps. Borders are
enabled at 2 points, with a mauve base color, an enabled gradient, and an
8-point glow at 60% opacity. A lone column stays centered at its configured
width. Focus does not follow the mouse; keyboard focus still moves the pointer
to the focused window. The workspace bar runs down the left screen edge, 32
points wide, below the macOS menu bar, and shows a dot on app icons with Dock
notification badges. Its position, size, and lanes come from the profile
override in `shell/shell.toml`, described below.
`reserveLayoutSpace = true` keeps tiled windows 32 points from the left edge,
and `notchMode = "off"` leaves the bar in place on a MacBook's notched screen.
The bar uses `windowLevel = "status"` (window layer 25), one layer below
Vorssaint's Dynamic Island (layer 26), so the island's expanded panel draws over the bar.
The `popup` level (layer 101) covered the panel. SketchyBar is not required by
this layout, although it remains in the Brewfile.

OmniWM 0.8.0 draws the workspace bar with OmniShell. Its bundled Default style
in `~/.config/omniwm/shell/default/` makes the bar full width at 32 points.
OmniWM manages that folder and overwrites it on update. A style's values take
precedence over the `[workspaceBar]` keys in `settings.toml`. A full-width bar
that is not `belowMenuBar` sets the macOS "Automatically hide and show the menu
bar" setting to Always. Third-party menu bar icons, such as BetterDisplay,
Raycast, and Tailscale, are then reachable only through OmniWM's Hidden Bar.
`shell/shell.toml` overrides the Default profile to keep the native menu bar
visible. It sets `position = "left"`, `fullWidth = false`, and `height = 32.0`,
which is the bar's thickness on a side edge. It limits the lanes to `omniwm`,
`workspaces`, and `scratchpads`, and uses the Catppuccin palette. A comment in
the file keeps the full-width top layout for switching back.

Quake Terminal is enabled with Ghostty as its provider, and Hyper+Return toggles
it. It slides in from the top at 80% width and 60% height, with 0.8 opacity and
a 25-point standard blur. It reads `~/.config/ghostty/config` through libghostty,
which ships no themes, so the repo keeps a copy of Ghostty's built-in
`Catppuccin Mocha` in `~/.config/ghostty/themes/`
([OmniWM #272](https://github.com/OmniNull/OmniWM/issues/272)). OmniWM fullscreen (`toggleFullscreen`) is Unassigned; Hyper+Period reaches
a 100% column width instead.

New Niri columns open at 50% width. A `[[monitorNiriOverrides]]` entry raises
that to 100% on the MacBook's built-in display only. OmniWM matches the entry
by display UUID (`37D8832A-…`), so external monitors keep 50% and the macmini
ignores the entry. `omniwmctl query displays` prints each display's UUID.

Twelve app rules set initial workspace placement for standard windows, including
Chrome to 1, T3 Code and Orca to 2, Notion to 6, Slack to 7, and Zotero to 8.
The complete assignments are in the file's `[[appRules]]` entries, alongside
app-specific minimum window sizes. Separate rules make Zoom and Granola's
standard windows float by default.

## Maintaining the config

Edit `private_dot_config/omniwm/settings.toml` or
`private_dot_config/omniwm/shell/shell.toml` in this repo, then preview and
apply the destination paths above on macOS. Chezmoi ignores this config on
Linux. Preserve workspace IDs and every hotkey ID, including Unassigned
entries, when editing the generated file. IPC is enabled for `omniwmctl` checks
on the Mac; it does not make those checks available on Linux.

`brew upgrade` replaces the app without restarting it, so the old version keeps
running until you quit and reopen OmniWM. Until then the new `omniwmctl` fails
with `transport_failure` or `protocol_mismatch`; `omniwmctl version` reports
the running version once they match. A restart can migrate `settings.toml` to a
new schema and leave the original as `settings.toml.pre-v<N>`. Compare the two,
capture the result with `chezmoi add` as below, then delete the backup to
dismiss OmniWM's notice. `settings.toml` uses schema 5, written by OmniWM 0.8.0,
which macmini and macbook both run. Upgrade OmniWM on a Mac before applying a
newer schema there.

After changing settings in OmniWM's GUI, capture the live files back into the
repo before applying dotfiles again:

```bash
chezmoi add ~/.config/omniwm/settings.toml ~/.config/omniwm/shell/shell.toml
chezmoi diff -r ~/.config/omniwm
chezmoi status ~/.config/omniwm
```

Both verification commands should print nothing when source and live settings
match. Review the captured changes with
`git diff -- private_dot_config/omniwm` from this repo. No
`chezmoi apply` is needed to capture GUI changes.

OmniWM rewrites `shell/shell.toml` when you change bar or palette settings in
its Settings window. The rewrite can drop the file's comments, including the
full-width lane layout, so check the diff for removed comments before
committing.

System-wide Window Corners and Start at Login are macOS preferences outside
this TOML file and must be configured separately on each Mac. This repo does
not set a custom system-wide corner override.

Official references: [installation](https://omniwm.app/guides/install/),
[configuration](https://omniwm.app/config/configuration/), and
[keyboard shortcuts](https://omniwm.app/guides/keyboard-shortcuts/).
