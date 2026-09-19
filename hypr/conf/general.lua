-- ~/.config/hypr/conf/general.lua

-- Monitores
hl.monitor({
	output = "eDP-1",
	mode = "1920x1200@60",
	position = "auto",
	scale = 1,
})

hl.monitor({
	output = "DP-1",
	mode = "1920x1080@74.97",
	position = "auto-right",
	scale = 1,
})

hl.monitor({
	output = "HDMI-A-1",
	mode = "1920x1080@60.00",
	position = "auto-right",
	scale = 1,
})

-- Monitor por defecto
hl.monitor({
	output = "",
	mode = "preferred",
	position = "auto",
	scale = 1,
})

-- General
hl.config({
	general = {
		gaps_in = 7,
		gaps_out = 10,
		border_size = 2,
		["col.active_border"] = "rgba(ffffffaa)",
		["col.inactive_border"] = "rgba(222222aa)",
		layout = "master",
	},

	decoration = {
		rounding = 10,
	},
})
