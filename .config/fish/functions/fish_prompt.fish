function fish_prompt
    set -l last_status $status
    set -l gold (set_color --bold ffb800)
    set -l amber (set_color d4af37)
    set -l border (set_color 8c7b58)
    set -l white (set_color ffffff)
    set -l normal (set_color normal)
    set -l red (set_color --bold ff5555)

    # Prompt symbol color based on last command exit code
    set -l arrow_color $gold
    if test $last_status -ne 0
        set arrow_color $red
    end

    # User & Host
    set -l user_host "$gold $USER$border@$white"(prompt_hostname)

    # Current working directory
    set -l pwd_display (prompt_pwd)

    # Git branch & dirty indicator
    set -l git_info ""
    set -l branch (command git symbolic-ref --short HEAD 2>/dev/null; or command git rev-parse --short HEAD 2>/dev/null)
    if test -n "$branch"
        set -l dirty (command git status --porcelain 2>/dev/null | head -n 1)
        if test -n "$dirty"
            set git_info "$border─[$amber $branch*$border]"
        else
            set git_info "$border─[$gold $branch$border]"
        end
    end

    # Two-line Wu-Tang TUI prompt
    echo ""
    echo "$border┌─[$user_host$border]─[$amber $pwd_display$border]$git_info"
    echo "$border└─$arrow_color❯$normal "
end
