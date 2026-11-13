-- ~/.config/hypr/conf/monitores.lua
--
-- Monitores, al estilo de Windows: cada combinación de pantallas conectadas
-- recuerda su modo (extender o solo una) y la posición de cada una.
--
-- Los perfiles los escribe el panel de pantallas de Waybar
-- (waybar/scripts/display_panel.py) en ~/.config/hypr/monitores.json.
-- Aquí solo se leen y se aplican:
--   * al cargar la configuración (arranque y cada recarga)
--   * al conectar o desconectar un monitor
--   * cuando el panel llama a MonitoresAplicar() con hyprctl eval
--
-- Formato de monitores.json:
-- {
--   "perfiles": {
--     "<descripción A> + <descripción B>": {
--       "modo": "extender" | "solo",
--       "solo": "<descripción>",                -- solo con modo "solo"
--       "monitores": { "<descripción>": { "x": 0, "y": -1080 } }
--     }
--   }
-- }
-- La clave son las descripciones de los monitores conectados, ordenadas.
-- Se usan descripciones (marca, modelo, número de serie) y no puertos:
-- el mismo monitor conserva su sitio aunque cambie de puerto.

local ARCHIVO = os.getenv("HOME") .. "/.config/hypr/monitores.json"

-- Modo y escala de cada puerto. No dependen del perfil: el panel solo
-- cambia el modo de pantalla y la posición.
local BASE = {
	["eDP-1"] = { mode = "1920x1200@60", scale = 1 },
	["DP-1"] = { mode = "1920x1080@74.97", scale = 1 },
	["HDMI-A-1"] = { mode = "1920x1080@60", scale = 1 },
}

-- ============================================
-- Tapa del portátil
-- ============================================

-- Con la tapa cerrada la pantalla interna se trata como si no estuviera:
-- se apaga y la disposición es la de los monitores externos solos (con su
-- propio perfil). Si no hay ningún externo no se toca nada: de eso se
-- encarga logind (suspende). Al abrir la tapa vuelve el perfil completo.
local function leer_tapa()
	local p = io.popen("cat /proc/acpi/button/lid/*/state 2>/dev/null")
	if not p then
		return false
	end
	local estado = p:read("a") or ""
	p:close()
	return estado:find("closed") ~= nil
end

local tapa_cerrada = leer_tapa()

-- Registro de lo que se aplica, para depurar: $XDG_RUNTIME_DIR/monitores.log
local REGISTRO = (os.getenv("XDG_RUNTIME_DIR") or "/tmp") .. "/monitores.log"

local function registrar(texto)
	local f = io.open(REGISTRO, "a")
	if f then
		f:write(os.date("%H:%M:%S "), texto, "\n")
		f:close()
	end
end

local function estado_actual()
	local partes = {}
	for _, m in ipairs(hl.get_monitors({ all = true })) do
		partes[#partes + 1] = string.format("%s%s@%d,%d", m.name, m.enabled and "" or "(off)", m.x, m.y)
	end
	return table.concat(partes, " ")
end

-- Cualquier monitor sin regla propia
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })

-- ============================================
-- JSON mínimo (el Lua de Hyprland no trae decodificador)
-- ============================================

