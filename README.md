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

### Requisitos previos
* Hyprland (versión reciente recomendada)
* Waybar
* Swaync
* Python 3 y librerías necesarias para los paneles

### Instalación
1. Clona el repositorio en tu carpeta de configuración:
   ```bash
   git clone <url-del-repositorio> ~/.config/hypr
   ```
2. Asegúrate de otorgar permisos de ejecución a los scripts:
   ```bash
   chmod +x ~/.config/hypr/scripts/*.sh
   ```
3. Verifica que las dependencias de los scripts de Waybar estén instaladas y reinicia la sesión.

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