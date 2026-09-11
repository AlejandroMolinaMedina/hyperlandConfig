--hl.gesture({
--	fingers = 3,
--	direction = "horizontal",
--	action = "workspace",
--})
--
--#region
hl.config({
	gestures = {
		workspace_swipe_distance = 30,
		workspace_swipe_cancel_ratio = 0.1,
	},
})

hl.gesture({
	fingers = 3,
	direction = "right",
	action = function()
		hl.dispatch(hl.dsp.focus({
			workspace = "-1",
		}))
	end,
})

hl.gesture({
	fingers = 3,
	direction = "left",
	action = function()
		hl.dispatch(hl.dsp.focus({
			workspace = "+1",
		}))
	end,
})

-- ============================================
-- Ventanas minimizadas
-- ============================================

local minimized_workspace = "special:minimized"

-- Pila de ventanas minimizadas
local minimized_stack = {}

-- ============================================
-- 3 dedos ↓ = Minimizar ventana
-- ============================================

hl.gesture({
	fingers = 3,
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
-- 3 dedos ↑ = Restaurar última minimizada
-- ============================================

hl.gesture({
	fingers = 3,
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
