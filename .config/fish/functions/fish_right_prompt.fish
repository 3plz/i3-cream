function fish_right_prompt
    set -l amber (set_color 8c7b58)
    set -l gold (set_color ffb800)
    set -l normal (set_color normal)

    # Command execution time if > 1.2s
    set -l duration ""
    if test -n "$CMD_DURATION" -a "$CMD_DURATION" -gt 1200
        set -l secs (math -s1 "$CMD_DURATION / 1000")
        set duration "$gold󱫐 "$secs"s $amber│ "
    end

    set -l time_str (date "+%H:%M")
    echo -n "$duration$amber$time_str$normal"
end
