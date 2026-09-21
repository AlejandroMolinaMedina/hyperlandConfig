# Hyprland Dotfiles

Una configuración modular y optimizada para el gestor de ventanas **Hyprland**, diseñada para ofrecer una experiencia de escritorio Wayland fluida, estética y altamente personalizable.

![Hyprland](https://img.shields.io/badge/Hyprland-Window_Manager-blue)
![Wayland](https://img.shields.io/badge/Wayland-Compositor-green)
![Lua](https://img.shields.io/badge/Config-Lua-yellow)

## Características Principales

- **Arquitectura Modular:** Configuración dividida en módulos Lua para un mantenimiento sencillo y ordenado.
- **Waybar Dinámico:** Paneles y widgets interactivos que incluyen control de medios y calendarios.
- **Automatización:** Scripts integrados para la gestión de fondos de pantalla, botones de energía y control de DPMS.
- **Notificaciones Elegantes:** Integración con `swaync` para un centro de notificaciones minimalista.
- **Gestión Avanzada:** Soporte para `hypridle` y `hyprlock` para seguridad y ahorro de energía.

## Guía de Inicio Rápido

### Requisitos Previos
- Arch Linux o distribución compatible con Wayland.
- `hyprland`, `waybar`, `swaync`, `hypridle`, y `hyprlock` instalados.
- Un emulador de terminal (ej. `kitty` o `foot`).

### Instalación
1. Clona el repositorio en tu carpeta de configuración:
   ```bash
   git clone <url-del-repositorio> ~/.config/hypr
   ```
2. Asegúrate de tener los permisos de ejecución para los scripts:
   ```bash
   chmod +x ~/.config/hypr/scripts/*.sh
   ```
3. Reinicia tu sesión de Hyprland para aplicar los cambios.

## Estructura del Proyecto

```text
.
├── hypr/
│   ├── conf/            # Módulos de configuración (Lua)
│   ├── scripts/         # Scripts de automatización
│   ├── hyprland.lua     # Punto de entrada principal
│   └── hyprlock.conf    # Bloqueo de pantalla
├── swaync/              # Configuración de centro de notificaciones
└── waybar/              # Configuración y scripts de barra superior
```

## Soporte y Documentación

Si encuentras algún problema o deseas sugerir una mejora, por favor abre un **Issue** en el repositorio. Para consultas rápidas sobre el uso de los componentes, revisa los comentarios dentro de los archivos `.lua` y `.conf`.

## Mantenimiento y Contribución

Este proyecto es de código abierto. Si deseas contribuir:

1. Realiza un *fork* del repositorio.
2. Crea una rama para tus cambios.
3. Envía un *Pull Request* explicando las mejoras realizadas.

Consulta el archivo `LICENSE` para detalles sobre los términos de uso.