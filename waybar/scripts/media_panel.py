#!/usr/bin/env python3
# ~/.config/waybar/scripts/media_panel.py
#
# Panel de brillo, volumen y salida de audio para Waybar/Hyprland.
# Se abre bajo el carrusel de brillo/volumen de la barra.
#
# Arranca oculto. Señales:
#   SIGUSR1 -> mostrar u ocultar
#   SIGUSR2 -> ocultar
# Uso desde Waybar (clic en custom/carousel#media):
#   pkill -USR1 -f '^python3 .*media_panel.py$'

import glob
import json
import os
import signal
import subprocess
import threading
import time

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")

from gi.repository import Gdk, Gio, GLib, Gtk, GtkLayerShell

# ============================================
# Ajustes
# ============================================

ANCHO = 360            # ancho de la tarjeta
MARGEN_DERECHA = 250   # deja el panel centrado bajo el carrusel de la barra
HUECO = 8              # separación con la barra

BRILLO_MINIMO = 1      # nunca apagar del todo la pantalla
VOLUMEN_MAXIMO = 100   # el sonido nunca pasa de aquí, venga de donde venga

# swaync y el panel del calendario: se cierran al abrir este
SWAYNC_NOMBRE = "org.erikreider.swaync.cc"
SWAYNC_RUTA = "/org/erikreider/swaync/cc"
CALENDARIO = "^python3 .*calendar_panel.py$"

# Iconos (JetBrainsMono Nerd Font, los mismos juegos que usa la barra)
ICONO_BRILLO = ""                                   # sol
ICONOS_VOLUMEN = ["\U000F057F", "\U000F0580", "\U000F057E"]
ICONO_MUDO = "\U000F0581"
ICONO_BLUETOOTH = ""
ICONO_AURICULARES = ""
ICONO_ALTAVOZ = "\U000F057E"
ICONO_PANTALLA = ""
ICONO_USB = ""
ICONO_ACTIVO = ""                                   # palomita


CSS = """
window.media-panel { background: transparent; }
window.fondo-clic { background: transparent; }

/* Mismo acabado que la barra: velo blanco en degradado, nada de negro.
   La sombra del texto lo mantiene legible sobre cualquier fondo. */
.tarjeta {
    background: linear-gradient(to bottom,
                rgba(255, 255, 255, 0.34),
                rgba(255, 255, 255, 0.20));
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 10px;
    padding: 14px;
    color: #cdd6f4;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.titulo {
    color: rgba(255, 255, 255, 0.72);
    font-size: 0.85rem;
    margin-bottom: 2px;
}

.icono { font-size: 1.15rem; color: #cdd6f4; }
.valor { color: #cdd6f4; font-weight: bold; }

.mudo .icono, .mudo .valor { color: rgba(255, 255, 255, 0.72); }

/* background-image: none es imprescindible; el tema lo pinta sobre el color */
scale trough {
    background-color: rgba(255, 255, 255, 0.15);
    background-image: none;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    min-height: 8px;
}

scale highlight {
    background-color: #cdd6f4;
    background-image: none;
    border: none;
    border-radius: 10px;
}

scale slider {
    background-color: #ffffff;
    background-image: none;
    border: none;
    box-shadow: none;
    border-radius: 50%;
    min-width: 14px;
    min-height: 14px;
    margin: -6px;
}

.mudo scale highlight { background-color: rgba(255, 255, 255, 0.72); }

.separador {
    background: rgba(255, 255, 255, 0.12);
    min-height: 1px;
    margin: 4px 0;
}

.salida {
    background: transparent;
    border: none;
    box-shadow: none;
    border-radius: 8px;
    padding: 6px 8px;
    color: #cdd6f4;
}

.salida:hover { background: rgba(255, 255, 255, 0.1); }

.salida-activa {
    background: rgba(255, 255, 255, 0.15);
    box-shadow: inset 2px 0 #ffffff;
}

.salida-nombre { color: #cdd6f4; }
.salida-tipo { color: rgba(255, 255, 255, 0.72); font-size: 0.85rem; }
.vacio { color: rgba(255, 255, 255, 0.72); }
"""


def elegir_icono(iconos, porcentaje):
    """Reparte 0-100 % entre los iconos disponibles, igual que Waybar."""
    return iconos[max(0, min(len(iconos) - 1, int(porcentaje * len(iconos) / 100)))]


