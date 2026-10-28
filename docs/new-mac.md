# Setting up another Mac

How to make a new Mac (first used for the LBNL MacBook, 2026-10) a copy of
macmini: same apps, dotfiles, synced folders, paths, and login items. The
visual version of this guide, with the reasoning behind each choice, lives in
the ignored `docs/plans/macbook-setup.html`.

The new Mac joins Syncthing as a third device. Project folders arrive directly
from macmini, so the receiving user creates every file and ownership is
correct. Do not stage data through an external drive: exFAT and volumes with
"Ignore ownership on this volume" drop owner and group.

## Before you start

- The account's short name must be `dkishore` (`id -un`). `work-sync`, the
  manifest, and absolute paths assume `/Users/dkishore`.
- The account needs admin rights (`id -Gn | grep -qw admin`), and macOS must
  be 26 or later on Apple silicon for OmniWM.
- On a managed laptop, MDM can block admin rights, extra APFS volumes,
  Karabiner's driver, Tailscale's network extension, or login items. If a check
  fails, ask IT before continuing.

## Sitting 1: bootstrap (about 45 minutes, then overnight)

On the new Mac:

1. Turn on System Settings > General > Sharing > Remote Login for your user.
   In its (i) panel, turn on "Allow full disk access for remote users";
   without it, macOS blocks SSH from writing into `~/Documents` and
   `~/Downloads`. Turn on FileVault under Privacy & Security, matching macmini.
   Sign in to the App Store so `mas` can install App Store apps.
2. Install Homebrew from <https://brew.sh>, then chezmoi, uv (several chezmoi
   templates run as uv scripts), and the network tools:

   ```bash
   brew install chezmoi uv
   brew install --cask tailscale-app syncthing-app
   ```

   Open Tailscale and sign in. Rename the machine to `macbook` in the Tailscale
   admin console so `macbook.tail870d70.ts.net` resolves. Open Syncthing once
   so it starts.
3. Create the synced-folder volume. It mounts at `/Volumes/WorkSSD`, matching
   macmini's paths exactly:

   ```bash
   diskutil list internal | grep "APFS Container Scheme"
   sudo diskutil apfs addVolume disk3 APFS WorkSSD -passprompt
   ```

   Use the container from the first command in place of `disk3`. In Disk
   Utility instead, select Macintosh HD, click + (Add APFS Volume), and choose
   "APFS (Encrypted)", not a case-sensitive format, since macmini's WorkSSD is
   case-insensitive. When Finder first asks for the passphrase, tick "Remember
   this password in my keychain". Reboot once and confirm `/Volumes/WorkSSD`
   mounts without a prompt.

   If the Mac came with Chrome or another Brewfile app already installed, let
   Homebrew take it over so `brew bundle` does not fail on it:
   `brew install --cask --adopt google-chrome`.

On macmini and on tsuki, give `ssh` the `macbook` alias. Without it, tsuki
logs in as `dileep` and `work-sync` reports the new Mac as unreachable:

```bash
chezmoi diff -r ~/.ssh/config   # adds Host macbook (and macmini on macOS)
chezmoi apply ~/.ssh/config
```

On macmini:

4. Authorize SSH once, then provision:

   ```bash
   ssh-copy-id macbook
   bash ~/zendots/pkgs/macos/provision.sh macbook
   ```

   The script copies the chezmoi age key and config, SSH keys, Zotero,
   Pictures, and the Vorssaint and BetterDisplay preferences. It writes
   `~/.config/work-sync/host`, runs `work-sync add-device macbook`, and waits
   until `~/zendots` is up to date on the new Mac. Quit Zotero first. Rerunning
   it skips what is already there, resumes an interrupted copy, and never
   overwrites a differing file. It waits until the new Mac has received
   macmini's current index of `~/zendots`, not only until the folder is idle.
   On a fresh Mac, `add-device` can sit for several minutes on one Syncthing
   call while the new device creates thousands of directories; it is busy, not
   hung.

   A managed laptop may sleep after a minute idle, which stops Syncthing. Keep
   it awake but let the screen sleep, and copy the home folders Syncthing does
   not carry. `ditto` keeps metadata and merges into the existing folders,
   overwriting same-named files, so check for name clashes first.
   `Library/Fonts` carries the fonts no cask provides, such as MonoLisa,
   Operator Mono, Dank Mono, Cartograph, SN Pro, and iA Writer:

   ```bash
   ssh macbook 'nohup caffeinate -ims -t 172800 >/dev/null 2>&1 </dev/null &'
   for d in Desktop Documents Downloads Library/Fonts; do
       ditto -c "$HOME/$d" - | ssh macbook "ditto -x - \"\$HOME/$d\""
   done
   ```

