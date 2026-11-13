# Dotfiles Hyprland

Una configuración modular, profesional y altamente optimizada para el compositor **Hyprland** en Arch Linux. Este entorno está diseñado para maximizar la productividad con un flujo de trabajo fluido, estéticamente refinado y altamente personalizable.

![Hyprland](https://img.shields.io/badge/WM-Hyprland-blue)
![Arch Linux](https://img.shields.io/badge/OS-Arch_Linux-informational)
![Lua](https://img.shields.io/badge/Config-Lua-blueviolet)

## Características Principales

* **Arquitectura Modular:** Configuración desglosada en componentes lógicos (`hypr/conf/`) para facilitar el mantenimiento y la extensibilidad.
* **Integración con Lua:** Gestión avanzada de reglas, gestos y animaciones mediante scripts Lua.
* **Waybar Dinámica:** Widgets interactivos (media, calendarios, carruseles) impulsados por scripts en Python.
* **Automatización y Control:** Scripts robustos para gestión de energía (`systemd` services), temas claros/oscuros y gestión de monitores.
* **Estética y Seguridad:** Integración nativa con `swaync` para notificaciones y `hyprlock`/`hypridle` para una sesión segura.

## Estructura del Proyecto

```text
.
├── hypr/               # Configuración central (Hyprland, Idle, Lock)
│   ├── conf/           # Módulos: bindings, input, animaciones, temas
│   └── scripts/        # Automatización de sistemas (dpms, power, themes)
├── waybar/             # Barra de estado, widgets y temas (claro/oscuro)
├── swaync/             # Estilos y configuración de notificaciones
└── systemd/            # Servicios de automatización (ej. power-button)
```

## Guía de Inicio Rápido

### Requisitos previos
* Arch Linux con `hyprland`, `waybar`, `swaync`, `hypridle`, `hyprlock` y `hyprpaper`.
* Python 3 instalado para los scripts de widgets.

### Instalación
1. Clona el repositorio en tu carpeta de configuración:
   ```bash
   git clone <url-del-repositorio> ~/.config/hypr
   ```
2. Ejecuta el script de instalación para asegurar permisos y dependencias:
   ```bash
   cd ~/.config/hypr
   chmod +x install.sh
   ./install.sh
   ```
3. Reinicia tu sesión para aplicar los cambios.

## Scripts y Herramientas

* `hypr/scripts/`: Incluye utilidades para el manejo de DPMS, gestión de energía mediante `power_button.py` y selección de ventanas con `share_picker.py`.
* `waybar/scripts/`: Contiene la lógica de los widgets interactivos (media, display, calendar).
* `temas/`: Los directorios de `waybar` y `swaync` contienen subdirectorios de temas (`claro.css`, `oscuro.css`) para una personalización visual rápida.

## Soporte y Contribución

Para reportar problemas o sugerir mejoras, por favor utiliza el sistema de **Issues** del repositorio. Las contribuciones mediante **Pull Requests** son bienvenidas siempre que se mantenga la estructura modular establecida.

## Mantenimiento

Este proyecto es una configuración personal mantenida activamente. Se recomienda realizar una copia de seguridad de tu configuración existente antes de implementar este entorno. Para cualquier duda, consulta el historial de commits o abre un issue.