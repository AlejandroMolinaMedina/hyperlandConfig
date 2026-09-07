import evdev
import subprocess
import sys

POWERMENU_SCRIPT = "/home/al3xmm14/.config/rofi/applets/bin/powermenu.sh"

def find_power_button_device():
    for path in evdev.list_devices():
        try:
            device = evdev.InputDevice(path)
            if "button" in device.name.lower():
                return device
        except Exception:
            continue
    return None

def monitor_power_button():
    device = find_power_button_device()
    if not device:
        sys.exit(1)

    try:
        device.grab()
        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY and event.code == evdev.ecodes.KEY_POWER and event.value == 1:
                subprocess.Popen(POWERMENU_SCRIPT, shell=True)
    except Exception:
        pass
    finally:
        device.ungrab()

if __name__ == "__main__":
    monitor_power_button()
