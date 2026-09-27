-- ~/.config/hypr/conf/rules.lua

-- ============================================
-- Desenfoque bajo los paneles que se despliegan
-- ============================================

-- Las capas (layer surfaces) no se desenfocan solas, aunque el blur esté
-- activado: hay que pedirlo por su namespace. ignore_alpha evita difuminar
-- las zonas completamente transparentes que rodean a la tarjeta.
for _, capa in ipairs({
	"calendar-panel",
	"media-panel",
	"player-panel",
	"swaync-control-center",
	"swaync-notification-window",
}) do
	hl.layer_rule({
		name = "blur-" .. capa,
		match = { namespace = "^" .. capa .. "$" },
		blur = true,
		ignore_alpha = 0.2,
	})
end

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
