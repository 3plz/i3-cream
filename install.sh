#!/usr/bin/env bash
# ============================================================
#  Wu-Tang Clan Rice - Dotfiles Symlink Installer
# ============================================================
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing dotfiles from: $DOTFILES_DIR"

# 1. Config directories
CONFIG_DIRS=(
    "alacritty"
    "dunst"
    "fastfetch"
    "fish"
    "gtk-3.0"
    "gtk-4.0"
    "i3"
    "nvim"
    "perf_widget"
    "picom"
    "polybar"
    "rofi"
    "sone_widget"
)

mkdir -p "$HOME/.config"
for dir in "${CONFIG_DIRS[@]}"; do
    src="$DOTFILES_DIR/.config/$dir"
    target="$HOME/.config/$dir"
    if [ -d "$src" ]; then
        if [ -e "$target" ] && [ ! -L "$target" ]; then
            echo "Backing up existing $target -> ${target}.backup"
            mv "$target" "${target}.backup"
        fi
        ln -sfn "$src" "$target"
        echo "Linked: ~/.config/$dir -> $src"
    fi
done

# 2. Vesktop
mkdir -p "$HOME/.config/vesktop/settings"
if [ -d "$DOTFILES_DIR/.config/vesktop/themes" ]; then
    ln -sfn "$DOTFILES_DIR/.config/vesktop/themes" "$HOME/.config/vesktop/themes"
    echo "Linked: Vesktop themes"
fi
if [ -f "$DOTFILES_DIR/.config/vesktop/settings/quickCss.css" ]; then
    ln -sfn "$DOTFILES_DIR/.config/vesktop/settings/quickCss.css" "$HOME/.config/vesktop/settings/quickCss.css"
    echo "Linked: Vesktop quickCss.css"
fi

# 3. Home files
for file in ".fehbg" ".gtkrc-2.0"; do
    if [ -f "$DOTFILES_DIR/$file" ]; then
        ln -sfn "$DOTFILES_DIR/$file" "$HOME/$file"
        echo "Linked: ~/$file"
    fi
done

# 4. Firefox chrome
FF_PROFILE_DIR=$(find "$HOME/.config/mozilla/firefox" -maxdepth 1 -name "*.default-release" 2>/dev/null | head -n 1)
if [ -n "$FF_PROFILE_DIR" ] && [ -d "$DOTFILES_DIR/firefox/chrome" ]; then
    ln -sfn "$DOTFILES_DIR/firefox/chrome" "$FF_PROFILE_DIR/chrome"
    echo "Linked: Firefox chrome -> $FF_PROFILE_DIR/chrome"
fi

# 5. Wallpapers
mkdir -p "$HOME/Pictures"
if [ -d "$DOTFILES_DIR/wallpapers" ]; then
    ln -sfn "$DOTFILES_DIR/wallpapers" "$HOME/Pictures/Wallpappers"
    echo "Linked: ~/Pictures/Wallpappers -> $DOTFILES_DIR/wallpapers"
fi

echo "All symlinks successfully created!"
