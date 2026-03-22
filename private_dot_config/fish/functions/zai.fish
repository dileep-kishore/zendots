function zai
    set -l session (zellij list-sessions | fzf --ansi -i | awk '{print $1}')
    or return
    zellij attach "$session"
end

