function fish_user_key_bindings
    if set -q AGENT_SHELL
        return
    end

    if functions -q _atuin_search
        bind \cr _atuin_search
        bind -M insert \cr _atuin_search
    end

    bind \ee aichat_edit
end
