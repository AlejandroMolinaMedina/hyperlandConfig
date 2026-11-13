-- ~/.config/hypr/conf/monitores.lua
--
-- Monitores, al estilo de Windows: cada combinación de pantallas conectadas
-- recuerda su modo (extender, duplicar o solo una) y la posición de cada una.
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
--       "modo": "extender" | "duplicar" | "solo",
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
local function conectados()
	local lista = {}
	local repetidos = {}
	for _, m in ipairs(hl.get_monitors({ all = true })) do
		repetidos[m.description] = (repetidos[m.description] or 0) + 1
		lista[#lista + 1] = {
			nombre = m.name,
			desc = m.description,
			-- Tamaño lógico: con escala 1,5 un 1920 ocupa 1280
			ancho = math.floor(m.width / (m.scale > 0 and m.scale or 1) + 0.5),
			alto = math.floor(m.height / (m.scale > 0 and m.scale or 1) + 0.5),
		}
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
	hl.monitor(spec)
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

function MonitoresAplicar(forzar)
	local lista = conectados()
	if #lista == 0 then
		return
	end
	local k = clave(lista)
	-- Apagar o duplicar un monitor también lanza monitor.removed/added:
	-- si la combinación no cambió, no hay nada que hacer
	if k == ultima_clave and not forzar then
		return
	end
	ultima_clave = k

	local perfil = cargar_perfiles()[k]
	local modo = perfil and perfil.modo or "extender"

	if #lista == 1 then
		regla(lista[1])
		return
	end

	if modo == "duplicar" then
		-- La interna (o la primera) es la original; las demás la copian
		local original = lista[1]
		regla(original)
		for i = 2, #lista do
			regla(lista[i], { mirror = original.nombre })
		end
	elseif modo == "solo" then
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
				hl.monitor({ output = m.nombre, disabled = true })
			end
		end
	else
		extender(lista, perfil)
	end
end

local function aplicar_si_cambia()
	-- pcall: un perfil roto no debe tumbar el manejador de eventos
	pcall(MonitoresAplicar, false)
end

hl.on("monitor.added", aplicar_si_cambia)
hl.on("monitor.removed", aplicar_si_cambia)

-- Al cargar (o recargar) la configuración, aplicar siempre
pcall(MonitoresAplicar, true)
