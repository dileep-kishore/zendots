#!/usr/bin/env bash
# Read, set, or list each repo's Linear project link (git config zendots.linearProject).
# The key lives in the repo's own .git/config: never committed, read by every
# worktree, and synced to the other machines with the project folder.
set -euo pipefail

KEY="zendots.linearProject"
# Team keys of the user's Linear workspace; override with LINEAR_TEAM_KEYS="ABC|XYZ".
TEAM_KEYS="${LINEAR_TEAM_KEYS:-LBNL|PLA|LEA|REL}"

usage() {
  cat <<'USAGE'
repo-link.sh: the repo-to-Linear-project link, stored as git config zendots.linearProject

Usage:
  repo-link.sh get   [--dir DIR]          print the project ID or "none"; exit 1 when unset
  repo-link.sh set   VALUE [--dir DIR]    VALUE is a Linear project ID (P-LBNL-31) or "none"
  repo-link.sh unset [--dir DIR]          remove the link
  repo-link.sh list  [--root DIR ...]     every repo under the synced roots, with its link
  repo-link.sh scan  [--dir DIR] [--base REF] [--text FILE]
                                          find Linear issue IDs or links in the branch name,
                                          the commits after REF, and FILE (a draft PR title
                                          or body); exit 1 when any is found

Examples:
  repo-link.sh get
  repo-link.sh set P-PLA-33 --dir /Volumes/WorkSSD/Personal/bellwether
  repo-link.sh set none
  repo-link.sh list
  repo-link.sh scan --base origin/main --text /tmp/pr-body.md
USAGE
}

die() { echo "repo-link.sh: $*" >&2; exit 2; }

default_roots() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "/Volumes/WorkSSD"
  else
    echo "$HOME/Documents"
  fi
  echo "$HOME/zendots"
}

cmd="${1:-}"
[[ -z "$cmd" || "$cmd" == "-h" || "$cmd" == "--help" ]] && { usage; exit 0; }
shift

dir="."
value=""
base=""
textfile=""
roots=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) [[ $# -ge 2 ]] || die "--dir needs a path"; dir="$2"; shift 2 ;;
    --root) [[ $# -ge 2 ]] || die "--root needs a path"; roots+=("$2"); shift 2 ;;
    --base) [[ $# -ge 2 ]] || die "--base needs a ref"; base="$2"; shift 2 ;;
    --text) [[ $# -ge 2 ]] || die "--text needs a file"; textfile="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    -*) die "unknown flag $1 (try --help)" ;;
    *) [[ -z "$value" ]] || die "unexpected argument $1"; value="$1"; shift ;;
  esac
done

in_repo() {
  git -C "$dir" rev-parse --git-dir >/dev/null 2>&1 || die "$dir is not a git repository"
}

case "$cmd" in
  get)
    in_repo
    if v="$(git -C "$dir" config --local --get "$KEY")"; then
      echo "$v"
    else
      echo "repo-link.sh: no Linear project linked for $(git -C "$dir" rev-parse --show-toplevel); run: repo-link.sh set <project-id|none>" >&2
      exit 1
    fi
    ;;
  set)
    in_repo
    [[ -n "$value" ]] || die "set needs a value, for example: repo-link.sh set P-LBNL-31"
    [[ "$value" == "none" || "$value" =~ ^P-[A-Z0-9]+-[0-9]+$ ]] \
      || die "value must be a Linear project ID such as P-LBNL-31, or none"
    current="$(git -C "$dir" config --local --get "$KEY" || true)"
    if [[ "$current" == "$value" ]]; then
      echo "already $KEY=$value"
    else
      git -C "$dir" config --local "$KEY" "$value"
      echo "set $KEY=$value"
    fi
    ;;
  unset)
    in_repo
    if git -C "$dir" config --local --get "$KEY" >/dev/null; then
      git -C "$dir" config --local --unset "$KEY"
      echo "unset $KEY"
    else
      echo "already unset"
    fi
    ;;
  list)
    if [[ ${#roots[@]} -eq 0 ]]; then
      while IFS= read -r r; do roots+=("$r"); done < <(default_roots)
    fi
    for root in "${roots[@]}"; do
      [[ -d "$root" ]] || continue
      # Main checkouts only: a worktree's .git is a file and shares its repo's config.
      # A permission-denied folder makes find exit non-zero; keep the other roots.
      find "$root" -maxdepth 9 \( -name node_modules -o -name .t3 -o -name .venv \) -prune \
        -o -type d -name .git -print -prune 2>/dev/null || true
    done | sort -u | while IFS= read -r gitdir; do
      repo="$(dirname "$gitdir")"
      printf '%s\t%s\n' "$repo" "$(git -C "$repo" config --local --get "$KEY" || echo "(unset)")"
    done
    ;;
  scan)
    in_repo
    pattern="linear\.app/|\b(${TEAM_KEYS})-[0-9]+\b"
    found=0
    branch="$(git -C "$dir" branch --show-current)"
    if printf '%s\n' "$branch" | grep -Eiq "$pattern"; then
      echo "branch: $branch"; found=1
    fi
    if [[ -n "$base" ]]; then
      git -C "$dir" rev-parse --verify -q "$base^{commit}" >/dev/null \
        || die "base $base does not resolve; fetch it or pass another ref"
      while IFS= read -r line; do
        echo "commit: $line"; found=1
      done < <(git -C "$dir" log --format='%h %s%n%b' "$base"..HEAD | grep -Ei "$pattern" || true)
    fi
    if [[ -n "$textfile" ]]; then
      [[ -f "$textfile" ]] || die "no such file $textfile"
      while IFS= read -r line; do
        echo "text: $line"; found=1
      done < <(grep -Ei "$pattern" "$textfile" || true)
    fi
    if [[ $found -eq 1 ]]; then
      echo "repo-link.sh: Linear references found; remove them before pushing" >&2
      exit 1
    fi
    echo "no Linear references"
    ;;
  *) die "unknown command $cmd (try --help)" ;;
esac
