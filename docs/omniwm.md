# OmniWM on macOS

OmniWM's Hyper chord is Control+Option+Command, leaving Shift available for
moving windows to workspaces. `systemHyperTrigger = "None"` keeps key remapping
independent of the window manager.

The Go60's existing Hyper key sends Right GUI. On macOS Karabiner translates
Right Command into Control+Option+Command for every app. On Linux Right GUI
remains Super. The firmware and Karabiner configuration are managed separately
from this OmniWM file. A four-modifier firmware Hyper key will not match these
three-modifier bindings.
Keep the existing physical positions, layer behaviors, arrow keys, and Option
position. The Niri config is unchanged.

## Setup

1. Install with `brew install --cask omniwm` if missing.
2. Turn off Stage Manager in System Settings > Desktop & Dock. Keep
   Displays have separate Spaces enabled under Mission Control. If you change
   that setting, log out and back in. Start with one native macOS Space.
3. Quit other window managers before starting OmniWM.
4. Preview `chezmoi diff -r ~/.config/omniwm/settings.toml`, then apply only
   that file after approval: `chezmoi apply ~/.config/omniwm/settings.toml`.
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
| H / J / K / L | Focus left / down / up / right |
| Arrow keys | Move in that direction |
| Tab | Previous workspace |
| Space | Raycast, configured separately in Raycast |
| P | OmniWM command palette |
| Return | Toggle OmniWM fullscreen, within the workspace |
| O | Overview |
| Period / Comma | Cycle column width forward / backward |
| C | Center the column |
| V | Toggle floating |
| T | Toggle tabbed column |

Hyper excludes Shift, so Hyper+Shift+number is distinct from Hyper+number.
All other keyboard bindings are Unassigned, preserving ordinary Option
shortcuts for apps. The remapper must keep the additional physical Shift
modifier when the WM key is held.

Reserve Hyper+Space for Raycast by setting its hotkey to
Control+Option+Command+Space. On the Go60, press Right Command+Space.
OmniWM's `openCommandPalette` uses Hyper+P, or Right Command+P on the Go60,
keeping Hyper+Space free for Raycast.

The config uses Niri scrolling, nine workspaces on the main monitor, 25/50/75/100%
column widths, a 4-point gap with no outer gaps, and a Catppuccin Mocha mauve
focus border with an 8-point glow at 60% opacity. A lone column stays centered
at its configured width. Focus follows the mouse, and keyboard focus moves the
pointer to the focused window. The 28-point workspace bar overlaps the macOS
menu bar without reserving layout space; SketchyBar is unnecessary.

Twelve app rules set initial workspace placement for standard windows, including Chrome to 1,
T3 Code and Orca to 2, Notion to 6, Slack to 7, and Zotero to 8. The complete
assignments are in the file's `[[appRules]]` entries.

## Maintaining the config

Edit `private_dot_config/omniwm/settings.toml` in this repo, then preview and
apply the destination path above. Keep every hotkey ID, including Unassigned
entries, when editing the generated file. IPC is enabled for `omniwmctl` checks.

After changing settings in OmniWM's GUI, capture the live file back into the
repo before applying dotfiles again:

```bash
chezmoi add ~/.config/omniwm/settings.toml
chezmoi diff -r ~/.config/omniwm/settings.toml
chezmoi status ~/.config/omniwm/settings.toml
```

Both verification commands should print nothing when source and live settings
match. Review the captured changes with
`git diff -- private_dot_config/omniwm/settings.toml` from this repo. No
`chezmoi apply` is needed to capture GUI changes.

System-wide Window Corners and Start at Login are macOS preferences outside
this TOML file and must be configured separately on each Mac. This repo does
not set a custom system-wide corner override.

Official references: [installation](https://omniwm.app/guides/install/),
[configuration](https://omniwm.app/config/configuration/), and
[keyboard shortcuts](https://omniwm.app/guides/keyboard-shortcuts/).
