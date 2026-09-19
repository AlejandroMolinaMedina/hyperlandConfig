#!/usr/bin/env python3
# ~/.config/waybar/scripts/player_panel.py
#
# Panel de reproducción para Waybar/Hyprland: carátula, título, artista,
# barra de progreso y controles (anterior, reproducir/pausar, siguiente).
# Se abre bajo el icono de reproducción de la barra (módulo custom/player).
#
# Arranca oculto. Señales:
#   SIGUSR1 -> mostrar u ocultar
#   SIGUSR2 -> ocultar

import signal
import threading
import urllib.parse
import urllib.request

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("Playerctl", "2.0")

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, GtkLayerShell, Playerctl

# ============================================
# Ajustes
# ============================================

ANCHO = 380
MARGEN_DERECHA = 299   # deja el panel centrado bajo el icono de la barra
HUECO = 8
CARATULA = 84          # lado de la carátula, en píxeles

ICONO_ANTERIOR = ""
ICONO_SIGUIENTE = ""
ICONO_PLAY = ""
ICONO_PAUSA = ""

CSS = """
window.player-panel { background: transparent; }
window.fondo-clic { background: transparent; }

.tarjeta {
    background: rgba(30, 30, 46, 0.85);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 14px;
    color: #cdd6f4;
}

.caratula {
    background: rgba(17, 17, 27, 0.8);
    border-radius: 8px;
}

.sin-caratula { color: #6c7086; font-size: 2rem; }

.cancion { color: #ffffff; font-weight: bold; font-size: 1.05rem; }
.artista { color: #cdd6f4; }
.album, .reproductor { color: #6c7086; font-size: 0.85rem; }
.tiempo { color: #6c7086; font-size: 0.8rem; }
.vacio { color: #6c7086; }

progressbar trough {
    background-color: rgba(17, 17, 27, 0.8);
    background-image: none;
    border: none;
    border-radius: 10px;
    min-height: 6px;
}

progressbar progress {
    background-color: #cdd6f4;
    background-image: none;
    border: none;
    border-radius: 10px;
}

.control {
    background: transparent;
    background-image: none;
    border: none;
    box-shadow: none;
    border-radius: 50%;
    padding: 6px 10px;
    color: #cdd6f4;
    font-size: 1.1rem;
}

.control:hover { background: rgba(255, 255, 255, 0.12); }
.control:disabled { color: #45475a; }

.control-principal {
    background: rgba(255, 255, 255, 0.15);
    font-size: 1.2rem;
}

.control-principal:hover { background: rgba(255, 255, 255, 0.28); }
"""


