#!/usr/bin/env python3
# ~/.config/waybar/scripts/calendar_panel.py
#
# Panel de calendario y próximos eventos para Waybar/Hyprland.
# Se coloca bajo el centro de notificaciones de swaync, anclado arriba a la derecha.
# Lee los calendarios de Evolution Data Server (cuentas de GNOME Online Accounts).
#
# Arranca oculto. Señales:
#   SIGUSR1 -> mostrar u ocultar
#   SIGUSR2 -> ocultar
# Uso desde Waybar (clic en el reloj):
#   swaync-client -t -sw ; pkill -USR1 -f '^python3 .*calendar_panel.py$'

import datetime
import locale
import signal
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("EDataServer", "1.2")
gi.require_version("ECal", "2.0")
gi.require_version("ICalGLib", "4.0")

from gi.repository import ECal, EDataServer, Gdk, Gio, GLib, Gtk, GtkLayerShell

# swaync: el panel sigue la visibilidad de su centro de notificaciones
SWAYNC_NOMBRE = "org.erikreider.swaync.cc"
SWAYNC_RUTA = "/org/erikreider/swaync/cc"

# ============================================
# Ajustes
# ============================================

ANCHO = 532          # mismo ancho que el centro de notificaciones de swaync
ALTO_SWAYNC = 600    # alto del centro de notificaciones (swaync/config)
HUECO = 8            # separación entre swaync y este panel
ALTO_RESTO = 330     # alto aproximado del calendario, el título y los márgenes
DIAS_LISTA = 30      # días hacia adelante en la lista de eventos
MAX_EVENTOS = 12     # máximo de eventos en la lista
REFRESCO_MIN = 5     # minutos entre refrescos periódicos

REGISTRO = False     # con --debug: apunta cada apertura, cierre y señal
SIN_SWAYNC = False   # con --sin-swaync: no habla con swaync (para diagnóstico)


def log(mensaje):
    if REGISTRO:
        print(f"{datetime.datetime.now():%H:%M:%S.%f} {mensaje}", file=sys.stderr, flush=True)


CSS = """
window.calendar-panel { background: transparent; }

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
    color: #ffffff;
    font-weight: bold;
    font-size: 1.1rem;
    margin-bottom: 8px;
}

calendar {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 6px;
    color: #cdd6f4;
}

calendar:selected {
    background: #ffffff;
    color: #11111b;
    border-radius: 5px;
}

calendar.highlight {          /* días con eventos */
    color: #ffffff;
    font-weight: bold;
}

.evento {
    padding: 6px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
}

.evento-hora { color: #cdd6f4; font-weight: bold; }
.evento-titulo { color: #cdd6f4; }
.evento-calendario { color: rgba(255, 255, 255, 0.72); font-size: 0.85rem; }
.dia { color: rgba(255, 255, 255, 0.72); font-size: 0.9rem; margin-top: 6px; }
.vacio { color: rgba(255, 255, 255, 0.72); }
"""


# ============================================
# Lectura de calendarios (Evolution Data Server)
# ============================================

class Evento:
    def __init__(self, inicio, todo_el_dia, titulo, calendario, color):
        self.inicio = inicio            # datetime local
        self.todo_el_dia = todo_el_dia
        self.titulo = titulo
        self.calendario = calendario
        self.color = color

    @property
    def dia(self):
        return self.inicio.date()


def _a_datetime(t):
    """Convierte un ICalTime a datetime local. Las fechas de todo el día se
    toman tal cual (sin hora), porque as_timet() las interpreta en UTC y eso
    desplaza el día."""
    if t.is_date():
        return datetime.datetime(t.get_year(), t.get_month(), t.get_day())
    return datetime.datetime.fromtimestamp(t.as_timet())