def lanzar(orden):
    """Ejecuta sin esperar: la interfaz no se queda parada mientras arrastras."""
    try:
        proceso = Gio.Subprocess.new(
            orden, Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE
        )
    except GLib.Error:
        return
    # Recoger el hijo al terminar para no dejar zombis
    proceso.wait_async(None, lambda p, r: p.wait_finish(r))


# ============================================
# Brillo (sysfs + brightnessctl)
# ============================================

class Brillo:
    def __init__(self):
        dispositivos = sorted(glob.glob("/sys/class/backlight/*"))
        self.ruta = dispositivos[0] if dispositivos else None
        self.maximo = self._leer("max_brightness") if self.ruta else None
        # Con la regla de udev habitual el archivo es escribible: así el cambio
        # es inmediato y no hace falta lanzar un proceso por cada paso
        self.directo = bool(self.ruta) and os.access(self._archivo("brightness"), os.W_OK)

    @property
    def disponible(self):
        return self.ruta is not None and self.maximo

    def _archivo(self, nombre):
        return os.path.join(self.ruta, nombre)

    def _leer(self, nombre):
        try:
            with open(self._archivo(nombre)) as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return None

    def porcentaje(self):
        if not self.disponible:
            return None
        actual = self._leer("brightness")
        return None if actual is None else round(100 * actual / self.maximo)

    def poner(self, porcentaje):
        porcentaje = max(BRILLO_MINIMO, min(100, int(porcentaje)))
        if self.directo:
            try:
                with open(self._archivo("brightness"), "w") as f:
                    f.write(str(max(1, round(self.maximo * porcentaje / 100))))
                return
            except OSError:
                self.directo = False
        lanzar(["brightnessctl", "-q", "set", f"{porcentaje}%"])


# ============================================
# Audio (pactl)
# ============================================

class Salida:
    def __init__(self, nombre, titulo, tipo, icono, disponible):
        self.nombre = nombre
        self.titulo = titulo
        self.tipo = tipo
        self.icono = icono
        self.disponible = disponible
        self.predeterminada = False
        # (tarjeta, perfil, puerto) si la salida solo existe en otro perfil
        self.perfil = None


