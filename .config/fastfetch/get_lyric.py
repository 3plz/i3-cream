#!/usr/bin/env python3
import sys
import os
import re
import json
import subprocess
import time

FALLBACK = "\033[1;38;2;255;184;0mSHAOLIN STYLE\033[0m ── \033[1;37m36 CHAMBERS\033[0m"
CACHE_DIR = os.path.expanduser("~/.cache/sone_widget")
CURRENT_FILE = os.path.join(CACHE_DIR, "current_lyric.txt")
LYRICS_DIR = os.path.join(CACHE_DIR, "lyrics")


def format_lyric(text):
    text = text.strip()
    if not text:
        return FALLBACK
    # Clean up outer parens if wrapped
    text = re.sub(r'^\((.*?)\)$', r'\1', text).strip()
    max_len = 42
    if len(text) > max_len:
        text = text[:max_len - 1].rstrip() + "…"
    return f"\033[1;38;2;255;184;0m♪\033[0m \033[1;37m{text}\033[0m \033[1;38;2;255;184;0m♪\033[0m"


def parse_lrc(lrc_text):
    lines = []
    pattern = re.compile(r'\[(\d+):(\d+(?:\.\d+)?)\](.*)')
    for raw in lrc_text.splitlines():
        match = pattern.match(raw.strip())
        if match:
            mins, secs, txt = match.groups()
            timestamp = int(mins) * 60 + float(secs)
            cleaned = txt.strip()
            if cleaned:
                lines.append((timestamp, cleaned))
    lines.sort(key=lambda x: x[0])
    return lines


def get_lyric():
    env = dict(os.environ, DISPLAY=":0", DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus")

    # Check playerctl status & position
    try:
        cmd = ["playerctl", "metadata", "--format", "{{status}}|||{{artist}}|||{{title}}|||{{album}}|||{{position}}"]
        res = subprocess.check_output(cmd, env=env, stderr=subprocess.DEVNULL, timeout=0.3).decode().strip()
        parts = res.split("|||")
        if len(parts) < 5:
            return FALLBACK
        status, artist, title, album, pos_raw = parts[:5]
        if status.lower() not in ("playing", "paused"):
            return FALLBACK
    except Exception:
        return FALLBACK

    # 1. Quick check: did widget write current_lyric.txt recently?
    if os.path.exists(CURRENT_FILE):
        try:
            mtime = os.path.getmtime(CURRENT_FILE)
            if time.time() - mtime < 4:
                with open(CURRENT_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return format_lyric(content)
        except Exception:
            pass

    # 2. Standalone calculation from position & LRC cache
    try:
        pos_sec = float(pos_raw) / 1000000.0 if pos_raw else 0.0
        safe_name = re.sub(r'[^\w\-_\.]', '_', f"{artist}_{title}")[:100]
        cache_file = os.path.join(LYRICS_DIR, f"{safe_name}.lrc")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                lines = parse_lrc(f.read())
            if lines:
                curr_t = ""
                for ts, txt in lines:
                    if ts <= pos_sec:
                        curr_t = txt
                    else:
                        break
                if curr_t:
                    return format_lyric(curr_t)
    except Exception:
        pass

    return FALLBACK


if __name__ == "__main__":
    print(get_lyric())
