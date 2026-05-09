[app]

# Título de tu aplicación
title = App Recordatorios Medicamentos y Citas

# Nombre del paquete
package.name = apprecordatorios

# Dominio
package.domain = org.MateoUR

# Directorio fuente
source.dir = .
source.main = main.py

# Extensiones a incluir (agregué json por si guardas datos ahí)
source.include_exts = py,png,json,mp3

# Archivos de datos específicos
source.include_patterns = bg_menu.png,bg_medications.png,bg_appointments.png

# Versión
version = 1.0

# -------------------------------------------------------
# Dependencias
# -------------------------------------------------------
requirements = python3,kivy==2.3.0,plyer,pillow

# Orientación
orientation = portrait

# -------------------------------------------------------
# Configuración de Android (CORREGIDA)
# -------------------------------------------------------

# Permisos
android.permissions = VIBRATE, RECEIVE_BOOT_COMPLETED, POST_NOTIFICATIONS

# Versiones de API y SDK (Fijadas para evitar errores de licencias)
android.api = 34
android.minapi = 26
android.ndk = 25b
android.build_tools_version = 34.0.0

# ESTA LÍNEA ES LA QUE ACEPTA LAS LICENCIAS AUTOMÁTICAMENTE
android.accept_sdk_license = True

# Arquitecturas modernas
android.archs = arm64-v8a, armeabi-v7a

# Salida de log detallada para ver progreso en GitHub Actions
log_level = 2

# -------------------------------------------------------
# Configuración del sistema Buildozer
# -------------------------------------------------------
[buildozer]
warn_on_root = 1
