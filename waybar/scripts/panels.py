#!/usr/bin/env python3
# ~/.config/waybar/scripts/panels.py
#
# Los tres paneles de la barra en un solo proceso.
#
# Antes cada panel era un proceso aparte: tres intérpretes de Python y tres
# instancias de GTK haciendo lo mismo (~103 MB en total). Aquí comparten todo.
#
# Además, al vivir juntos se cierran entre ellos sin dar rodeos: antes cada
# panel tenía que ir matando a los otros con pkill desde la configuración de
# Waybar.
#
# Señales (una por panel, desde Waybar con pkill). Cada una abre su panel si
# está cerrado y lo cierra si está abierto:
#   USR1  -> calendario y notificaciones
#   USR2  -> brillo, volumen y salida de audio
#   WINCH -> reproducción
#
# GLib solo sabe atender HUP, INT, TERM, USR1, USR2 y WINCH; las señales de
# tiempo real (RTMIN+n) no le valen. De ahí que WINCH, que para una ventana
# sin terminal no significa nada, haga de tercera señal libre.

import os
import signal
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gdk, GLib, Gtk

# Los módulos viven junto a este archivo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import calendar_panel
import media_panel
import player_panel

MODULOS = [
    ("calendario", calendar_panel, signal.SIGUSR1),
    ("media", media_panel, signal.SIGUSR2),
    ("reproduccion", player_panel, signal.SIGWINCH),
]


class Coordinador:
    """Crea los paneles y se asegura de que solo haya uno abierto."""

    def __init__(self):
        self.paneles = {nombre: modulo.Panel() for nombre, modulo, _ in MODULOS}

    def alternar(self, nombre):
        panel = self.paneles[nombre]
        # Si el que piden ya está abierto, alternar() lo cerrará; si no, hay
        # que apartar a los demás antes de abrirlo
        if not panel.get_visible():
            for otro, demas in self.paneles.items():
                if otro != nombre and demas.get_visible():
                    demas.ocultar()
        panel.alternar()
        return GLib.SOURCE_CONTINUE   # sin esto, la segunda señal mataría el proceso


def main():
    # Nombres de día y mes en el idioma del sistema (lo necesita el calendario)
    calendar_panel.locale.setlocale(calendar_panel.locale.LC_ALL, "")

    Gtk.init([])

    # Un solo proveedor con los estilos de los tres paneles
    proveedor = Gtk.CssProvider()
    proveedor.load_from_data("\n".join(m.CSS for _, m, _s in MODULOS).encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), proveedor, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    coordinador = Coordinador()
    for nombre, _modulo, senal in MODULOS:
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, senal, coordinador.alternar, nombre)

    Gtk.main()


if __name__ == "__main__":
    main()
