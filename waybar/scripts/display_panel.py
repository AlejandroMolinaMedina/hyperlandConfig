#!/usr/bin/env python3
# ~/.config/waybar/scripts/display_panel.py
#
# Sección "Displays" del panel de brillo y volumen (media_panel.py), al estilo
# de Windows (Win+P y "Configuración de pantalla"): elegir el modo (extender,
# duplicar o usar solo una pantalla) y, al extender, colocar los monitores
# arrastrándolos.
#
# Lo que se elige se guarda por combinación de monitores conectados en
# ~/.config/hypr/monitores.json y lo aplica hypr/conf/monitores.lua, que
# además lo recupera solo al volver a conectar esa misma combinación.
#
# Con un solo monitor conectado la sección no se muestra.

import json
import os
import subprocess

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Gdk, Gio, GLib, Gtk, PangoCairo

# ============================================
# Ajustes
# ============================================

ALTO_LIENZO = 150      # zona donde se dibujan y arrastran los monitores
IMAN = 12              # px del lienzo para que un borde se alinee solo
SOLAPE_MINIMO = 120    # px reales que dos monitores vecinos deben compartir

PERFILES = os.path.expanduser("~/.config/hypr/monitores.json")

ICONO_EXTENDER = "\U000F037A"   # monitor-multiple
ICONO_DUPLICAR = "\U000F018F"   # content-copy
ICONO_PORTATIL = "\U000F0322"   # laptop
ICONO_MONITOR = "\U000F0379"    # monitor


CSS = """
.lienzo {
    background: rgba(0, 0, 0, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
}

.pista {
    color: rgba(255, 255, 255, 0.72);
    font-size: 0.8rem;
}

/* Botones de modo, en fila: mismo acabado que las salidas de audio */
.modo {
    background: transparent;
    border: none;
    box-shadow: none;
    border-radius: 8px;
    padding: 6px 2px;
    color: #cdd6f4;
}

.modo:hover { background: rgba(255, 255, 255, 0.1); }

.modo-activo {
    background: rgba(255, 255, 255, 0.15);
    box-shadow: inset 0 -2px #ffffff;
}

.modo-texto { color: #cdd6f4; font-size: 0.8rem; }
"""


def lanzar(orden):
    """Ejecuta sin esperar ni dejar procesos zombis."""
    try:
        proceso = Gio.Subprocess.new(
            orden, Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE
        )
    except GLib.Error:
        return
    proceso.wait_async(None, lambda p, r: p.wait_finish(r))


# ============================================
# Estado de Hyprland
# ============================================

def es_interno(nombre):
    return nombre.startswith(("eDP", "LVDS", "DSI"))


class Monitor:
    def __init__(self, datos):
        self.nombre = datos["name"]
        self.desc = datos.get("description") or self.nombre
        self.modelo = datos.get("model") or ""
        self.activo = not datos.get("disabled", False)
        self.espejo = str(datos.get("mirrorOf", "none")) not in ("none", "")
        self.x = datos.get("x", 0)
        self.y = datos.get("y", 0)
        escala = datos.get("scale") or 1
        ancho, alto = datos.get("width", 1920), datos.get("height", 1080)
        if datos.get("transform", 0) % 2 == 1:   # girado 90° o 270°
            ancho, alto = alto, ancho
        # Tamaño lógico, el que cuenta para las posiciones
        self.ancho = round(ancho / escala)
        self.alto = round(alto / escala)
        self.resolucion = f"{datos.get('width', 0)}×{datos.get('height', 0)}"
        self.id = self.desc   # se corrige en leer_monitores() si hay repetidos

    @property
    def titulo(self):
        if es_interno(self.nombre):
            return "Laptop"
        return self.modelo if self.modelo and not self.modelo.startswith("0x") else self.nombre


