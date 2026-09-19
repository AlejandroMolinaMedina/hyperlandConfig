-- ~/.config/hypr/hyprland.lua

-- ============================================
-- Modular configuration
-- ============================================

require("conf.general")
require("conf.input")
require("conf.bindings")
require("conf.rules")
require("conf.theme")
require("conf.animations")
require("conf.gestures")

-- ============================================
-- Environment
-- ============================================
hl.env("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")

-- ============================================
-- Autostart
-- ============================================

hl.on("hyprland.start", function()
	hl.exec_cmd("waybar")
	hl.exec_cmd("hyprpaper")
	hl.exec_cmd("~/.config/hypr/scripts/wallpaper_daemon.sh")
	hl.exec_cmd("hyprctl keyword source ~/.config/hypr/conf/mouse.conf")
	hl.exec_cmd("swaync")
	-- Bloqueo por inactividad y apagado de pantalla (hypr/hypridle.conf)
	hl.exec_cmd("hypridle")
	-- Los tres paneles (calendario, brillo/volumen y reproducción) en un proceso
	hl.exec_cmd("~/.config/waybar/scripts/panels.py")
end)

-- ============================================
-- Misc
-- ============================================

hl.config({
	misc = {
		disable_hyprland_logo = true,
		disable_splash_rendering = true,
		force_default_wallpaper = 0,
		-- Al enfocar otra ventana (ALT + TAB), hereda el maximizado/pantalla completa
		on_focus_under_fullscreen = 1,
		-- Con la pantalla apagada, cualquier movimiento o tecla la vuelve a encender
		mouse_move_enables_dpms = true,
		key_press_enables_dpms = true,
	},
})

-- ============================================
-- Workspaces
-- ============================================

-- hl.workspace("1", {
--     persistent = true,
-- })

-- hl.workspace("2", {
--     persistent = true,
-- })

-- hl.workspace("3", {
--     persistent = true,
-- })

-- hl.workspace("4", {
--     persistent = true,
-- })

-- hl.workspace("5", {
--     persistent = true,
-- })
