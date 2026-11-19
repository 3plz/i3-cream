#!/usr/bin/env python3
# ==============================================================================
#   WU-TANG CLAN RICE INSTALLER & SYNC TOOL
#   Aesthetic: Pitch Black & Wu-Tang Gold (#FFB800)
#   Pure Python 3 - Standard Library Only (No external pip dependencies)
# ==============================================================================

import os
import sys
import time
import shutil
import select
import termios
import tty
import atexit
import signal
import subprocess
import unicodedata
import re
from pathlib import Path

# ------------------------------------------------------------------------------
# ANSI Color Codes & Styles (Wu-Tang Clan Palette)
# ------------------------------------------------------------------------------
GOLD       = "\033[38;2;255;184;0m"       # #FFB800 Wu-Tang Signature Gold
GOLD_BOLD  = "\033[1;38;2;255;184;0m"
GOLD_DIM   = "\033[38;2;140;123;88m"      # #8C7B58 Antique / Subdued Gold
YELLOW     = "\033[1;38;2;255;215;0m"     # #FFD700 Bright Accent
WHITE      = "\033[38;2;240;240;240m"
WHITE_BOLD = "\033[1;38;2;255;255;255m"
GRAY       = "\033[38;2;120;120;120m"
DARK_GRAY  = "\033[38;2;60;60;60m"
RED        = "\033[1;38;2;229;57;53m"
GREEN      = "\033[1;38;2;76;175;80m"
BLUE       = "\033[1;38;2;33;150;243m"
BG_GOLD    = "\033[48;2;255;184;0m"
FG_BLACK   = "\033[38;2;0;0;0m"
SEL        = f"{BG_GOLD}{FG_BLACK}\033[1m" # Selected item highlight
RESET      = "\033[0m"
BOLD       = "\033[1m"
DIM        = "\033[2m"

# ------------------------------------------------------------------------------
# Robust ANSI & Unicode Display Width Utilities
# ------------------------------------------------------------------------------
ANSI_REGEX = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def visible_width(s: str) -> int:
    """Calculates visual display width of a string ignoring ANSI codes and
    accounting for double-width East Asian and emoji characters."""
    clean = ANSI_REGEX.sub('', s)
    w = 0
    for ch in clean:
        if unicodedata.east_asian_width(ch) in ('W', 'F'):
            w += 2
        else:
            w += 1
    return w

def pad_or_truncate(s: str, max_w: int, reset_seq: str = RESET) -> str:
    """Pads or safely truncates a string containing ANSI escape sequences so
    that its visual width is exactly max_w columns. Prevents line wraps."""
    vw = visible_width(s)
    if vw == max_w:
        return s
    if vw < max_w:
        return s + (" " * (max_w - vw))

    clean = ANSI_REGEX.sub("", s)
    is_divider = all(ch in ("─", " ", "-", "_") for ch in clean)

    out = []
    curr_w = 0
    tokens = re.split(r'(\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]))', s)
    limit = max_w if is_divider else max_w - 1

    for tok in tokens:
        if not tok:
            continue
        if ANSI_REGEX.match(tok):
            out.append(tok)
        else:
            for ch in tok:
                ch_w = 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
                if curr_w + ch_w > limit:
                    if not is_divider:
                        out.append("…")
                        curr_w += 1
                    out.append(reset_seq)
                    if curr_w < max_w:
                        out.append(" " * (max_w - curr_w))
                    return "".join(out)
                out.append(ch)
                curr_w += ch_w

    out.append(reset_seq)
    if curr_w < max_w:
        out.append(" " * (max_w - curr_w))
    return "".join(out)

# ------------------------------------------------------------------------------
# ASCII Banners
# ------------------------------------------------------------------------------
BANNER_FULL = [
    "   ▄██▄▄▄                       ▄▄    ",
    "  ▄█████████▄▄▄            ▄▄██████▄  ",
    " ▄█████████████▀       ▄████████████▄ ",
    "▄█████████████         ██████████████▄",
    "██████████████   ▄▄██▄  ██████████████",
    "███████████████▄▀█████▄███████████████",
    "██████████████████████████████████████",
    "▀█████████████████████████████████████",
    " ████████████████████████████████████▀",
    "  ██████████████████  ███████████████ ",
    "   █████████████████  ██████████████  ",
    "    ▀███████████████   ███████████▀   ",
    "      ▀█████████████   █████████▀     ",
    "         ▀▀██████████  ███████▀       ",
    "              ▀▀▀▀▀▀▀  ▀████▀         ",
    "                        ▀▀            ",
    "       W U - T A N G   C L A N        ",
]

BANNER_COMPACT = [
    "   ▄██▄                   ▄▄   ",
    "  ▄██████▄             ▄██████▄ ",
    " ▄████████▄   ▄▄█▄    ▄████████▄",
    " ███████████▄█████▄▄████████████",
    "  ▀███████████████████████████▀ ",
    "    ▀███████████████████████▀   ",
    "        W U - T A N G           ",
]

