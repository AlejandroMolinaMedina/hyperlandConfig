-- ~/.config/hypr/conf/rules.lua

-- ============================================
-- Calendario de la barra (gsimplecal, clic en la fecha de Waybar)
-- ============================================

hl.window_rule({
	name = "gsimplecal-popup",
	match = { class = "^gsimplecal$" },
	float = true,
	-- Centrado bajo el puntero (donde se hizo clic), justo debajo de la barra
	move = "cursor_x-(window_w*0.5) 50",
})

-- ============================================
-- Diálogos flotantes (antes en rules.conf)
-- ============================================

-- Diálogos de git y petición de contraseña SSH
hl.window_rule({
	name = "float-dialogs-by-class",
	match = { class = "confirmreset|makebranch|maketag|ssh-askpass" },
	float = true,
})

-- Diálogo de ramas y petición de contraseña GPG
hl.window_rule({
	name = "float-dialogs-by-title",
	match = { title = "branchdialog|pinentry" },
	float = true,
})
