#!/usr/bin/env bash
# ==============================================================================
#   Wu-Tang Clan i3wm Display Mirror & Output Switcher
#   Opens interactive Rofi menu to mirror primary screen to capture cards
#   or external monitors via xrandr.
# ==============================================================================

# Ensure DISPLAY is set
export DISPLAY="${DISPLAY:-:0}"

# 1. Detect primary / internal display
primary=$(xrandr --query 2>/dev/null | grep -E " connected (primary )?[0-9]+x[0-9]+" | awk '{print $1}' | head -n1)
if [ -z "$primary" ]; then
    primary=$(xrandr --query 2>/dev/null | grep -E "^eDP" | grep " connected" | awk '{print $1}' | head -n1)
fi
if [ -z "$primary" ]; then
    primary=$(xrandr --query 2>/dev/null | grep " connected" | awk '{print $1}' | head -n1)
fi

# Fallback if xrandr failed completely
if [ -z "$primary" ]; then
    notify-send -u critical -i video-display "Display Error" "Could not query display server via xrandr."
    exit 1
fi

# 2. Detect all other connected displays (capture cards, HDMI, DP, Type-C)
externals=$(xrandr --query 2>/dev/null | grep " connected" | awk '{print $1}' | grep -v "^${primary}$")

# If no external displays detected
if [ -z "$externals" ]; then
    notify-send -u critical -i video-display "Display Mirror" "No external outputs or capture cards detected.\nPlease check your HDMI / Type-C cable connection."
    echo -e "[!] No external displays connected\n(Check HDMI / capture card cable)" | rofi -dmenu -theme ~/.config/rofi/rofi-tui.rasi -p "MIRROR //"
    exit 0
fi

# 3. Construct Rofi menu options
options=()
for ext in $externals; do
    options+=("⚡ Mirror: $primary -> $ext (Capture Card 1080p@60Hz)")
    options+=("⚡ Mirror: $primary -> $ext (Auto / Native)")
    options+=("⚡ Mirror: $primary -> $ext (Force 60Hz Both)")
    options+=("🖥️ Extend: $primary + $ext (Right of main)")
    options+=("❌ Turn Off $ext")
done
options+=("🔄 Reset: Single Display ($primary only)")

# 4. Prompt user with Rofi
selected=$(printf '%s\n' "${options[@]}" | rofi -dmenu -theme ~/.config/rofi/rofi-tui.rasi -p "MIRROR //" -i)

if [ -z "$selected" ]; then
    exit 0
fi

# 5. Execute selected action
case "$selected" in
    *"Capture Card 1080p@60Hz"*)
        ext=$(echo "$selected" | grep -oP '(?<=-> )[A-Za-z0-9\-_]+')
        if [ -n "$ext" ]; then
            xrandr --output "$ext" --mode 1920x1080 --rate 60 --same-as "$primary" 2>/dev/null || \
            xrandr --output "$ext" --auto --same-as "$primary" 2>/dev/null
            bash ~/.fehbg 2>/dev/null || true
            notify-send -u normal -i video-display "Display Mirror" "Screen $primary mirrored to $ext\n(Optimized 1080p @ 60Hz for capture card)"
        fi
        ;;

    *"Auto / Native"*)
        ext=$(echo "$selected" | grep -oP '(?<=-> )[A-Za-z0-9\-_]+')
        if [ -n "$ext" ]; then
            xrandr --output "$ext" --auto --same-as "$primary" 2>/dev/null
            bash ~/.fehbg 2>/dev/null || true
            notify-send -u normal -i video-display "Display Mirror" "Screen $primary mirrored to $ext\n(Auto Mode)"
        fi
        ;;

    *"Force 60Hz Both"*)
        ext=$(echo "$selected" | grep -oP '(?<=-> )[A-Za-z0-9\-_]+')
        if [ -n "$ext" ]; then
            xrandr --output "$primary" --mode 1920x1080 --rate 60 --output "$ext" --mode 1920x1080 --rate 60 --same-as "$primary" 2>/dev/null
            bash ~/.fehbg 2>/dev/null || true
            notify-send -u normal -i video-display "Display Mirror" "Forced 60Hz on both $primary and $ext"
        fi
        ;;

    *"Extend: "*)
        ext=$(echo "$selected" | grep -oP '(?<=\+ )[A-Za-z0-9\-_]+')
        if [ -n "$ext" ]; then
            xrandr --output "$ext" --auto --right-of "$primary" 2>/dev/null
            bash ~/.fehbg 2>/dev/null || true
            notify-send -u normal -i video-display "Display Extended" "Extended desktop to $ext (Right of $primary)"
        fi
        ;;

    *"Turn Off "*)
        ext=$(echo "$selected" | grep -oP '(?<=Turn Off )[A-Za-z0-9\-_]+')
        if [ -n "$ext" ]; then
            xrandr --output "$ext" --off 2>/dev/null
            notify-send -u normal -i video-display "Display Setup" "Turned off output $ext"
        fi
        ;;

    *"Reset: Single Display"*)
        for out in $externals; do
            xrandr --output "$out" --off 2>/dev/null
        done
        xrandr --output "$primary" --auto 2>/dev/null
        bash ~/.fehbg 2>/dev/null || true
        notify-send -u normal -i video-display "Display Setup" "Reset to single display ($primary)"
        ;;
esac
