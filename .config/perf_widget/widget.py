#!/usr/bin/env python3
"""
Wu-Tang Performance Monitor Desktop Widget
A Task-Manager-style desktop performance widget for Linux i3wm.
Features:
- Left Tab Navigation: CPU, Memory, Disk, GPU
- Real-time 60-second scrolling history graph with gold gradient fill
- Detailed metrics grid for active component
- Frameless, 0px border-radius, Wu-Tang Clan aesthetic (#FFB800 & #0C0C0C)
- Desktop-level lowering / raising with ghost button & SIGUSR1
- Position persistence across sessions
"""

import sys
import os
import time
import json
import signal
import subprocess
import psutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QPainterPath, QFont, QCursor
)

CONFIG_DIR = os.path.expanduser("~/.config/perf_widget")
POSITION_FILE = os.path.join(CONFIG_DIR, "position.json")
os.makedirs(CONFIG_DIR, exist_ok=True)


# -------------------------------------------------------------
# Chart Widget: Real-time scrolling Task Manager graph
# -------------------------------------------------------------
class TaskMgrChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self.history = [0.0] * 60
        self.unit_suffix = "%"

    def set_data(self, history, unit="%"):
        self.history = history[-60:]
        if len(self.history) < 60:
            self.history = [0.0] * (60 - len(self.history)) + self.history
        self.unit_suffix = unit
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        p.fillRect(0, 0, w, h, QColor(14, 14, 14, 210))

        # Grid lines (horizontal: 0%, 25%, 50%, 75%, 100%)
        grid_pen = QPen(QColor(255, 184, 0, 35), 1, Qt.DashLine)
        p.setPen(grid_pen)
        for i in range(1, 4):
            y = int((h * i) / 4)
            p.drawLine(0, y, w, y)

        # Grid lines (vertical: every 10 seconds)
        for i in range(1, 6):
            x = int((w * i) / 6)
            p.drawLine(x, 0, x, h)

        # Plot data points
        step_x = w / 59.0
        points = []
        for i, val in enumerate(self.history):
            clamped = max(0.0, min(100.0, float(val)))
            y = h - (clamped / 100.0) * (h - 6) - 3
            x = i * step_x
            points.append(QPointF(x, y))

        if len(points) >= 2:
            # Gradient fill under the curve
            path = QPainterPath()
            path.moveTo(points[0].x(), h)
            for pt in points:
                path.lineTo(pt)
            path.lineTo(points[-1].x(), h)
            path.closeSubpath()

            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0.0, QColor(255, 184, 0, 95))
            grad.setColorAt(0.7, QColor(255, 184, 0, 25))
            grad.setColorAt(1.0, QColor(255, 184, 0, 2))
            p.fillPath(path, QBrush(grad))

            # Main Gold Line
            line_pen = QPen(QColor("#FFB800"), 2)
            line_pen.setCapStyle(Qt.RoundCap)
            p.setPen(line_pen)
            for i in range(len(points) - 1):
                p.drawLine(points[i], points[i + 1])

        # Border
        border_pen = QPen(QColor(255, 184, 0, 65), 1)
        p.setPen(border_pen)
        p.drawRect(0, 0, w - 1, h - 1)

        # Axis annotations
        p.setFont(QFont("Silkscreen", 7))
        p.setPen(QColor("#8C7B58"))
        p.drawText(6, 12, "100" + self.unit_suffix)
        p.drawText(6, h - 4, "0" + self.unit_suffix)
        p.drawText(w - 28, h - 4, "0s")
        p.drawText(w - 68, h - 4, "60s")

        p.end()


