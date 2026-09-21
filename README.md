# Dotfiles Hyprland

Una configuración modular y optimizada para el gestor de ventanas **Hyprland**, diseñada para ofrecer un entorno de escritorio elegante, funcional y altamente personalizable en sistemas Arch Linux.

![Hyprland](https://img.shields.io/badge/WM-Hyprland-blue)
![Status](https://img.shields.io/badge/Arch-Linux-informational)

## Características Principales
* **Modularidad:** Configuración dividida en componentes lógicos (bindings, animaciones, reglas, temas) para un mantenimiento sencillo.
* **Waybar Dinámica:** Incluye scripts en Python para paneles avanzados, carruseles de medios y gestión de notificaciones.
* **Automatización:** Daemon de fondos de pantalla, gestión de energía y utilidades para compartir pantalla integradas.
* **Estética:** Configuración de `swaync` para notificaciones con estilo CSS personalizado.

## Estructura del Proyecto

```text
.
├── hypr/               # Configuración central de Hyprland
│   ├── conf/           # Módulos de configuración (input, bindings, etc.)
│   └── scripts/        # Automatización (daemon, energía, capturas)
├── swaync/             # Estilos y configuración del centro de notificaciones
└── waybar/             # Barra de estado y sus respectivos scripts
```

## Guía de Inicio Rápido

### Requisitos previos
* Hyprland
* Waybar
* Swaync
* Python 3 (para los scripts de Waybar y Hyprland)

### Instalación
1. Clona este repositorio en tu directorio de configuración local:
   ```bash
   git clone <url-del-repositorio> ~/.config/hypr
   ```
2. Asegúrate de que los scripts tengan permisos de ejecución:
   ```bash
   chmod +x ~/.config/hypr/scripts/*.sh
   ```
3. Reinicia tu sesión de Hyprland para aplicar los cambios.

## Scripts Incluidos
El entorno depende de varios scripts especializados ubicados en `hypr/scripts/` y `waybar/scripts/`:
* `wallpaper_daemon.sh`: Gestiona la rotación y aplicación de fondos.
* `power_button.py`: Maneja las acciones del botón de encendido.
* `carousel.py` / `media_panel.py`: Proporcionan widgets interactivos para la Waybar.

## Soporte y Contribución
Para reportar errores o sugerir nuevas configuraciones, por favor abre un *Issue* en el repositorio. Las contribuciones son bienvenidas mediante *Pull Requests*.

## Mantenimiento
Este proyecto se mantiene como una configuración personal optimizada. Se recomienda realizar una copia de seguridad de tu `hyprland.conf` existente antes de aplicar estos cambios.