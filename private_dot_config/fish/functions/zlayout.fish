function zlayout
    set -l layout (fd . (zellij list-sessions -s) | sed 's|.*/||; s|\.[^.]*$||' | fzf --ansi -i)
    or return
    zellij --layout "$layout"
end

