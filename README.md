# Dotfiles Hyprland

Una configuración modular, profesional y altamente optimizada para el compositor **Hyprland** en Arch Linux. Este entorno está diseñado para maximizar la productividad con un flujo de trabajo fluido, estéticamente refinado y altamente personalizable mediante Lua.

![Hyprland](https://img.shields.io/badge/WM-Hyprland-blue)
![Arch Linux](https://img.shields.io/badge/OS-Arch_Linux-informational)
![Lua](https://img.shields.io/badge/Config-Lua-blueviolet)

## Características Principales

* **Arquitectura Modular:** Configuración desglosada en componentes lógicos (`hypr/conf/`) para facilitar el mantenimiento y la escalabilidad.
* **Integración Nativa con Lua:** Uso de scripts en Lua (`hyprland.lua`) para una gestión dinámica y potente de reglas, gestos y animaciones.
* **Waybar Dinámica:** Sistema de widgets avanzados que incluye paneles multimedia, carruseles y calendarios interactivos gestionados mediante Python.
* **Automatización Integral:** Scripts dedicados para la gestión de energía, fondos de pantalla dinámicos y utilidades de captura de pantalla.
* **Gestión de Temas:** Soporte para estilos claros y oscuros integrados tanto en `waybar` como en `swaync`.
* **Seguridad y Sesión:** Configuración completa de bloqueo de sesión (`hyprlock`) e inactividad (`hypridle`).

## Estructura del Proyecto

```text
.
├── hypr/               # Configuración central (Hyprland, Idle, Lock)
│   ├── conf/           # Módulos: bindings, input, animaciones, temas
│   └── scripts/        # Automatización de sistemas (dpms, wallpaper, power)
├── waybar/             # Barra de estado, widgets y temas (claro/oscuro)
├── swaync/             # Estilos y configuración de notificaciones
```

## Guía de Inicio Rápido

### Requisitos previos
* Hyprland (última versión estable)
* Waybar
* Swaync
* Python 3 (para los paneles interactivos)

### Instalación
1. Clona el repositorio en tu carpeta de configuración:
   ```bash
   git clone <url-del-repositorio> ~/.config/hypr
   ```
2. Asegúrate de otorgar permisos de ejecución a los scripts:
   ```bash
   chmod +x ~/.config/hypr/scripts/*.sh
   chmod +x ~/.config/waybar/scripts/*.py
   ```
3. Instala las dependencias necesarias de Python y reinicia tu sesión de Hyprland.

## Herramientas Incluidas
El entorno potencia la experiencia mediante utilidades personalizadas:
* `wallpaper_daemon.sh`: Ciclo automático de fondos de pantalla.
* `panels.py`: Gestión centralizada de widgets en Waybar.
* `share_picker.py`: Utilidad para selección de ventanas.
* `power_button.py`: Gestión avanzada de estados de energía (Suspend, Hibernate, Shutdown).

## Soporte y Contribución
Para reportar problemas o sugerir mejoras, utiliza el sistema de **Issues** del repositorio. Las contribuciones mediante **Pull Requests** son bienvenidas siempre que mantengan el estándar modular y la estructura actual del proyecto.

## Mantenimiento
Este proyecto representa una configuración personal activa. Se recomienda encarecidamente realizar una copia de seguridad de tu configuración actual (`~/.config/hypr`) antes de reemplazarla.