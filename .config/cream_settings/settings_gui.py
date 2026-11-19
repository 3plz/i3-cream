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
    QCheckBox, QSizePolicy, QMessageBox, QFileDialog, QComboBox, QDialog
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

# Wu-Tang Logo
LOGO_PATH = os.path.join(DOTFILES, "assets", "logo.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")


# -----------------------------------------------------------------------------
# QSS Stylesheet: Wu-Tang Cyber-Shaolin Theme
# -----------------------------------------------------------------------------
QSS_STYLE = """
QWidget {
    background-color: #0C0C0C;
    color: #E0E0E0;
    font-family: 'Silkscreen', 'Terminess Nerd Font', monospace;
    font-size: 11px;
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
    font-family: 'Silkscreen', 'Terminess Nerd Font', monospace;
    font-weight: bold;
    border-left: 3px solid transparent;
    font-size: 9.5px;
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
    font-family: 'Silkscreen', monospace;
    font-size: 9.5px;
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
    font-family: 'Silkscreen', monospace;
    font-size: 9px;
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
    font-family: 'Silkscreen', monospace;
    font-size: 9px;
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

/* Dialogs & Comboboxes */
QDialog {
    background-color: #0C0C0C;
    border: 2px solid #FFB800;
}

QComboBox {
    background-color: #161616;
    color: #FFFFFF;
    border: 1px solid #333333;
    padding: 6px 10px;
    font-family: 'Terminess Nerd Font', 'Silkscreen', monospace;
    font-size: 11px;
}
QComboBox:hover, QComboBox:focus {
    border: 1px solid #FFB800;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    background-color: #141414;
    color: #E0E0E0;
    selection-background-color: #FFB800;
    selection-color: #0C0C0C;
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
        self.setAcceptDrops(True)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header
        head_layout = QHBoxLayout()
        title = QLabel("WALLPAPER MANAGER", self)
        title.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 13px; font-weight: bold; letter-spacing: 1px;")
        head_layout.addWidget(title)

        head_layout.addStretch()

        self.add_btn = QPushButton("+ Add Custom", self)
        self.add_btn.setProperty("class", "SecondaryBtn")
        self.add_btn.setToolTip("Upload or select custom wallpaper from files")
        self.add_btn.clicked.connect(self.add_custom_wallpaper)
        head_layout.addWidget(self.add_btn)

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

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                ext = os.path.splitext(url.toLocalFile())[1].lower()
                if ext in ('.jpg', '.jpeg', '.png', '.webp'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if os.path.isfile(local_path):
                    self.import_wallpaper_file(local_path)
                    event.acceptProposedAction()
                    break

    def add_custom_wallpaper(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Custom Wallpaper",
            HOME,
            "Images (*.png *.jpg *.jpeg *.webp);;All Files (*)"
        )
        if file_path:
            self.import_wallpaper_file(file_path)

    def import_wallpaper_file(self, file_path):
        if not file_path or not os.path.isfile(file_path):
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            QMessageBox.warning(self, "Invalid Format", "Please select a valid image file (.jpg, .png, .webp).")
            return

        target_dir = os.path.join(DOTFILES, "wallpapers")
        os.makedirs(target_dir, exist_ok=True)
        base_name = os.path.basename(file_path)
        target_path = os.path.join(target_dir, base_name)

        if os.path.abspath(file_path) != os.path.abspath(target_path):
            if os.path.exists(target_path):
                name, ext_part = os.path.splitext(base_name)
                counter = 1
                while os.path.exists(os.path.join(target_dir, f"{name}_{counter}{ext_part}")):
                    counter += 1
                target_path = os.path.join(target_dir, f"{name}_{counter}{ext_part}")
            shutil.copy2(file_path, target_path)

        self.load_wallpapers()
        self.on_wallpaper_selected(target_path)
        self.status_lbl.setText(f"Added: {os.path.basename(target_path)} — Click 'Apply Wallpaper' to set as desktop background")
        self.status_lbl.setStyleSheet("color: #FFB800; font-size: 11px; font-weight: bold;")

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
        title.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 13px; font-weight: bold; letter-spacing: 1px;")
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
        title.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 13px; font-weight: bold; letter-spacing: 1px;")
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
# Display Configuration Classes
# -----------------------------------------------------------------------------
def parse_xrandr_query(output):
    """Parse xrandr --query text into a dictionary of connected monitors."""
    monitors = {}
    current = None
    for line in output.splitlines():
        m_conn = re.match(
            r'^([\w\-]+)\s+(connected|disconnected)\s*(primary)?\s*([0-9]+x[0-9]+\+[0-9]+\+[0-9]+)?\s*(left|right|inverted)?',
            line
        )
        if m_conn:
            name, status, primary, geom, rot = m_conn.groups()
            if status == 'connected':
                current = name
                res, x, y = None, 0, 0
                if geom:
                    parts = geom.replace('+', 'x').split('x')
                    res = f"{parts[0]}x{parts[1]}"
                    x, y = int(parts[2]), int(parts[3])
                monitors[name] = {
                    'name': name,
                    'connected': True,
                    'primary': bool(primary),
                    'active': bool(geom),
                    'current_res': res,
                    'current_rate': None,
                    'preferred_res': None,
                    'preferred_rate': None,
                    'x': x,
                    'y': y,
                    'rotation': rot if rot else 'normal',
                    'modes': {},
                    'placement': None
                }
            else:
                current = None
            continue

        if current and line.startswith('   '):
            parts = line.strip().split()
            if not parts:
                continue
            mode_res = parts[0]
            rates = []
            for r in parts[1:]:
                is_current = '*' in r
                is_preferred = '+' in r
                clean_r = r.rstrip('*+ ')
                try:
                    float(clean_r)
                    rates.append(clean_r)
                    if is_current:
                        monitors[current]['current_rate'] = clean_r
                    if is_preferred and not monitors[current].get('preferred_res'):
                        monitors[current]['preferred_res'] = mode_res
                        monitors[current]['preferred_rate'] = clean_r
                except ValueError:
                    pass
            if mode_res not in monitors[current]['modes']:
                monitors[current]['modes'][mode_res] = []
            monitors[current]['modes'][mode_res].extend(rates)

    if not monitors:
        # Fallback display for testing / headless environments
        monitors = {
            "eDP-1": {
                "name": "eDP-1",
                "connected": True,
                "primary": True,
                "active": True,
                "current_res": "1920x1080",
                "current_rate": "60.00",
                "preferred_res": "1920x1080",
                "preferred_rate": "60.00",
                "x": 0,
                "y": 0,
                "rotation": "normal",
                "modes": {
                    "1920x1080": ["60.00", "59.94"],
                    "1600x900": ["60.00"],
                    "1280x720": ["60.00"]
                },
                "placement": None
            }
        }
    return monitors


class MonitorBox(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, monitor_data, number, is_selected=False, parent=None):
        super().__init__(parent)
        self.data = monitor_data
        self.number = number
        self.is_selected = is_selected
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(145, 92)
        self.init_ui()

    def init_ui(self):
        self.update_style()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        num_lbl = QLabel(str(self.number), self)
        num_lbl.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 13px; font-weight: bold;")
        top_row.addWidget(num_lbl)

        top_row.addStretch()

        if self.data.get("primary", False):
            badge = QLabel("MAIN", self)
            badge.setStyleSheet("color: #0C0C0C; background: #FFB800; font-family: 'Silkscreen', monospace; font-size: 8px; font-weight: bold; padding: 1px 4px;")
            top_row.addWidget(badge)
        elif not self.data.get("active", False):
            badge = QLabel("OFF", self)
            badge.setStyleSheet("color: #888888; background: #222222; font-family: 'Silkscreen', monospace; font-size: 8px; font-weight: bold; padding: 1px 4px;")
            top_row.addWidget(badge)

        layout.addLayout(top_row)

        name_lbl = QLabel(self.data["name"], self)
        name_lbl.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px;")
        layout.addWidget(name_lbl)

        if self.data.get("active", False):
            res_str = self.data.get("current_res") or "Auto"
            rate_str = f"{float(self.data['current_rate']):.0f}Hz" if self.data.get("current_rate") else ""
            info_text = f"{res_str} {rate_str}".strip()
        else:
            info_text = "Disabled"

        info_lbl = QLabel(info_text, self)
        info_lbl.setStyleSheet("color: #888888; font-size: 9.5px;")
        layout.addWidget(info_lbl)

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("background-color: #201A0E; border: 2px solid #FFB800;")
        elif not self.data.get("active", False):
            self.setStyleSheet("background-color: #0E0E0E; border: 1px dashed #444444;")
        else:
            self.setStyleSheet("background-color: #141414; border: 1px solid #333333;")

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.data["name"])


class RevertCountdownDialog(QDialog):
    def __init__(self, revert_callback, keep_callback, parent=None, timeout=15):
        super().__init__(parent)
        self.setWindowTitle("Confirm Display Settings")
        self.setFixedSize(420, 190)
        self.setStyleSheet(QSS_STYLE)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        self.revert_callback = revert_callback
        self.keep_callback = keep_callback
        self.time_left = timeout
        self.confirmed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("KEEP DISPLAY SETTINGS?", self)
        title.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Do you want to keep these display settings?\nIf screen goes blank or unreadable, it will automatically revert.", self)
        desc.setStyleSheet("color: #CCCCCC; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.timer_lbl = QLabel(f"Reverting in {self.time_left} seconds...", self)
        self.timer_lbl.setStyleSheet("color: #E53935; font-family: 'Silkscreen', monospace; font-size: 10px; font-weight: bold;")
        layout.addWidget(self.timer_lbl)

        btn_row = QHBoxLayout()
        self.keep_btn = QPushButton("Keep Changes", self)
        self.keep_btn.setProperty("class", "PrimaryBtn")
        self.keep_btn.clicked.connect(self.on_keep)
        btn_row.addWidget(self.keep_btn)

        self.revert_btn = QPushButton(f"Revert ({self.time_left}s)", self)
        self.revert_btn.setProperty("class", "SecondaryBtn")
        self.revert_btn.clicked.connect(self.on_revert)
        btn_row.addWidget(self.revert_btn)

        layout.addLayout(btn_row)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)
        self.timer.start(1000)

    def on_tick(self):
        self.time_left -= 1
        if self.time_left <= 0:
            self.timer.stop()
            self.on_revert()
        else:
            self.timer_lbl.setText(f"Reverting in {self.time_left} seconds...")
            self.revert_btn.setText(f"Revert ({self.time_left}s)")

    def on_keep(self):
        self.confirmed = True
        self.timer.stop()
        self.keep_callback()
        self.accept()

    def on_revert(self):
        self.confirmed = False
        self.timer.stop()
        self.revert_callback()
        self.reject()

    def closeEvent(self, event):
        if not self.confirmed:
            self.on_revert()
        event.accept()


# -----------------------------------------------------------------------------
# Display Configuration & Arrangement Tab
# -----------------------------------------------------------------------------
class DisplayTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitors = self.query_monitors()
        self.selected_monitor = self.get_initial_selected_monitor()
        self.monitor_boxes = {}
        self.previous_cmd = None
        self.init_ui()

    def get_initial_selected_monitor(self):
        for name, m in self.monitors.items():
            if m.get("primary"):
                return name
        return list(self.monitors.keys())[0] if self.monitors else None

    def query_monitors(self):
        try:
            env = dict(os.environ)
            if "DISPLAY" not in env or not env["DISPLAY"]:
                env["DISPLAY"] = ":0"
            out = subprocess.check_output(["xrandr", "--query"], env=env, stderr=subprocess.DEVNULL).decode("utf-8")
            return parse_xrandr_query(out)
        except Exception:
            return parse_xrandr_query("")

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0C0C0C; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("DISPLAY CONFIGURATION & ARRANGEMENT", container)
        title.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 13px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(title)

        # 1. Visual Canvas Card
        self.canvas_card = QFrame(container)
        self.canvas_card.setProperty("class", "CardFrame")
        cc_layout = QVBoxLayout(self.canvas_card)
        cc_layout.setContentsMargins(14, 12, 14, 12)
        cc_layout.setSpacing(10)

        cc_title = QLabel("Rearrange Displays (Click any display to configure)", self.canvas_card)
        cc_title.setStyleSheet("color: #888888; font-size: 11px; font-weight: bold;")
        cc_layout.addWidget(cc_title)

        self.boxes_row = QHBoxLayout()
        self.boxes_row.setSpacing(12)
        self.rebuild_monitor_boxes()
        cc_layout.addLayout(self.boxes_row)

        # Preset arrangement buttons
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)

        btn_extend_r = QPushButton("Extend Right", self.canvas_card)
        btn_extend_r.setProperty("class", "SecondaryBtn")
        btn_extend_r.clicked.connect(self.preset_extend_right)
        preset_row.addWidget(btn_extend_r)

        btn_extend_l = QPushButton("Extend Left", self.canvas_card)
        btn_extend_l.setProperty("class", "SecondaryBtn")
        btn_extend_l.clicked.connect(self.preset_extend_left)
        preset_row.addWidget(btn_extend_l)

        btn_mirror = QPushButton("Mirror All", self.canvas_card)
        btn_mirror.setProperty("class", "SecondaryBtn")
        btn_mirror.clicked.connect(self.preset_mirror)
        preset_row.addWidget(btn_mirror)

        btn_id = QPushButton("Identify", self.canvas_card)
        btn_id.setProperty("class", "SecondaryBtn")
        btn_id.clicked.connect(self.identify_displays)
        preset_row.addWidget(btn_id)

        preset_row.addStretch()
        cc_layout.addLayout(preset_row)

        layout.addWidget(self.canvas_card)

        # 2. Selected Display Controls Card
        self.detail_card = QFrame(container)
        self.detail_card.setProperty("class", "CardFrame")
        self.dc_layout = QVBoxLayout(self.detail_card)
        self.dc_layout.setContentsMargins(16, 14, 16, 14)
        self.dc_layout.setSpacing(12)

        self.detail_title = QLabel(f"SETTINGS FOR: {self.selected_monitor or 'No Display'}", self.detail_card)
        self.detail_title.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 12px; font-weight: bold;")
        self.dc_layout.addWidget(self.detail_title)

        toggles_row = QHBoxLayout()
        self.active_check = QCheckBox("Enable Display (Turned On)", self.detail_card)
        self.active_check.stateChanged.connect(self.on_active_toggled)
        toggles_row.addWidget(self.active_check)

        self.primary_check = QCheckBox("Make Primary Display", self.detail_card)
        self.primary_check.stateChanged.connect(self.on_primary_toggled)
        toggles_row.addWidget(self.primary_check)
        toggles_row.addStretch()
        self.dc_layout.addLayout(toggles_row)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(16)
        form_grid.setVerticalSpacing(10)

        # Resolution
        lbl_res = QLabel("Resolution:", self.detail_card)
        lbl_res.setStyleSheet("color: #888888; font-weight: bold; font-size: 11px;")
        form_grid.addWidget(lbl_res, 0, 0)
        self.combo_res = QComboBox(self.detail_card)
        self.combo_res.currentIndexChanged.connect(self.on_resolution_changed)
        form_grid.addWidget(self.combo_res, 0, 1)

        # Refresh Rate
        lbl_rate = QLabel("Refresh Rate:", self.detail_card)
        lbl_rate.setStyleSheet("color: #888888; font-weight: bold; font-size: 11px;")
        form_grid.addWidget(lbl_rate, 0, 2)
        self.combo_rate = QComboBox(self.detail_card)
        self.combo_rate.currentIndexChanged.connect(self.on_rate_changed)
        form_grid.addWidget(self.combo_rate, 0, 3)

        # Orientation
        lbl_rot = QLabel("Orientation:", self.detail_card)
        lbl_rot.setStyleSheet("color: #888888; font-weight: bold; font-size: 11px;")
        form_grid.addWidget(lbl_rot, 1, 0)
        self.combo_rot = QComboBox(self.detail_card)
        self.combo_rot.addItem("Landscape (Normal)", "normal")
        self.combo_rot.addItem("Portrait (Left 90°)", "left")
        self.combo_rot.addItem("Portrait (Right 270°)", "right")
        self.combo_rot.addItem("Landscape Inverted (180°)", "inverted")
        self.combo_rot.currentIndexChanged.connect(self.on_rotation_changed)
        form_grid.addWidget(self.combo_rot, 1, 1)

        # Position Relative To
        lbl_pos = QLabel("Placement:", self.detail_card)
        lbl_pos.setStyleSheet("color: #888888; font-weight: bold; font-size: 11px;")
        form_grid.addWidget(lbl_pos, 1, 2)
        self.combo_pos = QComboBox(self.detail_card)
        self.combo_pos.currentIndexChanged.connect(self.on_placement_changed)
        form_grid.addWidget(self.combo_pos, 1, 3)

        self.dc_layout.addLayout(form_grid)
        layout.addWidget(self.detail_card)

        # 3. Action Buttons Row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        self.apply_btn = QPushButton("Apply Display Settings", container)
        self.apply_btn.setProperty("class", "PrimaryBtn")
        self.apply_btn.clicked.connect(self.apply_display_settings)
        actions_row.addWidget(self.apply_btn)

        self.capture_btn = QPushButton("Capture Card 1080p@60Hz Preset", container)
        self.capture_btn.setProperty("class", "SecondaryBtn")
        self.capture_btn.clicked.connect(self.preset_capture_card)
        actions_row.addWidget(self.capture_btn)

        self.reset_btn = QPushButton("Reset All (Auto)", container)
        self.reset_btn.setProperty("class", "SecondaryBtn")
        self.reset_btn.clicked.connect(self.preset_reset_auto)
        actions_row.addWidget(self.reset_btn)

        actions_row.addStretch()
        layout.addLayout(actions_row)

        # 4. Quick Component Reloads Card
        act_card = QFrame(container)
        act_card.setProperty("class", "CardFrame")
        ac_layout = QVBoxLayout(act_card)
        ac_layout.setContentsMargins(14, 10, 14, 10)
        ac_layout.setSpacing(8)

        ac_title = QLabel("Quick Desktop Reloads", act_card)
        ac_title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11.5px;")
        ac_layout.addWidget(ac_title)

        btns_row = QHBoxLayout()
        btns_row.setSpacing(8)

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

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        self.populate_form_for_selected()

    def rebuild_monitor_boxes(self):
        for i in reversed(range(self.boxes_row.count())):
            item = self.boxes_row.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        self.monitor_boxes = {}
        for idx, (name, m) in enumerate(self.monitors.items(), start=1):
            is_sel = (name == self.selected_monitor)
            box = MonitorBox(m, idx, is_selected=is_sel)
            box.clicked.connect(self.select_monitor)
            self.boxes_row.addWidget(box)
            self.monitor_boxes[name] = box

        self.boxes_row.addStretch()

    def select_monitor(self, name):
        self.selected_monitor = name
        for m_name, box in self.monitor_boxes.items():
            box.set_selected(m_name == name)
        self.detail_title.setText(f"SETTINGS FOR: {name}")
        self.populate_form_for_selected()

    def populate_form_for_selected(self):
        if not self.selected_monitor or self.selected_monitor not in self.monitors:
            return

        m = self.monitors[self.selected_monitor]

        self.active_check.blockSignals(True)
        self.primary_check.blockSignals(True)
        self.combo_res.blockSignals(True)
        self.combo_rate.blockSignals(True)
        self.combo_rot.blockSignals(True)
        self.combo_pos.blockSignals(True)

        self.active_check.setChecked(m.get("active", True))
        self.primary_check.setChecked(m.get("primary", False))
        self.primary_check.setEnabled(m.get("active", True))

        # Populate Resolutions
        self.combo_res.clear()
        modes = list(m.get("modes", {}).keys())
        if not modes:
            modes = ["1920x1080", "1600x900", "1280x720"]

        pref = m.get("preferred_res")
        cur_res = m.get("current_res") or (modes[0] if modes else "1920x1080")

        for mode in modes:
            label = f"{mode} (Recommended)" if mode == pref else mode
            self.combo_res.addItem(label, mode)

        res_idx = 0
        for i in range(self.combo_res.count()):
            if self.combo_res.itemData(i) == cur_res:
                res_idx = i
                break
        self.combo_res.setCurrentIndex(res_idx)

        # Populate Rates
        self.populate_rates_for_res(cur_res, m.get("current_rate"))

        # Rotation
        cur_rot = m.get("rotation", "normal")
        rot_idx = 0
        for i in range(self.combo_rot.count()):
            if self.combo_rot.itemData(i) == cur_rot:
                rot_idx = i
                break
        self.combo_rot.setCurrentIndex(rot_idx)

        # Placement
        self.combo_pos.clear()
        other_monitors = [k for k in self.monitors.keys() if k != self.selected_monitor and self.monitors[k].get("active", True)]
        if not other_monitors:
            self.combo_pos.addItem("Standalone / Primary Screen", None)
            self.combo_pos.setEnabled(False)
        else:
            self.combo_pos.setEnabled(True)
            for other in other_monitors:
                self.combo_pos.addItem(f"Right of {other}", ("--right-of", other))
                self.combo_pos.addItem(f"Left of {other}", ("--left-of", other))
                self.combo_pos.addItem(f"Above {other}", ("--above", other))
                self.combo_pos.addItem(f"Below {other}", ("--below", other))
                self.combo_pos.addItem(f"Mirror / Duplicate {other}", ("--same-as", other))

            # Select current placement if any
            cur_placement = m.get("placement")
            if cur_placement:
                for i in range(self.combo_pos.count()):
                    if self.combo_pos.itemData(i) == cur_placement:
                        self.combo_pos.setCurrentIndex(i)
                        break

        self.active_check.blockSignals(False)
        self.primary_check.blockSignals(False)
        self.combo_res.blockSignals(False)
        self.combo_rate.blockSignals(False)
        self.combo_rot.blockSignals(False)
        self.combo_pos.blockSignals(False)

    def populate_rates_for_res(self, res, current_rate=None):
        m = self.monitors[self.selected_monitor]
        rates = m.get("modes", {}).get(res, ["60.00"])
        self.combo_rate.clear()
        for r in rates:
            self.combo_rate.addItem(f"{float(r):.2f} Hz", r)

        rate_idx = 0
        if current_rate:
            for i in range(self.combo_rate.count()):
                if self.combo_rate.itemData(i) == current_rate:
                    rate_idx = i
                    break
        self.combo_rate.setCurrentIndex(rate_idx)

    def on_resolution_changed(self, idx):
        if not self.selected_monitor:
            return
        res = self.combo_res.itemData(idx)
        self.monitors[self.selected_monitor]["current_res"] = res
        self.populate_rates_for_res(res)
        self.rebuild_monitor_boxes()

    def on_rate_changed(self, idx):
        if not self.selected_monitor:
            return
        rate = self.combo_rate.itemData(idx)
        self.monitors[self.selected_monitor]["current_rate"] = rate
        self.rebuild_monitor_boxes()

    def on_active_toggled(self, state):
        if not self.selected_monitor:
            return
        is_active = (state == Qt.Checked)
        self.monitors[self.selected_monitor]["active"] = is_active
        self.primary_check.setEnabled(is_active)
        self.rebuild_monitor_boxes()

    def on_primary_toggled(self, state):
        if not self.selected_monitor:
            return
        is_pri = (state == Qt.Checked)
        if is_pri:
            for k in self.monitors:
                self.monitors[k]["primary"] = (k == self.selected_monitor)
        else:
            self.monitors[self.selected_monitor]["primary"] = False
        self.rebuild_monitor_boxes()

    def on_rotation_changed(self, idx):
        if not self.selected_monitor:
            return
        rot = self.combo_rot.itemData(idx)
        self.monitors[self.selected_monitor]["rotation"] = rot

    def on_placement_changed(self, idx):
        if not self.selected_monitor:
            return
        placement = self.combo_pos.itemData(idx)
        self.monitors[self.selected_monitor]["placement"] = placement

    def preset_extend_right(self):
        names = list(self.monitors.keys())
        if len(names) >= 2:
            self.monitors[names[0]]["active"] = True
            self.monitors[names[0]]["primary"] = True
            self.monitors[names[0]]["placement"] = None

            self.monitors[names[1]]["active"] = True
            self.monitors[names[1]]["primary"] = False
            self.monitors[names[1]]["placement"] = ("--right-of", names[0])
            self.rebuild_monitor_boxes()
            self.populate_form_for_selected()
            self.apply_display_settings()

    def preset_extend_left(self):
        names = list(self.monitors.keys())
        if len(names) >= 2:
            self.monitors[names[0]]["active"] = True
            self.monitors[names[0]]["primary"] = True
            self.monitors[names[0]]["placement"] = None

            self.monitors[names[1]]["active"] = True
            self.monitors[names[1]]["primary"] = False
            self.monitors[names[1]]["placement"] = ("--left-of", names[0])
            self.rebuild_monitor_boxes()
            self.populate_form_for_selected()
            self.apply_display_settings()

    def preset_mirror(self):
        names = list(self.monitors.keys())
        if len(names) >= 2:
            pri = names[0]
            self.monitors[pri]["active"] = True
            self.monitors[pri]["primary"] = True
            self.monitors[pri]["placement"] = None

            for other in names[1:]:
                self.monitors[other]["active"] = True
                self.monitors[other]["primary"] = False
                self.monitors[other]["placement"] = ("--same-as", pri)
            self.rebuild_monitor_boxes()
            self.populate_form_for_selected()
            self.apply_display_settings()

    def preset_capture_card(self):
        names = list(self.monitors.keys())
        if len(names) >= 2:
            pri = names[0]
            sec = names[1]
            self.monitors[pri]["active"] = True
            self.monitors[pri]["primary"] = True
            self.monitors[pri]["current_res"] = "1920x1080"
            self.monitors[pri]["current_rate"] = "60.00"
            self.monitors[pri]["placement"] = None

            self.monitors[sec]["active"] = True
            self.monitors[sec]["primary"] = False
            self.monitors[sec]["current_res"] = "1920x1080"
            self.monitors[sec]["current_rate"] = "60.00"
            self.monitors[sec]["placement"] = ("--same-as", pri)
            self.rebuild_monitor_boxes()
            self.populate_form_for_selected()
            self.apply_display_settings()

    def preset_reset_auto(self):
        cmd = ["xrandr", "--auto"]
        subprocess.run(cmd)
        self.monitors = self.query_monitors()
        self.rebuild_monitor_boxes()
        self.populate_form_for_selected()
        self.refresh_environment()

    def identify_displays(self):
        lines = []
        for idx, (name, m) in enumerate(self.monitors.items(), start=1):
            status = f"{m.get('current_res')} @ {float(m.get('current_rate', 60)):.0f}Hz" if m.get('active') else "OFF"
            pri = " (Primary)" if m.get('primary') else ""
            lines.append(f"[{idx}] {name}: {status}{pri}")

        text = "\n".join(lines)
        if shutil.which("notify-send"):
            subprocess.Popen(["notify-send", "-u", "critical", "-t", "4000", "DISPLAY IDENTIFIER", text])
        else:
            QMessageBox.information(self, "Display Identifier", text)

    def build_xrandr_command(self):
        cmd = ["xrandr"]
        for name, m in self.monitors.items():
            if not m.get("active", True):
                cmd.extend(["--output", name, "--off"])
            else:
                cmd.extend(["--output", name])
                if m.get("primary", False):
                    cmd.append("--primary")
                if m.get("current_res"):
                    cmd.extend(["--mode", m["current_res"]])
                if m.get("current_rate"):
                    cmd.extend(["--rate", m["current_rate"]])
                rot = m.get("rotation", "normal")
                cmd.extend(["--rotate", rot])
                placement = m.get("placement")
                if placement and len(placement) == 2:
                    cmd.extend([placement[0], placement[1]])
        return cmd

    def apply_display_settings(self):
        # 1. Save previous state for revert
        prev_cmd = ["xrandr"]
        for name, m in self.monitors.items():
            if m.get("active"):
                prev_cmd.extend(["--output", name, "--auto"])
            else:
                prev_cmd.extend(["--output", name, "--off"])
        self.previous_cmd = prev_cmd

        # 2. Build and run new command
        new_cmd = self.build_xrandr_command()
        try:
            env = dict(os.environ)
            if "DISPLAY" not in env or not env["DISPLAY"]:
                env["DISPLAY"] = ":0"
            subprocess.run(new_cmd, env=env, check=False)
            self.refresh_environment()
        except Exception as e:
            QMessageBox.critical(self, "Error Applying Settings", str(e))
            return

        # 3. Confirmation Dialog with 15-second Revert Timer
        dialog = RevertCountdownDialog(
            revert_callback=self.revert_display_settings,
            keep_callback=lambda: self.save_to_autostart_script(new_cmd),
            parent=self,
            timeout=15
        )
        dialog.exec_()

    def revert_display_settings(self):
        if self.previous_cmd:
            env = dict(os.environ)
            if "DISPLAY" not in env or not env["DISPLAY"]:
                env["DISPLAY"] = ":0"
            subprocess.run(self.previous_cmd, env=env)
            self.refresh_environment()
            if shutil.which("notify-send"):
                subprocess.Popen(["notify-send", "-u", "normal", "Display Settings", "Reverted to previous display configuration."])

    def save_to_autostart_script(self, cmd):
        script_dir = os.path.join(CONFIG_DIR, "i3", "scripts")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, "display_layout.sh")

        cmd_str = " ".join(cmd)
        content = f"""#!/usr/bin/env bash
