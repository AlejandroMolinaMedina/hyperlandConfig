#!/bin/sh
# ~/.config/hypr/scripts/tema.sh
#
# Modo claro / oscuro de todo el escritorio. La fuente de verdad es el ajuste
# del sistema (org.gnome.desktop.interface color-scheme), el mismo que siguen
# las apps GTK4/libadwaita, Firefox, Chrome, etc.
#
#   tema.sh oscuro | claro | alternar   cambia el ajuste del sistema y aplica
#   tema.sh aplicar                     solo aplica lo que diga el sistema
#
# Aplicar = copiar temas/<modo>.css a tema.css en Waybar y swaync y
# recargarlos (solo si cambió). Los paneles de Waybar (panels.py) siguen el
# ajuste por su cuenta y además llaman a "aplicar" cuando cambia, así que
# también vale cambiarlo desde cualquier otro sitio.

CONFIG="$HOME/.config"
INTERFAZ="org.gnome.desktop.interface"

es_oscuro() {
	[ "$(gsettings get "$INTERFAZ" color-scheme)" = "'prefer-dark'" ]
}

poner_sistema() {
	if [ "$1" = oscuro ]; then
		gsettings set "$INTERFAZ" color-scheme prefer-dark
		gsettings set "$INTERFAZ" gtk-theme Adwaita-dark   # apps GTK3
	else
		gsettings set "$INTERFAZ" color-scheme default
		gsettings set "$INTERFAZ" gtk-theme Adwaita
	fi
}

# copiar <origen> <destino>: devuelve 0 si el archivo cambió
copiar() {
	cmp -s "$1" "$2" && return 1
	cp -f "$1" "$2.tmp" && mv -f "$2.tmp" "$2"
}

aplicar() {
	if es_oscuro; then modo=oscuro; else modo=claro; fi
	if copiar "$CONFIG/waybar/temas/$modo.css" "$CONFIG/waybar/tema.css"; then
		pkill -SIGUSR2 -x waybar
	fi
	if copiar "$CONFIG/swaync/temas/$modo.css" "$CONFIG/swaync/tema.css"; then
		swaync-client -rs >/dev/null 2>&1
	fi
}

case "$1" in
	oscuro | claro) poner_sistema "$1" ;;
	alternar) if es_oscuro; then poner_sistema claro; else poner_sistema oscuro; fi ;;
	aplicar | "") ;;
	*) echo "uso: tema.sh [oscuro|claro|alternar|aplicar]" >&2; exit 1 ;;
esac
aplicar
