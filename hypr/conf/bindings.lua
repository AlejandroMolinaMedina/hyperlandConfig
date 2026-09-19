-- ~/.config/hypr/conf/bindings.lua

-- Variables
local mod = "ALT"
local windows = "SUPER"

-- ============================================
-- Mover ventanas
-- ============================================

hl.bind("ALT + SHIFT + H", hl.dsp.window.move({ direction = "l" }))
hl.bind("ALT + SHIFT + L", hl.dsp.window.move({ direction = "r" }))
hl.bind("ALT + SHIFT + J", hl.dsp.window.move({ direction = "d" }))
hl.bind("ALT + SHIFT + K", hl.dsp.window.move({ direction = "u" }))

-- ============================================
-- Ventanas
-- ============================================

hl.bind("ALT + RETURN", hl.dsp.window.fullscreen({ mode = "maximized" }))
hl.bind("ALT + T", hl.dsp.window.float({ action = "toggle" }))
hl.bind("ALT + W", hl.dsp.window.close())

-- ============================================
-- Sistema
-- ============================================

hl.bind("ALT + CTRL + R", hl.dsp.exec_cmd("hyprctl reload"))

-- ============================================
-- Redimensionar ventanas
-- ============================================

hl.bind("CTRL + ALT + H", hl.dsp.window.resize({ x = -20, y = 0, relative = true }))

hl.bind("CTRL + ALT + L", hl.dsp.window.resize({ x = 20, y = 0, relative = true }))

hl.bind("CTRL + ALT + J", hl.dsp.window.resize({ x = 0, y = 20, relative = true }))

hl.bind("CTRL + ALT + K", hl.dsp.window.resize({ x = 0, y = -20, relative = true }))

-- ============================================
-- Lanzadores
-- ============================================

hl.bind("CTRL + SHIFT + P", hl.dsp.exec_cmd("flameshot gui"))

hl.bind("ALT + TAB", hl.dsp.window.cycle_next())

hl.bind("ALT + SPACE", hl.dsp.exec_cmd("rofi -show drun -theme ~/.config/rofi/launchers/type-4/style-3.rasi"))

hl.bind("ALT + L", hl.dsp.exec_cmd("/home/al3xmm14/.config/rofi/applets/bin/quicklinks.sh"))

-- ============================================
-- Multimedia
-- ============================================

-- repeating: mantener pulsada la tecla repite la acción (como binde)
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("pactl set-sink-volume @DEFAULT_SINK@ +5%"), { repeating = true })

hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("pactl set-sink-volume @DEFAULT_SINK@ -5%"), { repeating = true })

hl.bind("XF86AudioMute", hl.dsp.exec_cmd("pactl set-sink-mute @DEFAULT_SINK@ toggle"))

hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl set +1%"), { repeating = true })

hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl set 1%-"), { repeating = true })

hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("/home/al3xmm14/Documents/projects/qtileArchLinux/.scripts/mic_manager.sh"))

-- ============================================
-- Bloquear
-- ============================================

hl.bind("SUPER + L", hl.dsp.exec_cmd("hyprlock"))

-- ============================================
-- Workspaces
-- ============================================

for i = 1, 9 do
	hl.bind(
		"ALT + " .. i,
		hl.dsp.focus({
			workspace = i,
			on_current_monitor = true,
		})
	)
end

-- ============================================
-- Workspaces
-- ============================================

for i = 1, 9 do
	-- Cambiar al workspace
	hl.bind(
		"ALT + " .. i,
		hl.dsp.focus({
			workspace = i,
			on_current_monitor = true,
		})
	)

	-- Mover ventana al workspace y cambiar a él
	hl.bind("ALT + SHIFT + " .. i, function()
		hl.dispatch(hl.dsp.window.move({
			workspace = i,
		}))

		hl.dispatch(hl.dsp.focus({
			workspace = i,
			on_current_monitor = true,
		}))
	end)
end

-------
------
local function go_to_workspace(i)
	local ws = hl.get_workspace(i)

	if ws == nil then
		return
	end

	local monitor = ws.monitor

	if monitor == nil then
		return
	end

	-- Cambiar el foco al workspace
	hl.dispatch(hl.dsp.focus({
		workspace = i,
	}))

	-- Mover el mouse al centro del monitor
	hl.dispatch(hl.dsp.cursor.move({
		x = monitor.x + monitor.width / 2,
		y = monitor.y + monitor.height / 2,
	}))
end

for i = 1, 9 do
	hl.bind("ALT + CTRL + " .. i, function()
		go_to_workspace(i)
	end)
end
---

-- ===================a=========================
-- Capturas de pantalla
-- ============================================

hl.bind(
	"PRINT",
	hl.dsp.exec_cmd(
		[[grim -o "$(hyprctl monitors -j | jq -r '.[] | select(.focused == true) | .name')" ~/Images/screenshot_$(date +%Y-%m-%d_%H-%M-%S).png]]
	)
)

hl.bind(
	"SUPER + SHIFT + S",
	hl.dsp.exec_cmd([[slurp | grim -g - - | tee ~/Images/screenshotArea_$(date +%Y-%m-%d_%H-%M-%S).png | wl-copy]])
)
