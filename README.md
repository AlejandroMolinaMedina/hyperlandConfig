# Dotfiles Hyprland

Una configuración modular, profesional y altamente optimizada para el compositor **Hyprland** en Arch Linux. Este entorno está diseñado para maximizar la productividad con un flujo de trabajo fluido, estéticamente refinado y altamente personalizable.

![Hyprland](https://img.shields.io/badge/WM-Hyprland-blue)
![Arch Linux](https://img.shields.io/badge/OS-Arch_Linux-informational)
![Lua](https://img.shields.io/badge/Config-Lua-blueviolet)

## Características Principales

* **Arquitectura Modular:** Configuración desglosada en componentes lógicos (`hypr/conf/`) para facilitar el mantenimiento y la extensibilidad.
* **Integración con Lua:** Gestión avanzada de reglas, gestos, monitores y animaciones mediante archivos Lua dedicados.
* **Waybar Dinámica:** Widgets interactivos (media, calendarios, carruseles) impulsados por scripts en Python.
* **Sistema de Tematización:** Soporte nativo para temas claros y oscuros tanto en `waybar` como en `swaync`.
* **Automatización:** Herramientas integradas para gestión de energía, fondos de pantalla dinámicos y captura de sesiones.

## Estructura del Proyecto

```text
.
├── hypr/               # Configuración central (Lua) y scripts
│   ├── conf/           # Módulos de configuración (reglas, bindings, etc.)
│   └── scripts/        # Automatización de sistemas
├── waybar/             # Barra de estado y widgets interactivos
│   └── temas/          # Variables de estilo (claro/oscuro)
├── swaync/             # Estilos y configuración de notificaciones
│   └── temas/          # Variables de estilo (claro/oscuro)
```

## Guía de Inicio Rápido

### Requisitos previos
* Arch Linux con **Hyprland** instalado.
* `waybar`, `swaync`, `hyprpaper`, `hypridle` y `hyprlock`.
* Python 3 instalado para los scripts de widgets.

### Instalación
1. Clona el repositorio en tu carpeta de configuración:
   ```bash
   git clone <url-del-repositorio> ~/.config/hypr
   ```
2. Asegúrate de otorgar permisos de ejecución a los scripts:
   ```bash
   chmod +x ~/.config/hypr/scripts/*.sh
   ```
3. Verifica las dependencias de los módulos de Waybar y reinicia la sesión de Hyprland.

## Scripts y Herramientas
El entorno incluye utilidades en `hypr/scripts/` y `waybar/scripts/`:
* `wallpaper_daemon.sh`: Ciclo automático de fondos de pantalla.
* `power_button.py`: Gestión avanzada de estados de energía.
* `panels.py` / `carousel.py`: Lógica para los widgets interactivos de la barra.
* `share_picker.py`: Utilidad para la selección de ventanas en entornos compartidos.

## Soporte y Contribución
Para reportar problemas o sugerir mejoras, utiliza el sistema de **Issues** del repositorio. Las contribuciones mediante **Pull Requests** son bienvenidas siempre que mantengan la modularidad y el estándar de configuración del proyecto.

## Mantenimiento
Este proyecto representa una configuración personal activa. Se recomienda realizar una copia de seguridad de tus archivos de configuración actuales en `~/.config/` antes de aplicar estos cambios.