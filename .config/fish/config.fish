# Wu-Tang Clan Theme & Configuration for Fish Shell

if status is-interactive
    # Syntax Highlighting Colors (Wu-Tang Gold & Onyx Palette)
    set -g fish_color_normal ffffff
    set -g fish_color_command ffb800 --bold
    set -g fish_color_keyword ffd700
    set -g fish_color_quote d4af37
    set -g fish_color_redirection ffffff
    set -g fish_color_end ffb800
    set -g fish_color_error ff5555 --bold
    set -g fish_color_param ffffff
    set -g fish_color_comment 776644
    set -g fish_color_selection --background=ffb800 000000
    set -g fish_color_search_match --background=ffb800 000000
    set -g fish_color_operator ffb800
    set -g fish_color_escape ffd700
    set -g fish_color_autosuggestion 665533
    set -g fish_color_cwd ffb800
    set -g fish_color_user ffb800
    set -g fish_color_host ffffff
    set -g fish_color_cancel ff5555

    # Completion Pager Colors
    set -g fish_pager_color_prefix ffb800 --bold
    set -g fish_pager_color_completion ffffff
    set -g fish_pager_color_description 8c7b58
    set -g fish_pager_color_progress ffb800
    set -g fish_pager_color_selected_background --background=ffb800
    set -g fish_pager_color_selected_prefix 000000 --bold
    set -g fish_pager_color_selected_completion 000000
    set -g fish_pager_color_selected_description 333333

    # Useful Aliases
    alias c='clear'
    alias cr='reset'
    alias ff='fastfetch'
    alias fm='thunar'
    alias cdtmp='cd (mktemp -d)'
    alias ctmp='cd (mktemp -d)'
    alias ls='ls --color=auto'
    alias ll='ls -lh --color=auto'
    alias la='ls -la --color=auto'
end

# System Paths
fish_add_path $HOME/.local/bin
fish_add_path $HOME/.spicetify
