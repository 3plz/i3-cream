#!/usr/bin/env bash

export DISPLAY="${DISPLAY:-:0}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}"

# Kill existing instance if running
pkill -f "python3.*sone_widget/widget.py" 2>/dev/null || true
sleep 0.3

# Launch detached from parent session
setsid -f python3 "$HOME/.config/sone_widget/widget.py" >/tmp/sone_widget.log 2>&1

