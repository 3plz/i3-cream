#!/usr/bin/env python3
"""
Wu-Tang Control Center (C.R.E.A.M. Settings)
A unified, hardware & desktop configuration GUI for the Wu-Tang Clan i3wm rice.

Aesthetic:
- Pitch Black (#0C0C0C)
- Wu-Tang Signature Gold (#FFB800)
- Muted Slate (#888888) & Clean White (#F0F0F0)
- Sharp 0px borders and modern monospace typography
"""

import sys
import os
import glob
import re
import shutil
import subprocess
import psutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QStackedWidget, QScrollArea, QGridLayout,
    QCheckBox, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette, QIcon, QPainter, QBrush, QPen

# Paths
HOME = os.path.expanduser("~")
DOTFILES = os.path.join(HOME, ".dotfiles")
CONFIG_DIR = os.path.join(HOME, ".config")
WALLPAPERS_DIRS = [
    os.path.join(DOTFILES, "wallpapers"),
    os.path.join(HOME, "Pictures", "Wallpappers"),
    os.path.join(HOME, "Pictures", "Wallpapers"),
]
FEHBG_PATH = os.path.join(HOME, ".fehbg")
PERF_CONFIG = os.path.join(CONFIG_DIR, "perf_widget")
SONE_CONFIG = os.path.join(CONFIG_DIR, "sone_widget")


# -----------------------------------------------------------------------------
# QSS Stylesheet: Wu-Tang Cyber-Shaolin Theme
# -----------------------------------------------------------------------------
QSS_STYLE = """
QWidget {
    background-color: #0C0C0C;
    color: #E0E0E0;
    font-family: 'Terminess Nerd Font', 'Silkscreen', monospace;
    font-size: 13px;
    border: none;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #121212;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #FFB800;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Sidebar navigation buttons */
QPushButton#NavBtn {
    background-color: #121212;
    color: #A0A0A0;
    text-align: left;
    padding: 12px 16px;
    font-weight: bold;
    border-left: 3px solid transparent;
    font-size: 13px;
}
QPushButton#NavBtn:hover {
    background-color: #1A1A1A;
    color: #FFB800;
}
QPushButton#NavBtn:checked {
    background-color: #1E1A0F;
    color: #FFB800;
    border-left: 3px solid #FFB800;
}

/* Standard Buttons */
QPushButton.PrimaryBtn {
    background-color: #FFB800;
    color: #0C0C0C;
    font-weight: bold;
    padding: 8px 16px;
    border: none;
}
QPushButton.PrimaryBtn:hover {
    background-color: #FFA000;
}
QPushButton.PrimaryBtn:pressed {
    background-color: #E68900;
}

QPushButton.SecondaryBtn {
    background-color: #181818;
    color: #FFB800;
    border: 1px solid #FFB800;
    padding: 7px 14px;
    font-weight: bold;
}
QPushButton.SecondaryBtn:hover {
    background-color: #242014;
}

QPushButton.DangerBtn {
    background-color: #201010;
    color: #E53935;
    border: 1px solid #E53935;
    padding: 7px 14px;
    font-weight: bold;
}
QPushButton.DangerBtn:hover {
    background-color: #301818;
}

/* Cards & Frames */
QFrame.CardFrame {
    background-color: #141414;
    border: 1px solid #222222;
}

QFrame.ActiveCardFrame {
    background-color: #1A1812;
    border: 1px solid #FFB800;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    font-size: 13px;
    color: #E0E0E0;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    background: #141414;
}
QCheckBox::indicator:hover {
    border: 1px solid #FFB800;
}
QCheckBox::indicator:checked {
    background: #FFB800;
    border: 1px solid #FFB800;
}
"""