local function leer_json(texto)
	local pos = 1

	local function espacios()
		pos = texto:find("[^ \t\r\n]", pos) or #texto + 1
	end

	local valor

	local function cadena()
		local partes = {}
		pos = pos + 1 -- comilla de apertura
		while true do
			local c = texto:sub(pos, pos)
			if c == "" then
				error("cadena sin cerrar")
			elseif c == '"' then
				pos = pos + 1
				return table.concat(partes)
			elseif c == "\\" then
				local e = texto:sub(pos + 1, pos + 1)
				if e == "u" then
					partes[#partes + 1] = utf8.char(tonumber(texto:sub(pos + 2, pos + 5), 16))
					pos = pos + 6
				else
					local escapes = { b = "\b", f = "\f", n = "\n", r = "\r", t = "\t" }
					partes[#partes + 1] = escapes[e] or e
					pos = pos + 2
				end
			else
				partes[#partes + 1] = c
				pos = pos + 1
			end
		end
	end

	function valor()
		espacios()
		local c = texto:sub(pos, pos)
		if c == "{" then
			local t = {}
			pos = pos + 1
			espacios()
			if texto:sub(pos, pos) == "}" then
				pos = pos + 1
				return t
			end
			while true do
				espacios()
				local k = cadena()
				espacios()
				pos = pos + 1 -- dos puntos
				t[k] = valor()
				espacios()
				local sep = texto:sub(pos, pos)
				pos = pos + 1
				if sep == "}" then
					return t
				end
			end
		elseif c == "[" then
			local t = {}
			pos = pos + 1
			espacios()
			if texto:sub(pos, pos) == "]" then
				pos = pos + 1
				return t
			end
			while true do
				t[#t + 1] = valor()
				espacios()
				local sep = texto:sub(pos, pos)
				pos = pos + 1
				if sep == "]" then
					return t
				end
			end
		elseif c == '"' then
			return cadena()
		elseif texto:sub(pos, pos + 3) == "true" then
			pos = pos + 4
			return true
		elseif texto:sub(pos, pos + 4) == "false" then
			pos = pos + 5
			return false
		elseif texto:sub(pos, pos + 3) == "null" then
			pos = pos + 4
			return nil
		else
			local num = texto:match("^-?[%d%.eE+-]+", pos)
			if not num then
				error("JSON no válido en la posición " .. pos)
			end
			pos = pos + #num
			return tonumber(num)
		end
	end

	return valor()
end

local function cargar_perfiles()
	local f = io.open(ARCHIVO, "r")
	if not f then
		return {}
	end
	local texto = f:read("a")
	f:close()
	local ok, datos = pcall(leer_json, texto)
	if not ok or type(datos) ~= "table" then
		return {}
	end
	return datos.perfiles or {}
end

-- ============================================
-- Monitores conectados
-- ============================================

local function es_interno(nombre)
	return nombre:match("^eDP") or nombre:match("^LVDS") or nombre:match("^DSI")
end

-- Monitores conectados (también los apagados), con su identificador estable.
-- Si dos son idénticos y no informan número de serie, se les añade el puerto
-- para distinguirlos. display_panel.py hace exactamente lo mismo.
-- FALLBACK: pantalla virtual que Hyprland crea cuando no queda ninguna
-- encendida. No es un monitor: no se le aplican reglas ni cuenta en la clave
function es_virtual(nombre)
	return nombre == "FALLBACK" or nombre:match("^HEADLESS") ~= nil
end

local function conectados()
	local lista = {}
	local repetidos = {}
	for _, m in ipairs(hl.get_monitors({ all = true })) do
		if es_virtual(m.name) then
			goto siguiente
		end
		repetidos[m.description] = (repetidos[m.description] or 0) + 1
		lista[#lista + 1] = {
			nombre = m.name,
			desc = m.description,
			-- Tamaño lógico: con escala 1,5 un 1920 ocupa 1280
			ancho = math.floor(m.width / (m.scale > 0 and m.scale or 1) + 0.5),
			alto = math.floor(m.height / (m.scale > 0 and m.scale or 1) + 0.5),
		}
		::siguiente::
	end
	for _, m in ipairs(lista) do
		m.id = repetidos[m.desc] > 1 and (m.desc .. " @ " .. m.nombre) or m.desc
	end
	-- Internos primero y luego por puerto: orden fijo para la disposición por defecto
	table.sort(lista, function(a, b)
		local ia, ib = es_interno(a.nombre) and 0 or 1, es_interno(b.nombre) and 0 or 1
		if ia ~= ib then
			return ia < ib
		end
		return a.nombre < b.nombre
	end)
	return lista
end

local function clave(lista)
	local ids = {}
	for _, m in ipairs(lista) do
		ids[#ids + 1] = m.id
	end
	table.sort(ids)
	return table.concat(ids, " + ")
end

-- ============================================
-- Aplicar
-- ============================================

-- Las reglas no se aplican al momento: se juntan en `pendientes` y luego
-- ejecutar() las aplica en un orden que nunca deja dos pantallas encendidas
-- una encima de otra (Hyprland avisa con "Your monitor layout is set up
-- incorrectly") ni a Hyprland sin ninguna pantalla.
local pendientes = {}

local function apagar(m)
	pendientes[#pendientes + 1] = { output = m.nombre, disabled = true }
end

local function regla(m, extra)
	local base = BASE[m.nombre] or { mode = "preferred", scale = 1 }
	local spec = {
		output = m.nombre,
		mode = base.mode,
		scale = base.scale,
		position = "0x0",
		mirror = "", -- vacío deshace un duplicado anterior
		disabled = false,
	}
	for k, v in pairs(extra or {}) do
		spec[k] = v
	end
	pendientes[#pendientes + 1] = spec
end

-- Hyprland no aplica las reglas de monitor al momento ni en el orden en que
-- llegan: las junta y reconfigura todo un instante después. Por eso cada
-- paso va por separado, con una pausa entre uno y otro:
--   1. encender las que van a quedar encendidas y ahora no lo están,
--      apartadas a la derecha de todo para no pisar a nadie
--   2. apagar las que sobran
--   3. colocar cada una en su sitio
--   4. red de seguridad: si no quedó ninguna pantalla encendida, encender una
-- Una aplicación nueva cancela la que esté a medias.
local PAUSA_MS = 400
local generacion = 0
local temporizador = nil

local function encendidos()
	local t = {}
	for _, m in ipairs(hl.get_monitors({ all = true })) do
		if m.enabled and not m.is_mirror and not es_virtual(m.name) then
			t[m.name] = m
		end
	end
	return t
end

local function ancho_logico(m)
	return math.floor(m.width / (m.scale > 0 and m.scale or 1) + 0.5)
end

local function copia(spec, cambios)
	local t = {}
	for k, v in pairs(spec) do
		t[k] = v
	end
	for k, v in pairs(cambios or {}) do
		t[k] = v
	end
	return t
end

local function ejecutar(specs, rescate)
	generacion = generacion + 1
	local mia = generacion

	local activos = encendidos()
	local borde = 0
	for _, m in pairs(activos) do
		borde = math.max(borde, m.x + ancho_logico(m))
	end

	local apagadas, finales = {}, {}
	for _, spec in ipairs(specs) do
		if spec.disabled then
			apagadas[#apagadas + 1] = spec
		else
			finales[#finales + 1] = spec
		end
	end

	-- Paso 1: lo que va a quedar encendido y ahora no lo está, a la derecha
	-- de todo
	local provisionales = {}
	local minimo = math.huge
	for _, spec in ipairs(finales) do
		if not activos[spec.output] then
			minimo = math.min(minimo, tonumber(spec.position:match("^(-?%d+)x")) or 0)
		end
	end
	for _, spec in ipairs(finales) do
		if not activos[spec.output] then
			local x, y = spec.position:match("^(-?%d+)x(-?%d+)$")
			provisionales[#provisionales + 1] = copia(spec, {
				position = (tonumber(x or 0) - minimo + borde) .. "x" .. (y or 0),
			})
		end
	end

	local fases = {}
	local function fase(nombre, lista)
		if #lista > 0 then
			fases[#fases + 1] = { nombre = nombre, lista = lista }
		end
	end
	fase("provisional", provisionales)
	fase("apagar", apagadas)
	fase("colocar", finales)

	local function siguiente(i)
		if mia ~= generacion then
			return -- llegó otra aplicación más nueva
		end
		local f = fases[i]
		if f then
			for _, spec in ipairs(f.lista) do
				registrar(string.format("  [%s] %s pos=%s off=%s", f.nombre, spec.output,
					tostring(spec.position), tostring(spec.disabled)))
				hl.monitor(spec)
			end
		else
			-- Paso 4: red de seguridad
			if next(encendidos()) == nil and rescate then
				registrar("  [rescate] ninguna pantalla encendida: se enciende " .. rescate.output)
				hl.monitor(rescate)
			end
			temporizador = nil
			return
		end
		temporizador = hl.timer(function()
			siguiente(i + 1)
		end, { timeout = PAUSA_MS, type = "oneshot" })
	end
	siguiente(1)
end

local function extender(lista, perfil)
	local posiciones = perfil and perfil.monitores or {}

	-- Si falta la posición de alguno (monitor nuevo), se recoloca todo:
	-- los internos a la izquierda y los demás a su derecha, en fila
	local completas = true
	for _, m in ipairs(lista) do
		local p = posiciones[m.id]
		if type(p) ~= "table" or type(p.x) ~= "number" or type(p.y) ~= "number" then
			completas = false
		end
	end

	-- Posiciones guardadas con otra escala pueden dejar un monitor encima de
	-- otro: en ese caso también se recoloca todo en fila
	if completas then
		for i, a in ipairs(lista) do
			for j = i + 1, #lista do
				local b = lista[j]
				local pa, pb = posiciones[a.id], posiciones[b.id]
				if pa.x < pb.x + b.ancho and pb.x < pa.x + a.ancho
					and pa.y < pb.y + b.alto and pb.y < pa.y + a.alto then
					completas = false
				end
			end
		end
	end

	local x = 0
	for _, m in ipairs(lista) do
		local px, py
		if completas then
			px, py = posiciones[m.id].x, posiciones[m.id].y
		else
			px, py = x, 0
			x = x + m.ancho
		end
		regla(m, { position = math.floor(px) .. "x" .. math.floor(py) })
	end
end

local ultima_clave = nil

local function aplicar_modo(lista, perfil)
	local modo = perfil and perfil.modo or "extender"

	if #lista == 1 then
		regla(lista[1])
		return
	end

	-- Cualquier otro modo (p. ej. un "duplicar" guardado antes de quitarlo) extiende
	if modo == "solo" then
		local elegido = nil
		for _, m in ipairs(lista) do
			if m.id == perfil.solo then
				elegido = m
			end
		end
		if not elegido then
			-- El monitor elegido ya no está: mejor extender que dejar todo a oscuras
			extender(lista, perfil)
			return
		end
		regla(elegido)
		for _, m in ipairs(lista) do
			if m ~= elegido then
				apagar(m)
			end
		end
	else
		extender(lista, perfil)
	end
end

-- modo_forzado: aplica ese modo sin tocar el perfil guardado (rescate)
function MonitoresAplicar(forzar, modo_forzado)
	local todos = conectados()
	if #todos == 0 then
		return
	end

	-- Tapa cerrada: la interna queda fuera, salvo que sea la única pantalla
	local lista, cerrados = {}, {}
	for _, m in ipairs(todos) do
		if tapa_cerrada and es_interno(m.nombre) then
			cerrados[#cerrados + 1] = m
		else
			lista[#lista + 1] = m
		end
	end
	if #lista == 0 then
		lista, cerrados = todos, {}
	end

	local k = clave(lista)
	-- Apagar un monitor también lanza monitor.removed/added:
	-- si la combinación no cambió, no hay nada que hacer
	if k == ultima_clave and not forzar then
		return
	end
	ultima_clave = k
	registrar(string.format("aplicar tapa=%s forzar=%s clave=[%s] antes: %s",
		tostring(tapa_cerrada), tostring(forzar), k, estado_actual()))

	local perfil = cargar_perfiles()[k]
	if modo_forzado then
		perfil = copia(perfil or {}, { modo = modo_forzado })
	end

	pendientes = {}
	aplicar_modo(lista, perfil)
	for _, m in ipairs(cerrados) do
		apagar(m)
	end

	-- Si al final no queda ninguna pantalla encendida, se enciende esta
	local base = BASE[lista[1].nombre] or { mode = "preferred", scale = 1 }
	local rescate = { output = lista[1].nombre, mode = base.mode, scale = base.scale,
		position = "0x0", mirror = "", disabled = false }

	ejecutar(pendientes, rescate)
end

-- Super+Shift+P: si algo sale mal y no se ve nada, extender en todas las
-- pantallas (sin cambiar el perfil guardado; para guardarlo, elegir
-- "Extend" en el panel)
function MonitoresRescate()
	registrar("rescate (Super+Shift+P)")
	pcall(MonitoresAplicar, true, "extender")
end

hl.bind("SUPER + SHIFT + P", MonitoresRescate, { locked = true })

local function aplicar_si_cambia()
	registrar("evento de monitor: " .. estado_actual())
	-- pcall: un perfil roto no debe tumbar el manejador de eventos
	pcall(MonitoresAplicar, false)
end

hl.on("monitor.added", aplicar_si_cambia)
hl.on("monitor.removed", aplicar_si_cambia)

-- Abrir y cerrar la tapa. locked: también con la pantalla bloqueada.
-- MonitoresTapa(true|false) también sirve para probarlo con hyprctl eval.
function MonitoresTapa(cerrada)
	registrar(cerrada and "tapa cerrada" or "tapa abierta")
	tapa_cerrada = cerrada
	pcall(MonitoresAplicar, true)
end

hl.bind("switch:on:Lid Switch", function()
	MonitoresTapa(true)
end, { locked = true })
hl.bind("switch:off:Lid Switch", function()
	MonitoresTapa(false)
end, { locked = true })

-- Al cargar (o recargar) la configuración, aplicar siempre
pcall(MonitoresAplicar, true)
