function copypath
    set -l target

    if test (count $argv) -gt 0
        set target $argv[1]
    else
        set target $PWD
    end

    if command -q realpath
        set target (realpath "$target")
    end

    if command -q wl-copy
        printf '%s' "$target" | wl-copy
    else if command -q pbcopy
        printf '%s' "$target" | pbcopy
    else
        printf '%s\n' "$target"
        return 1
    end

    printf '%s\n' "$target"
end

