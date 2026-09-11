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
	hl.exec_cmd("~/.config/waybar/scripts/calendar_panel.py")
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
