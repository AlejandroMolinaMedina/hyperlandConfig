-- Gestos estilo macOS
hl.config({
	gestures = {
		workspace_swipe_distance = 300,
		workspace_swipe_cancel_ratio = 0.3,
		workspace_swipe_min_speed_to_force = 30,
		workspace_swipe_direction_lock = true,
	},
})

-- ============================================
-- 3 / 4 dedos ←→ = Cambiar de escritorio (sigue al dedo, como en Mac)
-- ============================================

hl.gesture({
	fingers = 3,
	direction = "horizontal",
	action = "workspace",
})

hl.gesture({
	fingers = 4,
	direction = "horizontal",
	action = "workspace",
})

-- ============================================
-- 3 dedos ↑ = Mission Control
-- (con la vista abierta, 3 / 4 dedos ←→ cambian de escritorio dentro de ella)
-- ============================================

-- Plugin hypr-mission-control (~/Documents/projects/hypr-mission-control),
-- cargado al iniciar sesión desde hyprland.lua. El gesto de 3 dedos ↑ y el
-- deslizamiento lateral con la vista abierta los registra el propio plugin.
-- Sus opciones solo existen una vez cargado (entonces recarga la config).
if hl.plugin.missioncontrol then
	hl.config({
		plugin = {
			missioncontrol = {
				gesture_fingers = 3,
				-- El ↓ lo define abajo esta config: también muestra las minimizadas
				gesture_close = false,
				workspace_label = "Escritorio {}",
			},
		},
	})
end

local function subida(e)
	return e.delta and -e.delta.y or 0
end

local vista = {}

-- Devuelve si el gesto la mueve (sin el plugin cargado o con la vista
-- cerrada, no: entonces 3 dedos ↓ muestra las minimizadas)
function vista.empezar()
	local mc = hl.plugin.missioncontrol
	return mc ~= nil and mc.gesture_begin("close")
end

function vista.mover(e)
	hl.plugin.missioncontrol.gesture_update(subida(e), e.time_ms or 0)
end

function vista.soltar(e)
	hl.plugin.missioncontrol.gesture_end(e.cancelled == true)
end

-- ============================================
-- 3 dedos ↓ = Cerrar Mission Control si está abierto (también siguiendo
--             al dedo); si no, ver las ventanas minimizadas (tipo App Exposé)
-- ============================================

local cerrando_vista = false

hl.gesture({
	fingers = 3,
	direction = "down",
	action = {
		start = function(e)
			cerrando_vista = vista.empezar()
			if cerrando_vista then
				vista.mover(e)
			end
		end,
		update = function(e)
			if cerrando_vista then
				vista.mover(e)
			end
		end,
		finish = function(e)
			if cerrando_vista then
				vista.soltar(e)
			elseif not e.cancelled then
				hl.dispatch(hl.dsp.workspace.toggle_special("minimized"))
			end
			cerrando_vista = false
		end,
	},
})

-- ============================================
-- Pellizco (3 dedos) = Launchpad
-- ============================================

hl.gesture({
	fingers = 3,
	direction = "pinchin",
	action = function()
		hl.dispatch(hl.dsp.exec_cmd("rofi -show drun -theme ~/.config/rofi/launchers/type-4/style-3.rasi"))
	end,
})

-- ============================================
-- Abrir (3 dedos) = Mostrar escritorio / volver
-- ============================================

hl.gesture({
	fingers = 3,
	direction = "pinchout",
	action = function()
		local workspace = hl.get_active_workspace()
		local target = (workspace and workspace.windows == 0) and "previous" or "emptym"
		hl.dispatch(hl.dsp.focus({ workspace = target }))
	end,
})

-- ============================================
-- Ventanas minimizadas
-- ============================================

local minimized_workspace = "special:minimized"

-- Pila de ventanas minimizadas
local minimized_stack = {}

-- ============================================
-- 4 dedos ↓ = Minimizar ventana
-- ============================================

hl.gesture({
	fingers = 4,
	direction = "down",
	action = function()
		local window = hl.get_active_window()

		if not window then
			return
		end

		local workspace = hl.get_active_workspace()

		if not workspace then
			return
		end

		-- Guardamos la ventana y el workspace de origen
		table.insert(minimized_stack, {
			window = window,
			workspace = workspace,
		})

		-- Marcamos la ventana como minimizada
		hl.dispatch(hl.dsp.window.tag({
			tag = "minimized",
			window = window,
		}))

		-- La mandamos al special workspace
		hl.dispatch(hl.dsp.window.move({
			workspace = minimized_workspace,
			window = window,
			follow = false,
		}))
	end,
})

-- ============================================
-- 4 dedos ↑ = Restaurar última minimizada
-- ============================================

hl.gesture({
	fingers = 4,
	direction = "up",
	action = function()
		-- No hay ventanas minimizadas
		if #minimized_stack == 0 then
			return
		end

		-- Sacamos la última ventana de la pila
		local item = table.remove(minimized_stack)

		if not item then
			return
		end

		-- Restauramos la ventana en su workspace original
		hl.dispatch(hl.dsp.window.move({
			workspace = item.workspace,
			window = item.window,
			follow = true,
		}))

		-- Quitamos el tag de minimizada
		hl.dispatch(hl.dsp.window.clear_tags({
			window = item.window,
		}))
	end,
})
