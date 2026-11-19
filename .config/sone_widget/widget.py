#!/usr/bin/env python3
"""
Sone Track & Synced Lyrics Desktop Widget
A semi-transparent, draggable desktop widget matching the Wu-Tang Clan aesthetic.
Features:
- Album cover art with rounded corners
- Track title, artist, album info
- Clickable progress bar & time elapsed/duration
- Playback controls: Previous, Play/Pause, Next
- 3-line real-time synchronized lyrics (Previous, Current highlighted in Gold, Next)
- Position persistence across sessions
"""

import sys
import os
import re
import json
import signal
import urllib.request
import urllib.parse
import subprocess
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QSlider,
    QHBoxLayout, QVBoxLayout, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QFont, QIcon, QCursor
)

CACHE_DIR = os.path.expanduser("~/.cache/sone_widget")
CONFIG_DIR = os.path.expanduser("~/.config/sone_widget")
POSITION_FILE = os.path.join(CONFIG_DIR, "position.json")
COVERS_DIR = os.path.join(CACHE_DIR, "covers")
LYRICS_DIR = os.path.join(CACHE_DIR, "lyrics")

os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(LYRICS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)


def parse_lrc(lrc_text):
    """Parse LRC content into a sorted list of (seconds, text) tuples."""
    lines = []
    pattern = re.compile(r'\[(\d+):(\d+(?:\.\d+)?)\](.*)')
    for raw in lrc_text.splitlines():
        match = pattern.match(raw.strip())
        if match:
            mins, secs, text = match.groups()
            timestamp = int(mins) * 60 + float(secs)
            cleaned = text.strip()
            if cleaned:
                lines.append((timestamp, cleaned))
    lines.sort(key=lambda x: x[0])
    return lines


class LyricsWorker(QObject):
    lyrics_ready = pyqtSignal(str, list)  # track_key, lines

    def fetch(self, track_key, artist, title, album):
        def _target():
            # Check disk cache first
            safe_name = re.sub(r'[^\w\-_\.]', '_', f"{artist}_{title}")[:100]
            cache_file = os.path.join(LYRICS_DIR, f"{safe_name}.lrc")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        lines = parse_lrc(f.read())
                        if lines:
                            self.lyrics_ready.emit(track_key, lines)
                            return
                except Exception:
                    pass

            # Fetch from LRCLIB API
            try:
                params = urllib.parse.urlencode({
                    "artist_name": artist,
                    "track_name": title,
                    "album_name": album
                })
                url = f"https://lrclib.net/api/get?{params}"
                req = urllib.request.Request(url, headers={"User-Agent": "SoneWidget/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                
                synced = data.get("syncedLyrics")
                if synced:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        f.write(synced)
                    lines = parse_lrc(synced)
                    self.lyrics_ready.emit(track_key, lines)
                    return
            except Exception:
                pass

            self.lyrics_ready.emit(track_key, [])

        threading.Thread(target=_target, daemon=True).start()


class CoverWorker(QObject):
    cover_ready = pyqtSignal(str, str)  # url, local_path

    def fetch(self, url):
        def _target():
            if not url or not url.startswith("http"):
                return
            safe_name = re.sub(r'[^\w\-_\.]', '_', url.split("/")[-2] if "/" in url else "cover") + ".jpg"
            cache_file = os.path.join(COVERS_DIR, safe_name)
            if not os.path.exists(cache_file):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "SoneWidget/1.0"})
                    with urllib.request.urlopen(req, timeout=5) as resp, open(cache_file, "wb") as f:
                        f.write(resp.read())
                except Exception:
                    return
            self.cover_ready.emit(url, cache_file)

        threading.Thread(target=_target, daemon=True).start()


class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.x()) / max(self.width(), 1)
            self.setValue(int(val))
            self.sliderMoved.emit(int(val))
        super().mousePressEvent(event)


class SoneWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sone Track Widget")
        self.setObjectName("SoneWidget")
        
        # Frameless, bypass window manager (bypasses i3 container wrapping, allows proper X11 stacking)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.current_track_key = ""
        self.lyrics_data = []
        self.current_position = 0.0
        self.duration = 0.0
        self.is_playing = False
        self.current_art_url = ""
        self.drag_position = QPoint()
        self.is_lowered = False

        self.lyrics_worker = LyricsWorker()
        self.lyrics_worker.lyrics_ready.connect(self.on_lyrics_ready)

        self.cover_worker = CoverWorker()
        self.cover_worker.cover_ready.connect(self.on_cover_ready)

        self.init_ui()
        self.load_position()
        self.setup_signals()

        # Update timer: 250ms for smooth lyrics and progress bar
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_state)
        self.timer.start(250)

        # Apply initial stacking layer after window is mapped in X11
        QTimer.singleShot(150, self.apply_initial_state)

    def setup_signals(self):
        try:
            signal.signal(signal.SIGUSR1, lambda sig, frame: self.toggle_pin())
        except Exception:
            pass

    def init_ui(self):
        self.setFixedSize(410, 230)

        # Main background card frame
        card = QFrame(self)
        card.setGeometry(0, 0, 410, 230)
        card.setObjectName("cardFrame")
        card.setStyleSheet("""
            QFrame#cardFrame {
                background-color: rgba(12, 12, 12, 0.88);
                border: 1.5px solid #FFB800;
                border-radius: 0px;
            }
        """)

        # Top-right subtle ghost button to lower widget behind all windows onto desktop
        self.btn_pin = QPushButton("▾", card)
        self.btn_pin.setGeometry(382, 4, 24, 24)
        self.btn_pin.setObjectName("pinBtn")
        self.btn_pin.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_pin.setToolTip("Скрыть за все окна на рабочий стол")
        self.btn_pin.setStyleSheet("""
            QPushButton#pinBtn {
                background: transparent;
                color: rgba(255, 255, 255, 0.22);
                font-size: 13px;
                font-family: 'Silkscreen', monospace;
                border: none;
                border-radius: 0px;
                padding: 1px;
            }
            QPushButton#pinBtn:hover {
                background: rgba(255, 184, 0, 0.20);
                color: #FFB800;
                border: 1px solid #FFB800;
            }
        """)
        self.btn_pin.clicked.connect(self.toggle_pin)

        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(6)

        # ---------------- Top Row: Cover + Info + Controls ----------------
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        # Album Cover
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(72, 72)
        self.cover_label.setStyleSheet("border-radius: 0px; background-color: #1a1a1a; border: 1px solid #333333;")
        self.set_default_cover()
        top_layout.addWidget(self.cover_label)

        # Metadata & Controls
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        self.title_label = QLabel("NO TRACK PLAYING")
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold; font-family: 'Silkscreen', monospace;")
        info_layout.addWidget(self.title_label)

        self.artist_label = QLabel("SONE MUSIC PLAYER")
        self.artist_label.setStyleSheet("color: #FFB800; font-size: 10px; font-weight: bold; font-family: 'Silkscreen', monospace;")
        info_layout.addWidget(self.artist_label)

        self.album_label = QLabel("")
        self.album_label.setStyleSheet("color: #8C7B58; font-size: 8.5px; font-family: 'Silkscreen', monospace;")
        info_layout.addWidget(self.album_label)

        # Controls Buttons
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)
        ctrl_layout.setContentsMargins(0, 4, 0, 0)

        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("⏭")

        for btn in (self.btn_prev, self.btn_play, self.btn_next):
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #FFFFFF;
                    font-size: 14px;
                    border: none;
                    border-radius: 0px;
                    padding: 2px 4px;
                }
                QPushButton:hover {
                    color: #FFB800;
                }
            """)

        self.btn_play.setStyleSheet("""
            QPushButton {
                background: rgba(255, 184, 0, 0.15);
                color: #FFB800;
                font-size: 14px;
                border: 1px solid #FFB800;
                border-radius: 0px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton:hover {
                background: #FFB800;
                color: #000000;
            }
        """)

        self.btn_prev.clicked.connect(lambda: self.run_playerctl("previous"))
        self.btn_play.clicked.connect(lambda: self.run_playerctl("play-pause"))
        self.btn_next.clicked.connect(lambda: self.run_playerctl("next"))

        ctrl_layout.addWidget(self.btn_prev)
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.btn_next)
        ctrl_layout.addStretch()

        info_layout.addLayout(ctrl_layout)
        top_layout.addLayout(info_layout)
        main_layout.addLayout(top_layout)

        # ---------------- Middle Row: Slider & Time ----------------
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(8)

        self.time_curr = QLabel("0:00")
        self.time_curr.setStyleSheet("color: #FFB800; font-size: 9px; font-family: 'Silkscreen', monospace;")
        
        self.slider = ClickableSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setCursor(QCursor(Qt.PointingHandCursor))
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #252525;
                border-radius: 0px;
            }
            QSlider::sub-page:horizontal {
                background: #FFB800;
                border-radius: 0px;
            }
            QSlider::handle:horizontal {
                width: 0px;
                margin: 0px;
            }
        """)
        self.slider.sliderMoved.connect(self.seek_position)

        self.time_total = QLabel("0:00")
        self.time_total.setStyleSheet("color: #8C7B58; font-size: 9px; font-family: 'Silkscreen', monospace;")

        slider_layout.addWidget(self.time_curr)
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.time_total)
        main_layout.addLayout(slider_layout)

        # ---------------- Bottom Row: 3-line Synced Lyrics ----------------
        lyrics_box = QFrame()
        lyrics_box.setStyleSheet("""
            QFrame {
                background: rgba(18, 18, 18, 0.65);
                border: 1px solid rgba(255, 184, 0, 0.25);
                border-radius: 0px;
                padding: 2px;
            }
        """)
        lyrics_layout = QVBoxLayout(lyrics_box)
        lyrics_layout.setContentsMargins(6, 4, 6, 4)
        lyrics_layout.setSpacing(2)

        self.lyric_prev = QLabel("")
        self.lyric_prev.setAlignment(Qt.AlignCenter)
        self.lyric_prev.setStyleSheet("color: rgba(220, 220, 220, 0.38); font-size: 9px; font-family: 'Silkscreen', monospace;")

        self.lyric_curr = QLabel("LYRICS WILL SYNC HERE")
        self.lyric_curr.setAlignment(Qt.AlignCenter)
        self.lyric_curr.setStyleSheet("color: #FFB800; font-size: 10px; font-weight: bold; background: rgba(255, 184, 0, 0.09); border-radius: 0px; font-family: 'Silkscreen', monospace;")

        self.lyric_next = QLabel("")
        self.lyric_next.setAlignment(Qt.AlignCenter)
        self.lyric_next.setStyleSheet("color: rgba(220, 220, 220, 0.38); font-size: 9px; font-family: 'Silkscreen', monospace;")

        lyrics_layout.addWidget(self.lyric_prev)
        lyrics_layout.addWidget(self.lyric_curr)
        lyrics_layout.addWidget(self.lyric_next)

        main_layout.addWidget(lyrics_box)
        self.btn_pin.raise_()

    def set_default_cover(self):
        # Create a stylish Wu-Tang golden placeholder pixmap
        pixmap = QPixmap(72, 72)
        pixmap.fill(QColor(20, 20, 20))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("#FFB800"))
        painter.setFont(QFont("WuTangIcons", 32))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "W")
        painter.end()
        self.cover_label.setPixmap(self.round_pixmap(pixmap, 8))

    def round_pixmap(self, src, radius=0):
        scaled = src.scaled(72, 72, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        target = QPixmap(72, 72)
        target.fill(Qt.transparent)
        p = QPainter(target)
        p.setRenderHint(QPainter.Antialiasing)
        if radius > 0:
            path = QPainterPath()
            path.addRoundedRect(0, 0, 72, 72, radius, radius)
            p.setClipPath(path)
        p.drawPixmap(0, 0, scaled)
        p.end()
        return target

    def on_cover_ready(self, url, local_path):
        if url == self.current_art_url and os.path.exists(local_path):
            pix = QPixmap(local_path)
            if not pix.isNull():
                self.cover_label.setPixmap(self.round_pixmap(pix, 0))

    def on_lyrics_ready(self, track_key, lines):
        if track_key == self.current_track_key:
            self.lyrics_data = lines
            self.refresh_lyrics_display()

    def apply_initial_state(self):
        if getattr(self, "is_lowered", False):
            self.lower_to_desktop()
        else:
            self.raise_to_top()

    def lower_to_desktop(self):
        self.is_lowered = True
        self.btn_pin.setText("▴")
        self.btn_pin.setToolTip("Поднять поверх всех окон (HUD mode)")
        self.clearFocus()
        self.lower()
        try:
            wid = str(int(self.winId()))
            env = dict(os.environ, DISPLAY=":0")
            subprocess.run(["xdotool", "windowlower", wid], env=env, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        self.save_position()

    def raise_to_top(self):
        self.is_lowered = False
        self.btn_pin.setText("▾")
        self.btn_pin.setToolTip("Скрыть за все окна на рабочий стол (Desktop mode)")
        self.raise_()
        try:
            wid = str(int(self.winId()))
            env = dict(os.environ, DISPLAY=":0")
            subprocess.run(["xdotool", "windowraise", wid], env=env, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        self.save_position()

    def toggle_pin(self):
        if getattr(self, "is_lowered", False):
            self.raise_to_top()
        else:
            self.lower_to_desktop()

    def run_playerctl(self, action):
        env = dict(os.environ, DISPLAY=":0", DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus")
        subprocess.Popen(["playerctl", action], env=env)

    def seek_position(self, val):
        if self.duration > 0:
            target_sec = (val / 1000.0) * self.duration
            env = dict(os.environ, DISPLAY=":0", DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus")
            subprocess.Popen(["playerctl", "position", str(target_sec)], env=env)

    def update_state(self):
        env = dict(os.environ, DISPLAY=":0", DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus")
        cmd = [
            "playerctl", "metadata",
            "--format", "{{status}}|||{{artist}}|||{{title}}|||{{album}}|||{{mpris:artUrl}}|||{{position}}|||{{mpris:length}}"
        ]
        try:
            res = subprocess.check_output(cmd, env=env, stderr=subprocess.DEVNULL).decode().strip()
            parts = res.split("|||")
            if len(parts) >= 7:
                status, artist, title, album, art_url, pos_raw, len_raw = parts[:7]
            else:
                return
        except Exception:
            self.title_label.setText("SONE offline / Idle")
            self.artist_label.setText("")
            self.album_label.setText("")
            self.btn_play.setText("▶")
            self.lyric_curr.setText("♪ No music playing ♪")
            self.lyric_prev.setText("")
            self.lyric_next.setText("")
            cache_lyric_file = os.path.join(CACHE_DIR, "current_lyric.txt")
            if os.path.exists(cache_lyric_file):
                try:
                    os.remove(cache_lyric_file)
                except Exception:
                    pass
            return

        self.is_playing = (status == "Playing")
        self.btn_play.setText("⏸" if self.is_playing else "▶")

        # Parse position and duration
        try:
            pos_sec = float(pos_raw) / 1_000_000.0 if pos_raw else 0.0
        except ValueError:
            pos_sec = 0.0
        try:
            dur_sec = float(len_raw) / 1_000_000.0 if len_raw else 0.0
        except ValueError:
            dur_sec = 0.0

        self.current_position = pos_sec
        self.duration = dur_sec

        # Slider and time labels
        if dur_sec > 0:
            pct = int((pos_sec / dur_sec) * 1000)
            self.slider.setValue(pct)
            self.time_curr.setText(self.format_time(pos_sec))
            self.time_total.setText(self.format_time(dur_sec))
        else:
            self.slider.setValue(0)
            self.time_curr.setText("0:00")
            self.time_total.setText("0:00")

        # Update metadata if track changed
        track_key = f"{artist} - {title}"
        if track_key != self.current_track_key:
            self.current_track_key = track_key
            self.title_label.setText(self.elide(title, 28))
            self.artist_label.setText(self.elide(artist, 32))
            self.album_label.setText(self.elide(album, 36))

            # Cover
            self.current_art_url = art_url
            if art_url:
                self.cover_worker.fetch(art_url)
            else:
                self.set_default_cover()

            # Lyrics
            self.lyrics_data = []
            self.lyric_curr.setText("Loading lyrics...")
            self.lyric_prev.setText("")
            self.lyric_next.setText("")
            self.lyrics_worker.fetch(track_key, artist, title, album)
        else:
            self.refresh_lyrics_display()

    def refresh_lyrics_display(self):
        if not self.lyrics_data:
            return

        # Find current active line
        pos = self.current_position
        curr_idx = -1
        for i, (ts, text) in enumerate(self.lyrics_data):
            if ts <= pos:
                curr_idx = i
            else:
                break

        if curr_idx == -1:
            prev_t = ""
            curr_t = self.lyrics_data[0][1] if self.lyrics_data else ""
            next_t = self.lyrics_data[1][1] if len(self.lyrics_data) > 1 else ""
        else:
            prev_t = self.lyrics_data[curr_idx - 1][1] if curr_idx > 0 else ""
            curr_t = self.lyrics_data[curr_idx][1]
            next_t = self.lyrics_data[curr_idx + 1][1] if curr_idx + 1 < len(self.lyrics_data) else ""

        self.lyric_prev.setText(self.elide(prev_t, 46))
        self.lyric_curr.setText(self.elide(curr_t, 42))
        self.lyric_next.setText(self.elide(next_t, 46))

        # Write current synchronized lyric for fastfetch
        cache_lyric_file = os.path.join(CACHE_DIR, "current_lyric.txt")
        if curr_t != getattr(self, "last_written_lyric", None):
            self.last_written_lyric = curr_t
            try:
                with open(cache_lyric_file, "w", encoding="utf-8") as f:
                    f.write(curr_t)
            except Exception:
                pass

    def format_time(self, seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"

    def elide(self, text, max_len):
        if len(text) > max_len:
            return text[:max_len - 1] + "…"
        return text

    # ---------------- Mouse Dragging & Position ----------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.save_position()
        if getattr(self, "is_lowered", False):
            try:
                wid = str(int(self.winId()))
                env = dict(os.environ, DISPLAY=":0")
                subprocess.run(["xdotool", "windowlower", wid], env=env, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def save_position(self):
        data = {
            "x": self.x(),
            "y": self.y(),
            "is_lowered": getattr(self, "is_lowered", False)
        }
        try:
            with open(POSITION_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def load_position(self):
        if os.path.exists(POSITION_FILE):
            try:
                with open(POSITION_FILE, "r") as f:
                    data = json.load(f)
                    self.move(data.get("x", 40), data.get("y", 780))
                    self.is_lowered = data.get("is_lowered", False)
                    return
            except Exception:
                pass
        # Default position: bottom-left above polybar
        self.move(40, 780)
        self.is_lowered = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = SoneWidget()
    widget.show()
    sys.exit(app.exec_())
