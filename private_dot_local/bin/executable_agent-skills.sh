#!/usr/bin/env bash
# Run `npx skills` against the global skill store and record the result in
# chezmoi, so an install on one machine survives a `chezmoi update` on another.
#
#   agent-skills.sh add mattpocock/skills
#   agent-skills.sh update
#   agent-skills.sh remove wayfinder
#   agent-skills.sh sync            # record a hand-authored skill, no installer
#
# A skill that carries an upstream runtime (a Node package, a binary) is
# *fetched* rather than installed: the runtime is cloned to ~/.agents/runtimes
# and only a relative symlink enters the store, so the payload never reaches
# this repository or Syncthing.
#
#   agent-skills.sh fetch tt-a1i/archify --path archify
#   agent-skills.sh fetch                 # restore every runtime missing here
#   agent-skills.sh fetch --bump archify  # move the pin to the ref's tip
#   agent-skills.sh remove archify        # works for either kind
set -euo pipefail

store="$HOME/.agents/skills"
runtimes="$HOME/.agents/runtimes"
skill_lock="$HOME/.agents/.skill-lock.json"
runtime_lock="$HOME/.agents/.runtime-lock.json"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$1" >&2
    exit 1
  }
}

require_cmd chezmoi

lock_get() { # <name> <field>
  [ -f "$runtime_lock" ] || return 1
  jq -er --arg n "$1" --arg f "$2" '.skills[$n][$f] // empty' "$runtime_lock"
}

lock_names() {
  [ -f "$runtime_lock" ] || return 0
  jq -r '.skills | keys[]' "$runtime_lock"
}

# A fetched skill's store entry must be a symlink we own. Anything else there is
# either a real skill or the user's own data, and `chezmoi apply --force` -- the
# documented cross-machine command -- replaces a directory with the symlink and
# deletes its contents without listing them. Refuse instead.
assert_free_slot() { # <name> <expected link target>
  local target="$store/$1"
  [ -e "$target" ] || [ -L "$target" ] || return 0
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$2" ]; then
    return 0
  fi
  printf '%s already exists and is not a fetched-skill link.\n' "$target" >&2
  printf 'Compare, migrate or remove it before fetching %s.\n' "$1" >&2
  exit 1
}

# Reserve the name in exactly one lock. A stale `.skill-lock.json` entry would
# let `update` spawn `add`, which recursively removes the canonical path and
# copies the whole upstream tree back into the store.
assert_not_installed() { # <name>
  [ -f "$skill_lock" ] || return 0
  jq -e --arg n "$1" '.skills | has($n)' "$skill_lock" >/dev/null 2>&1 || return 0
  printf '%s is recorded in .skill-lock.json as a normal install.\n' "$1" >&2
  printf 'Run `agent-skills.sh remove %s` before fetching it.\n' "$1" >&2
  exit 1
}

# `git clone --depth 1` fetches only the ref tip; checking out an older recorded
# revision then fails with "unable to read tree" *and leaves HEAD at the tip*,
# so the wrong code would run silently. Fetch the revision itself instead.
checkout_revision() { # <dir> <url> <revision>
  git -C "$1" remote set-url origin "$2" 2>/dev/null ||
    git -C "$1" remote add origin "$2"
  git -C "$1" fetch --depth 1 --quiet origin "$3"
  git -C "$1" checkout --quiet --detach FETCH_HEAD
}

fetch_one() { # <name>
  local name="$1" url path rev dir link
  url="$(lock_get "$name" url)"
  path="$(lock_get "$name" path || true)"
  rev="$(lock_get "$name" revision)"
  dir="$runtimes/$name"
  # The skill may sit in a subdirectory of the repository (archify's SKILL.md is
  # at archify/SKILL.md), so the link points at that subdirectory, not the root.
  link="../runtimes/$name${path:+/$path}"

  assert_not_installed "$name"
  assert_free_slot "$name" "$link"

  mkdir -p "$dir"
  [ -d "$dir/.git" ] || git -C "$dir" init --quiet
  checkout_revision "$dir" "$url" "$rev"
  [ -f "$dir${path:+/$path}/SKILL.md" ] || {
    printf 'no SKILL.md at %s\n' "$dir${path:+/$path}" >&2
    printf 'check --path; the repository root is %s\n' "$dir" >&2
    exit 1
  }
  # archify and its kind ship an update checker that contacts a remote manifest
  # on every use. Its own SKILL.md says to continue silently when the checker
  # cannot run. A checkout restores it, so drop it after every one.
  rm -f "$dir${path:+/$path}/scripts/check-update.mjs"

  mkdir -p "$store"
  ln -sfn "$link" "$store/$name"
  printf 'fetched %s at %s\n' "$name" "${rev:0:12}"
}

record() {
  # `skills add` recursively removes the canonical path before copying, so an
  # install that happens to carry a fetched skill's name replaces the link with
  # the whole upstream tree. Catch it here, before it reaches chezmoi and git.
  local name link
  for name in $(lock_names); do
    link="../runtimes/$name$(lock_get "$name" path >/dev/null 2>&1 && printf '/%s' "$(lock_get "$name" path)")"
    [ "$(readlink "$store/$name" 2>/dev/null)" = "$link" ] && continue
    printf '%s is a fetched skill but %s is no longer its link.\n' "$name" "$store/$name" >&2
    printf 'Refusing to record. Restore it with `agent-skills.sh fetch`.\n' >&2
    exit 1
  done
  chezmoi add "$store" "$skill_lock"
  [ -f "$runtime_lock" ] && chezmoi add "$runtime_lock"
  "$HOME/.local/bin/link-agent-skills.sh"
  printf '\nrecorded in chezmoi -- commit and push to sync:\n  cd %s && git add -A && git commit && git push\n' \
    "$(chezmoi source-path)"
}

