# Hyprland Dotfiles

Una configuración modular, profesional y altamente optimizada para **Hyprland** en Arch Linux. Este entorno está diseñado para maximizar la productividad y la estética, utilizando componentes configurables en Lua y scripts de automatización avanzados.

![Hyprland](https://img.shields.io/badge/WM-Hyprland-blue)
![Arch](https://img.shields.io/badge/OS-Arch_Linux-informational)
![Lua](https://img.shields.io/badge/Config-Lua-blueviolet)

## Características Principales
* **Arquitectura Modular:** Configuración dividida en componentes (`conf/`) para un mantenimiento limpio y escalable.
* **Integración Lua:** Implementación de archivos Lua para reglas, gestos e inputs, facilitando la personalización avanzada.
* **Waybar Dinámica:** Incluye múltiples paneles interactivos (calendario, media, reproductores) mediante scripts en Python.
* **Gestión de Sesión:** Herramientas integradas para bloqueo de pantalla (`hyprlock`), inactividad (`hypridle`) y selección de pantallas (`share_picker`).
* **Estética Coherente:** Estilos personalizados para `swaync` y Waybar para una experiencia de escritorio unificada.

## Estructura del Proyecto

```text
.
├── hypr/               # Configuración central de Hyprland
│   ├── conf/           # Módulos (bindings, animaciones, rules, etc.)
│   ├── scripts/        # Automatización (power, wallpaper, share)
│   ├── hyprland.lua    # Punto de entrada principal
│   └── hyprlock.conf   # Configuración de bloqueo
├── swaync/             # Notificaciones con estilo CSS
└── waybar/             # Barra de estado y widgets en Python
```

## Guía de Inicio Rápido

### Requisitos previos
* Hyprland, Waybar, Swaync, Hyprlock, Hypridle.
* Python 3 y librerías necesarias para los scripts de Waybar.

### Instalación
1. Clona el repositorio en tu configuración:
   ```bash
   git clone <url-del-repositorio> ~/.config/hypr
   ```
2. Asegúrate de otorgar permisos de ejecución a los scripts:
   ```bash
   chmod +x ~/.config/hypr/scripts/*.sh
   ```
3. Verifica que las rutas en `hyprland.lua` coincidan con tu entorno y reinicia la sesión.

## Scripts Incluidos
* `wallpaper_daemon.sh`: Ciclo automático de fondos de pantalla.
* `power_button.py`: Gestión del menú de apagado/reinicio.
* `share_picker.py`: Selección de ventanas/pantallas para compartir.
* `media_panel.py / calendar_panel.py`: Widgets interactivos para la Waybar.

## Soporte
Si encuentras algún problema o deseas proponer una mejora, abre un *Issue* en el repositorio. Asegúrate de incluir logs si el problema está relacionado con los scripts de Python.

## Mantenimiento y Contribución
Este proyecto es una configuración personal mantenida activamente. Las contribuciones mediante *Pull Requests* son bienvenidas siempre que mantengan la estructura modular del proyecto. Se recomienda validar la sintaxis Lua antes de enviar cambios en los archivos `.lua`.