def leer_monitores():
    try:
        salida = subprocess.run(
            ["hyprctl", "-j", "monitors", "all"], capture_output=True, text=True, timeout=3
        ).stdout
        monitores = [Monitor(d) for d in json.loads(salida)]
    except (OSError, subprocess.SubprocessError, ValueError):
        return []
    # Mismo criterio que hypr/conf/monitores.lua: dos monitores idénticos sin
    # número de serie se distinguen por el puerto
    cuenta = {}
    for m in monitores:
        cuenta[m.desc] = cuenta.get(m.desc, 0) + 1
    for m in monitores:
        if cuenta[m.desc] > 1:
            m.id = f"{m.desc} @ {m.nombre}"
    monitores.sort(key=lambda m: (0 if es_interno(m.nombre) else 1, m.nombre))
    return monitores


def clave(monitores):
    return " + ".join(sorted(m.id for m in monitores))


def modo_actual(monitores):
    """Lo que se ve ahora mismo: ("duplicar"|"solo"|"extender", monitor solo)."""
    if any(m.espejo for m in monitores):
        return "duplicar", None
    activos = [m for m in monitores if m.activo]
    if len(monitores) > 1 and len(activos) == 1:
        return "solo", activos[0]
    return "extender", None


def cargar_perfiles():
    try:
        with open(PERFILES) as f:
            datos = json.load(f)
    except (OSError, ValueError):
        datos = {}
    if not isinstance(datos.get("perfiles"), dict):
        datos["perfiles"] = {}
    return datos


def guardar_perfil(monitores, cambios):
    """Mezcla los cambios en el perfil de esta combinación y lo aplica."""
    datos = cargar_perfiles()
    perfil = datos["perfiles"].setdefault(clave(monitores), {})
    perfil.update(cambios)
    if perfil.get("modo") != "solo":
        perfil.pop("solo", None)

    # Escritura atómica: Hyprland nunca lee un archivo a medias
    temporal = PERFILES + ".tmp"
    with open(temporal, "w") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temporal, PERFILES)

    lanzar(["hyprctl", "eval", "MonitoresAplicar(true)"])


# ============================================
# Colocar monitores: imán contra los bordes de los vecinos
# ============================================

