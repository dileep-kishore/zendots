function extract
    if test (count $argv) -ne 1
        echo "usage: extract <archive>" >&2
        return 1
    end

    set -l archive $argv[1]

    if not test -f "$archive"
        echo "extract: file not found: $archive" >&2
        return 1
    end

    set -l lower (string lower -- "$archive")

    switch "$lower"
        case '*.tar.gz' '*.tgz'
            tar -xzf "$archive"
        case '*.tar.bz2' '*.tbz2'
            tar -xjf "$archive"
        case '*.tar.xz' '*.txz'
            tar -xJf "$archive"
        case '*.zip'
            unzip "$archive"
        case '*.gz'
            gunzip "$archive"
        case '*.bz2'
            bunzip2 "$archive"
        case '*.xz'
            unxz "$archive"
        case '*.7z'
            7z x "$archive"
        case '*'
            echo "extract: unsupported archive: $archive" >&2
            return 1
    end
end

