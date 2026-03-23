#!/usr/bin/env bash
set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$1" >&2
    exit 1
  }
}

list_candidates() {
  chezmoi status --include=files --path-style=absolute |
    while IFS= read -r line; do
      local action
      status=${line:0:2}
      target=${line:3}

      [[ "$status" == "MM" ]] || continue

      source=$(chezmoi source-path "$target")
      action=re-add
      if [[ "$source" == *.tmpl ]]; then
        action=merge
      fi

      printf '%s\t%s\t%s\t%s\n' "$action" "$target" "$source" "$status"
    done
}

select_targets() {
  local candidates
  local fzf_status
  local selections
  candidates=$(list_candidates)

  if [[ -z "$candidates" ]]; then
    printf 'No diverged managed files found.\n'
    exit 0
  fi

  set +e
  selections=$(printf '%s\n' "$candidates" | fzf -m \
    --delimiter=$'\t' \
    --with-nth=1,2,3 \
    --preview "bash -lc 'row=\$1; action=\$(printf \"%s\" \"\$row\" | cut -f1); target=\$(printf \"%s\" \"\$row\" | cut -f2); source=\$(printf \"%s\" \"\$row\" | cut -f3); printf \"action: %s\\n\" \"\$action\"; printf \"target: %s\\n\" \"\$target\"; printf \"source: %s\\n\\n\" \"\$source\"; chezmoi diff --no-pager --color=always \"\$target\"' _ {}" \
    --preview-window=right,70%,border-left)
  fzf_status=$?
  set -e

  case $fzf_status in
    0)
      ;;
    1 | 130)
      return 0
      ;;
    *)
      printf 'fzf failed with exit code: %s\n' "$fzf_status" >&2
      return "$fzf_status"
      ;;
  esac

  if [[ -z "$selections" ]]; then
    return 0
  fi

  printf '%s\n' "$selections"
}

apply_selection() {
  local selections=$1
  local action row target

  while IFS= read -r row; do
    [[ -n "$row" ]] || continue
    action=$(printf '%s' "$row" | cut -f1)
    target=$(printf '%s' "$row" | cut -f2)

    case "$action" in
      merge)
        printf 'opening merge for template-backed file: %s\n' "$target"
        chezmoi merge "$target"
        ;;
      *)
        chezmoi re-add "$target"
        printf 're-added: %s\n' "$target"
        ;;
    esac
  done <<<"$selections"
}

main() {
  require_cmd chezmoi
  require_cmd fzf

  selections=$(select_targets)
  if [[ -z "$selections" ]]; then
    printf 'No files selected.\n'
    exit 0
  fi

  apply_selection "$selections"
}

main "$@"
