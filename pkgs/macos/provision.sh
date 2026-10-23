#!/usr/bin/env bash
# Run on the Mac Mini to seed a new Mac over SSH: secrets, one-time copies,
# and Syncthing sharing. Safe to rerun; it never overwrites a differing file.
# Usage: provision.sh [macbook]

set -euo pipefail

target="${1:-macbook}"
# ServerAlive ends a session the laptop drops by sleeping, instead of hanging.
ssh_opts=(-o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=10 -o ServerAliveCountMax=3)
syncthing_bin="/Applications/Syncthing.app/Contents/Resources/syncthing/syncthing"

say() { printf '%s\n' "$*"; }
die() { printf 'provision: %s\n' "$*" >&2; exit 1; }
remote() { ssh "${ssh_opts[@]}" "$target" "$@"; }

# The alias doubles as the new Mac's work-sync host name.
[[ "$target" == "macbook" ]] || die "target must be macbook, the work-sync host name"
[[ "$(uname -s)" == "Darwin" ]] || die "run this on the Mac Mini"
[[ -d /Volumes/WorkSSD ]] || die "/Volumes/WorkSSD is not mounted here"
[[ -f "$HOME/.config/chezmoi/key.txt" ]] || die "missing ~/.config/chezmoi/key.txt"

say "== Preflight on $target"
remote true </dev/null 2>/dev/null || die "cannot ssh to $target; run: ssh-copy-id $target"
[[ "$(remote id -un </dev/null)" == "$(id -un)" ]] || die "username on $target differs from $(id -un)"
remote 'test -d /Volumes/WorkSSD && test -w /Volumes/WorkSSD' </dev/null ||
    die "/Volumes/WorkSSD is missing or read-only on $target"
remote "test -x '$syncthing_bin' && pgrep -x syncthing >/dev/null" </dev/null ||
    die "Syncthing is not installed and running on $target"
say "ok: ssh, user, WorkSSD, Syncthing"

say "== Secrets"
remote 'mkdir -p ~/.config/chezmoi ~/.ssh ~/.config/work-sync && chmod 700 ~/.config/chezmoi ~/.ssh' </dev/null

# Prints the file's SHA-256 or "absent"; any ssh or read failure aborts, so an
# unknown state is never mistaken for a missing file.
remote_sum() {
    remote "if [ -e ~/$1 ]; then s=\$(shasum -a 256 ~/$1) || exit 2; echo \${s%% *}; else echo absent; fi" </dev/null ||
        die "cannot inspect ~/$1 on $target"
}

# Copy a file under $HOME with its mode, only when the target lacks it.
copy_file() {
    local rel="$1" local_sum theirs
    [[ -f "$HOME/$rel" ]] || { say "skip $rel: not on this Mac"; return; }
    local_sum=$(shasum -a 256 "$HOME/$rel" | cut -d' ' -f1)
    theirs=$(remote_sum "$rel")
    [[ -n "$theirs" ]] || die "cannot inspect ~/$rel on $target"
    if [[ "$theirs" == "$local_sum" ]]; then
        say "same $rel"
    elif [[ "$theirs" != absent ]]; then
        say "WARN $rel differs on $target; left unchanged"
    else
        # A staged name keeps an interrupted copy from passing as a differing file.
        scp -p -q "${ssh_opts[@]}" "$HOME/$rel" "$target:$rel.provision-tmp" </dev/null
        [[ "$(remote_sum "$rel.provision-tmp")" == "$local_sum" ]] ||
            die "copy of ~/$rel to $target is incomplete; rerun"
        remote "if [ -e ~/$rel ]; then rm -f ~/$rel.provision-tmp; exit 3; fi; mv ~/$rel.provision-tmp ~/$rel" </dev/null ||
            die "~/$rel appeared on $target during the copy; left unchanged"
        say "copy $rel"
    fi
}

for rel in .config/chezmoi/key.txt .config/chezmoi/chezmoi.toml \
    .ssh/github .ssh/github.pub .ssh/id_ed25519 .ssh/id_ed25519.pub \
    .ssh/id_kbase .ssh/id_kbase.pub .ssh/nersc .ssh/nersc.pub .ssh/known_hosts; do
    copy_file "$rel"
done

# Both Macs share id_ed25519, so each must accept it for ssh between them.
pubkey=$(cat "$HOME/.ssh/id_ed25519.pub")
if ! grep -qxF "$pubkey" "$HOME/.ssh/authorized_keys" 2>/dev/null; then
    # A file missing its final newline would merge the new key into the last line.
    if [[ -s "$HOME/.ssh/authorized_keys" && -n "$(tail -c 1 "$HOME/.ssh/authorized_keys")" ]]; then
        printf '\n' >>"$HOME/.ssh/authorized_keys"
    fi
    printf '%s\n' "$pubkey" >>"$HOME/.ssh/authorized_keys"
    say "add id_ed25519.pub to this Mac's authorized_keys"
