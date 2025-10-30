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

dump:
  cd pkgs && rm Brewfile && brew bundle dump

install:
  cd pkgs && brew bundle install

sync-gtk:
  chezmoi add ~/.config/gtk-3.0/settings.ini
  chezmoi add ~/.config/gtk-4.0/settings.ini
