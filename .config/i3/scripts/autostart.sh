#!/usr/bin/env bash

# Compositor
pgrep -x picom >/dev/null || picom -b &

# Notification Daemon
pgrep -x dunst >/dev/null || dunst &

# Display Layout & Monitor Configuration
[ -f ~/.config/i3/scripts/display_layout.sh ] && bash ~/.config/i3/scripts/display_layout.sh

# Wallpappers
bash ~/.fehbg
bash ~/.config/polybar/launch.sh

# Desktop Music Widget
bash ~/.config/sone_widget/launch.sh

# Performance Monitor Widget
bash ~/.config/perf_widget/launch.sh
