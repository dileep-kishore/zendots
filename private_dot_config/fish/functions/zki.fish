function zki
    set -l session (zellij list-sessions | fzf --ansi -i | awk '{print $1}')
    or return
    zellij kill-session "$session"
end

