function tnew
    bash ~/.config/tmux/scripts/templater.sh $argv
    tmuxinator start $argv[1]
end

