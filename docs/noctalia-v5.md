# Noctalia v5 on Niri

Native Noctalia v5 reads TOML, so it does not import the old QML shell's
`~/.config/noctalia/settings.json`. That JSON, its colors, and its plugin
settings remain available for reference or rollback.

The port lives in `private_dot_config/noctalia/config.toml` and deploys to
`~/.config/noctalia/config.toml`. It carries the supported preferences and bar
layout, using the built-in Catppuccin palette in dark mode. Defaults stay in
Noctalia rather than being copied into this file.

Niri starts `noctalia`. Mod+Alt+W runs `noctalia msg bar-toggle`.
These commands belong to native v5; the old `qs -c noctalia-shell` commands
start the separate v4 shell.

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

## Plugin replacements

The old QML plugins cannot run in native v5. The port enables these native
equivalents from the catalog:

| v4 plugin | Native v5 plugin |
| --- | --- |
| Catwalk | `dotnetrob/cat` |
| Update count | `yuuto/arch-updater` |
| Syncthing status | `rylos/syncthing` |
| Tailscale | `rylos/tailnet` |
| Timer | `noctalia/timer` |

Timer remains available without adding a timer widget to the bar. The native
polkit agent replaces the old authentication plugin.

## Differences from v4

- Assistant and AI usage widgets have no ready replacement with the currently
  installed tools, so their bar entries are omitted.
- Native Caffeine replaces Keep Awake, but does not preserve its duration
  countdown or inhibition scopes.
- VPN status is shown inside Network. Workspace app groups use a native grouped
  taskbar; media progress and visualization use a fill and spectrum instead of
  the old ring and wave.
- Panel opacity does not reproduce the old `0.9` setting exactly. Per-urgency
  notification timeouts of 3/8/15 seconds and low-urgency notification history
  do not have equivalent native settings in this port.
- Control Center supports six shortcuts. The wallpaper shortcut is omitted
  because wallpaper management was disabled; the other six are retained.
- Tailnet provides the migrated status display and receive settings, without
  preserving the old plugin's Taildrop send or account-switching controls.

Keep the old shell packages and JSON until the native layout and plugin
behavior have been checked on the desktop.