# -------------------------------------------------------------
# Mini Progress Bar for sidebar tabs
# -------------------------------------------------------------
class MiniBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self.percent = 0.0

    def set_percent(self, val):
        self.percent = max(0.0, min(100.0, float(val)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w = self.width()
        p.fillRect(0, 0, w, 3, QColor(35, 35, 35))
        fill_w = int((self.percent / 100.0) * w)
        p.fillRect(0, 0, fill_w, 3, QColor("#FFB800"))
        p.end()


# -------------------------------------------------------------
# Sidebar Navigation Tab Button
# -------------------------------------------------------------
class TabButton(QFrame):
    def __init__(self, tab_id, title, on_click, parent=None):
        super().__init__(parent)
        self.tab_id = tab_id
        self.on_click = on_click
        self.is_active = False

        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(58)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-family: 'Silkscreen', monospace; font-size: 10px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self.title_lbl)

        self.sub_lbl = QLabel("...")
        self.sub_lbl.setStyleSheet("font-family: 'Silkscreen', monospace; font-size: 8.5px; color: #8C7B58;")
        layout.addWidget(self.sub_lbl)

        self.bar = MiniBar()
        layout.addWidget(self.bar)

        self.update_style()

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def update_info(self, subtext, percent):
        self.sub_lbl.setText(subtext)
        self.bar.set_percent(percent)

    def update_style(self):
        if self.is_active:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 184, 0, 0.16);
                    border-left: 3px solid #FFB800;
                    border-radius: 0px;
                }
            """)
            self.title_lbl.setStyleSheet("font-family: 'Silkscreen', monospace; font-size: 10px; font-weight: bold; color: #FFB800;")
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.02);
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                }
                QFrame:hover {
                    background-color: rgba(255, 184, 0, 0.07);
                    border-left: 3px solid rgba(255, 184, 0, 0.5);
                }
            """)
            self.title_lbl.setStyleSheet("font-family: 'Silkscreen', monospace; font-size: 10px; font-weight: bold; color: #FFFFFF;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_click(self.tab_id)


# -------------------------------------------------------------
# Metric Item Cell in Details Grid
# -------------------------------------------------------------
class MetricCell(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(1)

        self.label = QLabel(label_text.upper())
        self.label.setStyleSheet("color: #8C7B58; font-family: 'Silkscreen', monospace; font-size: 7.5px;")
        layout.addWidget(self.label)

        self.value = QLabel("—")
        self.value.setStyleSheet("color: #FFFFFF; font-family: 'Silkscreen', monospace; font-size: 9.5px; font-weight: bold;")
        layout.addWidget(self.value)

    def set_value(self, val_text, color=None):
        self.value.setText(str(val_text))
        if color:
            self.value.setStyleSheet(f"color: {color}; font-family: 'Silkscreen', monospace; font-size: 9.5px; font-weight: bold;")


# -------------------------------------------------------------
# Main Performance Widget
# -------------------------------------------------------------
class PerfWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager Performance")
        self.setObjectName("PerfWidget")

        # Bypass window manager for proper X11 stacking and i3wm compatibility
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.current_tab = "CPU"
        self.drag_position = QPoint()
        self.is_lowered = False

        # History buffers (60 seconds)
        self.history_cpu = [0.0] * 60
        self.history_mem = [0.0] * 60
        self.history_disk = [0.0] * 60
        self.history_gpu = [0.0] * 60

        # Hardware info cache
        self.cpu_name = self.detect_cpu_name()
        self.has_gpu = self.detect_gpu_available()

        # Prime psutil CPU percent
        psutil.cpu_percent(interval=None)

        self.init_ui()
        self.load_position()
        self.setup_signals()

        # Update timer: 1000ms
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_metrics)
        self.timer.start(1000)

        # Trigger initial update immediately
        QTimer.singleShot(50, self.update_metrics)
        QTimer.singleShot(150, self.apply_initial_state)

    def detect_cpu_name(self):
        try:
            with open("/proc/cpuinfo") as f:
                for l in f:
                    if "model name" in l:
                        raw = l.split(":", 1)[1].strip()
                        # Shorten if too long
                        return raw.replace("Intel(R) Xeon(R) CPU ", "").replace("Intel(R) Core(TM) ", "")
        except Exception:
            pass
        return "Generic Multi-Core CPU"

    def detect_gpu_available(self):
        try:
            subprocess.check_output(["which", "nvidia-smi"], stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def init_ui(self):
        self.setFixedSize(540, 330)

        # Background Card
        self.card = QFrame(self)
        self.card.setGeometry(0, 0, 540, 330)
        self.card.setObjectName("cardFrame")
        self.card.setStyleSheet("""
            QFrame#cardFrame {
                background-color: rgba(12, 12, 12, 0.90);
                border: 1.5px solid #FFB800;
                border-radius: 0px;
            }
        """)

        # Ghost pin/lower button in top-right
        self.btn_pin = QPushButton("▾", self.card)
        self.btn_pin.setGeometry(514, 5, 22, 22)
        self.btn_pin.setObjectName("pinBtn")
        self.btn_pin.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_pin.setToolTip("Скрыть за все окна на рабочий стол")
        self.btn_pin.setStyleSheet("""
            QPushButton#pinBtn {
                background: transparent;
                color: rgba(255, 255, 255, 0.22);
                font-size: 12px;
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

        # Main Layout: Left Sidebar + Right View
        main_layout = QHBoxLayout(self.card)
        main_layout.setContentsMargins(10, 10, 12, 10)
        main_layout.setSpacing(12)

        # ---------------- Left Sidebar ----------------
        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(136)
        sidebar_frame.setStyleSheet("background: transparent; border: none;")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(6)

        # Title at top of sidebar
        brand_lbl = QLabel("PERFORMANCE")
        brand_lbl.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 9px; font-weight: bold; margin-bottom: 2px;")
        sidebar_layout.addWidget(brand_lbl)

        # Tab buttons
        self.tabs = {}
        tab_list = ["CPU", "MEMORY", "DISK"]
        if self.has_gpu:
            tab_list.append("GPU")

        for tid in tab_list:
            btn = TabButton(tid, tid, self.switch_tab, sidebar_frame)
            sidebar_layout.addWidget(btn)
            self.tabs[tid] = btn

        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar_frame)

        # Separator Line between Left & Right
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setStyleSheet("color: rgba(255, 184, 0, 0.25);")
        main_layout.addWidget(sep)

        # ---------------- Right Content Area ----------------
        right_frame = QFrame()
        right_frame.setStyleSheet("background: transparent; border: none;")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(2, 0, 0, 0)
        right_layout.setSpacing(8)

        # Top Header (Name + Big Usage Metric)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 18, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        self.view_title = QLabel("CPU")
        self.view_title.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 13px; font-weight: bold;")
        self.device_name = QLabel(self.cpu_name)
        self.device_name.setStyleSheet("color: #AAAAAA; font-family: 'Silkscreen', monospace; font-size: 8px;")
        title_box.addWidget(self.view_title)
        title_box.addWidget(self.device_name)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        metric_box = QVBoxLayout()
        metric_box.setSpacing(1)
        self.metric_big = QLabel("0 %")
        self.metric_big.setAlignment(Qt.AlignRight)
        self.metric_big.setStyleSheet("color: #FFB800; font-family: 'Silkscreen', monospace; font-size: 18px; font-weight: bold;")
        self.metric_sub = QLabel("% UTILIZATION")
        self.metric_sub.setAlignment(Qt.AlignRight)
        self.metric_sub.setStyleSheet("color: #8C7B58; font-family: 'Silkscreen', monospace; font-size: 7.5px;")
        metric_box.addWidget(self.metric_big)
        metric_box.addWidget(self.metric_sub)
        header_layout.addLayout(metric_box)

        right_layout.addLayout(header_layout)

        # Live Chart
        self.chart = TaskMgrChart(right_frame)
        right_layout.addWidget(self.chart)

        # Bottom Details 2x3 Grid
        grid_frame = QFrame()
        grid_frame.setStyleSheet("""
            QFrame {
                background: rgba(18, 18, 18, 0.65);
                border: 1px solid rgba(255, 184, 0, 0.20);
                border-radius: 0px;
                padding: 4px;
            }
        """)
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setContentsMargins(8, 4, 8, 4)
        grid_layout.setHorizontalSpacing(16)
        grid_layout.setVerticalSpacing(4)

        self.cell_labels = [
            MetricCell("Utilization"),
            MetricCell("Speed"),
            MetricCell("Processes"),
            MetricCell("Uptime"),
            MetricCell("Cores"),
            MetricCell("Threads"),
        ]

        # 2 rows x 3 columns
        grid_layout.addWidget(self.cell_labels[0], 0, 0)
        grid_layout.addWidget(self.cell_labels[1], 0, 1)
        grid_layout.addWidget(self.cell_labels[2], 0, 2)
        grid_layout.addWidget(self.cell_labels[3], 1, 0)
        grid_layout.addWidget(self.cell_labels[4], 1, 1)
        grid_layout.addWidget(self.cell_labels[5], 1, 2)

        right_layout.addWidget(grid_frame)
        main_layout.addWidget(right_frame)

        # Activate initial tab
        self.switch_tab("CPU")
        self.btn_pin.raise_()

    def switch_tab(self, tab_id):
        self.current_tab = tab_id
        for tid, btn in self.tabs.items():
            btn.set_active(tid == tab_id)

        # Update right header view immediately
        if tab_id == "CPU":
            self.view_title.setText("CPU")
            self.device_name.setText(self.cpu_name)
            self.metric_sub.setText("% UTILIZATION")
            self.chart.set_data(self.history_cpu, "%")
            self.set_cell_names(["Utilization", "Speed", "Processes", "Uptime", "Cores", "Threads"])
        elif tab_id == "MEMORY":
            self.view_title.setText("MEMORY")
            total_gb = psutil.virtual_memory().total / (1024 ** 3)
            self.device_name.setText(f"DDR System Memory ({total_gb:.1f} GB)")
            self.metric_sub.setText("IN USE / TOTAL")
            self.chart.set_data(self.history_mem, "%")
            self.set_cell_names(["In Use", "Available", "Committed", "Cached", "Total", "Usage %"])
        elif tab_id == "DISK":
            self.view_title.setText("DISK")
            self.device_name.setText("Root Filesystem (ext4)")
            self.metric_sub.setText("% CAPACITY USED")
            self.chart.set_data(self.history_disk, "%")
            self.set_cell_names(["Used Space", "Free Space", "Capacity", "Mount", "Read / s", "Write / s"])
        elif tab_id == "GPU":
            self.view_title.setText("GPU")
            self.device_name.setText("NVIDIA GeForce GTX 650")
            self.metric_sub.setText("% VRAM USAGE")
            self.chart.set_data(self.history_gpu, "%")
            self.set_cell_names(["VRAM Used", "VRAM Free", "VRAM Total", "Temperature", "Fan Speed", "Driver"])

        self.update_metrics()

    def set_cell_names(self, names):
        for i, name in enumerate(names):
            if i < len(self.cell_labels):
                self.cell_labels[i].label.setText(name.upper())

    def update_metrics(self):
        # 1. CPU Metrics
        cpu_pct = psutil.cpu_percent(interval=None)
        self.history_cpu.append(cpu_pct)
        if len(self.history_cpu) > 60:
            self.history_cpu.pop(0)

        cpu_freq = psutil.cpu_freq()
        ghz = (cpu_freq.current / 1000.0) if cpu_freq else 3.30
        self.tabs["CPU"].update_info(f"{cpu_pct:.0f}%  {ghz:.2f}GHz", cpu_pct)

        # 2. Memory Metrics
        mem = psutil.virtual_memory()
        mem_pct = mem.percent
        self.history_mem.append(mem_pct)
        if len(self.history_mem) > 60:
            self.history_mem.pop(0)

        used_gb = mem.used / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        self.tabs["MEMORY"].update_info(f"{used_gb:.1f}/{total_gb:.1f} GB", mem_pct)

        # 3. Disk Metrics
        disk = psutil.disk_usage("/")
        disk_pct = disk.percent
        self.history_disk.append(disk_pct)
        if len(self.history_disk) > 60:
            self.history_disk.pop(0)

        disk_used = disk.used / (1024 ** 3)
        disk_total = disk.total / (1024 ** 3)
        self.tabs["DISK"].update_info(f"{disk_pct:.0f}%  ({disk_used:.0f}GB)", disk_pct)

        # 4. GPU Metrics (if available)
        gpu_info = self.query_gpu() if self.has_gpu else None
        if gpu_info and "GPU" in self.tabs:
            gpu_pct = (gpu_info["mem_used"] / max(gpu_info["mem_total"], 1.0)) * 100.0
            self.history_gpu.append(gpu_pct)
            if len(self.history_gpu) > 60:
                self.history_gpu.pop(0)
            self.tabs["GPU"].update_info(f"{gpu_info['temp']}°C  ({gpu_pct:.0f}%)", gpu_pct)

        # ---------------- Update Active View ----------------
        if self.current_tab == "CPU":
            self.metric_big.setText(f"{cpu_pct:.0f} %")
            self.chart.set_data(self.history_cpu, "%")

            pids_count = len(psutil.pids())
            boot = psutil.boot_time()
            up_sec = int(time.time() - boot)
            h = up_sec // 3600
            m = (up_sec % 3600) // 60
            s = up_sec % 60
            uptime_str = f"{h}:{m:02d}:{s:02d}"

            self.cell_labels[0].set_value(f"{cpu_pct:.1f} %", "#FFB800")
            self.cell_labels[1].set_value(f"{ghz:.2f} GHz", "#FFFFFF")
            self.cell_labels[2].set_value(f"{pids_count}", "#FFFFFF")
            self.cell_labels[3].set_value(uptime_str, "#FFB800")
            self.cell_labels[4].set_value(str(psutil.cpu_count(logical=False) or 4), "#FFFFFF")
            self.cell_labels[5].set_value(str(psutil.cpu_count(logical=True) or 8), "#FFFFFF")

        elif self.current_tab == "MEMORY":
            avail_gb = mem.available / (1024 ** 3)
            cached_gb = getattr(mem, "cached", 0) / (1024 ** 3)

            self.metric_big.setText(f"{used_gb:.1f} GB")
            self.chart.set_data(self.history_mem, "%")

            self.cell_labels[0].set_value(f"{used_gb:.2f} GB", "#FFB800")
            self.cell_labels[1].set_value(f"{avail_gb:.2f} GB", "#FFFFFF")
            self.cell_labels[2].set_value(f"{used_gb:.1f} / {total_gb:.1f} GB", "#FFFFFF")
            self.cell_labels[3].set_value(f"{cached_gb:.2f} GB", "#FFFFFF")
            self.cell_labels[4].set_value(f"{total_gb:.2f} GB", "#FFB800")
            self.cell_labels[5].set_value(f"{mem_pct:.1f} %", "#FFB800")

        elif self.current_tab == "DISK":
            free_gb = disk.free / (1024 ** 3)

            self.metric_big.setText(f"{disk_pct:.0f} %")
            self.chart.set_data(self.history_disk, "%")

            self.cell_labels[0].set_value(f"{disk_used:.1f} GB", "#FFB800")
            self.cell_labels[1].set_value(f"{free_gb:.1f} GB", "#FFFFFF")
            self.cell_labels[2].set_value(f"{disk_total:.1f} GB", "#FFFFFF")
            self.cell_labels[3].set_value("/", "#FFFFFF")
            self.cell_labels[4].set_value("ext4", "#FFFFFF")
            self.cell_labels[5].set_value(f"{disk_pct:.1f} %", "#FFB800")

        elif self.current_tab == "GPU" and gpu_info:
            v_used = gpu_info["mem_used"]
            v_total = gpu_info["mem_total"]
            v_free = v_total - v_used
            v_pct = (v_used / max(v_total, 1.0)) * 100.0

            self.metric_big.setText(f"{v_pct:.0f} %")
            self.chart.set_data(self.history_gpu, "%")

            self.cell_labels[0].set_value(f"{v_used:.0f} MB", "#FFB800")
            self.cell_labels[1].set_value(f"{v_free:.0f} MB", "#FFFFFF")
            self.cell_labels[2].set_value(f"{v_total:.0f} MB", "#FFFFFF")
            self.cell_labels[3].set_value(f"{gpu_info['temp']} °C", "#FFB800")
            self.cell_labels[4].set_value(f"{gpu_info['fan']} %", "#FFFFFF")
            self.cell_labels[5].set_value(gpu_info["driver"], "#FFFFFF")

    def query_gpu(self):
        try:
            cmd = ["nvidia-smi", "--query-gpu=memory.used,memory.total,temperature.gpu,fan.speed,driver_version", "--format=csv,noheader,nounits"]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=0.4).decode().strip()
            parts = [p.strip() for p in out.split(",")]
            return {
                "mem_used": float(parts[0]),
                "mem_total": float(parts[1]),
                "temp": parts[2],
                "fan": parts[3] if parts[3] != "[N/A]" else "20",
                "driver": parts[4],
            }
        except Exception:
            return None

    # ---------------- Window Stacking & Layer Toggle ----------------
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
            env = dict(os.environ)
            if "DISPLAY" not in env or not env["DISPLAY"]:
                env["DISPLAY"] = ":0"
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
            env = dict(os.environ)
            if "DISPLAY" not in env or not env["DISPLAY"]:
                env["DISPLAY"] = ":0"
            subprocess.run(["xdotool", "windowraise", wid], env=env, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        self.save_position()

    def toggle_pin(self):
        if getattr(self, "is_lowered", False):
            self.raise_to_top()
        else:
            self.lower_to_desktop()

    def setup_signals(self):
        try:
            signal.signal(signal.SIGUSR1, lambda sig, frame: self.toggle_pin())
        except Exception:
            pass

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
                env = dict(os.environ)
                if "DISPLAY" not in env or not env["DISPLAY"]:
                    env["DISPLAY"] = ":0"
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
                    self.move(data.get("x", 1350), data.get("y", 100))
                    self.is_lowered = data.get("is_lowered", False)
                    return
            except Exception:
                pass
        # Default top-right placement on 1920x1080 display
        self.move(1350, 100)
        self.is_lowered = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = PerfWidget()
    widget.show()
    sys.exit(app.exec_())
