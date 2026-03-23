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
  cd pkgs && rm Brewfile && brew bundle dump

install:
  cd pkgs && brew bundle install

sync-gtk:
  chezmoi add ~/.config/gtk-3.0/settings.ini
  chezmoi add ~/.config/gtk-4.0/settings.ini