# -----------------------------------------------------------------------------
# Wallpaper Tab
# -----------------------------------------------------------------------------
class WallpaperCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, file_path, is_current=False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_current = is_current
        self.setFixedSize(230, 170)
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()

    def init_ui(self):
        self.setProperty("class", "ActiveCardFrame" if self.is_current else "CardFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Thumbnail
        self.img_label = QLabel(self)
        self.img_label.setFixedSize(218, 120)
        self.img_label.setStyleSheet("background-color: #080808;")
        self.img_label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(self.file_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(218, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled)
        else:
            self.img_label.setText("[No Preview]")
            self.img_label.setStyleSheet("color: #666;")

        layout.addWidget(self.img_label)

        # Title & Badge
        meta_layout = QHBoxLayout()
        meta_layout.setContentsMargins(2, 2, 2, 2)
        base_name = os.path.basename(self.file_path)
        clean_name = base_name if len(base_name) <= 18 else base_name[:15] + "..."
        name_lbl = QLabel(clean_name, self)
        name_lbl.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold;")
        meta_layout.addWidget(name_lbl)

        meta_layout.addStretch()

        if self.is_current:
            badge = QLabel("ACTIVE", self)
            badge.setStyleSheet("color: #0C0C0C; background: #FFB800; font-size: 9px; font-weight: bold; padding: 1px 4px;")
            meta_layout.addWidget(badge)

        layout.addLayout(meta_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.file_path)


class WallpaperTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_path = None
        self.current_path = self.detect_current_wallpaper()
        self.init_ui()

    def detect_current_wallpaper(self):
        if os.path.exists(FEHBG_PATH):
            try:
                with open(FEHBG_PATH, "r") as f:
                    content = f.read()
                    matches = re.findall(r'feh\s+.*--bg-\w+\s+["\']?([^"\'\n]+)', content)
                    if matches:
                        p = os.path.expanduser(matches[-1].strip())
                        if os.path.exists(p):
                            return p
            except Exception:
                pass
        return None

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header
        head_layout = QHBoxLayout()
        title = QLabel("WALLPAPER MANAGER", self)
        title.setStyleSheet("color: #FFB800; font-size: 16px; font-weight: bold;")
        head_layout.addWidget(title)

        head_layout.addStretch()

        self.apply_btn = QPushButton("Apply Wallpaper", self)
        self.apply_btn.setProperty("class", "PrimaryBtn")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply_selected_wallpaper)
        head_layout.addWidget(self.apply_btn)

        main_layout.addLayout(head_layout)

        # Scroll Area for Wallpapers Grid
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #1A1A1A; background-color: #0C0C0C; }")

        grid_container = QWidget()
        grid_container.setStyleSheet("background-color: #0C0C0C;")
        self.grid = QGridLayout(grid_container)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.grid.setSpacing(14)

        self.load_wallpapers()

        scroll.setWidget(grid_container)
        main_layout.addWidget(scroll)

        # Bottom Info Status
        self.status_lbl = QLabel(f"Current: {os.path.basename(self.current_path) if self.current_path else 'Not detected'}", self)
        self.status_lbl.setStyleSheet("color: #888888; font-size: 11px;")
        main_layout.addWidget(self.status_lbl)

    def load_wallpapers(self):
        # Clear grid
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        found_files = []
        for d in WALLPAPERS_DIRS:
            if os.path.isdir(d):
                for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                    found_files.extend(glob.glob(os.path.join(d, ext)))

        # Unique files by basename
        seen = set()
        wallpapers = []
        for f in found_files:
            b = os.path.basename(f)
            if b not in seen:
                seen.add(b)
                wallpapers.append(f)

        wallpapers.sort(key=lambda x: os.path.basename(x).lower())

        cols = 2
        for idx, wp in enumerate(wallpapers):
            is_cur = bool(self.current_path and os.path.abspath(wp) == os.path.abspath(self.current_path))
            card = WallpaperCard(wp, is_current=is_cur)
            card.clicked.connect(self.on_wallpaper_selected)
            self.grid.addWidget(card, idx // cols, idx % cols)

    def on_wallpaper_selected(self, file_path):
        self.selected_path = file_path
        self.apply_btn.setEnabled(True)
        self.status_lbl.setText(f"Selected: {os.path.basename(file_path)} — Click 'Apply Wallpaper' to set")
        self.status_lbl.setStyleSheet("color: #FFB800; font-size: 11px;")

    def apply_selected_wallpaper(self):
        if not self.selected_path or not os.path.exists(self.selected_path):
            return

        try:
            # Execute feh
            subprocess.run(["feh", "--no-fehbg", "--bg-fill", self.selected_path], check=True)

            # Write ~/.fehbg
            with open(FEHBG_PATH, "w") as f:
                f.write("#!/bin/sh\n")
                f.write(f'feh --no-fehbg --bg-fill "{self.selected_path}"\n')
            os.chmod(FEHBG_PATH, 0o755)

            self.current_path = self.selected_path
            self.load_wallpapers()
            self.apply_btn.setEnabled(False)
            self.status_lbl.setText(f"Active: {os.path.basename(self.current_path)} (Applied successfully)")
            self.status_lbl.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")

            # Desktop notification
            if shutil.which("notify-send"):
                subprocess.Popen(["notify-send", "-u", "low", "Wu-Tang Rice", f"Wallpaper applied: {os.path.basename(self.selected_path)}"])
        except Exception as e:
            QMessageBox.critical(self, "Error Applying Wallpaper", str(e))


# -----------------------------------------------------------------------------
# Desktop Widgets Tab
# -----------------------------------------------------------------------------
class WidgetsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

        # Polling timer for widget running status
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.update_widget_states)
        self.poll_timer.start(1500)

    def is_process_running(self, pattern):
        try:
            out = subprocess.check_output(["pgrep", "-f", pattern], stderr=subprocess.DEVNULL)
            return bool(out.strip())
        except subprocess.CalledProcessError:
            return False

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        title = QLabel("DESKTOP WIDGETS MANAGER", self)
        title.setStyleSheet("color: #FFB800; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(
            "Manage background desktop widgets. Position updates are saved automatically in their configuration folders.",
            self
        )
        desc.setStyleSheet("color: #888888; font-size: 11.5px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Widget 1: Performance Monitor
        self.perf_card = self.create_widget_card(
            title="Performance Monitor (Task Manager)",
            desc="Real-time 60s CPU, RAM, Disk & GPU scrolling graphs with gold gradient styling.",
            bind_hint="Shortcut: Mod + p (Raise/Lower)",
            on_toggle=self.toggle_perf_widget,
            on_signal=self.signal_perf_widget
        )
        layout.addWidget(self.perf_card)

        # Widget 2: Sone Track & Synced Lyrics
        self.sone_card = self.create_widget_card(
            title="Music Player & Synced Lyrics (Sone)",
            desc="MPRIS music controls with 3-line live synced lyrics from LRCLIB.",
            bind_hint="Shortcut: Mod + m (Raise/Lower)",
            on_toggle=self.toggle_sone_widget,
            on_signal=self.signal_sone_widget
        )
        layout.addWidget(self.sone_card)

        # Reset positions button
        bottom_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset Widget Positions to Default", self)
        reset_btn.setProperty("class", "SecondaryBtn")
        reset_btn.clicked.connect(self.reset_positions)
        bottom_layout.addWidget(reset_btn)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

        layout.addStretch()

        self.update_widget_states()

    def create_widget_card(self, title, desc, bind_hint, on_toggle, on_signal):
        card = QFrame(self)
        card.setProperty("class", "CardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(8)

        # Top row
        top = QHBoxLayout()
        name_lbl = QLabel(title, card)
        name_lbl.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13.5px;")
        top.addWidget(name_lbl)
        top.addStretch()

        status_lbl = QLabel("CHECKING...", card)
        status_lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
        top.addWidget(status_lbl)
        card.status_lbl = status_lbl

        card_layout.addLayout(top)

        # Desc
        desc_lbl = QLabel(desc, card)
        desc_lbl.setStyleSheet("color: #A0A0A0; font-size: 11.5px;")
        desc_lbl.setWordWrap(True)
        card_layout.addWidget(desc_lbl)

        # Actions row
        actions = QHBoxLayout()
        hint_lbl = QLabel(bind_hint, card)
        hint_lbl.setStyleSheet("color: #FFB800; font-size: 11px;")
        actions.addWidget(hint_lbl)
        actions.addStretch()

        toggle_btn = QPushButton("Toggle", card)
        toggle_btn.setProperty("class", "PrimaryBtn")
        toggle_btn.clicked.connect(on_toggle)
        actions.addWidget(toggle_btn)
        card.toggle_btn = toggle_btn

        signal_btn = QPushButton("Show/Hide", card)
        signal_btn.setProperty("class", "SecondaryBtn")
        signal_btn.clicked.connect(on_signal)
        actions.addWidget(signal_btn)

        card_layout.addLayout(actions)
        return card

    def update_widget_states(self):
        # Perf widget
        perf_running = self.is_process_running("perf_widget/widget.py")
        if perf_running:
            self.perf_card.status_lbl.setText("● RUNNING")
            self.perf_card.status_lbl.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.perf_card.toggle_btn.setText("Stop")
            self.perf_card.toggle_btn.setProperty("class", "DangerBtn")
        else:
            self.perf_card.status_lbl.setText("○ STOPPED")
            self.perf_card.status_lbl.setStyleSheet("color: #888888; font-weight: bold;")
            self.perf_card.toggle_btn.setText("Launch")
            self.perf_card.toggle_btn.setProperty("class", "PrimaryBtn")
        self.perf_card.toggle_btn.style().unpolish(self.perf_card.toggle_btn)
        self.perf_card.toggle_btn.style().polish(self.perf_card.toggle_btn)

        # Sone widget
        sone_running = self.is_process_running("sone_widget/widget.py")
        if sone_running:
            self.sone_card.status_lbl.setText("● RUNNING")
            self.sone_card.status_lbl.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.sone_card.toggle_btn.setText("Stop")
            self.sone_card.toggle_btn.setProperty("class", "DangerBtn")
        else:
            self.sone_card.status_lbl.setText("○ STOPPED")
            self.sone_card.status_lbl.setStyleSheet("color: #888888; font-weight: bold;")
            self.sone_card.toggle_btn.setText("Launch")
            self.sone_card.toggle_btn.setProperty("class", "PrimaryBtn")
        self.sone_card.toggle_btn.style().unpolish(self.sone_card.toggle_btn)
        self.sone_card.toggle_btn.style().polish(self.sone_card.toggle_btn)

    def toggle_perf_widget(self):
        if self.is_process_running("perf_widget/widget.py"):
            subprocess.run(["pkill", "-f", "perf_widget/widget.py"])
        else:
            launch_script = os.path.join(PERF_CONFIG, "launch.sh")
            if os.path.exists(launch_script):
                subprocess.Popen(["bash", launch_script])
            else:
                subprocess.Popen(["python3", os.path.join(PERF_CONFIG, "widget.py")])
        QTimer.singleShot(400, self.update_widget_states)

    def signal_perf_widget(self):
        subprocess.run(["pkill", "-USR1", "-f", "perf_widget/widget.py"])

    def toggle_sone_widget(self):
        if self.is_process_running("sone_widget/widget.py"):
            subprocess.run(["pkill", "-f", "sone_widget/widget.py"])
        else:
            launch_script = os.path.join(SONE_CONFIG, "launch.sh")
            if os.path.exists(launch_script):
                subprocess.Popen(["bash", launch_script])
            else:
                subprocess.Popen(["python3", os.path.join(SONE_CONFIG, "widget.py")])
        QTimer.singleShot(400, self.update_widget_states)

    def signal_sone_widget(self):
        subprocess.run(["pkill", "-USR1", "-f", "sone_widget/widget.py"])

    def reset_positions(self):
        for path in (os.path.join(PERF_CONFIG, "position.json"), os.path.join(SONE_CONFIG, "position.json")):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        QMessageBox.information(
            self,
            "Positions Reset",
            "Saved widget coordinates have been cleared.\nRestart the widgets to place them at their default screen positions."
        )


# -----------------------------------------------------------------------------
# Touchpad Tab
# -----------------------------------------------------------------------------
class TouchpadTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.touchpad_id = None
        self.touchpad_name = "Not Detected"
        self.init_ui()
        self.detect_touchpad()

    def detect_touchpad(self):
        try:
            out = subprocess.check_output(["xinput", "list"], stderr=subprocess.DEVNULL).decode("utf-8")
            for line in out.splitlines():
                if re.search(r'touchpad|trackpad', line, re.IGNORECASE):
                    m = re.search(r'id=(\d+)', line)
                    if m:
                        self.touchpad_id = m.group(1)
                        # Extract name
                        parts = line.split("id=")
                        self.touchpad_name = parts[0].replace("↳", "").replace("⎜", "").strip()
                        break
        except Exception:
            pass

        if self.touchpad_id:
            self.info_lbl.setText(f"Device: {self.touchpad_name} (ID: {self.touchpad_id})")
            self.info_lbl.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
            self.tap_check.setEnabled(True)
            self.scroll_check.setEnabled(True)
            self.dwt_check.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.read_properties()
        else:
            self.info_lbl.setText("No hardware touchpad detected via Libinput / xinput.\n(If on desktop PC, mouse controls are active).")
            self.info_lbl.setStyleSheet("color: #888888; font-size: 12px;")
            self.tap_check.setEnabled(False)
            self.scroll_check.setEnabled(False)
            self.dwt_check.setEnabled(False)
            self.save_btn.setEnabled(False)

    def read_properties(self):
        if not self.touchpad_id:
            return
        try:
            out = subprocess.check_output(["xinput", "list-props", self.touchpad_id], stderr=subprocess.DEVNULL).decode("utf-8")
            # Tapping
            m_tap = re.search(r'libinput Tapping Enabled \(\d+\):\s+([01])', out)
            if m_tap:
                self.tap_check.setChecked(m_tap.group(1) == "1")

            # Natural scrolling
            m_scroll = re.search(r'libinput Natural Scrolling Enabled \(\d+\):\s+([01])', out)
            if m_scroll:
                self.scroll_check.setChecked(m_scroll.group(1) == "1")

            # DWT
            m_dwt = re.search(r'libinput Disable While Typing Enabled \(\d+\):\s+([01])', out)
            if m_dwt:
                self.dwt_check.setChecked(m_dwt.group(1) == "1")
        except Exception:
            pass

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("TOUCHPAD & LAPTOP SETTINGS", self)
        title.setStyleSheet("color: #FFB800; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self.info_lbl = QLabel("Detecting touchpad...", self)
        self.info_lbl.setWordWrap(True)
        layout.addWidget(self.info_lbl)

        # Options Card
        card = QFrame(self)
        card.setProperty("class", "CardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(14)

        self.tap_check = QCheckBox("Tap to Click (Tapping Enabled)", card)
        self.tap_check.stateChanged.connect(self.on_tap_changed)
        card_layout.addWidget(self.tap_check)

        self.scroll_check = QCheckBox("Natural Scrolling (Inverted Two-Finger Scroll)", card)
        self.scroll_check.stateChanged.connect(self.on_scroll_changed)
        card_layout.addWidget(self.scroll_check)

        self.dwt_check = QCheckBox("Disable While Typing (Palm Rejection)", card)
        self.dwt_check.stateChanged.connect(self.on_dwt_changed)
        card_layout.addWidget(self.dwt_check)

        layout.addWidget(card)

        # Save Button
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Defaults to Autostart", self)
        self.save_btn.setProperty("class", "PrimaryBtn")
        self.save_btn.clicked.connect(self.save_to_autostart)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def on_tap_changed(self, state):
        if self.touchpad_id:
            val = "1" if state == Qt.Checked else "0"
            subprocess.run(["xinput", "set-prop", self.touchpad_id, "libinput Tapping Enabled", val])

    def on_scroll_changed(self, state):
        if self.touchpad_id:
            val = "1" if state == Qt.Checked else "0"
            subprocess.run(["xinput", "set-prop", self.touchpad_id, "libinput Natural Scrolling Enabled", val])

    def on_dwt_changed(self, state):
        if self.touchpad_id:
            val = "1" if state == Qt.Checked else "0"
            subprocess.run(["xinput", "set-prop", self.touchpad_id, "libinput Disable While Typing Enabled", val])

    def save_to_autostart(self):
        script_dir = os.path.join(CONFIG_DIR, "i3", "scripts")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, "touchpad.sh")

        tap = 1 if self.tap_check.isChecked() else 0
        scroll = 1 if self.scroll_check.isChecked() else 0
        dwt = 1 if self.dwt_check.isChecked() else 0

        script_content = f"""#!/usr/bin/env bash
# Wu-Tang Clan Touchpad Configuration Script
for id in $(xinput list --id-only 2>/dev/null); do
    if xinput list-props "$id" 2>/dev/null | grep -q "libinput Tapping Enabled"; then
        xinput set-prop "$id" "libinput Tapping Enabled" {tap} 2>/dev/null || true
        xinput set-prop "$id" "libinput Natural Scrolling Enabled" {scroll} 2>/dev/null || true
        xinput set-prop "$id" "libinput Disable While Typing Enabled" {dwt} 2>/dev/null || true
    fi
done
"""
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        # Ensure call in autostart.sh
        autostart_path = os.path.join(script_dir, "autostart.sh")
        if os.path.exists(autostart_path):
            with open(autostart_path, "r") as f:
                content = f.read()
            if "touchpad.sh" not in content:
                with open(autostart_path, "a") as f:
                    f.write("\n# Touchpad Configuration\nbash ~/.config/i3/scripts/touchpad.sh &\n")

        QMessageBox.information(
            self,
            "Touchpad Settings Saved",
            "Touchpad configuration saved to ~/.config/i3/scripts/touchpad.sh and registered in autostart.sh."
        )


# -----------------------------------------------------------------------------
# Display & System Quick Actions Tab
# -----------------------------------------------------------------------------
class DisplayTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("DISPLAYS & SYSTEM ACTIONS", self)
        title.setStyleSheet("color: #FFB800; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Displays Card
        disp_card = QFrame(self)
        disp_card.setProperty("class", "CardFrame")
        dc_layout = QVBoxLayout(disp_card)
        dc_layout.setContentsMargins(16, 14, 16, 14)
        dc_layout.setSpacing(10)

        dc_title = QLabel("Connected Monitors & Video Outputs", disp_card)
        dc_title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")
        dc_layout.addWidget(dc_title)

        monitors = self.detect_monitors()
        for mon in monitors:
            lbl = QLabel(f"• {mon}", disp_card)
            lbl.setStyleSheet("color: #A0A0A0; font-size: 12px;")
            dc_layout.addWidget(lbl)

        # Capture card button
        cc_layout = QHBoxLayout()
        cc_btn = QPushButton("Launch Capture Card Mirroring (Alt + F7)", disp_card)
        cc_btn.setProperty("class", "PrimaryBtn")
        cc_btn.clicked.connect(self.launch_display_mirror)
        cc_layout.addWidget(cc_btn)
        cc_layout.addStretch()
        dc_layout.addLayout(cc_layout)

        layout.addWidget(disp_card)

        # Quick Reloads Card
        act_card = QFrame(self)
        act_card.setProperty("class", "CardFrame")
        ac_layout = QVBoxLayout(act_card)
        ac_layout.setContentsMargins(16, 14, 16, 14)
        ac_layout.setSpacing(10)

        ac_title = QLabel("Quick Desktop Reloads", act_card)
        ac_title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")
        ac_layout.addWidget(ac_title)

        btns_row = QHBoxLayout()
        btns_row.setSpacing(10)

        btn_i3 = QPushButton("Reload i3wm", act_card)
        btn_i3.setProperty("class", "SecondaryBtn")
        btn_i3.clicked.connect(lambda: subprocess.run(["i3-msg", "restart"]))
        btns_row.addWidget(btn_i3)

        btn_bar = QPushButton("Restart Polybar", act_card)
        btn_bar.setProperty("class", "SecondaryBtn")
        btn_bar.clicked.connect(self.restart_polybar)
        btns_row.addWidget(btn_bar)

        btn_picom = QPushButton("Restart Picom", act_card)
        btn_picom.setProperty("class", "SecondaryBtn")
        btn_picom.clicked.connect(self.restart_picom)
        btns_row.addWidget(btn_picom)

        btns_row.addStretch()
        ac_layout.addLayout(btns_row)

        layout.addWidget(act_card)
        layout.addStretch()

    def detect_monitors(self):
        res = []
        try:
            out = subprocess.check_output(["xrandr", "--query"], stderr=subprocess.DEVNULL).decode("utf-8")
            for line in out.splitlines():
                if " connected" in line:
                    res.append(line.split()[0] + (" (Primary)" if "primary" in line else ""))
        except Exception:
            pass
        return res if res else ["Standard Display (xrandr unavailable)"]

    def launch_display_mirror(self):
        script = os.path.join(CONFIG_DIR, "i3", "scripts", "display_mirror.sh")
        if os.path.exists(script):
            subprocess.Popen(["bash", script])

    def restart_polybar(self):
        script = os.path.join(CONFIG_DIR, "polybar", "launch.sh")
        if os.path.exists(script):
            subprocess.Popen(["bash", script])

    def restart_picom(self):
        subprocess.run(["pkill", "-x", "picom"])
        subprocess.Popen(["picom", "-b"])


# -----------------------------------------------------------------------------
# About & System Information Tab
# -----------------------------------------------------------------------------
class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        banner = QLabel(
            "   __      ____  __     _____ ___    _   _\n"
            "   \\ \\    / / / / /    |_   _/ _ \\  | \\ | |\n"
            "    \\ \\/\\/ / /_/ /_____  | || |_| | |  \\| |\n"
            "     \\_/\\_/\\____/______  |_| \\___/  |_|\\___|\n"
            "        WU-TANG CLAN // C.R.E.A.M. RICE",
            self
        )
        banner.setStyleSheet("color: #FFB800; font-family: monospace; font-size: 11px; font-weight: bold;")
        layout.addWidget(banner)

        card = QFrame(self)
        card.setProperty("class", "CardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(8)

        # System info
        uname = os.uname()
        c_layout.addWidget(self.make_info_row("Operating System:", f"{uname.sysname} ({uname.release})"))
        c_layout.addWidget(self.make_info_row("Node Hostname:", uname.nodename))

        cpu_count = psutil.cpu_count(logical=True)
        mem = psutil.virtual_memory()
        mem_gb = f"{mem.total / (1024**3):.1f} GB"
        c_layout.addWidget(self.make_info_row("Hardware:", f"{cpu_count} CPU Threads | {mem_gb} RAM"))
        c_layout.addWidget(self.make_info_row("Theme & Palette:", "Pitch Black (#0C0C0C) & Signature Gold (#FFB800)"))
        c_layout.addWidget(self.make_info_row("Window Manager:", "i3-wm (Tiling)"))

        layout.addWidget(card)

        # Update button
        update_layout = QHBoxLayout()
        update_btn = QPushButton("Update Rice (update-cream)", self)
        update_btn.setProperty("class", "PrimaryBtn")
        update_btn.clicked.connect(self.run_updater)
        update_layout.addWidget(update_btn)
        update_layout.addStretch()
        layout.addLayout(update_layout)

        layout.addStretch()

    def make_info_row(self, label, value):
        row = QWidget()
        l = QHBoxLayout(row)
        l.setContentsMargins(0, 0, 0, 0)
        k = QLabel(label, row)
        k.setStyleSheet("color: #888888; font-weight: bold; width: 140px;")
        v = QLabel(value, row)
        v.setStyleSheet("color: #FFFFFF;")
        l.addWidget(k)
        l.addWidget(v)
        l.addStretch()
        return row

    def run_updater(self):
        script = os.path.join(DOTFILES, "bin", "update-cream")
        if os.path.exists(script):
            # Launch in terminal
            subprocess.Popen(["alacritty", "-e", script])


# -----------------------------------------------------------------------------
# Main Application Window
# -----------------------------------------------------------------------------
class CreamSettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wu-Tang Control Center")
        self.setFixedSize(780, 520)
        self.setStyleSheet(QSS_STYLE)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Header Bar
        header = QFrame(self)
        header.setFixedHeight(46)
        header.setStyleSheet("background-color: #121212; border-bottom: 2px solid #FFB800;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        logo_lbl = QLabel("👐  WU-TANG CLAN // CONTROL CENTER", header)
        logo_lbl.setStyleSheet("color: #FFB800; font-weight: bold; font-size: 13px; letter-spacing: 1px;")
        h_layout.addWidget(logo_lbl)

        h_layout.addStretch()

        badge = QLabel("ARCH LINUX | i3WM", header)
        badge.setStyleSheet("color: #888888; font-size: 10px; font-weight: bold;")
        h_layout.addWidget(badge)

        main_layout.addWidget(header)

        # Body Layout: Sidebar + Stacked Content
        body = QWidget(self)
        b_layout = QHBoxLayout(body)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame(body)
        sidebar.setFixedWidth(190)
        sidebar.setStyleSheet("background-color: #0E0E0E; border-right: 1px solid #1C1C1C;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 12, 0, 12)
        sb_layout.setSpacing(4)

        # Stacked Pages
        self.stack = QStackedWidget(body)
        self.tab_wallpapers = WallpaperTab()
        self.tab_widgets = WidgetsTab()
        self.tab_touchpad = TouchpadTab()
        self.tab_display = DisplayTab()
        self.tab_about = AboutTab()

        self.stack.addWidget(self.tab_wallpapers)
        self.stack.addWidget(self.tab_widgets)
        self.stack.addWidget(self.tab_touchpad)
        self.stack.addWidget(self.tab_display)
        self.stack.addWidget(self.tab_about)

        # Nav items
        self.nav_buttons = []
        nav_items = [
            ("🖼️  Wallpapers", 0),
            ("⚡  Widgets", 1),
            ("🖱️  Touchpad", 2),
            ("🖥️  Displays", 3),
            ("ℹ️  About Rice", 4),
        ]

        for text, index in nav_items:
            btn = QPushButton(text, sidebar)
            btn.setObjectName("NavBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self.switch_tab(idx))
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()

        # Initial active tab
        self.nav_buttons[0].setChecked(True)

        b_layout.addWidget(sidebar)
        b_layout.addWidget(self.stack)

        main_layout.addWidget(body)

    def switch_tab(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)


def main():
    app = QApplication(sys.argv)
    window = CreamSettingsWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