def solapan(a, b):
    """True si dos rectángulos (x, y, ancho, alto) se pisan por dentro."""
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def encajar(propuesto, ancho, alto, otros, iman):
    """Busca la posición más cercana a `propuesto` en la que el monitor toque
    a algún vecino por un lado, sin pisar a ninguno. Como en Windows, no se
    pueden dejar huecos entre pantallas."""
    px, py = propuesto
    candidatos = []
    for (ox, oy, ow, oh) in otros:
        minimo = min(SOLAPE_MINIMO, ancho, alto, ow, oh)

        def a_lo_largo(valor, inicio, largo_otro, largo_propio):
            # Recorrido posible pegado a ese lado, con imán a los bordes y al centro
            valor = max(inicio - largo_propio + minimo, min(inicio + largo_otro - minimo, valor))
            alineados = (inicio, inicio + largo_otro - largo_propio,
                         inicio + (largo_otro - largo_propio) // 2)
            cercano = min(alineados, key=lambda a: abs(valor - a))
            return cercano if abs(valor - cercano) <= iman else valor

        candidatos.append((ox + ow, a_lo_largo(py, oy, oh, alto)))       # a la derecha
        candidatos.append((ox - ancho, a_lo_largo(py, oy, oh, alto)))    # a la izquierda
        candidatos.append((a_lo_largo(px, ox, ow, ancho), oy + oh))      # debajo
        candidatos.append((a_lo_largo(px, ox, ow, ancho), oy - alto))    # encima

    candidatos.sort(key=lambda c: (c[0] - px) ** 2 + (c[1] - py) ** 2)
    for cx, cy in candidatos:
        if not any(solapan((cx, cy, ancho, alto), o) for o in otros):
            return round(cx), round(cy)
    return None


# ============================================
# Lienzo con los monitores
# ============================================

class Lienzo(Gtk.DrawingArea):
    """Dibuja la disposición. En modo extender se puede arrastrar cada
    monitor; al soltarlo se pega al vecino más cercano y se guarda."""

    def __init__(self, al_mover):
        super().__init__()
        self.get_style_context().add_class("lienzo")
        self.set_size_request(-1, ALTO_LIENZO)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
                        | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self._dibujar)
        self.connect("button-press-event", self._pulsar)
        self.connect("motion-notify-event", self._mover)
        self.connect("button-release-event", self._soltar)
        self.connect("leave-notify-event", self._salir)

        self.al_mover = al_mover
        self.rects = []          # [monitor, x, y] en píxeles reales
        self.titulos = {}        # textos que se pintan dentro de cada rectángulo
        self.atenuados = set()   # monitores apagados en el modo actual
        self.editable = False
        self.arrastre = None     # (índice, desfase x, desfase y)
        self.encima = None
        self.vista = None        # (escala, desplazamiento x, desplazamiento y)

    def poner(self, rects, editable, titulos=None, atenuados=()):
        self.rects = [[m, x, y] for m, x, y in rects]
        self.editable = editable
        self.titulos = titulos or {}
        self.atenuados = set(atenuados)
        self.arrastre = None
        self.vista = None
        self.queue_draw()

    # -- geometría ----------------------------------------------

    def _calcular_vista(self):
        ancho, alto = self.get_allocated_width(), self.get_allocated_height()
        if not self.rects:
            return 1, 0, 0
        x0 = min(x for _m, x, _y in self.rects)
        y0 = min(y for _m, _x, y in self.rects)
        x1 = max(x + m.ancho for m, x, _y in self.rects)
        y1 = max(y + m.alto for m, _x, y in self.rects)
        margen = 22
        # Hueco de sobra para poder arrastrar hacia cualquier lado
        escala = min((ancho - 2 * margen) / max(1, x1 - x0), (alto - 2 * margen) / max(1, y1 - y0))
        escala = min(escala, 0.09) if len(self.rects) > 1 else min(escala, 0.07)
        dx = (ancho - (x1 - x0) * escala) / 2 - x0 * escala
        dy = (alto - (y1 - y0) * escala) / 2 - y0 * escala
        return escala, dx, dy

    def _en_pantalla(self, m, x, y):
        escala, dx, dy = self.vista
        return x * escala + dx, y * escala + dy, m.ancho * escala, m.alto * escala

    def _indice_en(self, px, py):
        if self.vista is None:
            return None
        for i in reversed(range(len(self.rects))):
            sx, sy, sw, sh = self._en_pantalla(*self.rects[i])
            if sx <= px <= sx + sw and sy <= py <= sy + sh:
                return i
        return None

    # -- dibujo -------------------------------------------------

    @staticmethod
    def _rectangulo_redondeado(cr, x, y, w, h, r):
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -1.5708, 0)
        cr.arc(x + w - r, y + h - r, r, 0, 1.5708)
        cr.arc(x + r, y + h - r, r, 1.5708, 3.1416)
        cr.arc(x + r, y + r, r, 3.1416, 4.7124)
        cr.close_path()

    def _texto(self, cr, texto, cx, cy, tam, alfa):
        capa = self.create_pango_layout("")
        capa.set_markup(f"<span size='{tam}'>{GLib.markup_escape_text(texto)}</span>", -1)
        _tinta, logico = capa.get_pixel_extents()
        x, y = cx - logico.width / 2, cy - logico.height / 2
        cr.set_source_rgba(0, 0, 0, 0.45 * alfa)   # sombra, como el resto de la barra
        cr.move_to(x, y + 1)
        PangoCairo.show_layout(cr, capa)
        cr.set_source_rgba(0.804, 0.839, 0.957, alfa)   # #cdd6f4
        cr.move_to(x, y)
        PangoCairo.show_layout(cr, capa)

    def _dibujar(self, _widget, cr):
        if self.arrastre is None:
            self.vista = self._calcular_vista()
        for i, (m, x, y) in enumerate(self.rects):
            sx, sy, sw, sh = self._en_pantalla(m, x, y)
            apagado = m.id in self.atenuados
            resaltado = self.editable and (i == self.encima or (self.arrastre and self.arrastre[0] == i))

            self._rectangulo_redondeado(cr, sx + 1, sy + 1, sw - 2, sh - 2, 6)
            if apagado:
                cr.set_source_rgba(1, 1, 1, 0.05)
                cr.fill_preserve()
                cr.set_source_rgba(1, 1, 1, 0.25)
                cr.set_dash([4, 3])
            else:
                cr.set_source_rgba(1, 1, 1, 0.32 if resaltado else 0.18)
                cr.fill_preserve()
                cr.set_source_rgba(1, 1, 1, 0.85 if resaltado else 0.45)
                cr.set_dash([])
            cr.set_line_width(1.5)
            cr.stroke()
            cr.set_dash([])

            alfa = 0.5 if apagado else 1
            titulo = self.titulos.get(m.id, m.titulo)
            self._texto(cr, titulo, sx + sw / 2, sy + sh / 2 - 7, "medium", alfa)
            detalle = "Off" if apagado else m.resolucion
            self._texto(cr, detalle, sx + sw / 2, sy + sh / 2 + 10, "small", alfa * 0.75)
        return False

    # -- arrastre -----------------------------------------------

    def _pulsar(self, _w, evento):
        if not self.editable or evento.button != 1:
            return False
        i = self._indice_en(evento.x, evento.y)
        if i is None:
            return False
        sx, sy, _sw, _sh = self._en_pantalla(*self.rects[i])
        self.arrastre = (i, evento.x - sx, evento.y - sy)
        # El que se arrastra se pinta encima de los demás
        self.rects.append(self.rects.pop(i))
        self.arrastre = (len(self.rects) - 1, self.arrastre[1], self.arrastre[2])
        self.encima = len(self.rects) - 1
        self.queue_draw()
        return True

    def _mover(self, _w, evento):
        if self.arrastre is None:
            encima = self._indice_en(evento.x, evento.y) if self.editable else None
            if encima != self.encima:
                self.encima = encima
                ventana = self.get_window()
                if ventana is not None:
                    cursor = Gdk.Cursor.new_from_name(self.get_display(), "grab") if encima is not None else None
                    ventana.set_cursor(cursor)
                self.queue_draw()
            return False
        i, ox, oy = self.arrastre
        escala, dx, dy = self.vista
        self.rects[i][1] = round((evento.x - ox - dx) / escala)
        self.rects[i][2] = round((evento.y - oy - dy) / escala)
        self.queue_draw()
        return True

    def _soltar(self, _w, evento):
        if self.arrastre is None:
            return False
        i = self.arrastre[0]
        escala = self.vista[0]
        m, x, y = self.rects[i]
        otros = [(r[1], r[2], r[0].ancho, r[0].alto) for j, r in enumerate(self.rects) if j != i]
        sitio = encajar((x, y), m.ancho, m.alto, otros, IMAN / escala)
        if sitio is not None:
            self.rects[i][1], self.rects[i][2] = sitio
        self.arrastre = None
        self.queue_draw()
        if sitio is not None:
            self.al_mover({r[0].id: (r[1], r[2]) for r in self.rects})
        return True

    def _salir(self, *_):
        if self.arrastre is None and self.encima is not None:
            self.encima = None
            self.queue_draw()
        return False


