# Noctalia v5 on Niri

The managed config is `private_dot_config/noctalia/config.toml`, deployed to
`~/.config/noctalia/config.toml` on Linux only. It uses the built-in Catppuccin
palette in dark mode and leaves unspecified settings at Noctalia's defaults.

Niri starts `noctalia` from `private_dot_config/niri/config.kdl`.
Mod+Alt+W runs `noctalia msg bar-toggle`. The Arch package scripts do not
install Noctalia itself; install native v5 separately using the
[upstream installation guide](https://docs.noctalia.dev/noctalia/getting-started/installation/).
The old `qs -c noctalia-shell` command starts the separate v4 QML shell, not
this configuration. QML plugins and `settings.json` are not native v5 config;
this repository no longer ships those files.

## Current desktop behavior

- A 37-pixel top bar reserves space and does not auto-hide. App icons, the
  active window, and media are on the left; workspace-grouped apps and the
  clock are centered; notifications, updates, tray, system status, session,
  and Caffeine are on the right.
- Noctalia's polkit agent is enabled. Its dock, desktop widgets, wallpaper
  management, idle lock/screen-off/suspend actions, and scheduled night light
  are disabled.
- Niri starts `hypridle` instead. The managed
  `private_dot_config/hypr/hypridle.conf` turns displays off after 15 minutes
  and requests a session lock after 60 minutes, using Hyprlock. Mod+Alt+L also
  powers off monitors and starts Hyprlock after a three-second delay.
- Niri's `change-wallpaper.py` cycles images from `~/Pictures/swww/` every
  15 minutes using `awww`; Noctalia's configured wallpaper directory is inactive.
- Control Center has Wi-Fi, Bluetooth, notifications, power profile, Caffeine,
  and night light shortcuts. Weather is enabled with imperial units, but its
  address stays local.

## Applying and maintaining

From this repository, validate the source and preview only this destination:

```bash
noctalia config validate private_dot_config/noctalia/config.toml
chezmoi diff -r ~/.config/noctalia/config.toml
```

After approving that diff, apply only this file:

```bash
chezmoi apply ~/.config/noctalia/config.toml
noctalia config validate
```

Noctalia reloads configuration changes. Enabled native plugins are fetched from
its official and community catalogs; they do not require a custom Noctalia build.

GUI changes are saved in `~/.local/state/noctalia/settings.toml`, which loads
after the config and overrides duplicate values. If a source edit appears to
have no effect, inspect that state file before changing the shared config.
Keep the weather address in this local state through the weather settings UI;
do not add the address to the shared TOML.

To keep a GUI preference in dotfiles, copy only that setting into the managed
TOML. Preview and approve the scoped diff before applying. Once the source is
applied, remove that setting's local override so future source changes can take
effect. Preserve unrelated local state, including the weather address and
monitor-specific lockscreen layout; do not sync the whole state directory.

## Native plugins

The config enables these catalog plugins and sets automatic updates to all
enabled git sources:

| Purpose | Plugin |
| --- | --- |
| Cat widget | `dotnetrob/cat` |
| Arch update count | `yuuto/arch-updater` |
| Syncthing status | `rylos/syncthing` |
| Tailscale status | `rylos/tailnet` |
| Timer | `noctalia/timer` |

Timer is enabled without a timer widget on the bar. The update plugin uses
`paru` and `ghostty`, checks hourly, and disables Flatpak checks and update
notifications. Status plugins still need their corresponding services;
enabling a plugin does not install Syncthing or Tailscale.

For a running shell, inspect plugin availability or update a source with:

```bash
noctalia msg plugins list
noctalia msg plugins update official
noctalia msg plugins update community
```

Native plugins are fetched from the official and community catalogs without a
custom Noctalia build. GUI plugin toggles can override the managed enabled
list in the local `settings.toml`, just like other settings.

References: [configuration and precedence](https://docs.noctalia.dev/noctalia/configuration/)
and [native plugins](https://docs.noctalia.dev/noctalia/plugins/).