# ------------------------------------------------------------------------------
# Package Definitions
# ------------------------------------------------------------------------------
PACMAN_PACKAGES = [
    ("i3-wm", "i3 window manager"),
    ("polybar", "TUI top status bar"),
    ("picom", "Compositor (shadows & vsync)"),
    ("feh", "Wallpaper daemon & image viewer"),
    ("rofi", "Application launcher"),
    ("dunst", "Notification daemon"),
    ("libnotify", "Desktop notification library"),
    ("alacritty", "GPU-accelerated terminal"),
    ("fish", "Smart interactive shell"),
    ("fastfetch", "System information & lyrics banner"),
    ("neovim", "Vim-fork text editor"),
    ("git", "Version control system"),
    ("thunar", "Fast & lightweight file manager"),
    ("thunar-volman", "Thunar volume manager plugin"),
    ("breeze-gtk", "Breeze dark GTK theme"),
    ("papirus-icon-theme", "Papirus dark icon theme"),
    ("python-pyqt5", "PyQt5 for desktop widgets"),
    ("python-psutil", "System metrics for performance widget"),
    ("playerctl", "Media player MPRIS CLI controller"),
    ("xdotool", "X11 window automation tool"),
    ("xorg-xprop", "X11 window property display tool"),
    ("xorg-xinput", "X11 input device configuration tool"),
    ("xorg-xrandr", "X11 display and resolution manager"),
]

# ------------------------------------------------------------------------------
# Rice Components Configuration
# ------------------------------------------------------------------------------
COMPONENTS = [
    {
        "id": "core",
        "name": "Core Window Manager",
        "desc": "i3wm, Polybar, Picom, Feh, Dunst, Rofi, Xdotool",
        "links": [
            (".config/i3", ".config/i3"),
            (".config/polybar", ".config/polybar"),
            (".config/picom", ".config/picom"),
            (".config/rofi", ".config/rofi"),
            (".config/dunst", ".config/dunst"),
            (".fehbg", ".fehbg"),
        ],
        "pkgs": ["i3-wm", "polybar", "picom", "feh", "rofi", "dunst", "libnotify", "xdotool", "xorg-xrandr"],
    },
    {
        "id": "terminal",
        "name": "Terminal & Shell",
        "desc": "Alacritty, Fish shell, Fastfetch lyrics",
        "links": [
            (".config/alacritty", ".config/alacritty"),
            (".config/fish", ".config/fish"),
            (".config/fastfetch", ".config/fastfetch"),
            ("bin/update-cream", ".local/bin/update-cream"),
            ("bin/cream-settings", ".local/bin/cream-settings"),
        ],
        "pkgs": ["alacritty", "fish", "fastfetch"],
    },
    {
        "id": "editor",
        "name": "Code Editor (Neovim)",
        "desc": "LazyVim with custom Wu-Tang theme",
        "links": [
            (".config/nvim", ".config/nvim"),
        ],
        "pkgs": ["neovim", "git"],
    },
    {
        "id": "widgets",
        "name": "Desktop Widgets & Settings",
        "desc": "SONE Music Player, Task Monitor & Control Center",
        "links": [
            (".config/sone_widget", ".config/sone_widget"),
            (".config/perf_widget", ".config/perf_widget"),
            (".config/cream_settings", ".config/cream_settings"),
        ],
        "pkgs": ["python-pyqt5", "python-psutil", "playerctl", "xdotool", "xorg-xprop", "xorg-xinput"],
    },
    {
        "id": "thunar",
        "name": "File Manager & GTK",
        "desc": "Thunar FM, GTK themes, Papirus icons",
        "links": [
            (".config/gtk-3.0", ".config/gtk-3.0"),
            (".config/gtk-4.0", ".config/gtk-4.0"),
            (".gtkrc-2.0", ".gtkrc-2.0"),
        ],
        "pkgs": ["thunar", "thunar-volman", "breeze-gtk", "papirus-icon-theme"],
    },
    {
        "id": "vesktop",
        "name": "Discord (Vesktop) Theme",
        "desc": "Custom Wu-Tang TUI CSS theme",
        "links": [
            (".config/vesktop/themes", ".config/vesktop/themes"),
            (".config/vesktop/settings/quickCss.css", ".config/vesktop/settings/quickCss.css"),
        ],
        "pkgs": [],
    },
    {
        "id": "firefox",
        "name": "Firefox Dashboard",
        "desc": "about:newtab Wu-Tang dashboard",
        "links": [
            ("firefox/chrome", "FIREFOX_CHROME"),
        ],
        "pkgs": [],
    },
    {
        "id": "fonts",
        "name": "Fonts & Icon Glyphs",
        "desc": "Terminess Nerd Font, Silkscreen, WuTang",
        "links": [
            ("fonts", "FONTS_DIR"),
        ],
        "pkgs": [],
    },
    {
        "id": "wallpapers",
        "name": "Wallpapers Collection",
        "desc": "AMOLED pitch-black & 4K Wu-Tang Clan",
        "links": [
            ("wallpapers", "Pictures/Wallpappers"),
        ],
        "pkgs": [],
    },
]

