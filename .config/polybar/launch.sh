#!/usr/bin/env bash

# Останавливаем предыдущие инстансы
killall -q polybar 2>/dev/null || true
pkill -x polybar 2>/dev/null || true
sleep 0.2

# Запускаем полибар в фоне
nohup polybar main -c "$HOME/.config/polybar/config.ini" >/dev/null 2>&1 &
disown

