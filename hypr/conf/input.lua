-- ~/.config/hypr/conf/input.lua

hl.config({
	input = {
		kb_layout = "latam",
		follow_mouse = 1,

		touchpad = {
			natural_scroll = true,
			tap_to_click = true, -- tocar = clic
			clickfinger_behavior = true, -- clic con 2 dedos = derecho, con 3 = central
			disable_while_typing = true,
		},
	},

	cursor = {
		no_hardware_cursors = true,
	},
})
