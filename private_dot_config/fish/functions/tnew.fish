function tnew
    if test (count $argv) -lt 1
        echo "Usage: tnew <session-name> [directory]" >&2
        return 1
    end

    set -l session_name $argv[1]
    set -l target $PWD
    if test (count $argv) -gt 1
        set target $argv[2]
    end

    ~/.config/tmux/scripts/register-sesh-session.sh $session_name $target
    and ~/.config/tmux/scripts/start-standard-session.sh $target $session_name
end
