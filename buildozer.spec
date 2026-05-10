[app]

# Título de la aplicación
title = App Recordatorios

# Nombre del paquete
package.name = apprecordatorios

# Dominio
package.domain = org.MateoUR

# Directorio fuente
source.dir = .
source.main = main.py

# Extensiones a incluir (java para que empaquete BootReceiver)
source.include_exts = py,png,json,mp3,java

# Archivos de datos (incluye utils.py que importan main.py y service.py)
source.include_patterns = bg_menu.png,bg_medications.png,bg_appointments.png,sound_button.mp3,sound_notification.mp3,service.py,utils.py

# Versión de la app
version = 1.0

# -------------------------------------------------------
# Dependencias
# -------------------------------------------------------
requirements = python3,kivy==2.3.0,plyer,pillow,pyjnius

# Gradle: necesario para androidx.core (NotificationCompat)
android.gradle_dependencies = androidx.core:core:1.12.0

# Orientación
orientation = portrait

# Icono de la app
icon.filename = %(source.dir)s/bg_menu.png

# -------------------------------------------------------
# Android
# -------------------------------------------------------

# Permisos: alarmas exactas, segundo plano, arranque automático y notificaciones
android.permissions = POST_NOTIFICATIONS,FOREGROUND_SERVICE,VIBRATE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,SCHEDULE_EXACT_ALARM

# Servicio en segundo plano (foreground)
# service.py se ejecuta como Foreground Service y recibe las alarmas del AlarmManager
services = Recordatorio:service.py:foreground

# Incluir el código Java del BootReceiver
android.add_src = src

# Script de pre-construcción: modifica el AndroidManifest para añadir el BootReceiver
# y el foregroundServiceType requerido en Android 14+
android.pre_build = python3 pre_build.py

# API objetivo
android.api = 34
android.minapi = 26
android.sdk = 34
android.ndk = 25b

# Build tools
android.build_tools_version = 34.0.0

android.enable_androidx = True

# LÍNEA CRÍTICA: Acepta las licencias automáticamente
android.accept_sdk_license = True

# Arquitecturas
android.archs = arm64-v8a, armeabi-v7a

# -------------------------------------------------------
# Sistema
# -------------------------------------------------------
[buildozer]

# Nivel de log: 2 (Verbose)
log_level = 2

warn_on_root = 1
