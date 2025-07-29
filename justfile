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
