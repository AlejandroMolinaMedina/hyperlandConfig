#!/usr/bin/env bash
# install.sh — monta este escritorio Hyprland en un Arch recién instalado.
#
#   git clone git@github.com:AlejandroMolinaMedina/hyperlandConfig.git
#   cd hyperlandConfig && ./install.sh
#
# Pasos (cada uno se puede saltar, ver --ayuda):
#   1. paquetes      pacman + AUR (yay; si no está, lo instala)
#   2. enlaces       ~/.config/{hypr,waybar,swaync} -> este repo
#                    (lo que ya hubiera se guarda como <carpeta>.respaldo-<fecha>)
#   3. servicios     botón de encendido (systemd de usuario), llavero de GNOME
#   4. sistema       logind ignora el botón de encendido, usuario en el grupo input
#   5. plugin        hypr-mission-control (vista general con 3 dedos)
#
# Se puede volver a ejecutar sin miedo: lo que ya está hecho se salta.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
PROYECTOS="${PROYECTOS:-$HOME/Documents/projects}"
PLUGIN_REPO="https://github.com/AlejandroMolinaMedina/hypr-mission-control.git"
FECHA="$(date +%Y%m%d-%H%M%S)"

# Paquetes de los repos oficiales
PACMAN=(
	# Hyprland y su ecosistema
	hyprland hyprlock hypridle hyprpaper
	xdg-desktop-portal-hyprland xdg-desktop-portal-gtk
	# Notificaciones, lanzador, capturas
	swaync rofi grim slurp wl-clipboard jq
	# Brillo, sonido y reproducción
	brightnessctl playerctl pipewire pipewire-pulse wireplumber libpulse
	# Paneles de Waybar (Python + GTK3 + capa de Wayland)
	python python-gobject gtk3 gtk-layer-shell python-evdev
	# Calendario del panel: cuentas en línea y Evolution Data Server
	evolution-data-server libical gnome-online-accounts gnome-keyring gnome-control-center
	# Fuentes e iconos
	ttf-jetbrains-mono-nerd ttf-nerd-fonts-symbols otf-font-awesome papirus-icon-theme
	# Para compilar (AUR y el plugin)
	git base-devel
)

# Del AUR: la versión git de Waybar trae workspace-taskbar (iconos de ventanas)
AUR=(waybar-git)

# Carpetas que se enlazan a ~/.config
ENLACES=(hypr waybar swaync)

# ============================================
# Utilidades
# ============================================

SIMULAR=0
SALTAR=()

azul() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
info() { printf '    %s\n' "$*"; }
aviso() { printf '\033[1;33m    ! %s\033[0m\n' "$*"; }
error() { printf '\033[1;31m    ✗ %s\033[0m\n' "$*" >&2; }

# Ejecuta un comando, o solo lo muestra con --simular
hacer() {
	if ((SIMULAR)); then
		printf '    [simular] %s\n' "$*"
	else
		"$@"
	fi
}

saltar() {
	local paso
	for paso in "${SALTAR[@]}"; do
		[[ $paso == "$1" ]] && return 0
	done
	return 1
}

ayuda() {
	cat <<EOF
Uso: ./install.sh [opciones]

  --simular            muestra lo que haría, sin tocar nada
  --sin-paquetes       no instala paquetes
  --sin-enlaces        no crea los enlaces en ~/.config
  --sin-servicios      no activa servicios de usuario
  --sin-sistema        no toca /etc ni grupos (no pide sudo para eso)
  --sin-plugin         no instala hypr-mission-control
  -h, --ayuda          esta ayuda

Variables:
  PROYECTOS=<carpeta>  dónde clonar el plugin (por defecto ~/Documents/projects)
EOF
}

while (($#)); do
	case "$1" in
		--simular) SIMULAR=1 ;;
		--sin-paquetes) SALTAR+=(paquetes) ;;
		--sin-enlaces) SALTAR+=(enlaces) ;;
		--sin-servicios) SALTAR+=(servicios) ;;
		--sin-sistema) SALTAR+=(sistema) ;;
		--sin-plugin) SALTAR+=(plugin) ;;
		-h | --ayuda) ayuda; exit 0 ;;
		*) error "opción desconocida: $1"; ayuda; exit 1 ;;
	esac
	shift
done

# ============================================
# Comprobaciones
# ============================================

if [[ $EUID -eq 0 ]]; then
	error "No lo ejecutes como root: usa tu usuario (pedirá sudo cuando haga falta)."
	exit 1
fi
if ! command -v pacman >/dev/null; then
	error "Este instalador es para Arch Linux (no encuentro pacman)."
	exit 1
fi
((SIMULAR)) && azul "Modo simulación: no se cambia nada"

# ============================================
# 1. Paquetes
# ============================================

instalar_yay() {
	command -v yay >/dev/null && return 0
	info "yay no está: se instala desde el AUR (yay-bin)"
	local tmp
	tmp="$(mktemp -d)"
	hacer git clone --depth 1 https://aur.archlinux.org/yay-bin.git "$tmp/yay-bin"
	if ((SIMULAR)); then
		info "[simular] (cd $tmp/yay-bin && makepkg -si)"
	else
		(cd "$tmp/yay-bin" && makepkg -si --noconfirm)
	fi
	rm -rf "$tmp"
}