def formato_tiempo(microsegundos):
    segundos = max(0, int(microsegundos // 1_000_000))
    return f"{segundos // 60}:{segundos % 60:02d}"


# ============================================
# Carátula
# ============================================

class Caratula:
    """Descarga y recuerda la última portada (las webs la dan por http)."""

    def __init__(self, al_cargar):
        self.al_cargar = al_cargar
        self.url = None

    def pedir(self, url):
        if url == self.url:
            return
        self.url = url
        if not url:
            self.al_cargar(None)
            return
        threading.Thread(target=self._cargar, args=(url,), daemon=True).start()

    def _cargar(self, url):
        try:
            if url.startswith("file://"):
                ruta = urllib.parse.unquote(urllib.parse.urlparse(url).path)
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(ruta, CARATULA, CARATULA, True)
            elif url.startswith(("http://", "https://")):
                with urllib.request.urlopen(url, timeout=10) as respuesta:
                    datos = respuesta.read()
                cargador = GdkPixbuf.PixbufLoader()
                cargador.set_size(CARATULA, CARATULA)
                cargador.write(datos)
                cargador.close()
                pixbuf = cargador.get_pixbuf()
            else:
                pixbuf = None
        except (OSError, GLib.Error, ValueError):
            pixbuf = None

        # Si mientras tanto cambió la canción, esta portada ya no vale
        if url == self.url:
            GLib.idle_add(self.al_cargar, pixbuf)


# ============================================
# Panel
# ============================================

class Fondo(Gtk.Window):
    """Ventana transparente que detecta el clic fuera del panel.
    No cubre la barra, así el icono sigue abriendo y cerrando el panel."""

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
        GtkLayerShell.set_namespace(self, "player-panel-fondo")
        for borde in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM,
                      GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, borde, True)

        caja = Gtk.EventBox()
        caja.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        caja.connect("button-press-event", lambda *_: al_hacer_clic() or True)
        self.add(caja)


class Panel(Gtk.Window):
    def __init__(self):
        super().__init__(title="Now playing")
        self.get_style_context().add_class("player-panel")
        self.set_default_size(ANCHO, -1)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self, "player-panel")
        for borde in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, borde, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, HUECO)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, MARGEN_DERECHA)

        tarjeta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tarjeta.get_style_context().add_class("tarjeta")
        tarjeta.set_size_request(ANCHO, -1)
        self.add(tarjeta)

        # -- carátula + textos --
        arriba = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        tarjeta.pack_start(arriba, False, False, 0)

        self.imagen = Gtk.Image()
        self.imagen.get_style_context().add_class("caratula")
        self.imagen.set_size_request(CARATULA, CARATULA)
        arriba.pack_start(self.imagen, False, False, 0)

        textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        textos.set_valign(Gtk.Align.CENTER)
        arriba.pack_start(textos, True, True, 0)

        self.titulo = self._etiqueta("cancion")
        self.artista = self._etiqueta("artista")
        self.album = self._etiqueta("album")
        self.reproductor = self._etiqueta("reproductor")
        for etiqueta in (self.titulo, self.artista, self.album, self.reproductor):
            textos.pack_start(etiqueta, False, False, 0)

        # -- progreso --
        self.progreso = Gtk.ProgressBar()
        self.progreso.set_show_text(False)
        tarjeta.pack_start(self.progreso, False, False, 0)

        tiempos = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.transcurrido = self._etiqueta("tiempo")
        self.total = self._etiqueta("tiempo")
        self.total.set_xalign(1)
        tiempos.pack_start(self.transcurrido, True, True, 0)
        tiempos.pack_start(self.total, True, True, 0)
        tarjeta.pack_start(tiempos, False, False, 0)

        # -- controles --
        controles = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controles.set_halign(Gtk.Align.CENTER)
        tarjeta.pack_start(controles, False, False, 0)

        self.boton_anterior = self._control(ICONO_ANTERIOR, self._anterior)
        self.boton_play = self._control(ICONO_PLAY, self._play_pausa, principal=True)
        self.boton_siguiente = self._control(ICONO_SIGUIENTE, self._siguiente)
        for boton in (self.boton_anterior, self.boton_play, self.boton_siguiente):
            controles.pack_start(boton, False, False, 0)

        # -- reproductores --
        self.caratula = Caratula(self._pintar_caratula)
        self.gestor = Playerctl.PlayerManager()
        self.gestor.connect("name-appeared", self._aparece)
        self.gestor.connect("player-vanished", lambda *_: self.refrescar())
        for nombre in self.gestor.props.player_names:
            self._seguir(nombre)

        self.fondo = Fondo(self.ocultar)
        self.reloj = None

    # -- construcción -------------------------------------------

    @staticmethod
    def _etiqueta(clase):
        etiqueta = Gtk.Label(label="", xalign=0)
        etiqueta.get_style_context().add_class(clase)
        etiqueta.set_ellipsize(3)   # PANGO_ELLIPSIZE_END
        return etiqueta

    @staticmethod
    def _control(icono, al_pulsar, principal=False):
        boton = Gtk.Button(label=icono, relief=Gtk.ReliefStyle.NONE)
        boton.get_style_context().add_class("control")
        if principal:
            boton.get_style_context().add_class("control-principal")
        boton.connect("clicked", al_pulsar)
        return boton

    # -- reproductores ------------------------------------------

    def _aparece(self, _gestor, nombre):
        self._seguir(nombre)
        self.refrescar()

    def _seguir(self, nombre):
        try:
            reproductor = Playerctl.Player.new_from_name(nombre)
        except GLib.Error:
            return
        for senal in ("playback-status", "metadata", "seeked"):
            reproductor.connect(senal, lambda *_: self.refrescar())
        self.gestor.manage_player(reproductor)

    def _activo(self):
        reproductores = self.gestor.props.players
        for reproductor in reproductores:
            if reproductor.props.playback_status == Playerctl.PlaybackStatus.PLAYING:
                return reproductor
        return reproductores[0] if reproductores else None

    # -- controles ----------------------------------------------

    def _accion(self, metodo):
        reproductor = self._activo()
        if reproductor is None:
            return
        try:
            getattr(reproductor, metodo)()
        except GLib.Error:
            pass
        self.refrescar()

    def _anterior(self, *_):
        self._accion("previous")

    def _siguiente(self, *_):
        self._accion("next")

    def _play_pausa(self, *_):
        self._accion("play_pause")

    # -- pintado ------------------------------------------------

    def _pintar_caratula(self, pixbuf):
        if pixbuf is None:
            self.imagen.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)
        else:
            self.imagen.set_from_pixbuf(pixbuf)
        return False

    def refrescar(self, *_):
        reproductor = self._activo()

        if reproductor is None:
            self.titulo.set_label("Nothing playing")
            self.titulo.get_style_context().add_class("vacio")
            for etiqueta in (self.artista, self.album, self.reproductor,
                             self.transcurrido, self.total):
                etiqueta.set_label("")
            self.progreso.set_fraction(0)
            self.boton_play.set_label(ICONO_PLAY)
            for boton in (self.boton_anterior, self.boton_play, self.boton_siguiente):
                boton.set_sensitive(False)
            self.caratula.pedir(None)
            return False

        for boton in (self.boton_anterior, self.boton_play, self.boton_siguiente):
            boton.set_sensitive(True)
        self.titulo.get_style_context().remove_class("vacio")

        self.titulo.set_label(reproductor.get_title() or "(no title)")
        self.artista.set_label(reproductor.get_artist() or "")
        self.album.set_label(reproductor.get_album() or "")
        self.reproductor.set_label(reproductor.props.player_name)

        sonando = reproductor.props.playback_status == Playerctl.PlaybackStatus.PLAYING
        self.boton_play.set_label(ICONO_PAUSA if sonando else ICONO_PLAY)

        self.caratula.pedir(self._metadato(reproductor, "mpris:artUrl"))
        self._pintar_progreso(reproductor)
        return False

    @staticmethod
    def _metadato(reproductor, clave):
        try:
            valor = reproductor.props.metadata
            return valor[clave] if valor and clave in valor.keys() else None
        except (GLib.Error, AttributeError, TypeError):
            return None

    def _pintar_progreso(self, reproductor=None):
        reproductor = reproductor or self._activo()
        if reproductor is None:
            return GLib.SOURCE_REMOVE

        duracion = self._metadato(reproductor, "mpris:length") or 0
        try:
            posicion = reproductor.props.position
        except GLib.Error:
            posicion = 0

        if duracion > 0:
            self.progreso.set_fraction(min(1.0, posicion / duracion))
            self.total.set_label(formato_tiempo(duracion))
        else:
            self.progreso.set_fraction(0)
            self.total.set_label("")
        self.transcurrido.set_label(formato_tiempo(posicion))
        return GLib.SOURCE_CONTINUE if self.get_visible() else GLib.SOURCE_REMOVE

    # -- mostrar / ocultar --------------------------------------

    def mostrar(self, visible):
        if visible and not self.get_visible():
            self.refrescar()
            self.fondo.show_all()
            self.show_all()
            # El tiempo avanza solo: refrescar mientras esté a la vista
            self.reloj = GLib.timeout_add_seconds(1, self._pintar_progreso)
        elif not visible and self.get_visible():
            if self.reloj is not None:
                GLib.source_remove(self.reloj)
                self.reloj = None
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
