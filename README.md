# 👐 Wu-Tang Clan Rice & Dotfiles

> **"Wu-Tang Clan Ain't Nutthin ta Fuck Wit"**
>
> Custom Arch Linux / i3wm Rice in Wu-Tang Clan TUI Aesthetic: Pitch Black (`#0C0C0C`), Gold (`#FFB800`), Sharp pixel borders (`border-radius: 0px`), and high contrast.

---

## 📁 Repository Structure

```
~/.dotfiles/
├── .config/
│   ├── alacritty/      # Alacritty terminal emulator (Gold & Onyx palette)
│   ├── dunst/          # Notification daemon (Papirus-Dark, Terminess Nerd Font, Gold frames)
│   ├── fastfetch/      # Dynamic lyrics fetcher + Wu-Tang logo banner
│   ├── fish/           # Fish shell 2-line prompt with Git integration & Gold highlighting
│   ├── gtk-3.0/        # GTK3 Wu-Tang theme & Thunar custom CSS
│   ├── gtk-4.0/        # GTK4 Breeze-Dark configuration
│   ├── i3/             # i3 window manager config, window rules & autostart
│   ├── nvim/           # Neovim (LazyVim) with custom Wu-Tang colorscheme, Lualine & Dashboard
│   ├── perf_widget/    # Hardware monitor widget (CPU, RAM, Disk, GPU real-time graphs)
│   ├── picom/          # Picom GLX compositor (shadows, vsync, sharp corners)
│   ├── polybar/        # Top status bar with Terminess Nerd Font & Silkscreen
│   ├── rofi/           # Application launcher styled with Silkscreen & Gold theme
│   ├── sone_widget/    # Desktop music player widget with synced lyrics from SONE
│   └── vesktop/        # Discord (Vesktop) Wu-Tang TUI custom theme & QuickCSS
├── firefox/
│   └── chrome/         # Firefox about:newtab Wu-Tang dashboard & userChrome.css
├── wallpapers/         # AMOLED & Dark Wu-Tang Clan wallpapers (1080p / 4K)
├── .fehbg              # Wallpaper startup script (feh --bg-fill)
├── .gtkrc-2.0          # GTK2 dark settings
└── install.sh          # One-click symlink installer
```

---

## ⚡ Keybindings

| Shortcut | Action |
|---|---|
| `Super + Return` | Launch Alacritty terminal |
| `Super + R` | Open Rofi launcher |
| `Super + E` | Open Thunar file manager |
| `Super + B` | Open Firefox browser |
| `Super + D` | Open Discord (Vesktop) |
| `Super + M` | Toggle Desktop Music Widget (Sone) |
| `Super + P` | Toggle Performance Monitor Widget |
| `Print` | Flameshot screenshot tool |
| `Super + Shift + R` | Restart i3 inplace |
| `Super + Q` | Close focused window |

---

## 🚀 Installation & Sync

To re-link all configurations on a new install:

```bash
cd ~/.dotfiles
./install.sh
```