# Wu-Tang Clan Display Layout Configuration
# Auto-generated by cream-settings
export DISPLAY="${{DISPLAY:-:0}}"
{cmd_str}
"""
        with open(script_path, "w") as f:
            f.write(content)
        os.chmod(script_path, 0o755)

        if shutil.which("notify-send"):
            subprocess.Popen(["notify-send", "-u", "low", "Display Settings", "Configuration saved to autostart!"])

    def refresh_environment(self):
        # Update wallpaper
        if os.path.exists(FEHBG_PATH):
            subprocess.Popen(["bash", FEHBG_PATH])
        # Restart Polybar
        self.restart_polybar()

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
        layout.setSpacing(16)

        # Header with Real Wu-Tang Logo & Silkscreen Typography
        header_widget = QWidget(self)
        hw_layout = QHBoxLayout(header_widget)
        hw_layout.setContentsMargins(0, 0, 0, 0)
        hw_layout.setSpacing(18)

        # Wu-Tang Logo
        logo_lbl = QLabel(header_widget)
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        logo_lbl.setFixedSize(72, 72)
        hw_layout.addWidget(logo_lbl)

        # Titles & Author
        titles_col = QVBoxLayout()
        titles_col.setSpacing(5)

        title_main = QLabel("WU-TANG CLAN", header_widget)
        title_main.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 16px; font-weight: bold; letter-spacing: 1.5px;")
        titles_col.addWidget(title_main)

        title_sub = QLabel("C.R.E.A.M. RICE // ARCH LINUX", header_widget)
        title_sub.setStyleSheet("color: #E0E0E0; font-family: 'Silkscreen', monospace; font-size: 9px; font-weight: bold;")
        titles_col.addWidget(title_sub)

        # Author badge for 3plz
        author_badge = QLabel("AUTHOR: 3plz", header_widget)
        author_badge.setStyleSheet(
            "color: #0C0C0C; background-color: #FFB800; font-family: 'Silkscreen', monospace; "
            "font-size: 9px; font-weight: bold; padding: 2px 8px;"
        )
        author_badge.setFixedWidth(112)
        titles_col.addWidget(author_badge)

        hw_layout.addLayout(titles_col)
        hw_layout.addStretch()

        layout.addWidget(header_widget)

        card = QFrame(self)
        card.setProperty("class", "CardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(8)

        # System info & Author
        uname = os.uname()
        c_layout.addWidget(self.make_info_row("Author & Creator:", "3plz"))
        c_layout.addWidget(self.make_info_row("Operating System:", f"{uname.sysname} ({uname.release})"))
        c_layout.addWidget(self.make_info_row("Node Hostname:", uname.nodename))

        cpu_count = psutil.cpu_count(logical=True)
        mem = psutil.virtual_memory()
        mem_gb = f"{mem.total / (1024**3):.1f} GB"
        c_layout.addWidget(self.make_info_row("Hardware:", f"{cpu_count} CPU Threads | {mem_gb} RAM"))
        c_layout.addWidget(self.make_info_row("Theme & Palette:", "Pitch Black (#0C0C0C) & Signature Gold (#FFB800)"))
        c_layout.addWidget(self.make_info_row("Typography:", "Silkscreen & Terminess Nerd Font"))
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
        k.setStyleSheet("color: #888888; font-weight: bold; font-size: 11px; width: 150px;")
        v = QLabel(value, row)
        if value == "3plz":
            v.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-weight: bold; font-size: 11px;")
        else:
            v.setStyleSheet("color: #FFFFFF; font-size: 11px;")
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
        if os.path.exists(LOGO_PATH):
            self.setWindowIcon(QIcon(LOGO_PATH))
        self.setFixedSize(780, 520)
        self.setStyleSheet(QSS_STYLE)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Header Bar
        header = QFrame(self)
        header.setFixedHeight(48)
        header.setStyleSheet("background-color: #121212; border-bottom: 2px solid #FFB800;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 0, 16, 0)
        h_layout.setSpacing(10)

        # Wu-Tang Logo Icon in Header
        logo_icon = QLabel(header)
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_icon.setPixmap(pix)
        logo_icon.setFixedSize(24, 24)
        h_layout.addWidget(logo_icon)

        # Title in Silkscreen font (matching Polybar WU-TANG label)
        logo_lbl = QLabel("WU-TANG // CONTROL CENTER", header)
        logo_lbl.setStyleSheet(
            "color: #FFB800; font-family: 'Silkscreen', monospace; "
            "font-size: 11px; font-weight: bold; letter-spacing: 1.5px;"
        )
        h_layout.addWidget(logo_lbl)

        h_layout.addStretch()

        badge = QLabel("ARCH LINUX | i3WM", header)
        badge.setStyleSheet("color: #888888; font-family: 'Silkscreen', monospace; font-size: 8.5px; font-weight: bold;")
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
