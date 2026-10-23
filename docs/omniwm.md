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
| H / L | Focus left / right |
| J / K | Focus down / up; switch to next / previous workspace at the edge |
| Arrow keys | Move in that direction |
| Tab | Toggle between current and last-used workspace |
| Space | Raycast, configured separately in Raycast |
| P | OmniWM command palette |
| Return | Toggle OmniWM fullscreen, within the workspace |
| O | Overview |
| Period / Comma | Cycle column width forward / backward |
| C | Center the column |
| V | Toggle floating |
| T | Toggle tabbed column |

Hyper excludes Shift, so Hyper+Shift+number is distinct from Hyper+number.
J/K use `focusWindowOrWorkspaceDown` / `focusWindowOrWorkspaceUp`, matching
Niri's Mod+J/K behavior. Workspace switching at the edge does not wrap.
All other keyboard bindings are Unassigned, preserving ordinary Option
shortcuts for apps. The remapper must keep the additional physical Shift
modifier when the WM key is held.

Reserve Hyper+Space for Raycast by setting its hotkey to
Control+Option+Command+Space. On the Go60, press Right Command+Space.
OmniWM's `openCommandPalette` uses Hyper+P, or Right Command+P on the Go60,
keeping Hyper+Space free for Raycast.

The config uses Niri scrolling, nine workspaces on the main monitor, 25/50/75/100%
column widths (50% by default), and a 6-point gap with no outer gaps. Borders
are enabled at 2 points, with a mauve base color, an enabled gradient, and an
8-point glow at 60% opacity. A lone column stays centered at its configured
width. Focus does not follow the mouse; keyboard focus still moves the pointer
to the focused window. The 28-point workspace bar overlaps the macOS menu bar
without reserving layout space. SketchyBar is not required by this layout,
although it remains in the Brewfile.

Twelve app rules set initial workspace placement for standard windows, including
Chrome to 1, T3 Code and Orca to 2, Notion to 6, Slack to 7, and Zotero to 8.
The complete assignments are in the file's `[[appRules]]` entries, alongside
app-specific minimum window sizes. Separate rules make Zoom and Granola's
standard windows float by default.

## Maintaining the config

Edit `private_dot_config/omniwm/settings.toml` in this repo, then preview and
apply the destination path above on macOS. Chezmoi ignores this config on
Linux. Preserve workspace IDs and every hotkey ID, including Unassigned
entries, when editing the generated file. IPC is enabled for `omniwmctl` checks
on the Mac; it does not make those checks available on Linux.

`brew upgrade` replaces the app without restarting it, so the old version keeps
running until you quit and reopen OmniWM. Until then the new `omniwmctl` fails
with `transport_failure` or `protocol_mismatch`; `omniwmctl version` reports
the running version once they match. A restart can migrate `settings.toml` to a
new schema and leave the original as `settings.toml.pre-v<N>`. Compare the two,
capture the result with `chezmoi add` as below, then delete the backup to
dismiss OmniWM's notice. The file uses schema 4, written by OmniWM 0.7.6;
upgrade OmniWM on each other Mac before applying it there.

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
