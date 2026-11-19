# 🎯 Wu-Tang Clan Rice — Roadmap & Goal List

Custom Arch Linux / i3wm ricing project following the **Wu-Tang Clan (Pitch Black & Gold #FFB800)** aesthetic.

---

## 📌 Active Backlog & Goals

### 🔋 1. Laptop Battery Indicator & Monitoring — HIGH PRIORITY
- [ ] **Universal Polybar Module**:
  - Automatic detection of battery identifiers (`BAT0`, `BAT1`, `BATT`) and AC power adapters via `/sys/class/power_supply/`.
  - TUI-styled status format: `[BAT 85%⚡]` while charging, `[BAT 85%]` on discharge.
  - Accent coloring: Wu-Tang Gold (`#FFB800`) and warning Red (`#E53935`) when below 20%.
- [ ] **Performance Widget Integration (`perf_widget`)**:
  - Add a dedicated battery gauge bar alongside CPU, RAM, Disk, and GPU.
  - Display remaining runtime / charging estimation and AC connection status.
- [ ] **Critical Battery Notifications (Dunst Daemon)**:
  - Lightweight background alert script firing desktop alerts at 15% (Low Battery) and 5% (Critical Battery).

---

### ⚙️ 2. Laptop & Mobile Enhancements
- [ ] **Touchpad Support & Optimization (Libinput)**:
  - Enable tap-to-click (`Tapping = on`).
  - Enable two-finger natural scrolling (`Natural Scrolling`).
  - Palm rejection / disable-while-typing (DWT).
  - Ready-to-use Xorg drop-in config `30-touchpad.conf` (for `/etc/X11/xorg.conf.d/`) or dynamic auto-configuration via `xinput` in `autostart.sh` (non-root).
  - Optional: 3-finger swipe gestures for rapid i3 workspace switching (`libinput-gestures`).
- [ ] **Screen Brightness Controls**:
  - Keybindings for `XF86MonBrightnessUp` / `XF86MonBrightnessDown` via `brightnessctl`.
  - Polybar brightness module with percentage display (`[BRI 70%]`).
- [ ] **Network & Bluetooth Menus**:
  - Interactive Wi-Fi network selector and Bluetooth pairing menu in Wu-Tang Rofi style.

---

### 📦 3. Installer & Customization
- [ ] **SDDM Theme Installer Integration**:
  - Add SDDM theme (`sddm-theme-wutang`) setup as an optional checkbox in `install.py`.
- [ ] **Display Profiles (Autorandr)**:
  - Automatically detect and apply capture card mirroring profiles without manual Rofi invocation.

---

## ✅ Completed Tasks (Changelog)

- [x] **TUI Installer (`install.py`)**:
  - Mathematically aligned box-drawing UI, Wu-Tang banner, and smooth live progress bars for pacman.
- [x] **Quick Updater (`update-cream`)**:
  - Global alias and script to fetch latest commits from GitHub, refresh symlinks, set permissions, and restart i3.
- [x] **Capture Card Mirroring (`display_mirror.sh`)**:
  - Interactive Rofi menu toggled via `Alt + F7` with dedicated 1080p@60Hz profiles for capture cards.
- [x] **Discord (Vesktop) Theme**:
  - Retro pixel arcade font `Silkscreen` (matching WU-TANG label on Polybar) with fallback to `Terminess Nerd Font`.
- [x] **SDDM Theme (Shaolin Style)**:
  - Standalone Qt6 QML display manager theme in signature Wu-Tang gold styling.
- [x] **Desktop Widgets**:
  - Music widget with synchronized lyrics (LRCLIB via MPRIS) and PyQt5 system performance monitor.