def pactl(*args, json_salida=False):
    orden = ["pactl"] + (["-f", "json"] if json_salida else []) + list(args)
    try:
        proceso = subprocess.run(orden, capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proceso.returncode != 0:
        return None
    if not json_salida:
        return proceso.stdout.strip()
    try:
        return json.loads(proceso.stdout)
    except ValueError:
        return None


def describir(sink):
    """Nombre corto, tipo e icono de una salida de audio."""
    props = sink.get("properties") or {}
    bus = (props.get("device.bus") or "").lower()
    api = (props.get("device.api") or "").lower()
    forma = (props.get("device.form_factor") or "").lower()
    icono_freedesktop = (props.get("device.icon_name") or "").lower()

    puerto, disponible = "", True
    for p in sink.get("ports") or []:
        if p.get("name") == sink.get("active_port"):
            puerto = (p.get("type") or p.get("description") or "").lower()
            # Los HDMI sin monitor enchufado avisan con "not available"
            disponible = p.get("availability") != "not available"
            break

    titulo = props.get("node.nick") or sink.get("description") or sink.get("name", "")

    if bus == "bluetooth" or api == "bluez5" or "bluez" in (sink.get("name") or ""):
        icono = ICONO_AURICULARES if forma in ("headset", "headphone") else ICONO_BLUETOOTH
        return Salida(sink["name"], titulo, "Bluetooth", icono, disponible)
    if "hdmi" in puerto or icono_freedesktop == "video-display":
        return Salida(sink["name"], titulo, "HDMI / DisplayPort", ICONO_PANTALLA, disponible)
    if forma in ("headset", "headphone") or "headphone" in puerto:
        return Salida(sink["name"], titulo, "Headphones", ICONO_AURICULARES, disponible)
    if bus == "usb":
        return Salida(sink["name"], titulo, "USB", ICONO_USB, disponible)
    return Salida(sink["name"], titulo, "Built-in", ICONO_ALTAVOZ, disponible)


class Audio:
    def volumen(self):
        """(porcentaje, silenciado) del destino predeterminado."""
        sinks = pactl("list", "sinks", json_salida=True)
        if not sinks:
            return None, False
        predeterminado = pactl("get-default-sink")
        actual = next((s for s in sinks if s.get("name") == predeterminado), sinks[0])
        valores = []
        for canal in (actual.get("volume") or {}).values():
            texto = (canal.get("value_percent") or "").rstrip("%")
            if texto.isdigit():
                valores.append(int(texto))
        porcentaje = round(sum(valores) / len(valores)) if valores else 0
        return porcentaje, bool(actual.get("mute"))

    def poner_volumen(self, porcentaje):
        porcentaje = max(0, min(100, int(porcentaje)))
        lanzar(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{porcentaje}%"])

    def alternar_mudo(self):
        lanzar(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])

    def salidas(self):
        sinks = pactl("list", "sinks", json_salida=True) or []
        predeterminado = pactl("get-default-sink")
        lista = []
        puertos_con_sink = set()
        for sink in sinks:
            puertos_con_sink.add(sink.get("active_port"))
            salida = describir(sink)
            salida.predeterminada = salida.nombre == predeterminado
            # Fuera las que no se pueden usar (HDMI sin monitor), salvo la activa
            if salida.disponible or salida.predeterminada:
                lista.append(salida)

        lista.extend(self._salidas_de_otros_perfiles(puertos_con_sink))

        # Primero la activa, después el resto por tipo y nombre
        lista.sort(key=lambda s: (not s.predeterminada, s.tipo, s.titulo))
        return lista

    @staticmethod
    def _salidas_de_otros_perfiles(puertos_con_sink):
        """Salidas que no existen con el perfil actual de la tarjeta.

        En portátiles con SOF, altavoz y auriculares van en perfiles distintos:
        con el perfil de auriculares activo el altavoz no aparece como destino
        y no hay forma de elegirlo con set-default-sink."""
        extra = []
        for tarjeta in pactl("list", "cards", json_salida=True) or []:
            activo = tarjeta.get("active_profile")
            # pactl -f json da los puertos de la tarjeta como {nombre: datos}
            for nombre_puerto, puerto in (tarjeta.get("ports") or {}).items():
                puerto = dict(puerto, name=nombre_puerto)
                if not nombre_puerto.startswith("[Out]") or nombre_puerto in puertos_con_sink:
                    continue
                if puerto.get("availability") == "not available":
                    continue
                perfiles = [
                    p for p in puerto.get("profiles") or []
                    if p != activo and p not in ("off", "pro-audio")
                ]
                if not perfiles:
                    continue

                # Se describe como si fuera un destino más, para reutilizar describir()
                falso = {
                    "name": None,
                    "description": puerto.get("description"),
                    "active_port": nombre_puerto,
                    "ports": [puerto],
                    "properties": {
                        "device.bus": (tarjeta.get("properties") or {}).get("device.bus"),
                        "node.nick": puerto.get("description"),
                    },
                }
                salida = describir(falso)
                salida.perfil = (tarjeta.get("name"), perfiles[0], nombre_puerto)
                extra.append(salida)
        return extra

    def cambiar_salida(self, salida):
        nombre = salida.nombre
        if salida.perfil is not None:
            tarjeta, perfil, puerto = salida.perfil
            pactl("set-card-profile", tarjeta, perfil)
            nombre = self._esperar_sink(puerto)
            if nombre is None:
                return
        pactl("set-default-sink", nombre)
        # Llevarse también lo que ya está sonando
        for entrada in pactl("list", "sink-inputs", json_salida=True) or []:
            pactl("move-sink-input", str(entrada.get("index")), nombre)

    @staticmethod
    def _esperar_sink(puerto, intentos=20):
        """Tras cambiar de perfil, el destino tarda un momento en aparecer."""
        for _ in range(intentos):
            for sink in pactl("list", "sinks", json_salida=True) or []:
                if sink.get("active_port") == puerto:
                    return sink.get("name")
            time.sleep(0.1)
        return None

    def escuchar(self, al_cambiar):
        """Avisa de los cambios que hace cualquier otro (teclas, Bluetooth...)."""
        threading.Thread(target=self._escuchar, args=(al_cambiar,), daemon=True).start()

    @staticmethod
    def _escuchar(al_cambiar):
        while True:
            try:
                proceso = subprocess.Popen(
                    ["pactl", "subscribe"], stdout=subprocess.PIPE, text=True
                )
            except OSError:
                return
            for linea in proceso.stdout:
                if "sink" in linea or "server" in linea or "card" in linea:
                    GLib.idle_add(al_cambiar)
            proceso.wait()  # pipewire reiniciado: volver a suscribirse


# ============================================
# Deslizador
# ============================================

class Deslizador:
    """Fila de icono + deslizador + porcentaje.

    Tres cosas para que el control vaya suave:
    - la rueda se atiende a mano, acumulando los desplazamientos suaves del
      touchpad, en vez de dejar que GTK salte un paso entero por evento;
    - los cambios se mandan como mucho cada RITMO_MS, y sin esperar a que
      terminen, así arrastrar no atasca la interfaz;
    - mientras el usuario toca (y un instante después) los refrescos de fuera
      no tocan el valor, que si no se pelean con el arrastre.
    """

    PASO_RUEDA = 2     # % por muesca de la rueda
    RITMO_MS = 40      # como mucho un cambio cada 40 ms
    GRACIA = 0.4       # segundos de calma tras tocarlo

    def __init__(self, minimo, aplicar, icono_para, al_pulsar_icono=None):
        self.aplicar = aplicar
        self.icono_para = icono_para
        self.pendiente = None
        self.reloj = None
        self.arrastrando = False
        self.ultimo_toque = 0.0
        self.acumulado = 0.0
        self.pintando = False

        self.fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.icono = Gtk.Label()
        self.icono.get_style_context().add_class("icono")
        self.icono.set_size_request(22, -1)
        if al_pulsar_icono is None:
            self.fila.pack_start(self.icono, False, False, 0)
        else:
            caja = Gtk.EventBox()
            caja.add(self.icono)
            caja.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            caja.connect("button-press-event", al_pulsar_icono)
            self.fila.pack_start(caja, False, False, 0)

        self.escala = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, minimo, 100, 1)
        self.escala.set_draw_value(False)
        self.escala.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK
        )
        self.escala.connect("button-press-event", self._empieza_arrastre)
        self.escala.connect("button-release-event", self._termina_arrastre)
        self.escala.connect("scroll-event", self._rueda)
        self.escala.connect("value-changed", self._movido)
        self.fila.pack_start(self.escala, True, True, 0)

        self.valor = Gtk.Label(label="--%", xalign=1)
        self.valor.get_style_context().add_class("valor")
        self.valor.set_size_request(42, -1)
        self.fila.pack_start(self.valor, False, False, 0)

    # -- lo que hace el usuario ---------------------------------

    def _empieza_arrastre(self, *_):
        self.arrastrando = True
        return False

    def _termina_arrastre(self, *_):
        self.arrastrando = False
        self.ultimo_toque = time.monotonic()
        return False

    def _rueda(self, escala, evento):
        if evento.direction == Gdk.ScrollDirection.SMOOTH:
            hay_delta, _dx, dy = evento.get_scroll_deltas()
            if not hay_delta:
                return True
            self.acumulado -= dy * self.PASO_RUEDA
        elif evento.direction == Gdk.ScrollDirection.UP:
            self.acumulado += self.PASO_RUEDA
        elif evento.direction == Gdk.ScrollDirection.DOWN:
            self.acumulado -= self.PASO_RUEDA
        else:
            return True

        # Solo se mueve por unidades enteras; el resto se guarda para la
        # siguiente rueda, así el touchpad avanza poco a poco en vez de a saltos
        paso = int(self.acumulado)
        if paso:
            self.acumulado -= paso
            escala.set_value(escala.get_value() + paso)
        return True   # GTK no debe mover además el deslizador por su cuenta

    def _movido(self, escala):
        if self.pintando:
            return
        valor = int(escala.get_value())
        self.ultimo_toque = time.monotonic()
        self._pintar(valor)
        self._encolar(valor)

    # -- envío con ritmo ----------------------------------------

    def _encolar(self, valor):
        self.pendiente = valor
        if self.reloj is None:
            self._enviar()
            self.reloj = GLib.timeout_add(self.RITMO_MS, self._latido)

    def _enviar(self):
        if self.pendiente is not None:
            self.aplicar(self.pendiente)
            self.pendiente = None

    def _latido(self):
        if self.pendiente is None:
            self.reloj = None
            return GLib.SOURCE_REMOVE
        self._enviar()
        return GLib.SOURCE_CONTINUE

    # -- refresco desde fuera -----------------------------------

    @property
    def ocupado(self):
        return self.arrastrando or (time.monotonic() - self.ultimo_toque) < self.GRACIA

    def _pintar(self, valor):
        self.valor.set_label("--%" if valor is None else f"{valor}%")
        self.icono.set_label(self.icono_para(valor or 0))

    def poner(self, porcentaje, forzar=False):
        """Refleja un valor que viene de fuera, sin reenviarlo ni estorbar."""
        if porcentaje is None:
            self._pintar(None)
            return
        if self.ocupado and not forzar:
            return
        self.pintando = True
        self.escala.set_value(porcentaje)
        self.pintando = False
        self._pintar(porcentaje)