On the new Mac:

5. Apply the dotfiles and run the installer. The chezmoi config copied in
   step 4 already points at `~/zendots`, so no `chezmoi init` is needed:

   ```bash
   chezmoi diff -r | less
   chezmoi apply
   bash ~/zendots/pkgs/macos/setup-mac.sh
   ```

   This unscoped apply is a one-time exception to the repository's
   scoped-apply rule: on a fresh Mac the whole diff is the setup. The installer
   trusts the Brewfile's taps, runs `brew bundle`, `defaults.sh`, and
   `login-items.sh`, then installs TPM, Yazi plugins, the bat cache, and pipx
   packages. It lists failed steps at the end and can be rerun. Run over SSH,
   it installs everything except the `.pkg` casks and `mas` apps, which need a
   sudo password, and the login items, which need a click to let Terminal
   control System Events. Rerun it once in Terminal on the new Mac to finish
   those.

   The Brewfile installs opencode. Install the other coding agents with their
   vendors' installers, so each agent's own update command, which
   `agent-update` runs, works:

   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   curl -fsSL https://chatgpt.com/codex/install.sh | sh
   curl -fsSL https://pi.dev/install.sh | sh
   curl -fsSL https://omp.sh/install | sh
   curl https://cursor.com/install -fsS | bash
   ```

   Over SSH, `cursor-agent --version` fails on the locked login keychain. Check
   `agent-update` with
   `launchctl kickstart "gui/$(id -u)/com.dkishore.agent-update"` and read
   `~/.local/state/agent-update.log`.
6. On tsuki, run `ssh macbook true` once and accept the host key, so
   `work-sync`'s non-interactive SSH can reach the new Mac.
7. Leave the Mac plugged in and awake overnight while Syncthing copies the
   project folders.

## Sitting 2: permissions and sign-ins (about 45 minutes)

First, on macmini, once `work-sync status` shows every folder up to date on
the new Mac, run `work-sync add-device macbook` again. The first pass ran before
any `.git` arrived; this one sets each repository's machine-local Git settings,
such as `core.ignorecase`, which Syncthing does not carry.

macOS does not let scripts grant privacy permissions, so these stay manual.

- Grant Accessibility and Input Monitoring to OmniWM, Karabiner-Elements,
  Raycast, AltTab, BetterDisplay, and Wispr Flow when each asks. Give OmniWM
  Screen Recording for Overview. Approve Karabiner's driver under System
  Settings > General > Login Items & Extensions.
- Confirm Stage Manager is off and "Displays have separate Spaces" is on, then
  log out and back in.
- Import Raycast settings from a `.rayconfig` exported on macmini
  (Settings > Advanced), or turn on Cloud Sync. Set its hotkey to Hyper+Space.
- Enter the BetterDisplay license; its license files are not copied.
- Sign in to Chrome, Slack, Notion, Notion Calendar, Morgen, Superlist,
  Linear, Granola, Zoom, Spotify, ProtonVPN, ChatGPT, Claude, Grammarly,
  Cursor, and VS Code. Link Signal from your phone.
- Sign in to Zotero and enable sync; the library is already in `~/Zotero`.
- In Obsidian, open the vaults in `/Volumes/WorkSSD`.
- Run `claude` then `/login`, `codex login`, and `gh auth login`.
- Download the apps without a Homebrew cask from their vendors: Grok Bot and
  Superhuman Go. Rerun `pkgs/macos/login-items.sh` afterwards so Grok Bot
  becomes a login item.

## Final check

```bash
chezmoi status                                   # prints nothing
brew bundle check --file ~/zendots/pkgs/Brewfile # dependencies are satisfied
ssh macmini true && ssh tsuki true && echo ssh ok
ssh tsuki 'ssh -o BatchMode=yes macbook true' && echo tsuki reaches macbook
work-sync status                                 # every folder up to date
ssh macmini '~/.local/bin/work-sync add-device macbook --dry-run' # nothing left to change
osascript -e 'tell application "System Events" to get the name of every login item'
```

The login items should match macmini's, except Superfocus, which is retired.
With two windows open, Hyper+2 and Hyper+1 should switch OmniWM workspaces.

## Deliberately not installed

The laptop skips apps macmini has but rarely uses: Warp, AeroSpace, iMovie,
GarageBand, Pages, Sunsama, Todoist, OpenUsage, Quotio, Helium, Paseo, and bb.
Their configs stay in the repository. Agent session history (Claude Code,
Codex) is not copied.
