#!/usr/bin/env bash

export DISPLAY="${DISPLAY:-:0}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}"

# Kill existing instance if running
pkill -f "python3.*perf_widget/widget.py" 2>/dev/null || true
sleep 0.3

# Launch in background
nohup python3 /home/3plz/.config/perf_widget/widget.py >/tmp/perf_widget.log 2>&1 &
disown
