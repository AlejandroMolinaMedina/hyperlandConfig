#!/bin/bash

WALLPAPER_DIR="$HOME/.secrets/wallpapers"
LOG_FILE="$HOME/.cache/wallpaper_daemon.log"

mkdir -p "$(dirname "$LOG_FILE")"

# Evitar múltiples instancias
if pgrep -f "$(basename "$0")" | grep -v $$ > /dev/null; then
    exit 0
fi

while true; do
    find "$WALLPAPER_DIR" -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" \) -print0 | shuf -z | while IFS= read -r -d '' wallpaper; do
        if [ -f "$wallpaper" ]; then
            # 2. Aplicar la nueva imagen a todos los monitores
            hyprctl hyprpaper wallpaper ",$wallpaper"
        fi
        sleep 300
    done
done