class Calendarios:
    """Mantiene la conexión con los calendarios y avisa de los cambios."""

    def __init__(self, al_cambiar):
        self.al_cambiar = al_cambiar
        self.clientes = {}              # uid -> (cliente, nombre, color)
        self.vistas = []
        self.registro = None
        self._lock = threading.Lock()

    def arrancar(self):
        threading.Thread(target=self._conectar_todo, daemon=True).start()

    def _conectar_todo(self):
        try:
            self.registro = EDataServer.SourceRegistry.new_sync(None)
        except GLib.Error as e:
            print(f"no se pudo abrir el registro de calendarios: {e.message}", file=sys.stderr)
            return

        # Calendarios nuevos (por ejemplo al añadir una cuenta) y eliminados
        self.registro.connect("source-added", lambda r, s: self._quizas_conectar(s))
        self.registro.connect("source-removed", lambda r, s: self._olvidar(s))

        for src in self.registro.list_sources(EDataServer.SOURCE_EXTENSION_CALENDAR):
            self._quizas_conectar(src)
        GLib.idle_add(self.al_cambiar)

    def _quizas_conectar(self, src):
        if not src.has_extension(EDataServer.SOURCE_EXTENSION_CALENDAR) or not src.get_enabled():
            return
        if src.get_uid() in self.clientes:
            return
        threading.Thread(target=self._conectar, args=(src,), daemon=True).start()

    def _conectar(self, src):
        nombre = src.get_display_name()
        try:
            cliente = ECal.Client.connect_sync(src, ECal.ClientSourceType.EVENTS, 30, None)
        except GLib.Error as e:
            print(f"calendario {nombre!r} no conecta: {e.message}", file=sys.stderr)
            return

        color = None
        ext = src.get_extension(EDataServer.SOURCE_EXTENSION_CALENDAR)
        if ext is not None:
            color = ext.dup_color()

        with self._lock:
            self.clientes[src.get_uid()] = (cliente, nombre, color)

        # Vista en vivo: avisa cuando se crean, cambian o borran eventos
        try:
            ok, vista = cliente.get_view_sync("#t", None)
            if ok and vista is not None:
                for senal in ("objects-added", "objects-modified", "objects-removed"):
                    vista.connect(senal, lambda *a: GLib.idle_add(self.al_cambiar))
                vista.start()
                self.vistas.append(vista)
        except GLib.Error as e:
            print(f"calendario {nombre!r} sin avisos en vivo: {e.message}", file=sys.stderr)

        GLib.idle_add(self.al_cambiar)

    def _olvidar(self, src):
        with self._lock:
            self.clientes.pop(src.get_uid(), None)
        GLib.idle_add(self.al_cambiar)

    def eventos(self, desde, hasta):
        """Eventos (con sus repeticiones) entre dos datetime locales."""
        encontrados = []
        with self._lock:
            clientes = list(self.clientes.values())

        ini, fin = int(desde.timestamp()), int(hasta.timestamp())
        for cliente, nombre, color in clientes:
            def recoger(icomp, istart, iend, *args, _n=nombre, _c=color):
                encontrados.append(Evento(
                    _a_datetime(istart), istart.is_date(),
                    icomp.get_summary() or "(no title)", _n, _c,
                ))
                return True

            try:
                cliente.generate_instances_sync(ini, fin, None, recoger)
            except GLib.Error as e:
                print(f"calendario {nombre!r} no responde: {e.message}", file=sys.stderr)

        encontrados.sort(key=lambda e: (e.inicio, e.titulo))
        return encontrados


# ============================================
# Panel
# ============================================

