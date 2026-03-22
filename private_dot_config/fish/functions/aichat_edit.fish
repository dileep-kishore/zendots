function aichat_edit
    if not command -q aichat
        return 1
    end

    set -l buffer (commandline)
    if test -z "$buffer"
        return 0
    end

    commandline --replace "$buffer [ai]"
    commandline -f repaint

    set -l rewritten (aichat -e "$buffer")
    if test $status -ne 0
        commandline --replace "$buffer"
        commandline -f repaint
        return 1
    end

    commandline --replace "$rewritten"
    commandline -f end-of-line
    commandline -f repaint
end

