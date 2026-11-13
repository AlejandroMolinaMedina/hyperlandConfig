# Dotfiles Hyprland

Una configuración modular, profesional y altamente optimizada para el compositor **Hyprland** en Arch Linux. Este entorno está diseñado para maximizar la productividad con un flujo de trabajo fluido y estéticamente refinado.

![Hyprland](https://img.shields.io/badge/WM-Hyprland-blue)
![Arch Linux](https://img.shields.io/badge/OS-Arch_Linux-informational)
![Lua](https://img.shields.io/badge/Config-Lua-blueviolet)

## Características Principales

* **Arquitectura Modular:** Configuración desglosada en componentes lógicos (`conf/`) para facilitar el mantenimiento y la personalización.
* **Integración con Lua:** Uso de scripts en Lua para una gestión dinámica de reglas, gestos y animaciones.
* **Waybar Avanzada:** Módulos personalizados que incluyen paneles multimedia, carruseles y calendarios interactivos mediante scripts en Python.
* **Automatización Integral:** Scripts dedicados para la gestión de energía, fondos de pantalla dinámicos y utilidades de captura de pantalla.
* **Estética Cohesiva:** Integración con `swaync` para notificaciones estilizadas y `hyprlock`/`hypridle` para seguridad y gestión de sesión.

## Estructura del Proyecto

```text
.
├── hypr/               # Configuración central (Hyprland, Idle, Lock)
│   ├── conf/           # Módulos: bindings, input, animaciones, temas
│   └── scripts/        # Automatización de sistemas (dpms, shares, power)
├── waybar/             # Barra de estado y widgets interactivos
├── swaync/             # Estilos y configuración de notificaciones
```

## Guía de Inicio Rápido

### Instalación (Arch Linux)
En un Arch recién instalado, con tu usuario (no root):

```bash
git clone git@github.com:AlejandroMolinaMedina/hyperlandConfig.git ~/Documents/projects/hyperland
cd ~/Documents/projects/hyperland
./install.sh            # ./install.sh --simular para ver antes lo que hará
```

`install.sh` hace, por pasos (cada uno se puede saltar con `--sin-<paso>`):

1. **Paquetes:** Hyprland, hyprlock/hypridle/hyprpaper, swaync, rofi, PipeWire, GTK3 + gtk-layer-shell para los paneles, Evolution Data Server para el calendario, fuentes Nerd Font… y `waybar-git` del AUR (instala `yay` si falta).
2. **Enlaces:** `~/.config/hypr`, `waybar` y `swaync` apuntan a este repo; lo que hubiera se guarda como `<carpeta>.respaldo-<fecha>`.
3. **Servicios de usuario:** botón de encendido (`systemd/power-button.service`) y llavero de GNOME.
4. **Sistema:** logind ignora el botón de encendido y el usuario entra al grupo `input`.
5. **Plugin** [hypr-mission-control](https://github.com/AlejandroMolinaMedina/hypr-mission-control) (vista general con 3 dedos).

Se puede volver a ejecutar sin problema: lo que ya está hecho se salta. Al final indica lo que queda a mano (fondos de pantalla, configuración de rofi, cuentas del calendario).

## Scripts y Herramientas
El entorno potencia la experiencia mediante utilidades en `hypr/scripts/` y `waybar/scripts/`:
* `wallpaper_daemon.sh`: Ciclo automático de fondos de pantalla.
* `power_button.py`: Gestión avanzada de estados de energía.
* `media_panel.py` / `calendar_panel.py`: Widgets interactivos para la barra de estado.
* `share_picker.py`: Utilidad para la selección de ventanas en sesiones compartidas.

## Soporte y Contribución
Para reportar problemas o sugerir mejoras, utiliza el sistema de **Issues** del repositorio. Las contribuciones mediante **Pull Requests** son bienvenidas siempre que mantengan el estándar modular del proyecto.

## Mantenimiento
Este proyecto representa una configuración personal activa. Se recomienda encarecidamente realizar una copia de seguridad de tu configuración actual antes de reemplazarla.