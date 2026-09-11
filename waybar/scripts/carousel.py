#!/usr/bin/env python3
# ~/.config/waybar/scripts/carousel.py
#
# Carruseles automáticos para Waybar (módulos custom/carousel#<grupo>).
# Uso: carousel.py <grupo>   (grupos definidos en GROUPS; sin argumento rota todo)
# Cada grupo rota sus elementos cada ROTATE_EVERY segundos.
# Clic izquierdo (SIGUSR1): siguiente. Clic derecho (SIGUSR2): anterior.

import glob
import json
import os
import re
import signal
import subprocess
import sys
import time

ROTATE_EVERY = 4  # segundos que se muestra cada elemento

# Elementos de cada grupo, en el orden en que rotan
GROUPS = {
    "media": ["backlight", "volume"],
    "system": ["cpu", "memory", "network"],
}

# Mismos iconos que tenían los módulos de Waybar
ICON_CPU = "\U000F035B"
ICON_MEM = "\U000F061A"
ICON_WIFI = "\uF1EB"
ICON_ETH = "\U000F0200"
ICON_NET_OFF = "\U000F092F"
ICON_MUTED = "\U000F0581"
ICONS_VOLUME = ["\U000F057F", "\U000F0580", "\U000F057E"]
ICONS_BACKLIGHT = ["●", "◕", "◗", "◔", "○"]


def pick_icon(icons, percent):
    # Igual que Waybar: reparte 0-100 % entre los iconos disponibles
    return icons[max(0, min(len(icons) - 1, int(percent * len(icons) / 100)))]


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


# ============================================
# Fuentes de datos (devuelven None si no están disponibles)
# ============================================

class Cpu:
    def __init__(self):
        self.prev = self._sample()

    @staticmethod
    def _sample():
        with open("/proc/stat") as f:
            fields = [int(x) for x in f.readline().split()[1:]]
        idle = fields[3] + fields[4]  # idle + iowait
        return idle, sum(fields)

    def text(self):
        idle, total = self._sample()
        d_idle, d_total = idle - self.prev[0], total - self.prev[1]
        self.prev = (idle, total)
        usage = 0 if d_total <= 0 else round(100 * (1 - d_idle / d_total))
        return f"{ICON_CPU} : {usage}%"


def memory_text():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, value = line.split(":", 1)
            info[key] = int(value.split()[0])
    used = round(100 * (1 - info["MemAvailable"] / info["MemTotal"]))
    return f"{ICON_MEM} : {used}%"


def format_bits(bps):
    for unit in ("", "k", "M", "G"):
        if bps < 1000 or unit == "G":
            return f"{bps:.1f}{unit}b/s"
        bps /= 1000


class Network:
    def __init__(self):
        self.prev = None  # (interfaz, bytes recibidos, instante)

    @staticmethod
    def _default_interface():
        with open("/proc/net/route") as f:
            for line in f.readlines()[1:]:
                parts = line.split()
                if len(parts) > 1 and parts[1] == "00000000":
                    return parts[0]
        return None

    def text(self):
        iface = self._default_interface()
        if iface is None:
            self.prev = None
            return ICON_NET_OFF

        rx = read_int(f"/sys/class/net/{iface}/statistics/rx_bytes")
        now = time.monotonic()
        rate = 0.0
        if self.prev and self.prev[0] == iface and now > self.prev[2]:
            rate = max(0, rx - self.prev[1]) * 8 / (now - self.prev[2])
        self.prev = (iface, rx, now)

        icon = ICON_WIFI if os.path.isdir(f"/sys/class/net/{iface}/wireless") else ICON_ETH
        return f"{icon} : {format_bits(rate)}"


def pactl(*args):
    return subprocess.run(["pactl", *args], capture_output=True, text=True, timeout=2).stdout


def volume_text():
    try:
        volume = pactl("get-sink-volume", "@DEFAULT_SINK@")
        mute = pactl("get-sink-mute", "@DEFAULT_SINK@")
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"(\d+)%", volume)
    if not match:
        return None
    if "yes" in mute:
        return ICON_MUTED
    percent = int(match.group(1))
    return f"{pick_icon(ICONS_VOLUME, percent)} {percent}%"


def backlight_text():
    devices = sorted(glob.glob("/sys/class/backlight/*"))
    if not devices:
        return None
    current = read_int(f"{devices[0]}/brightness")
    maximum = read_int(f"{devices[0]}/max_brightness")
    percent = round(100 * current / maximum) if maximum else 0
    return f"{pick_icon(ICONS_BACKLIGHT, percent)} {percent}%"


# ============================================
# Bucle principal
# ============================================

def main():
    # Bloquear las señales para recogerlas con sigtimedwait (sin perder clics)
    signals = {signal.SIGUSR1, signal.SIGUSR2}
    signal.pthread_sigmask(signal.SIG_BLOCK, signals)

    group = sys.argv[1] if len(sys.argv) > 1 else None
    if group is not None and group not in GROUPS:
        sys.exit(f"Grupo desconocido: {group} (opciones: {', '.join(GROUPS)})")

    cpu, network = Cpu(), Network()
    sources = {
        "cpu": cpu.text,
        "memory": memory_text,
        "network": network.text,
        "volume": volume_text,
        "backlight": backlight_text,
    }
    names = GROUPS[group] if group else list(sources)
    items = [(name, sources[name]) for name in names]

    index, shown_for, flip = 0, 0, False
    while True:
        values = {}
        for name, source in items:
            try:
                values[name] = source()
            except (OSError, ValueError, KeyError):
                values[name] = None

        # Si el elemento actual no está disponible, pasar al siguiente que sí lo esté
        for _ in range(len(items)):
            if values[items[index][0]]:
                break
            index = (index + 1) % len(items)

        name = items[index][0]
        output = {
            "text": values[name] or "",
            "tooltip": "\n".join(v for v in values.values() if v),
            # Alternar a/b reinicia la animación CSS en cada cambio de elemento
            "class": [name, "a" if flip else "b"],
        }
        try:
            print(json.dumps(output, ensure_ascii=False), flush=True)
        except BrokenPipeError:
            sys.exit(0)

        received = signal.sigtimedwait(signals, 1)
        if received is None:
            shown_for += 1
            step = 1 if shown_for >= ROTATE_EVERY else 0
        else:
            step = 1 if received.si_signo == signal.SIGUSR1 else -1

        if step:
            index = (index + step) % len(items)
            shown_for = 0
            flip = not flip


if __name__ == "__main__":
    main()