# ============================================
# Sección del panel
# ============================================

class SeccionPantallas(Gtk.Box):
    """Separador + "Displays" + lienzo + fila de modos. El panel que la
    contiene llama a refrescar() al abrirse; al_cerrar() lo oculta."""

    def __init__(self, al_cerrar):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        # El panel hace show_all(): esta sección decide sola si se ve
        self.set_no_show_all(True)
        self.al_cerrar = al_cerrar
        self.monitores = []

        separador = Gtk.Box()
        separador.get_style_context().add_class("separador")
        self.pack_start(separador, False, False, 0)

        titulo = Gtk.Label(label="Displays", xalign=0)
        titulo.get_style_context().add_class("titulo")
        self.pack_start(titulo, False, False, 0)

        self.lienzo = Lienzo(self._al_mover)
        self.pack_start(self.lienzo, False, False, 0)

        self.pista = Gtk.Label(xalign=0)
        self.pista.get_style_context().add_class("pista")
        self.pack_start(self.pista, False, False, 0)

        self.fila_modos = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, homogeneous=True)
        self.pack_start(self.fila_modos, False, False, 0)

    # -- refresco -----------------------------------------------

    def refrescar(self):
        self.monitores = leer_monitores()
        if len(self.monitores) < 2:
            self.hide()
            return GLib.SOURCE_REMOVE
        modo, solo = modo_actual(self.monitores)
        self._pintar_lienzo(modo, solo)
        self._pintar_modos(modo, solo)
        # show_all() no hace nada sobre un widget con no_show_all activado
        self.set_no_show_all(False)
        self.show_all()
        self.set_no_show_all(True)
        return GLib.SOURCE_REMOVE

    def _posiciones_extendidas(self):
        """Dónde quedaría cada monitor al extender: lo que se ve ahora si ya
        se está extendiendo; si no, lo guardado o, en su defecto, en fila."""
        modo, _solo = modo_actual(self.monitores)
        if modo == "extender":
            return [(m, m.x, m.y) for m in self.monitores]
        guardado = cargar_perfiles()["perfiles"].get(clave(self.monitores), {}).get("monitores", {})
        if all(m.id in guardado for m in self.monitores):
            return [(m, guardado[m.id]["x"], guardado[m.id]["y"]) for m in self.monitores]
        rects, x = [], 0
        for m in self.monitores:
            rects.append((m, x, 0))
            x += m.ancho
        return rects

    def _pintar_lienzo(self, modo, solo):
        if modo == "duplicar":
            original = next((m for m in self.monitores if not m.espejo), self.monitores[0])
            titulo = " = ".join(m.titulo for m in self.monitores)
            self.lienzo.poner([(original, 0, 0)], False, {original.id: titulo})
            self.pista.set_text("Same image on every display")
            return
        rects = self._posiciones_extendidas()
        if modo == "solo":
            apagados = [m.id for m in self.monitores if m is not solo]
            self.lienzo.poner(rects, False, atenuados=apagados)
            self.pista.set_text(f"Only {solo.titulo} is on")
            return
        self.lienzo.poner(rects, True)
        self.pista.set_text("Drag a display to move it")

    def _pintar_modos(self, modo, solo):
        for hijo in self.fila_modos.get_children():
            self.fila_modos.remove(hijo)

        opciones = [
            (ICONO_EXTENDER, "Extend", "One desktop across every display",
             modo == "extender", {"modo": "extender"}),
            (ICONO_DUPLICAR, "Duplicate", "Same image on every display",
             modo == "duplicar", {"modo": "duplicar"}),
        ]
        for m in self.monitores:
            icono = ICONO_PORTATIL if es_interno(m.nombre) else ICONO_MONITOR
            opciones.append((icono, m.titulo, f"Only {m.titulo} ({m.nombre} · {m.resolucion})",
                             modo == "solo" and solo is m, {"modo": "solo", "solo": m.id}))

        for icono_txt, titulo, detalle, activo, cambios in opciones:
            boton = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
            boton.get_style_context().add_class("modo")
            if activo:
                boton.get_style_context().add_class("modo-activo")
            boton.set_tooltip_text(detalle)
            boton.connect("clicked", self._elegir_modo, cambios)

            caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            icono = Gtk.Label(label=icono_txt)
            icono.get_style_context().add_class("icono")
            caja.pack_start(icono, False, False, 0)
            texto = Gtk.Label(label=titulo)
            texto.get_style_context().add_class("modo-texto")
            texto.set_ellipsize(3)   # PANGO_ELLIPSIZE_END
            texto.set_max_width_chars(9)
            caja.pack_start(texto, False, False, 0)

            boton.add(caja)
            self.fila_modos.pack_start(boton, True, True, 0)

    # -- acciones -----------------------------------------------

    def _elegir_modo(self, _boton, cambios):
        if not self.monitores:
            return
        guardar_perfil(self.monitores, dict(cambios))
        if cambios["modo"] == "extender":
            # Sigue abierto para poder colocar las pantallas
            GLib.timeout_add(900, self.refrescar)
        else:
            # Duplicar o apagar una pantalla puede quitar justo aquella en la
            # que está el panel: se cierra, como el Win+P de Windows
            self.al_cerrar()

    def _al_mover(self, posiciones):
        guardar_perfil(self.monitores, {
            "modo": "extender",
            "monitores": {i: {"x": x, "y": y} for i, (x, y) in posiciones.items()},
        })
        GLib.timeout_add(900, self.refrescar)
