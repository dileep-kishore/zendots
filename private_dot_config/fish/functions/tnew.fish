function tnew
    set -l target $PWD
    if test (count $argv) -gt 0
        set target $argv[1]
    end

    ~/.config/tmux/scripts/start-standard-session.sh $target
end