class Panel(Gtk.Window):
    def __init__(self):
        super().__init__(title="Calendar")
        self.get_style_context().add_class("calendar-panel")
        self.set_default_size(ANCHO, -1)

        GtkLayerShell.init_for_window(self)
        # OVERLAY, por encima de las ventanas transparentes con las que swaync
        # detecta los clics fuera de su panel. Si no, se llevan nuestros clics.
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self, "calendar-panel")
        # Anclado arriba y a la derecha. La ventana mide lo que mide la tarjeta,
        # sin zonas transparentes que se traguen los clics.
        for borde in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.RIGHT):
            GtkLayerShell.set_anchor(self, borde, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, ALTO_SWAYNC + HUECO)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 0)

        tarjeta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tarjeta.get_style_context().add_class("tarjeta")
        tarjeta.set_size_request(ANCHO, -1)
        self.add(tarjeta)

        # Ajustar el alto de la lista al monitor donde se muestre
        self.connect("map", self._ajustar_altura)

        # Saber si el puntero está encima: sirve para distinguir un clic en el
        # calendario (swaync pierde el foco y se cierra) de un clic fuera
        self.puntero_dentro = False
        self.add_events(
            Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.SCROLL_MASK
        )
        self.connect("enter-notify-event", self._entra_puntero)
        self.connect("leave-notify-event", self._sale_puntero)
        self.connect("button-press-event", self._clic_registrado)
        self.connect("scroll-event", self._scroll_registrado)

        self.calendario = Gtk.Calendar()
        self.calendario.set_display_options(
            Gtk.CalendarDisplayOptions.SHOW_HEADING | Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES
        )
        self.calendario.connect("month-changed", self._cambio_de_mes)
        tarjeta.pack_start(self.calendario, False, False, 0)

        titulo = Gtk.Label(label="Upcoming events", xalign=0)
        titulo.get_style_context().add_class("titulo")
        tarjeta.pack_start(titulo, False, False, 0)

        self.scroll = scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(120)
        scroll.set_max_content_height(300)
        scroll.set_propagate_natural_height(True)
        self.lista = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll.add(self.lista)
        tarjeta.pack_start(scroll, True, True, 0)

        # Seguir la visibilidad del centro de notificaciones de swaync
        self.bus = None
        if SIN_SWAYNC:
            log("modo sin swaync: el panel va por su cuenta")
        else:
            try:
                self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                self.bus.signal_subscribe(
                    SWAYNC_NOMBRE, SWAYNC_NOMBRE, "SubscribeV2", SWAYNC_RUTA,
                    None, Gio.DBusSignalFlags.NONE, self._swaync_cambio,
                )
            except GLib.Error as e:
                print(f"sin conexión con swaync: {e.message}", file=sys.stderr)

        self.datos = Calendarios(self.refrescar)
        self.datos.arrancar()

        GLib.timeout_add_seconds(REFRESCO_MIN * 60, self._refresco_periodico)

    def _clic_registrado(self, widget, evento):
        log(f"clic recibido en el panel: x={evento.x:.0f} y={evento.y:.0f}")
        return False

    def _scroll_registrado(self, widget, evento):
        log("desplazamiento recibido en el panel")
        return False

    def _entra_puntero(self, *_):
        self.puntero_dentro = True
        return False

    def _sale_puntero(self, widget, evento):
        # INFERIOR: el puntero solo pasó a un hijo (un botón), sigue encima
        if evento.detail != Gdk.NotifyType.INFERIOR:
            self.puntero_dentro = False
        return False

    def _ajustar_altura(self, *_):
        """La lista no debe empujar el panel fuera de la pantalla."""
        ventana = self.get_window()
        pantalla = Gdk.Display.get_default()
        if ventana is None or pantalla is None:
            return
        monitor = pantalla.get_monitor_at_window(ventana)
        if monitor is None:
            return
        alto = monitor.get_geometry().height
        # lo que queda bajo swaync, descontando el calendario y los márgenes
        disponible = alto - (ALTO_SWAYNC + HUECO) - HUECO - ALTO_RESTO
        self.scroll.set_max_content_height(max(120, min(300, disponible)))

    # -- datos --------------------------------------------------

    def _refresco_periodico(self):
        self.refrescar()
        return True

    def refrescar(self):
        ahora = datetime.datetime.now()
        eventos = self.datos.eventos(ahora, ahora + datetime.timedelta(days=DIAS_LISTA))
        self._pintar_lista(eventos)
        self.marcar_dias(eventos)
        return False

    def _cambio_de_mes(self, *_):
        anio, mes0, _dia = self.calendario.get_date()
        log(f"cambio de mes -> {mes0 + 1}/{anio}")
        self.marcar_dias()
        log("cambio de mes atendido")

    def marcar_dias(self, eventos=None):
        anio, mes0, _ = self.calendario.get_date()
        inicio = datetime.datetime(anio, mes0 + 1, 1)
        fin = datetime.datetime(anio + (mes0 + 1) // 12, (mes0 + 1) % 12 + 1, 1)
        if eventos is None or not (inicio <= datetime.datetime.now() <= fin):
            eventos = self.datos.eventos(inicio, fin)

        self.calendario.clear_marks()
        for ev in eventos:
            if ev.dia.year == anio and ev.dia.month == mes0 + 1:
                self.calendario.mark_day(ev.dia.day)

    # -- interfaz -----------------------------------------------

    def _pintar_lista(self, eventos):
        for hijo in self.lista.get_children():
            self.lista.remove(hijo)

        if not eventos:
            vacio = Gtk.Label(label="No upcoming events", xalign=0)
            vacio.get_style_context().add_class("vacio")
            self.lista.pack_start(vacio, False, False, 0)
            self.lista.show_all()
            return

        hoy = datetime.date.today()
        dia_actual = None
        for ev in eventos[:MAX_EVENTOS]:
            if ev.dia != dia_actual:
                dia_actual = ev.dia
                if ev.dia == hoy:
                    texto = "Today"
                elif ev.dia == hoy + datetime.timedelta(days=1):
                    texto = "Tomorrow"
                else:
                    # El nombre del día sale en el idioma del sistema
                    texto = ev.inicio.strftime("%a %d/%m").capitalize()
                cabecera = Gtk.Label(label=texto, xalign=0)
                cabecera.get_style_context().add_class("dia")
                self.lista.pack_start(cabecera, False, False, 0)

            fila = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            fila.get_style_context().add_class("evento")

            hora = Gtk.Label(label="All day" if ev.todo_el_dia else ev.inicio.strftime("%H:%M"), xalign=0)
            hora.get_style_context().add_class("evento-hora")
            hora.set_size_request(80, -1)
            fila.pack_start(hora, False, False, 0)

            textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            titulo = Gtk.Label(label=ev.titulo, xalign=0)
            titulo.get_style_context().add_class("evento-titulo")
            titulo.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
            textos.pack_start(titulo, False, False, 0)
            cal = Gtk.Label(label=ev.calendario, xalign=0)
            cal.get_style_context().add_class("evento-calendario")
            cal.set_ellipsize(3)
            textos.pack_start(cal, False, False, 0)
            fila.pack_start(textos, True, True, 0)

            self.lista.pack_start(fila, False, False, 0)

        self.lista.show_all()

    # -- mostrar / ocultar --------------------------------------

    def _swaync(self, metodo, parametros=None):
        """Llama a swaync por D-Bus. Devuelve None si swaync no está disponible."""
        if self.bus is None:
            return None
        try:
            return self.bus.call_sync(
                SWAYNC_NOMBRE, SWAYNC_RUTA, SWAYNC_NOMBRE, metodo,
                parametros, None, Gio.DBusCallFlags.NONE, 1000, None,
            )
        except GLib.Error:
            return None

    def _swaync_cambio(self, conexion, emisor, ruta, interfaz, senal, parametros):
        # SubscribeV2: (cantidad, no-molestar, panel-abierto, inhibido)
        datos = parametros.unpack()
        if len(datos) < 3:
            return
        abierto = datos[2]
        log(f"swaync avisa: abierto={abierto} puntero_dentro={self.puntero_dentro}")

        if abierto:
            self.mostrar(True)
        elif self.get_visible():
            if self.puntero_dentro:
                # Estabas usando el calendario: swaync se cerró por perder el
                # foco, así que se vuelve a abrir y los dos siguen juntos
                log("reabriendo swaync (clic dentro del calendario)")
                self._swaync("SetVisibility", GLib.Variant("(b)", (True,)))
            else:
                # Clic fuera: se cierra todo
                log("clic fuera: se cierra el calendario")
                self.mostrar(False)

    def mostrar(self, visible):
        if visible and not self.get_visible():
            log("mostrando el panel")
            self.refrescar()
            self.show_all()
        elif not visible and self.get_visible():
            log("ocultando el panel")
            self.hide()

    def alternar(self):
        log("señal SIGUSR1 (clic en el reloj)")
        abrir = not self.get_visible()
        self._swaync("SetVisibility", GLib.Variant("(b)", (abrir,)))
        self.mostrar(abrir)
        return GLib.SOURCE_CONTINUE   # sin esto, la segunda señal mataría el proceso

    def ocultar(self):
        self._swaync("SetVisibility", GLib.Variant("(b)", (False,)))
        self.hide()
        return GLib.SOURCE_CONTINUE


def main():
    global REGISTRO, SIN_SWAYNC
    REGISTRO = "--debug" in sys.argv
    SIN_SWAYNC = "--sin-swaync" in sys.argv
    # Nombres de día y mes en el idioma del sistema (Python usa "C" si no)
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass

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
