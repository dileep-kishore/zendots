# OmniWM on macOS

OmniWM's Hyper chord is Control+Option+Command, leaving Shift available for
moving windows to workspaces. `systemHyperTrigger = "None"` keeps key remapping
independent of the window manager.

The intended Go60 change is limited to its existing Hyper key: make it send
Right GUI. On macOS a separate remapper must translate Right Command into
Control+Option+Command for every app. On Linux Right GUI remains Super.
The remapper and firmware change are not configured by this repo yet; a
four-modifier firmware Hyper key will not match the new three-modifier bindings.
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
| Space | Command palette for commands without shortcuts |
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

The config uses Niri scrolling, nine workspaces on the main monitor, 25/50/75/100%
column widths, an 8-point gap, and a Catppuccin Mocha mauve focus border. A lone
column stays centered at its configured width. OmniWM's workspace bar sits below
the macOS menu bar with reserved space; SketchyBar is unnecessary.

## Maintaining the config

Edit `private_dot_config/omniwm/settings.toml` in this repo, then preview and
apply the destination path above. The file was generated from OmniWM 0.7.2.
Its strict schema requires every hotkey ID, including Unassigned entries.
OmniWM GUI changes write to the live file; review and bring any wanted changes
back into the repo before the next apply. IPC is enabled for `omniwmctl` checks.

Official references: [installation](https://omniwm.app/guides/install/),
[configuration](https://omniwm.app/config/configuration/), and
[keyboard shortcuts](https://omniwm.app/guides/keyboard-shortcuts/).