if ! saltar paquetes; then
	azul "1/5 Paquetes"
	# Waybar oficial y waybar-git chocan: si está el oficial, quitarlo primero
	if pacman -Qq waybar 2>/dev/null | grep -qx waybar; then
		aviso "Está instalado 'waybar' (oficial); se cambia por 'waybar-git'"
		hacer sudo pacman -Rdd --noconfirm waybar
	fi
	hacer sudo pacman -S --needed "${PACMAN[@]}"
	instalar_yay
	hacer yay -S --needed "${AUR[@]}"
fi

# ============================================
# 2. Enlaces en ~/.config
# ============================================

enlazar() {
	local origen="$1" destino="$2"
	if [[ -L $destino && "$(readlink -f "$destino")" == "$(readlink -f "$origen")" ]]; then
		info "ya enlazado: $destino"
		return
	fi
	if [[ -e $destino || -L $destino ]]; then
		info "respaldo: $destino -> $destino.respaldo-$FECHA"
		hacer mv "$destino" "$destino.respaldo-$FECHA"
	fi
	hacer mkdir -p "$(dirname "$destino")"
	hacer ln -s "$origen" "$destino"
	info "enlazado: $destino -> $origen"
}

if ! saltar enlaces; then
	azul "2/5 Enlaces en $CONFIG"
	for carpeta in "${ENLACES[@]}"; do
		enlazar "$REPO/$carpeta" "$CONFIG/$carpeta"
	done
	enlazar "$REPO/systemd/power-button.service" "$CONFIG/systemd/user/power-button.service"
	# Scripts ejecutables (git conserva el permiso, pero por si acaso)
	hacer chmod +x "$REPO"/hypr/scripts/*.sh "$REPO"/hypr/scripts/*.py "$REPO"/waybar/scripts/*.py
fi

# ============================================
# 3. Servicios de usuario
# ============================================

if ! saltar servicios; then
	azul "3/5 Servicios de usuario"
	hacer systemctl --user daemon-reload
	# Botón de encendido -> menú de apagado de rofi
	hacer systemctl --user enable power-button.service
	# Llavero: guarda las credenciales de las cuentas del calendario
	hacer systemctl --user enable gnome-keyring-daemon.socket
	info "Se ponen en marcha al iniciar la próxima sesión"
fi

# ============================================
# 4. Ajustes del sistema (sudo)
# ============================================

if ! saltar sistema; then
	azul "4/5 Ajustes del sistema"
	# Que el botón de encendido no apague el equipo: lo atiende power_button.py
	LOGIND=/etc/systemd/logind.conf.d/10-boton-encendido.conf
	if grep -qs '^HandlePowerKey=ignore' /etc/systemd/logind.conf "$LOGIND"; then
		info "logind ya ignora el botón de encendido"
	else
		info "logind: HandlePowerKey=ignore ($LOGIND)"
		if ((SIMULAR)); then
			info "[simular] escribir $LOGIND"
		else
			sudo mkdir -p "$(dirname "$LOGIND")"
			printf '[Login]\nHandlePowerKey=ignore\n' | sudo tee "$LOGIND" >/dev/null
		fi
	fi
	# power_button.py lee el botón desde /dev/input
	if id -nG "$USER" | tr ' ' '\n' | grep -qx input; then
		info "ya estás en el grupo input"
	else
		info "añadiendo $USER al grupo input (vale desde el próximo inicio de sesión)"
		hacer sudo usermod -aG input "$USER"
	fi
fi

# ============================================
# 5. Plugin hypr-mission-control
# ============================================

if ! saltar plugin; then
	azul "5/5 Plugin hypr-mission-control"
	DIR_PLUGIN="$PROYECTOS/hypr-mission-control"
	if [[ -d $DIR_PLUGIN/.git ]]; then
		info "ya clonado: $DIR_PLUGIN (se actualiza)"
		hacer git -C "$DIR_PLUGIN" pull --ff-only || aviso "no se pudo actualizar; se instala lo que hay"
	else
		hacer mkdir -p "$PROYECTOS"
		hacer git clone "$PLUGIN_REPO" "$DIR_PLUGIN"
	fi
	# Instala el cargador en ~/.local/bin; el plugin se compila solo al
	# arrancar Hyprland, para la versión que esté corriendo
	hacer make -C "$DIR_PLUGIN" install PREFIX="$HOME/.local"
fi

# ============================================
# Lo que queda a mano
# ============================================

azul "Listo. Queda a mano:"
pendiente() { printf '    • %s\n' "$*"; }

if [[ $HOME != /home/al3xmm14 ]]; then
	pendiente "Tu carpeta personal no es /home/al3xmm14: cambia esa ruta en"
	pendiente "  hypr/hyprpaper.conf y hypr/xdph.conf (no admiten ~)"
fi
[[ -d $HOME/.secrets/wallpapers ]] ||
	pendiente "Fondos de pantalla: copia tus imágenes a ~/.secrets/wallpapers"
[[ -d $CONFIG/rofi ]] ||
	pendiente "rofi: falta ~/.config/rofi (lanzador, menú de apagado y quicklinks)"
[[ -x $PROYECTOS/qtileArchLinux/.scripts/mic_manager.sh ]] ||
	pendiente "Micrófono: el atajo usa $PROYECTOS/qtileArchLinux/.scripts/mic_manager.sh"
[[ -d $HOME/Images ]] ||
	pendiente "Capturas: crea ~/Images (Impr Pant y Super+Shift+S guardan ahí)"
pendiente "Calendario: añade tus cuentas en 'gnome-control-center online-accounts'"
pendiente "Cierra sesión y entra en Hyprland para que todo arranque"
