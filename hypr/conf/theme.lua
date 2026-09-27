hl.config({
	decoration = {
		active_opacity = 1.0,
		inactive_opacity = 0.95,

		-- Desenfoque más marcado: con un solo paso apenas se notaba tras los
		-- paneles translúcidos. Las capas además lo piden en conf/rules.lua.
		blur = {
			enabled = true,
			size = 10,
			passes = 3,
			new_optimizations = true,
			ignore_opacity = true,
			vibrancy = 0.2,
		},

		shadow = {
			enabled = true,
			range = 4,
			render_power = 3,
			color = "rgba(1a1a1aee)",
		},
	},
})
