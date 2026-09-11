-- ~/.config/hypr/conf/animations.lua

-- ============================================
-- Curvas
-- ============================================

hl.curve("easeOutQuint", { type = "bezier", points = { { 0.23, 1 }, { 0.32, 1 } } })
hl.curve("almostLinear", { type = "bezier", points = { { 0.5, 0.5 }, { 0.75, 1 } } })
hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
hl.curve("quick", { type = "bezier", points = { { 0.15, 0 }, { 0.1, 1 } } })

-- ============================================
-- Animaciones (speed en décimas de segundo: 2 = 200 ms)
-- ============================================

-- Borde al cambiar de foco
hl.animation({ leaf = "border", enabled = true, speed = 2, bezier = "easeOutQuint" })

-- Ventanas: mover, abrir y cerrar
hl.animation({ leaf = "windows", enabled = true, speed = 2.5, bezier = "easeOutQuint" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 2.5, bezier = "easeOutQuint", style = "popin 90%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.5, bezier = "linear", style = "popin 90%" })

-- Fundidos (incluye la opacidad de ventanas inactivas al cambiar de foco)
hl.animation({ leaf = "fade", enabled = true, speed = 2, bezier = "quick" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.5, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.2, bezier = "almostLinear" })
