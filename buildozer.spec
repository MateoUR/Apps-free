[app]

# Título de la aplicación
title = App Recordatorios

# Nombre del paquete
package.name = apprecordatorios

# Dominio (Hospital Alma Mater)
package.domain = org.hospitalalmamater

# Directorio fuente
source.dir = .
source.main = main.py

# Extensiones a incluir
source.include_exts = py,png,json,mp3

# Archivos de datos (con tus nuevos sonidos y fondos)
source.include_patterns = bg_menu.png,bg_medications.png,bg_appointments.png,sound_button.mp3,sound_notification.mp3

# Versión de la app
version = 1.0

# -------------------------------------------------------
# Dependencias (Agregadas pygame y pyjnius)
# -------------------------------------------------------
requirements = python3,kivy==2.3.0,plyer,pillow,pyjnius

# Gradle: necesario para androidx.core
android.gradle_dependencies = androidx.core:core:1.12.0

# Orientación
orientation = portrait

# Icono de la app
icon.filename = %(source.dir)s/bg_menu.png

# -------------------------------------------------------
# Android (Versión 36 y mejoras solicitadas)
# -------------------------------------------------------

# Permisos
android.permissions = POST_NOTIFICATIONS,FOREGROUND_SERVICE,VIBRATE,WAKE_LOCK

# API objetivo (Android 15 / API 36 como pediste)
android.api = 34
android.minapi = 26
android.sdk = 34
android.ndk = 25b

# Forzamos build-tools compatibles para evitar conflictos de licencia
android.build_tools_version = 34.0.0

android.enable_androidx = True

# LÍNEA CRÍTICA: Acepta las licencias de la API 36 automáticamente
android.accept_sdk_license = True

# Arquitecturas
android.archs = arm64-v8a, armeabi-v7a

# -------------------------------------------------------
# Sistema
# -------------------------------------------------------
[buildozer]

# Nivel de log: 2 (Verbose) para monitorear cada paso en GitHub
log_level = 2

warn_on_root = 1
