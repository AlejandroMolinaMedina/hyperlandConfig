#!/usr/bin/env python3
# ~/.config/hypr/scripts/share_picker.py
#
# Selector para compartir pantalla con rofi (sustituye a hyprland-share-picker).
# Lo llama xdg-desktop-portal-hyprland (hypr/xdph.conf: custom_picker_binary)
# cuando Chrome, Teams, Meet... piden una pantalla o una ventana.
#
# Entrada: XDPH_WINDOW_SHARING_LIST, con una entrada por ventana:
#   <handle>[HC>]<clase>[HT>]<título>[HE>]<dirección>[HA>]
# Salida: una línea "[SELECTION]/screen:<monitor>" o "[SELECTION]/window:<handle>".
# Salir con error = cancelar.
#
# Chrome abre DOS peticiones a la vez al abrir su diálogo (una para "Window" y
# otra para "Entire Screen"). Para no preguntar dos veces, la segunda espera a
# que termine la primera y reutiliza su respuesta (o su cancelación).

import fcntl
import json
import os
import subprocess
import sys
import time

TEMA = os.path.expanduser("~/.config/rofi/launchers/type-4/style-3.rasi")
REUTILIZAR_SEGUNDOS = 5   # ventana en la que una segunda petición reusa la respuesta

DIR = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
CANDADO = os.path.join(DIR, "share_picker.lock")
CACHE = os.path.join(DIR, "share_picker.last")

ICONO_PANTALLA = "video-display"


def hyprctl_json(*args):
    try:
        return json.loads(subprocess.run(
            ["hyprctl", *args, "-j"], capture_output=True, text=True, timeout=3
        ).stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []


def ventanas():
    """[(handle, clase, título)] a partir de la lista que pasa XDPH."""
    lista = []
    for entrada in os.environ.get("XDPH_WINDOW_SHARING_LIST", "").split("[HA>]"):
        if "[HC>]" not in entrada:
            continue
        handle, resto = entrada.split("[HC>]", 1)
        clase, resto = resto.split("[HT>]", 1) if "[HT>]" in resto else (resto, "")
        titulo = resto.split("[HE>]", 1)[0]
        lista.append((handle, clase, titulo))
    return lista


def elegir():
    opciones = []   # (texto que ve rofi, selección para XDPH)

    for monitor in hyprctl_json("monitors"):
        nombre = monitor.get("name", "")
        modelo = monitor.get("model") or ""
        # Las pantallas de portátil suelen reportar un código ("0x41A0"): mejor el fabricante
        if not modelo or modelo.lower().startswith("0x"):
            modelo = monitor.get("make") or monitor.get("description") or nombre
        texto = f"Screen  {nombre}  ({modelo}, {monitor.get('width')}x{monitor.get('height')})"
        opciones.append((texto, ICONO_PANTALLA, f"screen:{nombre}"))

    for handle, clase, titulo in ventanas():
        titulo = titulo.replace("\n", " ")
        if len(titulo) > 70:
            titulo = titulo[:69] + "…"
        texto = f"Window  {clase}  —  {titulo}"
        opciones.append((texto, clase.lower(), f"window:{handle}"))

    if not opciones:
        return None

    # Cada línea lleva su icono: "texto\0icon\x1fnombre"
    entrada = "\n".join(f"{t}\0icon\x1f{i}" for t, i, _ in opciones)
    orden = ["rofi", "-dmenu", "-i", "-show-icons", "-format", "i",
             "-p", "Share", "-mesg", "Choose a screen or window to share"]
    if os.path.exists(TEMA):
        orden += ["-theme", TEMA]

    try:
        resultado = subprocess.run(orden, input=entrada, capture_output=True, text=True)
    except OSError:
        return None
    indice = resultado.stdout.strip()
    if resultado.returncode != 0 or not indice.isdigit() or int(indice) >= len(opciones):
        return None   # Escape o clic fuera: cancelar
    return opciones[int(indice)][2]


def main():
    with open(CANDADO, "w") as candado:
        # La segunda petición de Chrome se queda aquí hasta que acabe la primera
        fcntl.flock(candado, fcntl.LOCK_EX)

        try:
            reciente = time.time() - os.path.getmtime(CACHE) < REUTILIZAR_SEGUNDOS
        except OSError:
            reciente = False

        if reciente:
            with open(CACHE) as f:
                seleccion = f.read().strip() or None
        else:
            seleccion = None
            try:
                seleccion = elegir()
            finally:
                # Guardar siempre, incluso si algo falla: si no, la segunda
                # petición de Chrome volvería a preguntar
                with open(CACHE, "w") as f:
                    f.write(seleccion or "")

    if seleccion is None:
        sys.exit(1)
    print(f"[SELECTION]/{seleccion}", flush=True)


if __name__ == "__main__":
    main()
