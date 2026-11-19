#/usr/bin/sh

# Compositor
pgrep -x picom >/dev/null || picom -b &

# Notification Daemon
pgrep -x dunst >/dev/null || dunst &

# Wallpappers
bash ~/.fehbg
polybar main -c ~/.config/polybar/config.ini & disown

# Desktop Music Widget
bash ~/.config/sone_widget/launch.sh

# Performance Monitor Widget
bash ~/.config/perf_widget/launch.sh
