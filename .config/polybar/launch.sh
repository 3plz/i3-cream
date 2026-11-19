#!/usr/bin/env bash

# Останавливаем все запущенные инстансы polybar
killall -q polybar

# Ждём, пока процессы точно завершатся
while pgrep -u "$UID" -x polybar >/dev/null; do sleep 1; done

# Запускаем бар (имя бара "main" берётся из [bar/main] в config.ini)
nohup polybar main -c "$HOME/.config/polybar/config.ini" >/dev/null 2>&1 &