cmd_fetch() {
  require_cmd git
  require_cmd jq

  case "${1:-}" in
  "")
    # Restore every runtime this machine is missing. The store symlink is
    # already there from `chezmoi apply`; only the target is absent.
    local restored=0 path link
    for name in $(lock_names); do
      path="$(lock_get "$name" path || true)"
      link="../runtimes/$name${path:+/$path}"
      # Repair a missing runtime *or* a missing/incorrect store link; either one
      # leaves the skill undiscoverable.
      if [ -d "$runtimes/$name/.git" ] &&
        [ "$(readlink "$store/$name" 2>/dev/null)" = "$link" ]; then
        continue
      fi
      # No rm here: fetch_one refuses anything that is not already our link,
      # and `ln -sfn` replaces a stale one.
      fetch_one "$name"
      restored=1
    done
    [ "$restored" = 1 ] || {
      printf 'every fetched runtime is present\n'
      return 0
    }
    ;;
  --bump)
    local name="${2:?usage: agent-skills.sh fetch --bump <name>}"
    local url ref rev
    url="$(lock_get "$name" url)"
    ref="$(lock_get "$name" ref)"
    rev="$(git ls-remote "$url" "$ref" | cut -f1)"
    [ -n "$rev" ] || {
      if [ "${#ref}" = 40 ]; then
        printf '%s is pinned to commit %s, which has no branch to follow.\n' "$name" "${ref:0:12}" >&2
        printf 'Re-fetch with `--ref <branch>` to track one.\n' >&2
      else
        printf 'cannot resolve %s on %s\n' "$ref" "$url" >&2
      fi
      exit 1
    }
    tmp="$(mktemp)"
    jq --arg n "$name" --arg r "$rev" '.skills[$n].revision = $r' \
      "$runtime_lock" >"$tmp" && mv "$tmp" "$runtime_lock" && chmod 644 "$runtime_lock"
    fetch_one "$name"
    ;;
  *)
    local repo="$1" name path ref url rev tmp
    shift
    path=""
    ref=""
    while [ $# -gt 0 ]; do
      case "$1" in
      --path)
        path="${2:?--path needs a value}"
        shift 2
        ;;
      --ref)
        ref="${2:?--ref needs a value}"
        shift 2
        ;;
      *)
        printf 'unknown option: %s\n' "$1" >&2
        exit 1
        ;;
      esac
    done
    # `owner/name` is GitHub shorthand; anything with a scheme or a leading
    # slash is taken as the URL itself, which also covers other hosts.
    case "$repo" in
    *://* | /*) url="$repo" ;;
    *) url="https://github.com/$repo.git" ;;
    esac
    # The skill is named for its directory, which is the subdirectory when one
    # was given and the repository otherwise.
    name="$(basename "${path:-${repo%.git}}")"
    if [ -z "$ref" ]; then
      ref="$(git ls-remote --symref "$url" HEAD |
        awk '/^ref:/ {sub("refs/heads/", "", $2); print $2; exit}')"
    fi
    # `ls-remote` lists refs, never bare object ids, so a commit passed as --ref
    # is already the revision.
    case "$ref" in
    [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]*)
      if [ "${#ref}" = 40 ]; then rev="$ref"; else rev=""; fi
      ;;
    *) rev="" ;;
    esac
    [ -n "$rev" ] || rev="$(git ls-remote "$url" "$ref" | cut -f1)"
    [ -n "$rev" ] || {
      printf 'cannot resolve %s on %s\n' "$ref" "$url" >&2
      exit 1
    }
    [ -f "$runtime_lock" ] || printf '{"version":1,"skills":{}}\n' >"$runtime_lock"
    tmp="$(mktemp)"
    jq --arg n "$name" --arg u "$url" --arg f "$ref" --arg r "$rev" --arg p "$path" \
      '.skills[$n] = ({url: $u, ref: $f, revision: $r} + (if $p == "" then {} else {path: $p} end))' \
      "$runtime_lock" >"$tmp" && mv "$tmp" "$runtime_lock" && chmod 644 "$runtime_lock"
    fetch_one "$name"
    ;;
  esac
  record
}

# `npx skills remove` filters candidates with isDirectory(), so it reports
# "No skills found to remove" for a fetched symlink. And dropping the link is
# not enough: `chezmoi add` on the parent leaves the managed symlink_<name>
# source entry, which the next apply would restore.
cmd_remove_fetched() { # <name>
  require_cmd jq
  local name="$1" tmp
  rm -f "$store/$name"
  chezmoi forget --force "$store/$name" 2>/dev/null || true
  rm -rf "${runtimes:?}/$name"
  tmp="$(mktemp)"
  jq --arg n "$name" 'del(.skills[$n])' "$runtime_lock" >"$tmp" && mv "$tmp" "$runtime_lock" && chmod 644 "$runtime_lock"
  printf 'removed fetched skill %s\n' "$name"
  record
}

case "${1:-}" in
fetch)
  shift
  cmd_fetch "$@"
  exit 0
  ;;
remove)
  if [ -n "${2:-}" ] && command -v jq >/dev/null 2>&1 &&
    jq -e --arg n "$2" '.skills | has($n)' "$runtime_lock" >/dev/null 2>&1; then
    cmd_remove_fetched "$2"
    exit 0
  fi
  ;;
esac

# `skills` installs project-locally when the cwd is a git repo; run from $HOME so
# it always resolves to the global store, whether or not -g was passed.
if [ "${1:-}" != "sync" ]; then
  require_cmd npx
  (cd "$HOME" && npx -y skills@latest "$@")
fi

record