# ============================================
# Panel
# ============================================

class Fondo(Gtk.Window):
    """Ventana transparente a pantalla completa: detecta el clic fuera del panel.
    No cubre la barra (respeta su zona exclusiva), así el clic en el carrusel
    sigue llegando a Waybar y el módulo abre y cierra el panel."""

    def __init__(self, al_hacer_clic):
        super().__init__(title="Background")
        self.get_style_context().add_class("fondo-clic")
        self.set_app_paintable(True)
        pantalla = Gdk.Screen.get_default()
        visual = pantalla.get_rgba_visual() if pantalla else None
        if visual is not None:
            self.set_visual(visual)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_namespace(self, "media-panel-fondo")
        for borde in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                      GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, borde, True)

        caja = Gtk.EventBox()
        caja.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        caja.connect("button-press-event", lambda *_: al_hacer_clic() or True)
        self.add(caja)


class Panel(Gtk.Window):
    def __init__(self):
        super().__init__(title="Brightness and sound")
        self.get_style_context().add_class("media-panel")
        self.set_default_size(ANCHO, -1)

        GtkLayerShell.init_for_window(self)
        # OVERLAY: por encima del fondo que detecta los clics fuera
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self, "media-panel")
        for borde in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, borde, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, HUECO)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, MARGEN_DERECHA)

        self.brillo = Brillo()
        self.audio = Audio()
        self.mudo = False

        tarjeta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        tarjeta.get_style_context().add_class("tarjeta")
        tarjeta.set_size_request(ANCHO, -1)
        self.add(tarjeta)

        self.brillo_ui = None
        if self.brillo.disponible:
            tarjeta.pack_start(self._etiqueta("Brightness"), False, False, 0)
            self.brillo_ui = Deslizador(
                BRILLO_MINIMO, self.brillo.poner, lambda _v: ICONO_BRILLO
            )
            tarjeta.pack_start(self.brillo_ui.fila, False, False, 0)

        tarjeta.pack_start(self._etiqueta("Volume"), False, False, 0)
        self.volumen_ui = Deslizador(
            0, self.audio.poner_volumen, self._icono_volumen, self._clic_mudo
        )
        tarjeta.pack_start(self.volumen_ui.fila, False, False, 0)

        separador = Gtk.Box()
        separador.get_style_context().add_class("separador")
        tarjeta.pack_start(separador, False, False, 0)

        tarjeta.pack_start(self._etiqueta("Audio output"), False, False, 0)
        self.lista_salidas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        tarjeta.pack_start(self.lista_salidas, False, False, 0)

        self.fondo = Fondo(self.ocultar)

        self.bus = None
        try:
            self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error:
            pass

        self.audio.escuchar(self._refrescar_audio)
        self.reloj_brillo = None

    # -- construcción -------------------------------------------

    @staticmethod
    def _etiqueta(texto):
        etiqueta = Gtk.Label(label=texto, xalign=0)
        etiqueta.get_style_context().add_class("titulo")
        return etiqueta

    def _icono_volumen(self, porcentaje):
        return ICONO_MUDO if self.mudo else elegir_icono(ICONOS_VOLUMEN, porcentaje)

    # -- controles ----------------------------------------------

    def _clic_mudo(self, *_):
        self.audio.alternar_mudo()
        return True

    def _elegir_salida(self, _boton, salida):
        # En un hilo: cambiar de perfil tarda y no debe congelar el panel
        def cambiar():
            self.audio.cambiar_salida(salida)
            GLib.idle_add(self._refrescar_audio)
        threading.Thread(target=cambiar, daemon=True).start()

    # -- refresco -----------------------------------------------

    def _refrescar_brillo(self, forzar=False):
        if self.brillo_ui is None:
            return GLib.SOURCE_REMOVE
        self.brillo_ui.poner(self.brillo.porcentaje(), forzar)
        return GLib.SOURCE_CONTINUE if self.get_visible() else GLib.SOURCE_REMOVE

    def _refrescar_audio(self, forzar=False):
        porcentaje, self.mudo = self.audio.volumen()

        # Tope duro del 100 %: las teclas ya lo respetan (wpctl -l 1.0), pero
        # pavucontrol o la propia aplicación pueden pasarse. Como aquí ya
        # estamos escuchando cada cambio de audio, se devuelve a 100 sin
        # añadir ningún proceso extra.
        if porcentaje is not None and porcentaje > VOLUMEN_MAXIMO:
            self.audio.poner_volumen(VOLUMEN_MAXIMO)
            porcentaje = VOLUMEN_MAXIMO

        self.volumen_ui.poner(porcentaje, forzar)

        estilo = self.volumen_ui.fila.get_style_context()
        if self.mudo:
            estilo.add_class("mudo")
        else:
            estilo.remove_class("mudo")

        self._pintar_salidas()
        return GLib.SOURCE_REMOVE   # se llama desde idle_add

    def _pintar_salidas(self):
        for hijo in self.lista_salidas.get_children():
            self.lista_salidas.remove(hijo)

        salidas = self.audio.salidas()
        if not salidas:
            vacio = Gtk.Label(label="No audio outputs", xalign=0)
            vacio.get_style_context().add_class("vacio")
            self.lista_salidas.pack_start(vacio, False, False, 0)
            self.lista_salidas.show_all()
            return

        for salida in salidas:
            boton = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
            boton.get_style_context().add_class("salida")
            if salida.predeterminada:
                boton.get_style_context().add_class("salida-activa")
            boton.connect("clicked", self._elegir_salida, salida)

            fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            icono = Gtk.Label(label=salida.icono)
            icono.get_style_context().add_class("icono")
            icono.set_size_request(22, -1)
            fila.pack_start(icono, False, False, 0)

            textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            nombre = Gtk.Label(label=salida.titulo, xalign=0)
            nombre.get_style_context().add_class("salida-nombre")
            nombre.set_ellipsize(3)   # PANGO_ELLIPSIZE_END
            textos.pack_start(nombre, False, False, 0)
            tipo = Gtk.Label(label=salida.tipo, xalign=0)
            tipo.get_style_context().add_class("salida-tipo")
            textos.pack_start(tipo, False, False, 0)
            fila.pack_start(textos, True, True, 0)

            if salida.predeterminada:
                marca = Gtk.Label(label=ICONO_ACTIVO)
                marca.get_style_context().add_class("icono")
                fila.pack_start(marca, False, False, 0)

            boton.add(fila)
            self.lista_salidas.pack_start(boton, False, False, 0)

        self.lista_salidas.show_all()

    # -- mostrar / ocultar --------------------------------------

    def _cerrar_los_demas(self):
        """Cierra el centro de notificaciones de swaync, que no es nuestro.
        De los otros paneles se encarga el coordinador (scripts/panels.py)."""
        if self.bus is not None:
            try:
                self.bus.call_sync(
                    SWAYNC_NOMBRE, SWAYNC_RUTA, SWAYNC_NOMBRE, "SetVisibility",
                    GLib.Variant("(b)", (False,)), None, Gio.DBusCallFlags.NONE, 1000, None,
                )
            except GLib.Error:
                pass
        lanzar(["pkill", "-USR2", "-f", CALENDARIO])

    def mostrar(self, visible):
        if visible and not self.get_visible():
            self._cerrar_los_demas()
            self._refrescar_audio(forzar=True)
            self.fondo.show_all()
            self.show_all()
            if self.brillo_ui is not None:
                self._refrescar_brillo(forzar=True)
                self.reloj_brillo = GLib.timeout_add(500, self._refrescar_brillo)
        elif not visible and self.get_visible():
            if self.reloj_brillo is not None:
                GLib.source_remove(self.reloj_brillo)
                self.reloj_brillo = None
            self.hide()
            self.fondo.hide()

    def alternar(self):
        self.mostrar(not self.get_visible())
        return GLib.SOURCE_CONTINUE   # sin esto, la segunda señal mataría el proceso

    def ocultar(self):
        self.mostrar(False)
        return GLib.SOURCE_CONTINUE


def main():
    Gtk.init([])
    proveedor = Gtk.CssProvider()
    proveedor.load_from_data(CSS.encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), proveedor, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    panel = Panel()
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, panel.alternar)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR2, panel.ocultar)
    Gtk.main()


if __name__ == "__main__":
    main()