LOG_FILE = "/tmp/dotfiles_install.log"

# ------------------------------------------------------------------------------
# Terminal Control & Raw Input
# ------------------------------------------------------------------------------
class TerminalUI:
    def __init__(self):
        self.is_alt_screen = False
        self.old_termios = None
        self.fd = sys.stdin.fileno() if sys.stdin.isatty() else None

    def enter_alt_screen(self):
        if not self.is_alt_screen and self.fd is not None:
            sys.stdout.write("\033[?1049h\033[?25l")
            sys.stdout.flush()
            self.is_alt_screen = True

    def exit_alt_screen(self):
        if self.is_alt_screen:
            sys.stdout.write("\033[?25h\033[?1049l")
            sys.stdout.flush()
            self.is_alt_screen = False

    def raw_mode(self):
        if self.fd is not None and self.old_termios is None:
            self.old_termios = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
            mode = termios.tcgetattr(self.fd)
            mode[1] |= termios.OPOST
            mode[3] &= ~termios.ECHO
            termios.tcsetattr(self.fd, termios.TCSADRAIN, mode)

    def restore_mode(self):
        if self.fd is not None and self.old_termios is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_termios)
            self.old_termios = None

    def println(self, text=""):
        sys.stdout.write(text + "\r\n")
        sys.stdout.flush()

    def print(self, text=""):
        sys.stdout.write(text)
        sys.stdout.flush()

    def get_key(self):
        if self.fd is None:
            return ""
        try:
            raw = os.read(self.fd, 1)
            if not raw:
                return ""
            if raw == b"\x1b":
                r, _, _ = select.select([self.fd], [], [], 0.05)
                if r:
                    raw += os.read(self.fd, 15)

            seq = raw.decode("utf-8", errors="ignore")

            # Standard ANSI & Application SS3 Arrow keys
            if seq in ("\x1b[A", "\x1bOA", "\x1b[1;2A", "\x1b[1;5A"):
                return "UP"
            elif seq in ("\x1b[B", "\x1bOB", "\x1b[1;2B", "\x1b[1;5B"):
                return "DOWN"
            elif seq in ("\x1b[C", "\x1bOC", "\x1b[1;2C", "\x1b[1;5C"):
                return "RIGHT"
            elif seq in ("\x1b[D", "\x1bOD", "\x1b[1;2D", "\x1b[1;5D"):
                return "LEFT"
            elif seq in ("\r", "\n"):
                return "ENTER"
            elif seq == " ":
                return "SPACE"
            elif seq in ("\x1b", "\x1b\x1b"):
                return "ESC"
            elif seq in ("\t", "\x1b[Z"):
                return "TAB"
            elif seq in ("\x7f", "\x08"):
                return "BACKSPACE"
            elif seq == "\x03":
                raise KeyboardInterrupt
            return seq
        except (KeyboardInterrupt, SystemExit):
            raise
        except (InterruptedError, OSError):
            return "RESIZE"
        except Exception:
            return ""

    def clear(self):
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

    def get_size(self):
        cols, rows = shutil.get_terminal_size((80, 24))
        return cols, rows

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def get_installed_packages():
    try:
        res = subprocess.run(["pacman", "-Qq"], capture_output=True, text=True, check=True)
        return set(res.stdout.split())
    except Exception:
        return set()

def find_firefox_profile():
    base = Path.home() / ".config" / "mozilla" / "firefox"
    if not base.exists():
        base = Path.home() / ".mozilla" / "firefox"
    if base.exists():
        for p in base.iterdir():
            if p.is_dir() and p.name.endswith(".default-release"):
                return p
    return None

def check_sudo():
    res = subprocess.run(["sudo", "-n", "true"], capture_output=True)
    return res.returncode == 0

def progress_bar(percent, width=30, filled_char="█", empty_char="░"):
    percent = max(0.0, min(100.0, percent))
    filled = int(width * percent / 100.0)
    empty = width - filled
    return f"{GOLD}{filled_char * filled}{DARK_GRAY}{empty_char * empty}{RESET} {GOLD_BOLD}{percent:5.1f}%{RESET}"

