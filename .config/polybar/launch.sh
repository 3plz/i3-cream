#!/usr/bin/env bash

# Останавливаем предыдущие инстансы
killall -q polybar 2>/dev/null || true
pkill -x polybar 2>/dev/null || true
sleep 0.2

# Запускаем полибар в новой независимой сессии (защита от SIGHUP)
setsid -f polybar main -c "$HOME/.config/polybar/config.ini" >/tmp/polybar.log 2>&1


