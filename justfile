default:
    @just --list --unsorted

host := `uname -n`
user := `whoami`
curr_dir := `pwd`

alias a := apply
alias d := diff

apply:
  chezmoi apply

diff:
  chezmoi diff

sync-from-home:
  ./private_dot_local/bin/executable_chezmoi-sync-from-home.sh

dump:
  cd pkgs && rm Brewfile && brew bundle dump --no-vscode

install:
  cd pkgs && brew bundle install

sync-gtk:
  chezmoi add ~/.config/gtk-3.0/settings.ini
  chezmoi add ~/.config/gtk-4.0/settings.ini

# Install/update agent skills, e.g. `just skills add mattpocock/skills`
skills *ARGS:
  agent-skills.sh {{ARGS}}

# Relink ~/.agents/skills into Claude Code
link-skills:
  link-agent-skills.sh

# Capture managed keys from a live tool config into its fragment, e.g. `just capture codex`
capture tool:
  uv run tools/cfg-capture.py {{tool}}