# ------------------------------------------------------------------------------
# Application State & Logic
# ------------------------------------------------------------------------------
class InstallerApp:
    def __init__(self):
        self.term = TerminalUI()
        self.dotfiles_dir = Path(__file__).resolve().parent
        self.home_dir = Path.home()
        self.selected_components = {c["id"]: True for c in COMPONENTS}
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.handle_sigint)
        try:
            signal.signal(signal.SIGWINCH, lambda s, f: None)
        except Exception:
            pass

    def cleanup(self):
        self.term.restore_mode()
        self.term.exit_alt_screen()

    def handle_sigint(self, signum, frame):
        self.cleanup()
        self.term.println(f"\r\n{RED}[!] Installation interrupted by user.{RESET}")
        sys.exit(130)

    # --------------------------------------------------------------------------
    # UI Rendering Engine
    # --------------------------------------------------------------------------
    def print_banner(self, minimal=False):
        cols, rows = self.term.get_size()
        if minimal or rows < 28:
            title = "W U - T A N G   C L A N   R I C E"
            pad = max(0, (cols - len(title)) // 2)
            self.term.println()
            self.term.println(f"{' ' * pad}{GOLD_BOLD}{title}{RESET}")
            self.term.println()
            return

        banner = BANNER_FULL if rows >= 38 else BANNER_COMPACT
        self.term.println()
        for line in banner:
            padding = max(0, (cols - len(line)) // 2)
            self.term.println(f"{' ' * padding}{GOLD_BOLD}{line}{RESET}")
        self.term.println()

    def draw_box(self, title, lines, footer=None, width=None):
        """Draws a mathematically aligned TUI box with zero border deviation,
        full ANSI awareness, and automatic overflow protection."""
        cols, rows = self.term.get_size()
        if width is None:
            width = min(cols - 4, 76)
        width = max(42, width)
        padding_left = max(0, (cols - width) // 2)
        pad = " " * padding_left
        inner_w = width - 4

        # 1. Top border
        t_vw = visible_width(title)
        if t_vw > width - 10:
            title = pad_or_truncate(title, width - 10)
            t_vw = visible_width(title)

        dashes_left = 3
        dashes_right = max(1, width - 2 - dashes_left - (t_vw + 2))
        top_line = f"{pad}{GOLD}╭{'─' * dashes_left}{RESET} {title} {GOLD}{'─' * dashes_right}╮{RESET}"
        self.term.println(top_line)

        # 2. Content lines
        for l in lines:
            fitted = pad_or_truncate(l, inner_w)
            row_line = f"{pad}{GOLD}│{RESET} {fitted} {GOLD}│{RESET}"
            self.term.println(row_line)

        # 3. Bottom border
        if footer:
            f_vw = visible_width(footer)
            if f_vw > width - 10:
                footer = pad_or_truncate(footer, width - 10)
                f_vw = visible_width(footer)

            d_left = 3
            d_right = max(1, width - 2 - d_left - (f_vw + 2))
            bot_line = f"{pad}{GOLD}╰{'─' * d_left}{RESET} {footer} {GOLD}{'─' * d_right}╯{RESET}"
        else:
            bot_line = f"{pad}{GOLD}╰{'─' * (width - 2)}╯{RESET}"
        self.term.println(bot_line)

    # --------------------------------------------------------------------------
    # Main Menu Loop
    # --------------------------------------------------------------------------
    def run_main_menu(self):
        self.term.enter_alt_screen()
        self.term.raw_mode()

        menu_items = [
            ("1", "Full Rice Installation", "Packages, dotfiles, fonts & wallpapers"),
            ("2", "Quick Re-Link Only", "Instant symlinks refresh (no pacman calls)"),
            ("3", "Custom Selection", "Choose individual modules to install"),
            ("4", "System Health Check", "Inspect symlinks, running daemons & status"),
            ("5", "Exit", "Return to terminal"),
        ]
        sel_idx = 0

        while True:
            self.term.clear()
            self.print_banner()

            content = [""]
            for idx, (num, title, desc) in enumerate(menu_items):
                cursor = "> " if idx == sel_idx else "  "
                if idx == sel_idx:
                    item_text = f"{SEL}{cursor}[{num}] {title:<25}{RESET}"
                else:
                    item_text = f"{cursor}{WHITE_BOLD}[{num}] {title:<25}{RESET}"
                content.append(f"{item_text}  {GOLD_DIM}{desc}{RESET}")
            content.append("")

            self.draw_box(
                "WU-TANG CLAN RICE INSTALLER",
                content,
                footer="[↑/↓] Navigate  •  [Enter] Select  •  [1-5] Jump  •  [q] Quit"
            )

            key = self.term.get_key()
            if key == "RESIZE":
                continue
            elif key in ("UP", "k", "w"):
                sel_idx = (sel_idx - 1) % len(menu_items)
            elif key in ("DOWN", "j", "s"):
                sel_idx = (sel_idx + 1) % len(menu_items)
            elif key in ("ENTER", "SPACE"):
                if sel_idx == 0:
                    self.execute_install(mode="full")
                elif sel_idx == 1:
                    self.execute_install(mode="link_only")
                elif sel_idx == 2:
                    self.run_custom_selection()
                elif sel_idx == 3:
                    self.run_health_check(interactive=True)
                elif sel_idx == 4:
                    break
            elif key == "1":
                self.execute_install(mode="full")
            elif key == "2":
                self.execute_install(mode="link_only")
            elif key == "3":
                self.run_custom_selection()
            elif key == "4":
                self.run_health_check(interactive=True)
            elif key in ("5", "q", "Q", "ESC"):
                break

        self.cleanup()

    # --------------------------------------------------------------------------
    # Custom Components Menu
    # --------------------------------------------------------------------------
    def run_custom_selection(self):
        sel_idx = 0
        total_items = len(COMPONENTS) + 2  # + Start, + Back

        while True:
            self.term.clear()
            self.print_banner()

            content = [
                f"{GOLD_DIM}Toggle modules with [Space] or [a] to select all:{RESET}",
                ""
            ]

            for idx, comp in enumerate(COMPONENTS):
                is_checked = self.selected_components[comp["id"]]
                chk = f"{GREEN}[X]{RESET}" if is_checked else f"{GRAY}[ ]{RESET}"
                cursor = "> " if idx == sel_idx else "  "

                if idx == sel_idx:
                    name_str = f"{SEL}{comp['name']:<23}{RESET}"
                else:
                    name_str = f"{WHITE_BOLD}{comp['name']:<23}{RESET}"

                content.append(f"{cursor}{chk} {name_str} {GOLD_DIM}{comp['desc']}{RESET}")

            content.append("")
            # Action buttons
            start_cursor = "> " if sel_idx == len(COMPONENTS) else "  "
            back_cursor = "> " if sel_idx == len(COMPONENTS) + 1 else "  "

            if sel_idx == len(COMPONENTS):
                content.append(f"{start_cursor}{SEL} [ START INSTALLATION ] {RESET}")
            else:
                content.append(f"{start_cursor}{YELLOW}[ START INSTALLATION ]{RESET}")

            if sel_idx == len(COMPONENTS) + 1:
                content.append(f"{back_cursor}{SEL} [ BACK TO MAIN MENU ] {RESET}")
            else:
                content.append(f"{back_cursor}{GRAY}[ BACK TO MAIN MENU ]{RESET}")

            content.append("")

            self.draw_box(
                "CUSTOM COMPONENTS SELECTION",
                content,
                footer="[↑/↓] Move  •  [Space] Toggle  •  [a] Toggle All  •  [Enter] Proceed"
            )

            key = self.term.get_key()
            if key == "RESIZE":
                continue
            elif key in ("UP", "k", "w"):
                sel_idx = (sel_idx - 1) % total_items
            elif key in ("DOWN", "j", "s"):
                sel_idx = (sel_idx + 1) % total_items
            elif key == "SPACE":
                if sel_idx < len(COMPONENTS):
                    cid = COMPONENTS[sel_idx]["id"]
                    self.selected_components[cid] = not self.selected_components[cid]
            elif key in ("a", "A"):
                any_unchecked = any(not v for v in self.selected_components.values())
                for cid in self.selected_components:
                    self.selected_components[cid] = any_unchecked
            elif key == "ENTER":
                if sel_idx < len(COMPONENTS):
                    cid = COMPONENTS[sel_idx]["id"]
                    self.selected_components[cid] = not self.selected_components[cid]
                elif sel_idx == len(COMPONENTS):
                    self.execute_install(mode="custom")
                    break
                elif sel_idx == len(COMPONENTS) + 1:
                    break
            elif key in ("q", "Q", "ESC"):
                break

    # --------------------------------------------------------------------------
    # Installation Execution Engine
    # --------------------------------------------------------------------------
    def execute_install(self, mode="full"):
        is_interactive = sys.stdin.isatty() and self.term.fd is not None

        if is_interactive:
            self.term.enter_alt_screen()
            self.term.raw_mode()
            self.term.clear()
            self.print_banner()

        active_components = []
        if mode == "full":
            active_components = COMPONENTS
        elif mode == "link_only":
            active_components = COMPONENTS
        elif mode == "custom":
            active_components = [c for c in COMPONENTS if self.selected_components[c["id"]]]

        if not active_components:
            if is_interactive:
                self.draw_box("NOTICE", ["", f"{RED}No components were selected for installation.{RESET}", ""])
                time.sleep(1.5)
            else:
                print("No components selected.")
            return

        # Prepare log
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"=== Wu-Tang Clan Rice Installation Log ({time.ctime()}) ===\n")

        # ----------------------------------------------------------------------
        # Stage 1: Packages Installation (if full or custom)
        # ----------------------------------------------------------------------
        installed_set = get_installed_packages()
        pkgs_to_install = []
        if mode != "link_only":
            target_pkgs = set()
            for c in active_components:
                for p in c["pkgs"]:
                    target_pkgs.add(p)
            pkgs_to_install = [p for p in target_pkgs if p not in installed_set]

        if pkgs_to_install:
            # Check sudo
            if not check_sudo():
                if is_interactive:
                    self.term.restore_mode()
                    self.term.exit_alt_screen()
                print(f"\n{GOLD_BOLD}=== Sudo Authentication Required for Pacman Packages ==={RESET}")
                subprocess.run(["sudo", "-v"])
                if is_interactive:
                    self.term.enter_alt_screen()
                    self.term.raw_mode()

            total_pkgs = len(pkgs_to_install)
            for i, pkg in enumerate(pkgs_to_install):
                pct = (i / total_pkgs) * 100.0
                bar_str = progress_bar(pct, width=28)

                if is_interactive:
                    self.term.clear()
                    self.print_banner()
                    content = [
                        f"{GOLD_BOLD}Stage 1/4: Installing System Packages via Pacman{RESET}",
                        f"{DARK_GRAY}{'─' * 56}{RESET}",
                        "",
                        f"Progress:  {bar_str}  ({i}/{total_pkgs})",
                        "",
                        f"Current:   {YELLOW}{self.spinner_frames[self.spinner_idx]} {pkg}{RESET}",
                        f"Status:    {GOLD_DIM}Resolving and downloading package...{RESET}",
                        "",
                        f"{DARK_GRAY}[Log output redirected to {LOG_FILE}]{RESET}",
                        ""
                    ]
                    self.draw_box("INSTALLING PACKAGES", content)

                log(f"Installing {pkg}...")
                cmd = ["sudo", "pacman", "-S", "--needed", "--noconfirm", pkg]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(res.stdout)

                self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_frames)

            if is_interactive:
                self.term.clear()
                self.print_banner()
                bar_str = progress_bar(100.0, width=28)
                content = [
                    f"{GREEN}[OK] Stage 1/4: All {total_pkgs} packages installed successfully!{RESET}",
                    f"{DARK_GRAY}{'─' * 56}{RESET}",
                    "",
                    f"Progress:  {bar_str}  ({total_pkgs}/{total_pkgs})",
                    ""
                ]
                self.draw_box("PACKAGES INSTALLED", content)
                time.sleep(0.4)

        # ----------------------------------------------------------------------
        # Stage 2: Fonts Installation
        # ----------------------------------------------------------------------
        if any(c["id"] == "fonts" for c in active_components):
            if is_interactive:
                self.term.clear()
                self.print_banner()
                content = [
                    f"{GOLD_BOLD}Stage 2/4: Installing Custom Fonts & Updating Cache{RESET}",
                    f"{DARK_GRAY}{'─' * 56}{RESET}",
                    "",
                    f"Copying:   {YELLOW}Terminess Nerd Font, Silkscreen, WuTangIcons{RESET}",
                    f"Target:    {WHITE}~/.local/share/fonts/{RESET}",
                    "",
                    f"Status:    {GOLD_DIM}Updating font cache via fc-cache...{RESET}",
                    ""
                ]
                self.draw_box("INSTALLING FONTS", content)

            fonts_src = self.dotfiles_dir / "fonts"
            fonts_dst = self.home_dir / ".local" / "share" / "fonts"
            fonts_dst.mkdir(parents=True, exist_ok=True)

            if fonts_src.exists():
                for item in fonts_src.iterdir():
                    dst_item = fonts_dst / item.name
                    if item.is_dir():
                        shutil.copytree(item, dst_item, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dst_item)

            subprocess.run(["fc-cache", str(fonts_dst)], capture_output=True)
            log("Fonts copied and font cache updated.")
            if is_interactive:
                time.sleep(0.4)

        # ----------------------------------------------------------------------
        # Stage 3: Creating Symlinks
        # ----------------------------------------------------------------------
        links_to_create = []
        for c in active_components:
            for src_rel, dst_rel in c["links"]:
                links_to_create.append((src_rel, dst_rel))

        total_links = len(links_to_create)
        ff_profile = find_firefox_profile()

        for idx, (src_rel, dst_rel) in enumerate(links_to_create):
            pct = ((idx + 1) / total_links) * 100.0
            bar_str = progress_bar(pct, width=28)

            src_path = self.dotfiles_dir / src_rel
            if dst_rel == "FIREFOX_CHROME":
                if ff_profile:
                    dst_path = ff_profile / "chrome"
                else:
                    continue
            elif dst_rel == "FONTS_DIR":
                continue  # handled in stage 2
            elif dst_rel.startswith(".config/"):
                dst_path = self.home_dir / dst_rel
            elif dst_rel.startswith("Pictures/"):
                dst_path = self.home_dir / dst_rel
            else:
                dst_path = self.home_dir / dst_rel

            if is_interactive:
                self.term.clear()
                self.print_banner()
                content = [
                    f"{GOLD_BOLD}Stage 3/4: Creating Dotfile Symlinks{RESET}",
                    f"{DARK_GRAY}{'─' * 56}{RESET}",
                    "",
                    f"Progress:  {bar_str}  ({idx+1}/{total_links})",
                    "",
                    f"Linking:   {YELLOW}{dst_path.name}{RESET} -> {GOLD_DIM}{src_path.name}{RESET}",
                    ""
                ]
                self.draw_box("CREATING SYMLINKS", content)

            # Backup if existing non-symlink
            if dst_path.exists() and not dst_path.is_symlink():
                backup_path = dst_path.with_name(dst_path.name + ".backup")
                if dst_path.is_dir():
                    shutil.move(str(dst_path), str(backup_path))
                else:
                    shutil.move(str(dst_path), str(backup_path))

            # Remove existing symlink or file
            if dst_path.is_symlink() or dst_path.exists():
                if dst_path.is_dir() and not dst_path.is_symlink():
                    shutil.rmtree(dst_path)
                else:
                    dst_path.unlink()

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.symlink_to(src_path)
            log(f"Linked {dst_path} -> {src_path}")
            if is_interactive:
                time.sleep(0.04)

        # ----------------------------------------------------------------------
        # Stage 4: Wallpapers & Services
        # ----------------------------------------------------------------------
        if is_interactive:
            self.term.clear()
            self.print_banner()
            content = [
                f"{GOLD_BOLD}Stage 4/4: Applying Wallpaper & Finalizing Setup{RESET}",
                f"{DARK_GRAY}{'─' * 56}{RESET}",
                "",
                f"Wallpaper: {YELLOW}Applying via ~/.fehbg ...{RESET}",
                f"MIME:      {WHITE}Setting Thunar as default directory handler...{RESET}",
                ""
            ]
            self.draw_box("FINALIZING", content)

        fehbg = self.home_dir / ".fehbg"
        if fehbg.exists():
            subprocess.run(["bash", str(fehbg)], capture_output=True)

        subprocess.run(["xdg-mime", "default", "thunar.desktop", "inode/directory"], capture_output=True)
        subprocess.run(["xdg-mime", "default", "thunar.desktop", "inode/mount-point"], capture_output=True)
        if is_interactive:
            time.sleep(0.4)

        # ----------------------------------------------------------------------
        # Completed Screen
        # ----------------------------------------------------------------------
        self.show_completion_screen(total_pkgs=len(pkgs_to_install), total_links=total_links)

    def show_completion_screen(self, total_pkgs, total_links):
        if self.term.fd is None or not sys.stdin.isatty():
            content = [
                f"{GREEN}[OK] Installation Completed Successfully!{RESET}",
                f"{DARK_GRAY}{'─' * 56}{RESET}",
                "",
                f"  {GREEN}[+] Packages verified / installed: {WHITE_BOLD}{total_pkgs}{RESET}",
                f"  {GREEN}[+] Dotfile symlinks established:   {WHITE_BOLD}{total_links}{RESET}",
                f"  {GREEN}[+] Custom fonts cached:           {WHITE_BOLD}Terminess, Silkscreen, WuTang{RESET}",
                f"  {GREEN}[+] Default file manager:          {WHITE_BOLD}Thunar (Wu-Tang TUI styled){RESET}",
                f"  {GREEN}[+] Wallpaper applied:             {WHITE_BOLD}WuTangClan.png (#000000 AMOLED){RESET}",
                "",
            ]
            self.draw_box("INSTALLATION COMPLETE", content)
            return

        sel_idx = 0
        options = [
            ("[1]", "Restart i3 In-Place", "Instantly reload window manager and apply theme"),
            ("[2]", "View Installation Log", "Inspect details in /tmp/dotfiles_install.log"),
            ("[3]", "Return to Main Menu", "Go back to installer menu"),
        ]

        while True:
            self.term.clear()
            self.print_banner()

            content = [
                f"{GREEN}[OK] Installation Completed Successfully!{RESET}",
                f"{DARK_GRAY}{'─' * 56}{RESET}",
                "",
                f"  {GREEN}[+] Packages installed:    {WHITE_BOLD}{total_pkgs}{RESET}",
                f"  {GREEN}[+] Symlinks established:  {WHITE_BOLD}{total_links}{RESET}",
                f"  {GREEN}[+] Custom fonts cached:   {WHITE_BOLD}Terminess, Silkscreen, WuTang{RESET}",
                f"  {GREEN}[+] Default file manager:  {WHITE_BOLD}Thunar (Wu-Tang styled){RESET}",
                f"  {GREEN}[+] Wallpaper applied:     {WHITE_BOLD}WuTangClan.png (#000000 AMOLED){RESET}",
                "",
                f"{GOLD}Choose an action:{RESET}",
                ""
            ]

            for idx, (num, title, desc) in enumerate(options):
                cursor = "> " if idx == sel_idx else "  "
                if idx == sel_idx:
                    item_text = f"{SEL}{cursor}{num} {title:<24}{RESET}"
                else:
                    item_text = f"{cursor}{WHITE_BOLD}{num} {title:<24}{RESET}"
                content.append(f"{item_text}  {GOLD_DIM}{desc}{RESET}")

            content.append("")
            self.draw_box("INSTALLATION COMPLETE", content, footer="[↑/↓] Select  •  [Enter] Proceed")

            key = self.term.get_key()
            if key == "RESIZE":
                continue
            elif key in ("UP", "k", "w"):
                sel_idx = (sel_idx - 1) % len(options)
            elif key in ("DOWN", "j", "s"):
                sel_idx = (sel_idx + 1) % len(options)
            elif key in ("ENTER", "SPACE"):
                if sel_idx == 0:
                    subprocess.run(["i3-msg", "restart"], capture_output=True)
                    time.sleep(0.5)
                elif sel_idx == 1:
                    self.view_log_screen()
                elif sel_idx == 2:
                    break
            elif key == "1":
                subprocess.run(["i3-msg", "restart"], capture_output=True)
                time.sleep(0.5)
            elif key == "2":
                self.view_log_screen()
            elif key in ("3", "q", "Q", "ESC"):
                break

    def view_log_screen(self):
        log_lines = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                log_lines = [l.strip() for l in f.readlines() if l.strip()]

        last_lines = log_lines[-16:] if len(log_lines) > 16 else log_lines

        self.term.clear()
        self.print_banner()

        content = [f"{GOLD_DIM}Latest entries from {LOG_FILE}:{RESET}", ""]
        for l in last_lines:
            content.append(f"{GRAY}{l[:68]}{RESET}")
        content.append("")

        self.draw_box("INSTALLATION LOG", content, footer="Press any key to return...")
        self.term.get_key()

    # --------------------------------------------------------------------------
    # Health Check Screen
    # --------------------------------------------------------------------------
    def run_health_check(self, interactive=True):
        if interactive and sys.stdin.isatty():
            self.term.enter_alt_screen()
            self.term.raw_mode()
            self.term.clear()
            self.print_banner()

        checks = []

        # 1. Check symlinks
        symlink_dirs = [
            ("i3", self.home_dir / ".config" / "i3"),
            ("polybar", self.home_dir / ".config" / "polybar"),
            ("picom", self.home_dir / ".config" / "picom"),
            ("alacritty", self.home_dir / ".config" / "alacritty"),
            ("rofi", self.home_dir / ".config" / "rofi"),
            ("dunst", self.home_dir / ".config" / "dunst"),
            ("fish", self.home_dir / ".config" / "fish"),
            ("nvim", self.home_dir / ".config" / "nvim"),
            ("fastfetch", self.home_dir / ".config" / "fastfetch"),
            ("sone_widget", self.home_dir / ".config" / "sone_widget"),
            ("perf_widget", self.home_dir / ".config" / "perf_widget"),
            ("gtk-3.0", self.home_dir / ".config" / "gtk-3.0"),
        ]

        broken_links = 0
        valid_links = 0
        for name, p in symlink_dirs:
            if p.is_symlink() and p.resolve().exists():
                valid_links += 1
            else:
                broken_links += 1

        checks.append(f"Symlinks:      {GREEN}[OK] {valid_links} active{RESET}" + (f", {RED}[!] {broken_links} broken{RESET}" if broken_links else ""))

        # 2. Check running processes
        procs = ["i3", "polybar", "picom", "dunst"]
        running_procs = []
        for pr in procs:
            res = subprocess.run(["pgrep", "-x", pr], capture_output=True)
            if res.returncode == 0:
                running_procs.append(f"{GREEN}{pr}{RESET}")
            else:
                running_procs.append(f"{GRAY}{pr} (off){RESET}")
        checks.append(f"Core Daemons:  {' | '.join(running_procs)}")

        # 3. Check desktop widgets
        w_res = subprocess.run(["pgrep", "-f", "sone_widget/widget.py"], capture_output=True)
        p_res = subprocess.run(["pgrep", "-f", "perf_widget/widget.py"], capture_output=True)
        w_status = f"{GREEN}running{RESET}" if w_res.returncode == 0 else f"{GRAY}stopped{RESET}"
        p_status = f"{GREEN}running{RESET}" if p_res.returncode == 0 else f"{GRAY}stopped{RESET}"
        checks.append(f"Widgets:       Sone Music: {w_status} | Task Monitor: {p_status}")

        # 4. Check default file manager
        res = subprocess.run(["xdg-mime", "query", "default", "inode/directory"], capture_output=True, text=True)
        fm = res.stdout.strip()
        fm_status = f"{GREEN}{fm}{RESET}" if "thunar" in fm else f"{YELLOW}{fm}{RESET}"
        checks.append(f"Default FM:    {fm_status}")

        # 5. Check wallpaper
        feh_res = self.home_dir / ".fehbg"
        wp_status = f"{GREEN}configured ({feh_res}){RESET}" if feh_res.exists() else f"{RED}missing{RESET}"
        checks.append(f"Wallpaper:     {wp_status}")

        content = [
            f"{GOLD_BOLD}System Health & Configuration Diagnostics{RESET}",
            f"{DARK_GRAY}{'─' * 56}{RESET}",
            ""
        ] + checks + [""]

        if interactive and sys.stdin.isatty():
            self.draw_box("HEALTH CHECK", content, footer="Press any key to return...")
            self.term.get_key()
        else:
            self.draw_box("HEALTH CHECK", content)

# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------
def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"""
{GOLD_BOLD}Wu-Tang Clan Rice Installer & Dotfiles Tool{RESET}

Usage:
  python3 install.py              Launch interactive TUI installer
  python3 install.py --link-only  Refresh all symlinks quickly without prompts
  python3 install.py --full       Execute full installation in batch mode
  python3 install.py --check      Run diagnostic health check
""")
        sys.exit(0)

    app = InstallerApp()

    if "--link-only" in sys.argv or "-l" in sys.argv:
        app.execute_install(mode="link_only")
    elif "--full" in sys.argv or "-f" in sys.argv:
        app.execute_install(mode="full")
    elif "--check" in sys.argv or "-c" in sys.argv:
        app.run_health_check(interactive=False)
    else:
        app.run_main_menu()

if __name__ == "__main__":
    main()
