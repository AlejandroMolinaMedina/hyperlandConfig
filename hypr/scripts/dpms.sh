#!/bin/sh
# ~/.config/hypr/scripts/dpms.sh on|off
#
# Enciende o apaga la pantalla de forma fiable.
#
# Por qué existe: con la configuración en Lua, `hyprctl dispatch dpms off`
# falla (el parser espera Lua) y `hl.dsp.dpms("off")` acepta el argumento
# pero lo ignora: siempre ALTERNA. Si hypridle lo usara tal cual, al mover
# el ratón la pantalla se apagaría en lugar de encenderse.
# Solución: consultar el estado real y alternar solo si hace falta.

deseado="$1"
case "$deseado" in
	on | off) ;;
	*)
		echo "uso: $0 on|off" >&2
		exit 2
		;;
esac

# "true" si alguna pantalla está encendida
encendida() {
	hyprctl monitors -j | jq -r 'map(.dpmsStatus) | any'
}

alternar() {
	hyprctl dispatch 'hl.dsp.dpms("toggle")' >/dev/null
}

actual=$(encendida)
[ "$deseado" = "on" ] && [ "$actual" = "false" ] && alternar
[ "$deseado" = "off" ] && [ "$actual" = "true" ] && alternar

exit 0