fi
# Keys travel on stdin as data, and the file is read on fd 3 so ssh cannot
# consume the remaining lines.
while IFS= read -r key <&3 || [[ -n "$key" ]]; do
    [[ -n "$key" ]] || continue
    if printf '%s\n' "$key" | remote 'IFS= read -r k; f=~/.ssh/authorized_keys; [ -e "$f" ] || exit 1; grep -qxF -- "$k" "$f"'; then
        say "same authorized key: ${key##* }"
    else
        rc=$?
        ((rc == 1)) || die "cannot read ~/.ssh/authorized_keys on $target"
        printf '%s\n' "$key" | remote 'umask 077; f=~/.ssh/authorized_keys; if [ -s "$f" ] && [ -n "$(tail -c 1 "$f")" ]; then printf "\n" >>"$f"; fi; cat >>"$f"; chmod 600 "$f"'
        say "add authorized key: ${key##* }"
    fi
done 3<"$HOME/.ssh/authorized_keys"

host_file=$(remote 'cat ~/.config/work-sync/host 2>/dev/null || true' </dev/null) ||
    die "cannot read ~/.config/work-sync/host on $target"
if [[ "$host_file" != "$target" ]]; then
    remote "printf '%s\n' '$target' >~/.config/work-sync/host" </dev/null
    say "write ~/.config/work-sync/host = $target"
fi

say "== One-time copies"
# rsync fills a staging directory that is renamed only after it completes, so
# a rerun resumes an interrupted copy and never touches a finished one.
copy_dir() {
    local src="$1" dest="$2" state
    state=$(remote "if [ -e '$dest' ]; then echo exists; else echo absent; fi" </dev/null) ||
        die "cannot inspect $dest on $target"
    if [[ "$state" == exists ]]; then
        say "skip $dest: already on $target"
        return
    fi
    rsync -a -e "ssh ${ssh_opts[*]}" "$src/" "$target:$dest.partial/" </dev/null
    remote "mv '$dest.partial' '$dest'" </dev/null
    say "copy $src -> $dest"
}
if pgrep -x zotero >/dev/null; then
    say "WARN Zotero is running; quit it and rerun to copy ~/Zotero"
else
    copy_dir "$HOME/Zotero" "/Users/$(id -un)/Zotero"
fi
copy_dir /Volumes/WorkSSD/Pictures /Volumes/WorkSSD/Pictures

# Preferences only: BetterDisplay's license files stay with this Mac.
for domain in com.vorssaint.utils pro.betterdisplay.BetterDisplay; do
    state=$(remote "if defaults read $domain >/dev/null 2>&1; then echo present; else echo absent; fi" </dev/null) ||
        die "cannot read $domain settings on $target"
    if [[ "$state" == present ]]; then
        say "skip $domain: $target already has settings"
    else
        defaults export "$domain" - | remote "defaults import $domain -"
        say "copy $domain settings"
    fi
done

say "== Syncthing"
"$HOME/.local/bin/work-sync" add-device "$target" --yes </dev/null

say "== Waiting for ~/zendots on $target (up to 30 min)"
folder=zendots
mac_id=$("$syncthing_bin" device-id)
mac_key=$("$syncthing_bin" cli config gui apikey get)
mac_address=$("$syncthing_bin" cli config gui raw-address get)
key=$(remote "'$syncthing_bin' cli config gui apikey get" </dev/null)
address=$(remote "'$syncthing_bin' cli config gui raw-address get" </dev/null)
deadline=$((SECONDS + 1800))
failures=0
while :; do
    # An idle folder with nothing needed can still be empty, so also require
    # that the new Mac has received this Mac's current index.
    if ours=$(printf 'X-API-Key: %s\n' "$mac_key" |
        curl -fsS --max-time 15 -H @- "http://$mac_address/rest/db/status?folder=$folder") &&
        theirs=$(printf 'X-API-Key: %s\n' "$key" |
            remote "curl -fsS --max-time 15 -H @- 'http://$address/rest/db/status?folder=$folder'"); then
        failures=0
        progress=$(OURS="$ours" THEIRS="$theirs" MAC_ID="$mac_id" python3 -c '
import json, os
ours, theirs = json.loads(os.environ["OURS"]), json.loads(os.environ["THEIRS"])
received = theirs.get("remoteSequence", {}).get(os.environ["MAC_ID"], -1)
done = (theirs["state"] == "idle" and theirs["needTotalItems"] == 0
        and received >= ours["sequence"] and theirs["globalTotalItems"] > 0)
state, need, want = theirs["state"], theirs["needTotalItems"], ours["sequence"]
print("done" if done else "%s, %d items needed, index %d/%d" % (state, need, received, want))')
        if [[ "$progress" == done ]] &&
            remote 'test -f ~/zendots/.chezmoiignore && test -f ~/zendots/pkgs/macos/setup-mac.sh' </dev/null; then
            say "zendots is up to date on $target"
            break
        fi
    else
        failures=$((failures + 1))
        ((failures < 3)) || die "cannot read Syncthing status for $folder; is Syncthing running on both Macs?"
        progress="status unavailable"
    fi
    ((SECONDS < deadline)) || die "zendots still syncing ($progress); check the Syncthing GUI"
    say "zendots: $progress"
    sleep 20
done

say "Done. On $target: review chezmoi diff -r, run chezmoi apply,"
say "then run bash ~/zendots/pkgs/macos/setup-mac.sh."
say "After the overnight sync, rerun: work-sync add-device $target"
say "(it sets each repository's machine-local Git settings once .git has arrived)."
